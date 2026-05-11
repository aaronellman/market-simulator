from bots.base import BaseBot
from httpx import AsyncClient
from random import choice, uniform
from core.order import Side
from asyncio import sleep


class RandomBot(BaseBot):
    """creates and starts up a bot that randomly picks a stock, and chooses whether to buy or sell it"""

    def __init__(self, balance: float = 1000.00, base_api_url: str = "http://127.0.0.1:8000", interval: int = 1):
        super().__init__(balance, base_api_url, interval)


    @staticmethod
    def _get_random_symbol(symbols: list[str]) -> str:
        return choice(symbols)
    
    @staticmethod
    def _add_price_noise(price):
        noise_multiplier = uniform(-0.05, 0.05)
        return round((1 + noise_multiplier) * price, 2)
    
    
    def _get_trade_quantity(self, price: float, side: Side, symbol):
        if side == Side.BUY:
            return self.balance // price 
        else:
            return self.portfolio.get(symbol, 0)
    

    def _get_random_price(self):
        return round(uniform(0.01, self.balance), 2)


    def _get_random_side(self):
        return choice(list(Side))
    

    async def run(self):
        async with AsyncClient() as client:
            while True:
                await sleep(self.interval)

                response = await client.get(self.symbols_url)
                symbols = response.json()
                symbol = self._get_random_symbol(symbols)

                if self.balance == 0 and self.portfolio.get(symbol) == 0:
                    continue
                
                prices = await client.get(self.order_book_url)
                asks = prices.json()["asks"]
                bids = prices.json()["bids"]

                ask_price = asks[0]["price"] if asks else None
                bid_price = bids[0]["price"] if bids else None

                if ask_price is None and bid_price is None:
                    price = self._get_random_price()
                    side = self._get_random_side()
                    quantity = self._get_trade_quantity(price, side, symbol)
                elif ask_price is None:
                    price = self._get_random_price()
                    side = Side.SELL
                    quantity = self._get_trade_quantity(price, side, symbol)
                elif bid_price is None:
                    price = self._get_random_price()
                    side = Side.BUY
                    quantity = self._get_trade_quantity(price, side, symbol)
                else:

                    if self.balance > 0 and self.portfolio.get(symbol) == 0: #have to buy, only balance
                        price = ask_price
                        side = Side.BUY
                        quantity = self._get_trade_quantity(price, side, symbol)
                    elif self.balance == 0: #have to sell, no balance
                        price = bid_price
                        side = Side.SELL
                        quantity = self._get_trade_quantity(price, side, symbol)
                    else:   #have to choose whether to buy or sell, have balance and stocks in portfolio
                        side = self._get_random_side()
                        price = ask_price if side == Side.BUY else bid_price
                        quantity = self._get_trade_quantity(price, side, symbol)

                if quantity == 0:
                    continue

                query_params = {"price": self._add_price_noise(price), "quantity": quantity, "side": side.value, "symbol": symbol}
                response = await client.post(self.orders_url, json=query_params)

                if response.json().get("matched") != []:
                    self._update_state(symbol, quantity, side, price)
                