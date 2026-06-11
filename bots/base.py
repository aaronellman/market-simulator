from abc import ABC, abstractmethod
from httpx import AsyncClient
from core.order import Side
import uuid

class BaseBot(ABC):

    def __init__(self, balance: float = 10000.00, base_api_url: str = "http://127.0.0.1:8000", interval: int = 1):
        self.bot_id = str(uuid.uuid4())[:8]
        self.balance = balance
        self.portfolio: dict[str, float] = {}
        self.interval = interval
        self.pending_orders: list[dict] = []

        self.base_api_url = base_api_url
        self.orders_url = f"{self.base_api_url}/orders"
        self.symbols_url = f"{self.base_api_url}/symbols"
        self.order_book_url = f"{self.base_api_url}/orderbook"

    @abstractmethod
    def run(self):
        pass

    def _update_state(self, symbol: str, quantity: int, side: Side, price: float) -> None:
        if side == Side.BUY:
            self.portfolio[symbol] = self.portfolio.get(symbol, 0) + quantity
            self.balance = round(self.balance - price * quantity, 2)
        else:
            self.portfolio[symbol] = self.portfolio.get(symbol) - quantity
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
