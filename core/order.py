from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid


class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass(order=True, slots=True)
class Order:
    price: float
    quantity: int #no fractional buy/sell orders
    side: Side
    symbol: str
    timestamp: datetime = field(default_factory=datetime.now)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
