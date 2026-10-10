
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

def test_order_without_match_rests():
    query_params = {"price": 10.0, "quantity": 1, "side": Side.BUY.value, "symbol": "AAPL"}
    response = client.post(url=ORDERS_URL,json=query_params)
    assert response.status_code == 201

    data = response.json()
    assert data["matched"] == []

def test_matched_order_returns_201():
    query_params = {"price": 10.0, "quantity": 1, "side": Side.BUY.value, "symbol": "AAPL"}
    response = client.post(url=ORDERS_URL, json=query_params)
    data = response.json()
    assert response.status_code == 201 and data["matched"] == []

    query_params = {"price": 10.0, "quantity": 1, "side": Side.SELL.value, "symbol": "AAPL"}
    response = client.post(url=ORDERS_URL, json=query_params)
    data = response.json()
    assert response.status_code == 201 and data["matched"] != []

def test_invalid_order():
    query_params = {"price": 10.0, "quantity": 1, "side": Side.BUY.value, "symbol": "INVALID"}
    response = client.post(url=ORDERS_URL, json=query_params)
    data = response.json()
    assert response.status_code == 422

def test_get_resting_order_by_id():
    query_params = {"price": 10.0, "quantity": 1, "side": Side.BUY.value, "symbol": "AAPL"}
    response = client.post(url=ORDERS_URL, json=query_params)
    data = response.json()
    id = data["order_id"]
    assert response.status_code == 201

    response = client.get(url=ORDERS_URL, params={"order_ids": id})
    data = response.json()
    order = data["orders"][0]
    assert response.status_code == 200 and order["id"] == id

def test_unknown_order_id_is_handled():
    id = "efc77495-2c75-49f9-ab0a-975da0642f73"
    response = client.get(url=ORDERS_URL, params={"order_ids": id})
    data = response.json()
    assert response.status_code == 200 and data["orders"] == []

def test_delete_order():
    query_params = {"price": 10.0, "quantity": 1, "side": Side.BUY.value, "symbol": "AAPL"}
    response = client.post(url=ORDERS_URL, json=query_params)
    data = response.json()
    id = data["order_id"]
    assert response.status_code == 201

    response = client.delete(f"{ORDERS_URL}/{id}")
    assert response.status_code == 200

    response = client.get("/orderbook", params={"symbol": "AAPL"})
    assert response.status_code == 200
    data = response.json()
    assert data["bids"] == []

def test_delete_unknown_id_returns_404():
    id = "efc77495-2c75-49f9-ab0a-975da0642f73"
    response = client.delete(f"{ORDERS_URL}/{id}")
    assert response.status_code == 404

def test_orderbook_contains_correct_values():
    query_params = {"price": 10.0, "quantity": 1, "side": Side.BUY.value, "symbol": "AAPL"}
    response = client.post(url=ORDERS_URL, json=query_params)
    assert response.status_code == 201

    query_params = {"price": 1000.50, "quantity": 23, "side": Side.SELL.value, "symbol": "TSLA"}
    response = client.post(url=ORDERS_URL, json=query_params)
    assert response.status_code == 201

    response = client.get("/orderbook", params={"symbol": "AAPL"})
    assert response.status_code == 200
    data = response.json()
    assert data["bids"][0] == {"price": 10.0, "quantity": 1.0}

    response = client.get("/orderbook", params={"symbol": "TSLA"})
    assert response.status_code == 200
    data = response.json()
    assert data["asks"][0] == {"price": 1000.5, "quantity": 23.0}

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