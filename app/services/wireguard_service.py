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
        config = Config()  # Create instance to access properties
        return f"""[Interface]
    PrivateKey = {private_key}
    Address = {ip_address}/24
    DNS = 8.8.8.8

    [Peer]
    PublicKey = {config.SERVER_PUBLIC_KEY}
    Endpoint = {Config.SERVER_ENDPOINT}:{Config.SERVER_PORT}
    AllowedIPs = 0.0.0.0/0
    PersistentKeepalive = 25"""

    def get_peer(self, public_key: str) -> Optional[Peer]:
        """دریافت اطلاعات یک peer با کلید عمومی"""
        try:
            # استفاده از دستور wg برای دریافت اطلاعات peer
            output = subprocess.check_output(
                ['wg', 'show', Config.WG_INTERFACE, 'peer', public_key],
                stderr=subprocess.PIPE
            ).decode()

            if output:
                # پردازش خروجی
                peer_data = {}
                for line in output.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        peer_data[key.strip()] = value.strip()

                # استخراج IP از AllowedIPs
                ip_address = None
                if 'allowed ips' in peer_data:
                    ip_addresses = peer_data['allowed ips'].split(',')
                    for ip in ip_addresses:
                        if ip.strip().startswith('10.66.66.'):
                            ip_address = ip.strip().split('/')[0]
                            break

                if ip_address:
                    return Peer(
                        public_key=public_key,
                        ip_address=ip_address,
                        last_handshake=datetime.fromtimestamp(int(peer_data.get('last handshake', 0))) if peer_data.get('last handshake', '0') != '0' else None,
                        transfer_rx=int(peer_data.get('transfer', '0').split('received,')[0].strip() or 0),
                        transfer_tx=int(peer_data.get('transfer', '0').split('received,')[1].strip().split('sent')[0].strip() or 0) if 'received,' in peer_data.get('transfer', '') else 0
                    )

            return None

        except subprocess.CalledProcessError:
            return None

    def get_all_peers(self) -> List[Peer]:
        """دریافت لیست تمام peerها"""
        try:
            # خواندن خروجی کامل wg
            output = subprocess.check_output(['wg', 'show', Config.WG_INTERFACE], stderr=subprocess.PIPE).decode()

            peers = []
            current_peer = None

            for line in output.split('\n'):
                if line.startswith('peer:'):
                    if current_peer:
                        peers.append(current_peer)
                    current_peer = {'public_key': line.split(':')[1].strip()}
                elif current_peer and ':' in line:
                    key, value = line.split(':', 1)
                    current_peer[key.strip()] = value.strip()

            if current_peer:
                peers.append(current_peer)

            # تبدیل دیکشنری‌ها به آبجکت‌های Peer
            result = []
            for peer_data in peers:
                ip_address = None
                if 'allowed ips' in peer_data:
                    ip_addresses = peer_data['allowed ips'].split(',')
                    for ip in ip_addresses:
                        if ip.strip().startswith('10.66.66.'):
                            ip_address = ip.strip().split('/')[0]
                            break

                if ip_address and 'public_key' in peer_data:
                    peer = Peer(
                        public_key=peer_data['public_key'],
                        ip_address=ip_address,
                        last_handshake=datetime.fromtimestamp(int(peer_data.get('last handshake', 0))) if peer_data.get('last handshake', '0') != '0' else None,
                        transfer_rx=int(peer_data.get('transfer', '0').split('received,')[0].strip() or 0),
                        transfer_tx=int(peer_data.get('transfer', '0').split('received,')[1].strip().split('sent')[0].strip() or 0) if 'received,' in peer_data.get('transfer', '') else 0
                    )
                    result.append(peer)

            return result

        except subprocess.CalledProcessError:
            return []



    def delete_peer(self, public_key: str) -> bool:
        """حذف یک peer"""
        try:
            # بررسی وجود peer
            peer = self.get_peer(public_key)
            if not peer:
                return False

            # حذف peer از وایرگارد
            subprocess.run(
                ['wg', 'set', Config.WG_INTERFACE, 'peer', public_key, 'remove'],
                check=True,
                stderr=subprocess.PIPE
            )

            # بروزرسانی فایل کانفیگ
            config = self._read_config()
            lines = config.split('\n')
            new_lines = []
            skip = False

            for line in lines:
                if line.strip().startswith('# BEGIN_PEER') and public_key in line:
                    skip = True
                    continue
                elif line.strip().startswith('# END_PEER') and public_key in line:
                    skip = False
                    continue
                elif not skip:
                    new_lines.append(line)

            new_config = '\n'.join(new_lines)
            self._write_config(new_config)

            # آزادسازی IP
            if peer.ip_address:
                self.ip_service.release_ip(peer.ip_address)

            return True

        except subprocess.CalledProcessError as e:
            print(f"Error deleting peer: {e.stderr.decode() if e.stderr else str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
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






