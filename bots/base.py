from abc import ABC, abstractmethod
from time import sleep
from core.order import Side

class BaseBot(ABC):

    def __init__(self, balance: float = 1000.00, base_api_url: str = "http://127.0.0.1:8000", interval: int = 1):
        self.balance = balance
        self.portfolio: dict[str, int] = {}
        self.interval = interval

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
            self.balance -= price * quantity
        else:
            self.portfolio[symbol] = self.portfolio.get(symbol) - quantity
            self.balance += price * quantity