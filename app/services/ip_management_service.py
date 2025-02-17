# app/services/ip_management_service.py
import ipaddress
from typing import Set, Optional
from config.config import Config
import json
import os

class IPManagementService:
    def __init__(self):
        self.ip_range = ipaddress.IPv4Network(Config.IP_RANGE)
        self.ip_storage_path = 'data/ip_assignments.json'
        self._used_ips = self._load_used_ips()

    def _load_used_ips(self) -> Set[str]:
        if os.path.exists(self.ip_storage_path):
            with open(self.ip_storage_path, 'r') as f:
                data = json.load(f)
                return set(data.get('used_ips', []))
        return {Config.SERVER_IP}

    def _save_used_ips(self):
        os.makedirs(os.path.dirname(self.ip_storage_path), exist_ok=True)
        with open(self.ip_storage_path, 'w') as f:
            json.dump({'used_ips': list(self._used_ips)}, f)

    def get_next_available_ip(self) -> Optional[str]:
        for ip in self.ip_range.hosts():
            ip_str = str(ip)
            if ip_str not in self._used_ips:
                self._used_ips.add(ip_str)
                self._save_used_ips()
                return ip_str
        return None

    def release_ip(self, ip: str):
        if ip in self._used_ips:
            self._used_ips.remove(ip)
            self._save_used_ips()

