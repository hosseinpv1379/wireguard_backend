# app/services/wireguard_service.py
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

    def create_peer(self) -> Optional[dict]:
        try:
            # Generate keys
            private_key = subprocess.check_output(['wg', 'genkey']).decode().strip()
            public_key = subprocess.check_output(
                ['echo', private_key, '|', 'wg', 'pubkey'], 
                shell=True
            ).decode().strip()

            # Get next available IP
            ip_address = self.ip_service.get_next_available_ip()
            if not ip_address:
                raise Exception("No available IPs")

            # Create peer configuration
            peer_config = self._generate_peer_config(public_key, ip_address)
            
            # Add to config file
            current_config = self._read_config()
            new_config = current_config + peer_config
            self._write_config(new_config)
            
            # Apply changes
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

    def _generate_peer_config(self, public_key: str, ip_address: str) -> str:
        return f'''
[Peer]
PublicKey = {public_key}
AllowedIPs = {ip_address}/32
'''

    def _generate_client_config(self, private_key: str, ip_address: str) -> str:
        return f'''
[Interface]
PrivateKey = {private_key}
Address = {ip_address}/24
DNS = 8.8.8.8

[Peer]
PublicKey = {Config.SERVER_PUBLIC_KEY}
Endpoint = {Config.SERVER_ENDPOINT}:{Config.SERVER_PORT}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
'''

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
            peer_pattern = re.compile(
                rf'\[Peer\].*?PublicKey = {public_key}.*?(?=\[Peer\]|\Z)',
                re.DOTALL
            )
            new_config = peer_pattern.sub('', config)
            self._write_config(new_config)
            
            # Release IP
            self.ip_service.release_ip(peer.ip_address)
            
            # Apply changes
            self._apply_changes()
            
            return True
            
        except Exception:
            return False

    def _apply_changes(self):
        subprocess.run(['systemctl', 'restart', f'wg-quick@{Config.WG_INTERFACE}'])

