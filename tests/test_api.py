
from fastapi.testclient import TestClient
from api.main import app
from core.order import Side

client = TestClient(app)
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
