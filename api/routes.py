from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from core.order import Order, Side
from core.order_book import OrderBook
from core.matching_engine import MatchingEngine
from db.repository import Repository
import uuid
from datetime import datetime

SYMBOLS = {"AAPL", "TSLA", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "NFLX"}

router = APIRouter()


class OrderModel(BaseModel):
    price: float
    quantity: int
    side: Side
    symbol: str
    
    
    @field_validator("symbol")
    def validate_symbol(cls, v):
        if v in SYMBOLS:
            return v
        else:
            raise ValueError(f"Invalid Symbol {v} in order, use a symbol from GET /symbols")


class PriceLevelModel(BaseModel):
    price: float
    quantity: int


class OrderBookResponse(BaseModel):
    asks: list[PriceLevelModel]
    bids: list[PriceLevelModel]


class TradeResponse(BaseModel):
    symbol: str
    price: float 
    quantity: int 
    buyer_order_id: uuid.UUID 
    seller_order_id: uuid.UUID
    timestamp: datetime
    id: uuid.UUID


order_book = OrderBook()
repository = Repository()
matching_engine = MatchingEngine(order_book, repository)


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
def orderbook(matching_engine = Depends(get_matching_engine)):
    response = {}
    bids = matching_engine.order_book.bids
    asks = matching_engine.order_book.asks
    
    response["bids"] = matching_engine.order_book.format_price_levels(bids)
    response["asks"] = matching_engine.order_book.format_price_levels(asks)

    return response


@router.get("/trades", status_code=200, response_model=list[TradeResponse])
def trades(symbol: str | None = None, matching_engine = Depends(get_matching_engine)):

    try:
        result = matching_engine.repository.get_trades(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return result

@router.get("/symbols", status_code=200)
def symbols():
    return list(SYMBOLS)
