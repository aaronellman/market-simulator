from fastapi import Depends, APIRouter
from pydantic import BaseModel
from core.order import Order, Side
from core.order_book import OrderBook
from core.matching_engine import MatchingEngine

router = APIRouter()

class OrderModel(BaseModel):
    price: float
    quantity: int
    side: Side
    symbol: str

order_book = OrderBook()
matching_engine = MatchingEngine(order_book)

def get_matching_engine():
    return matching_engine

@router.post("/orders")
def orders(order_data: OrderModel, matching_engine = Depends(get_matching_engine)):
    order = Order(**order_data.model_dump())
    result = matching_engine.match(order)
    
    return {"matched": result, "timestamp": order.timestamp}