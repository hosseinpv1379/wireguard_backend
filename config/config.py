import os

class Config:
    # WireGuard Interface Settings
    WG_CONFIG_PATH = '/etc/wireguard/wg0.conf'
    WG_INTERFACE = 'wg0'
    
    # Network Settings
    IP_RANGE = '10.66.66.0/24'
    SERVER_IP = '10.66.66.1'
    SERVER_PORT = 51820
    
    # Server Endpoint (Your server's public IP)
    SERVER_ENDPOINT = '176.119.203.43'  # Change this to your server's public IP
    
    # Server Keys
    SERVER_PRIVATE_KEY_PATH = '/etc/wireguard/private.key'
    SERVER_PUBLIC_KEY_PATH = '/etc/wireguard/public.key'
    
    @classmethod
    def get_server_public_key(cls):
        try:
            with open(cls.SERVER_PUBLIC_KEY_PATH, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            # اگر کلید وجود نداشت، کلیدهای جدید بسازیم
            import subprocess
            
            # ساخت کلید خصوصی
            private_key = subprocess.check_output(['wg', 'genkey']).decode().strip()
            with open(cls.SERVER_PRIVATE_KEY_PATH, 'w') as f:
                f.write(private_key)
            
            # ساخت کلید عمومی
            public_key = subprocess.check_output(['echo', private_key, '|', 'wg', 'pubkey'], 
                                              shell=True).decode().strip()
            with open(cls.SERVER_PUBLIC_KEY_PATH, 'w') as f:
                f.write(public_key)
            
            # تنظیم مجوزها
            subprocess.run(['chmod', '600', cls.SERVER_PRIVATE_KEY_PATH])
            subprocess.run(['chmod', '600', cls.SERVER_PUBLIC_KEY_PATH])
            
            return public_key
    
    @classmethod
    def get_server_private_key(cls):
        try:
            with open(cls.SERVER_PRIVATE_KEY_PATH, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return None
            
    # اطلاعات سرور را به صورت property در اختیار بقیه کلاس‌ها قرار می‌دهیم
    @property
    def SERVER_PUBLIC_KEY(self):
        return self.get_server_public_key()
