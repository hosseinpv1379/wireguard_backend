import subprocess
from typing import List, Optional
import re
from datetime import datetime
from config.config import Config
from app.models.peer import Peer
from app.services.ip_management_service import IPManagementService

class WireguardService:
    def __init__(self):
        self.ip_service = IPManagementService()
        
    def _read_config(self) -> str:
        try:
            with open(Config.WG_CONFIG_PATH, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return ''

    def _write_config(self, content: str):
        with open(Config.WG_CONFIG_PATH, 'w') as f:
            f.write(content)

    def _generate_peer_config(self, public_key: str, ip_address: str) -> str:
        """تولید کانفیگ peer با فرمت صحیح"""
        return f"""# BEGIN_PEER {public_key}
[Peer]
PublicKey = {public_key}
AllowedIPs = {ip_address}/32
# END_PEER {public_key}
"""



    def _remove_existing_peer(self, config: str, ip_address: str) -> str:
        """حذف peer های تکراری از کانفیگ"""
        # حذف peer های با IP یکسان
        lines = config.split('\n')
        cleaned_lines = []
        skip = False
        
        for line in lines:
            if line.startswith('# BEGIN_PEER'):
                skip = False
            elif line.strip() == f'AllowedIPs = {ip_address}/32':
                skip = True
                continue
                
            if not skip:
                cleaned_lines.append(line)
                
        return '\n'.join(cleaned_lines)

    def _generate_client_config(self, private_key: str, ip_address: str) -> str:
        """تولید کانفیگ کلاینت"""
        return f"""[Interface]
PrivateKey = {private_key}
Address = {ip_address}/24
DNS = 8.8.8.8

[Peer]
PublicKey = {Config.SERVER_PUBLIC_KEY}
Endpoint = {Config.SERVER_ENDPOINT}:{Config.SERVER_PORT}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25"""

    def get_peer(self, public_key: str) -> Optional[Peer]:
        peers = self.get_all_peers()
        return next((peer for peer in peers if peer.public_key == public_key), None)

    def get_all_peers(self) -> List[Peer]:
        try:
            output = subprocess.check_output(['wg', 'show', Config.WG_INTERFACE, 'dump']).decode()
            peers = []
            
            for line in output.split('\n')[1:]:  # Skip first line (interface)
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 7:  # Make sure we have all required fields
                        peer = Peer(
                            public_key=parts[0],
                            ip_address=parts[3].split('/')[0],
                            last_handshake=datetime.fromtimestamp(int(parts[4])) if parts[4] != '0' else None,
                            transfer_rx=int(parts[5]),
                            transfer_tx=int(parts[6])
                        )
                        peers.append(peer)
                    
            return peers
            
        except subprocess.CalledProcessError:
            return []

    def delete_peer(self, public_key: str) -> bool:
        try:
            # Get peer's IP before removal
            peer = self.get_peer(public_key)
            if not peer:
                return False
                
            # Remove from WireGuard
            subprocess.run(['wg', 'set', Config.WG_INTERFACE, 'peer', public_key, 'remove'])
            
            # Remove from config file
            config = self._read_config()
            pattern = re.compile(
                rf'# BEGIN_PEER {public_key}.*?# END_PEER {public_key}\n?',
                re.DOTALL
            )
            new_config = pattern.sub('', config)
            self._write_config(new_config)
            
            # Release IP
            self.ip_service.release_ip(peer.ip_address)
            
            # Apply changes
            self._apply_changes()
            
            return True
            
        except Exception:
            return False

    def _apply_changes(self):
        """اعمال تغییرات روی سرویس وایرگارد"""
        subprocess.run(['systemctl', 'restart', f'wg-quick@{Config.WG_INTERFACE}'])
    def create_peer(self) -> Optional[dict]:
        try:
            # Generate private key properly
            process = subprocess.Popen(['wg', 'genkey'], stdout=subprocess.PIPE)
            private_key = process.stdout.read().decode('utf-8').strip()

            # Generate public key from private key
            process = subprocess.Popen(['wg', 'pubkey'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            public_key = process.communicate(input=private_key.encode())[0].decode('utf-8').strip()

            # Get next available IP
            ip_address = self.ip_service.get_next_available_ip()
            if not ip_address:
                raise Exception("No available IPs")

            # Generate peer config
            peer_config = f"""# BEGIN_PEER {public_key}
    [Peer]
    PublicKey = {public_key}
    AllowedIPs = {ip_address}/32
    # END_PEER {public_key}
    """
            # Read and update config
            current_config = self._read_config()
            if "[Interface]" in current_config:
                parts = current_config.split("# Peers will be added below this line")
                base_config = parts[0] + "# Peers will be added below this line\n\n"
                
                # Get existing peers part if any
                existing_peers = ""
                if len(parts) > 1:
                    existing_peers = parts[1]
                
                # Remove any duplicate peer configs
                if existing_peers:
                    existing_peers = self._remove_existing_peer(existing_peers, ip_address)
                
                # Combine all parts
                new_config = base_config + existing_peers + peer_config
            else:
                new_config = current_config + "\n" + peer_config

            # Write config and apply changes
            self._write_config(new_config)
            self._apply_changes()

            # Generate client config
            client_config = self._generate_client_config(private_key, ip_address)

            return {
                'public_key': public_key,
                'ip_address': ip_address,
                'client_config': client_config
            }

        except Exception as e:
            if 'ip_address' in locals():
                self.ip_service.release_ip(ip_address)
            raise
