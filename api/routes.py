from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel
from core.order import Order, Side
from core.order_book import OrderBook
from core.matching_engine import MatchingEngine
import uuid


router = APIRouter()


class OrderModel(BaseModel):
    price: float
    quantity: int
    side: Side
    symbol: str


class PriceLevelModel(BaseModel):
    price: float
    quantity: int


class OrderBookResponse(BaseModel):
    asks: list[PriceLevelModel]
    bids: list[PriceLevelModel]


order_book = OrderBook()
matching_engine = MatchingEngine(order_book)


def get_matching_engine():
    return matching_engine


@router.post("/orders", status_code=201)
def orders(order_data: OrderModel, matching_engine = Depends(get_matching_engine)):
    order = Order(**order_data.model_dump())
    
    try:
        result = matching_engine.match(order)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"matched": result, "timestamp": order.timestamp}


@router.delete("/orders/{order_id}", status_code=200)
def orders(order_id: uuid.UUID, matching_engine = Depends(get_matching_engine)):
    order = matching_engine.order_book.get_order_by_id(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    
    matching_engine.order_book.cancel_order(order)
    return {"message": "order cancelled"}


@router.get("/orderbook", status_code=200, response_model=OrderBookResponse)
def orders(matching_engine = Depends(get_matching_engine)):
    response = {}
    bids = matching_engine.order_book.bids
    asks = matching_engine.order_book.asks
    
    response["bids"] = matching_engine.order_book.format_price_levels(bids)
    response["asks"] = matching_engine.order_book.format_price_levels(asks)

    return response
