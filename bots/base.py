from abc import ABC, abstractmethod
from time import sleep

class BaseBot(ABC):

    def __init__(self, balance: float = 100.0, interval: int = 100):
        self.balance = balance
        self.portfolio: dict[str, int] = {}
        self.interval = interval

    @abstractmethod
    def run(self):
        pass