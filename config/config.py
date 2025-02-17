# config/config.py
import os

class Config:
    WG_CONFIG_PATH = '/etc/wireguard/wg0.conf'
    WG_INTERFACE = 'wg0'
    IP_RANGE = '10.0.0.0/24'
    SERVER_IP = '10.0.0.1'
    SERVER_PORT = 51820
    SERVER_PUBLIC_KEY = os.getenv('WG_SERVER_PUBLIC_KEY')
    SERVER_ENDPOINT = os.getenv('WG_SERVER_ENDPOINT')
