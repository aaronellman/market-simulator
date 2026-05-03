from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass(slots=True)
class Trade:
    symbol: str
    price: float 
    quantity: int 
    buyer_order_id: uuid.UUID 
    seller_order_id: uuid.UUID
    timestamp: datetime = field(default_factory=datetime.now)
    id: uuid.UUID = field(default_factory=uuid.uuid4)