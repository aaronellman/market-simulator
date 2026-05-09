from bots.base import BaseBot
from httpx import AsyncClient
from random import choice, uniform
from core.order import Side
from asyncio import sleep


class RandomBot(BaseBot):
    """creates and starts up a bot that randomly picks a stock, and chooses whether to buy or sell it"""

    def __init__(self):
        super().__init__()


    @staticmethod
    def _get_random_symbol(symbols: list[str]) -> str:
        return choice(symbols)
    
    
    def _get_trade_quantity(self, price: float, side: Side, symbol):
        if side == Side.BUY:
            return self.balance // price 
        else:
            return self.portfolio.get(symbol, 0)
    

    def _get_random_price(self):
        return round(uniform(0.01, self.balance))


    def _get_random_side(self):
        return choice(list(Side))
    

    async def run(self):
        async with AsyncClient() as client:
            while True:

                response = await client.get(self.symbols_url)
                symbols = response.json()
                symbol = self._get_random_symbol(symbols)

                if self.balance == 0 and self.portfolio.get(symbol) == 0:
                    continue
                
                prices = await client.get(self.order_book_url)
                asks = prices.json()["asks"]
                bids = prices.json()["bids"]

                if not asks and not bids:
                    price = self._get_random_price()
                    side = self._get_random_side()
                    quantity = self._get_trade_quantity(price, side, symbol)

                    query_params = {"price": price, "quantity": quantity, "side": side.value, "symbol": symbol}
                    response = await client.post(self.orders_url, json=query_params)
                    #add _update_state() method here
                    await sleep(self.interval)
                    continue
                else:
                    ask_price = asks[0]["price"]
                    bid_price = bids[0]["price"]

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

                query_params = {"price": price, "quantity": quantity, "side": side.value, "symbol": symbol}
                response = await client.post(self.orders_url, json=query_params)
                #add _update_state() method here

                await sleep(self.interval)
                