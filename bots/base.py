from abc import ABC, abstractmethod
from time import sleep
from core.order import Side

class BaseBot(ABC):

    def __init__(self, balance: float = 100.0, interval: int = 100):
        self.balance = balance
        self.portfolio: dict[str, int] = {}
        self.interval = interval

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