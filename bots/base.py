from abc import ABC, abstractmethod
from httpx import AsyncClient
from core.order import Side
import uuid

class BaseBot(ABC):

    def __init__(self, balance: float = 10000.00, base_api_url: str = "http://127.0.0.1:8000", interval: float = 1.0):
        self.bot_id = str(uuid.uuid4())[:8]
        self.balance = balance
        self.portfolio: dict[str, float] = {}
        self.interval = interval
        self.pending_orders: list[dict] = []

        self.base_api_url = base_api_url
        self.orders_url = f"{self.base_api_url}/orders"
        self.symbols_url = f"{self.base_api_url}/symbols"
        self.order_book_url = f"{self.base_api_url}/orderbook"
        self.trades_url = f"{self.base_api_url}/trades"

    @abstractmethod
    def run(self):
        pass

    def _update_state(self, symbol: str, quantity: int, side: Side, price: float) -> None:
        if side == Side.BUY:
            self.portfolio[symbol] = round(self.portfolio.get(symbol, 0) + quantity, 8)
            self.balance = round(self.balance - price * quantity, 2)
        else:
            self.portfolio[symbol] = round(self.portfolio.get(symbol) - quantity, 8)
            self.balance = round(self.balance + price * quantity, 2)

    async def _poll_orders(self):
        
        if not self.pending_orders:
            return

        async with AsyncClient() as client:
            response = await client.get(f"{self.orders_url}", params={"order_ids": [order["id"] for order in self.pending_orders]})
            data = response.json()
            order_dict = {order["id"]: order for order in data["orders"]}

            for order in self.pending_orders.copy():
                symbol = order.get("symbol")
                side = Side(order.get("side"))
                price = order.get("price")

                if order_dict.get(order["id"], None) == None:
                    self.pending_orders.remove(order)
                    
                    self._update_state(symbol, order.get("quantity"), side, price)
                else:
                    traded_amount = order["quantity"] - order_dict[order["id"]]["quantity"]
                    
                    if traded_amount > 0:
                        order["quantity"] = order["quantity"] - traded_amount
                        self._update_state(symbol, traded_amount, side, price)

    async def _cancel_pending_orders(self):
        
        if not self.pending_orders:
            return None
        
        orders_to_remove = []
        order_ids = [o["id"] for o in self.pending_orders]
        
        async with AsyncClient() as client:
            for id in order_ids:
                response = await client.delete(f"{self.orders_url}/{id}")
                
                if response.status_code == 200:
                    orders_to_remove.append(id)
            
            self.pending_orders = [o for o in self.pending_orders if o["id"] not in orders_to_remove]

            return orders_to_remove

    async def _place_order(self, client, price: float, quantity: float, side: Side, symbol: str):

        query_params = {"price": price, "quantity": quantity, "side": side.value, "symbol": symbol}
        response = await client.post(self.orders_url, json=query_params)

        data = response.json()
        order_id = data.get("order_id")
        trades_made = data.get("matched")

        order = query_params.copy()
        order["id"] = order_id

        if response.status_code == 201:
            quantity_traded = sum(trade["quantity"] for trade in trades_made)
            order["quantity"] = quantity - quantity_traded

            if data["matched"]:
                self._update_state(symbol, quantity_traded, side, price) 
            if quantity_traded < quantity:
                self.pending_orders.append(order)

    async def _get_last_price(self, client, symbol: str):

        response = await client.get(f"{self.trades_url}/last", params={"symbol": symbol})

        if response.status_code == 200:
            result = response.json()
            return result

        return None 