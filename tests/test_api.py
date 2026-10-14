
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


def place_order(price: float, quantity: float, side: Side, symbol: str) -> dict:
    order_data = {"price": price, "quantity": quantity, "side": side.value, "symbol": symbol}
    response = client.post(url=ORDERS_URL, json=order_data)
    assert response.status_code == 201

    return response.json()


def create_trade(price: float, quantity: float, symbol: str) -> tuple[str, str]:
    buyer_order_id = place_order(price, quantity, Side.BUY, symbol)["order_id"]

    data = place_order(price, quantity, Side.SELL, symbol)
    assert data["matched"] != []

    return buyer_order_id, data["order_id"]


def test_matching_partitioned_by_symbol():
    data = place_order(10.0, 1, Side.BUY, "AAPL")
    assert data["matched"] == []

    data = place_order(10.0, 1, Side.SELL, "TSLA")
    assert data["matched"] == []


def test_order_without_match_rests():
    data = place_order(10.0, 1, Side.BUY, "AAPL")
    assert data["matched"] == []


def test_matched_order_returns_201():
    data = place_order(10.0, 1, Side.BUY, "AAPL")
    assert data["matched"] == []

    data = place_order(10.0, 1, Side.SELL, "AAPL")
    assert data["matched"] != []


def test_invalid_order():
    order_data = {"price": 10.0, "quantity": 1, "side": Side.BUY.value, "symbol": "INVALID"}
    response = client.post(url=ORDERS_URL, json=order_data)
    assert response.status_code == 422


def test_get_resting_order_by_id():
    id = place_order(10.0, 1, Side.BUY, "AAPL")["order_id"]

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
    id = place_order(10.0, 1, Side.BUY, "AAPL")["order_id"]

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
    place_order(10.0, 1, Side.BUY, "AAPL")
    place_order(1000.50, 23, Side.SELL, "TSLA")

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


def test_get_trades_returns_correct_values():
    buyer_order_id, seller_order_id = create_trade(10.0, 1, "AAPL")

    query_params = {"symbol": "AAPL"}
    response = client.get(url="/trades", params=query_params)
    assert response.status_code == 200
    data = response.json()
    matches = [trade for trade in data
               if trade["buyer_order_id"] == buyer_order_id and trade["seller_order_id"] == seller_order_id]
    assert len(matches) == 1

    trade = matches[0]
    assert trade["price"] == 10.0
    assert trade["quantity"] == 1
    assert trade["symbol"] == "AAPL"


def test_get_trades_symbol_filter():
    create_trade(2.2, 3, "AAPL")
    tsla_buyer_order_id, _ = create_trade(100.0, 2, "TSLA")

    query_params = {"symbol": "AAPL"}
    response = client.get(url="/trades", params=query_params)
    assert response.status_code == 200
    data = response.json()

    assert len(data) > 0
    assert all(trade["symbol"] == "AAPL" for trade in data)
    assert not any(trade["buyer_order_id"] == tsla_buyer_order_id for trade in data)


def test_get_trades_last_returns_correct_price_for_symbol():
    create_trade(10.0, 1, "AAPL")

    query_params = {"symbol": "AAPL"}
    response = client.get(url="/trades/last", params=query_params)
    assert response.status_code == 200
    price = response.json()
    assert price == 10.0


def test_get_symbols_returns_correct_list():
    response = client.get("/symbols")
    assert response.status_code == 200
    assert SYMBOLS == set(response.json())


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