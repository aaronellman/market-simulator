from fastapi import FastAPI
from core.order_book import OrderBook
from core.matching_engine import MatchingEngine
from api.routes import router
import logging

logging.getLogger().setLevel(logging.INFO)

app = FastAPI()
app.include_router(router)