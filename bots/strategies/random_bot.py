from bots.base import BaseBot
from httpx import AsyncClient
from random import choice, uniform, betavariate
from core.order import Side
from asyncio import sleep


class RandomBot(BaseBot):
    """creates and starts up a bot that randomly picks a stock, and chooses whether to buy or sell it"""

    def __init__(self, balance: float = 10000.00, base_api_url: str = "http://127.0.0.1:8000", interval: float = 1.0):
        super().__init__(balance, base_api_url, interval)


    @staticmethod
    def _get_random_symbol(symbols: list[str]) -> str:
        return choice(symbols)
    
    
    @staticmethod
    def _add_price_noise(price, scale: float = 1.0):
        max_noise = abs(0.05 * scale) #scalar value to adjust noise range
        noise_multiplier = uniform(-1 * max_noise, max_noise)
        return round((1 + noise_multiplier) * price, 2)
    
    
    def _get_trade_quantity(self, price: float, side: Side, symbol):

        if side == Side.BUY:
            pending_buy_cost = sum(o["quantity"] * o["price"] for o in self.pending_orders if o["side"] == Side.BUY.value)
            tradeable_quantity = (self.balance - pending_buy_cost) / price
            return round(betavariate(2, 5) * tradeable_quantity, 8)
        else:
            pending_sell_qty = sum(o["quantity"] for o in self.pending_orders if o["side"] == Side.SELL.value and o["symbol"] == symbol)

            tradeable_quantity = self.portfolio.get(symbol, 0) - pending_sell_qty
            return round(betavariate(2, 5) * tradeable_quantity, 8)


    def _get_random_side(self):
        return choice(list(Side))
    

    async def run(self):
        async with AsyncClient() as client:
            while True:
                await sleep(self.interval)

                noise_scale: float = 1.0

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
                    price = await self._get_last_price(client, symbol)
                    side = self._get_random_side()
                    noise_scale = 4.0
                elif ask_price is None:
                    price = bid_price
                    side = Side.SELL
                elif bid_price is None:
                    price = ask_price
                    side = Side.BUY
                else:

                    if self.balance > 0 and self.portfolio.get(symbol) == 0: #have to buy, only balance
                        price = ask_price
                        side = Side.BUY
                    elif self.balance == 0: #have to sell, no balance
                        price = bid_price
                        side = Side.SELL
                    else:   #have to choose whether to buy or sell, have balance and stocks in portfolio
                        side = self._get_random_side()
                        price = ask_price if side == Side.BUY else bid_price

                price = self._add_price_noise(price, noise_scale)
                quantity = self._get_trade_quantity(price, side, symbol)

                if quantity == 0:

                    #polling to eliminate cancellation of past orders preventing missed fills
                    await self._poll_orders() 
                    await self._cancel_pending_orders()
                    continue

                await self._place_order(client, price, quantity, side, symbol)

                tnw = await self._get_total_net_worth(client)
                print(f"[{self.bot_id}] TNW: {tnw}")
                
                print(f"[{self.bot_id}] pending after: {self.pending_orders}")
                print(f"[{self.bot_id}] balance: {self.balance} portfolio: {self.portfolio}")

                await self._poll_orders()
                