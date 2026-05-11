from fastapi import FastAPI
from core.order import Order, Side
from api.routes import router, matching_engine, SYMBOLS
import logging
from contextlib import asynccontextmanager


logger = logging.getLogger()
logging.basicConfig()
logger.setLevel(logging.INFO)


def supply_market(quantity: int = 1000, price: float = 10):
    side = Side.SELL
    
    for symbol in SYMBOLS:

        order = Order(price, quantity, side, symbol)
        matching_engine.match(order)


@asynccontextmanager
async def lifespan(app: FastAPI):
    supply_market()
    logger.info("Market Supplied")

    yield
    

app = FastAPI(lifespan=lifespan)
app.include_router(router)