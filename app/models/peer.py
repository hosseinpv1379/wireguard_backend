# app/models/peer.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Peer:
    public_key: str
    ip_address: str
    created_at: datetime = datetime.now()
    last_handshake: datetime = None
    transfer_rx: int = 0
    transfer_tx: int = 0
    
    def to_dict(self):
        return {
            'public_key': self.public_key,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat(),
            'last_handshake': self.last_handshake.isoformat() if self.last_handshake else None,
            'transfer_rx': self.transfer_rx,
            'transfer_tx': self.transfer_tx
        }
