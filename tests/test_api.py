
from fastapi.testclient import TestClient
from api.main import app
from core.order import Side
import pytest
from api.routes import get_matching_engines, SYMBOLS, repository, symbol_by_order_id
from core.matching_engine import MatchingEngine
from core.order_book import OrderBook

client = TestClient(app)
REPOSITORY = repository
ORDERS_URL = "/orders"


def test_matching_partitioned_by_symbol():
    try:
        query_params = {"price": 10.0, "quantity": 1, "side": Side.BUY.value, "symbol": "AAPL"}

        response = client.post(url=ORDERS_URL,json=query_params)
        assert response.status_code == 201

        data = response.json()
        aapl_matched = data["matched"]
        assert aapl_matched == []

        query_params.copy()
        query_params["side"] = Side.SELL.value
        query_params["symbol"] = "TSLA"
        response = client.post(url=ORDERS_URL,json=query_params)

        assert response.status_code == 201
        data = response.json()
        tsla_matched = data["matched"]

        assert tsla_matched == [] 
    finally:
        # reset the market
        pass

def test_create_resting_order():
    query_params = {"price": 10.0, "quantity": 1, "side": Side.BUY.value, "symbol": "AAPL"}
    response = client.post(url=ORDERS_URL,json=query_params)
    assert response.status_code == 201

    data = response.json()
    assert data["matched"] == []

def test_orderbook_resets_between_tests():
    query_params = {"symbol": "AAPL"}
    response = client.get(url="/orderbook", params=query_params)
    data = response.json()
    assert data["bids"] == []

def build_matching_engines(): 
    matching_engines = {}
    for symbol in SYMBOLS:
        order_book = OrderBook()
        matching_engines[symbol] = MatchingEngine(order_book, REPOSITORY)

    return matching_engines

@pytest.fixture(autouse=True)
def setup_market():
    #SETUP
    symbol_by_order_id.clear()
    matching_engines = build_matching_engines()
    app.dependency_overrides[get_matching_engines] = lambda : matching_engines

    yield
    
    #TEARDOWN
    app.dependency_overrides.clear()