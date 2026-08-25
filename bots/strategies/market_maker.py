from dataclasses import dataclass
from bots.base import BaseBot
from httpx import AsyncClient
from asyncio import sleep
import asyncio
from core.order import Side

@dataclass()
class MarketMakerConfig():
    spread: float = 0.005
    quote_quantity: int = 10
    ladder_levels: int = 3
    target_stock_ratio: float = 0.6
    adjustment_rate: float = 0.001


class MarketMaker(BaseBot):

    def __init__(self, balance: float = 10000.00, base_api_url: str = "http://127.0.0.1:8000", interval: int = 1, config: MarketMakerConfig = None):

        if config is None:
            config = MarketMakerConfig()

        self.config = config
        super().__init__(balance, base_api_url, interval)


    @staticmethod
    def _get_quantity_distribution(quantity) -> tuple:
            """Determines the distribution of the quantity for each ladder level given N total quantity"""

            #currently uses a 3:2:1 ratio from closest to furthest from mid
            unit = quantity / 6
            return (unit * 3, unit * 2, unit)

    def _get_trade_quantity(self, price: float, side: Side, symbol: str):
        if side == Side.BUY:
            pending_buy_cost = sum(o["quantity"] * o["price"] for o in self.pending_orders if o["side"] == Side.BUY.value)

            return round((self.balance - pending_buy_cost) / price, 8)
        else:
            pending_sell_qty = sum(o["quantity"] for o in self.pending_orders if o["side"] == Side.SELL.value and o["symbol"] == symbol)

            return round(self.portfolio.get(symbol, 0) - pending_sell_qty, 8)


    async def run(self):
        """
        we need to place more of the side that we have less of, so we use the target_stock_ratio and adjustment_rate to do so.
        1. place orders at each ladder level with the quote quantity(prices are calculated from mid + (spread)/2 and mid - (spread)/2)
        2. when an order gets filled, recompute mid and recalculate ladder levels for both sides
        3. rebalancing stocks can be done by increasing the rung increment amount on that side to decrease chance of getting a hit on that side untill the target_stock ratio is hit again, then we would set it back to the normal spread.
        """
        #temporarily using only one stock for simplicity for now
        SYMBOL = "TSLA"

        async with AsyncClient() as client:
            while True:
                await sleep(self.interval)

                prices = await client.get(self.order_book_url)
                asks = prices.json()["asks"]
                bids = prices.json()["bids"]
                
                ask_price = asks[0]["price"] if asks else None
                bid_price = bids[0]["price"] if bids else None
                mid = (bid_price + ask_price) / 2

                stock_value = self.portfolio.get(SYMBOL, 0) * mid
                current_stock_ratio = stock_value / (stock_value + self.balance)

                deviation = self.config.target_stock_ratio - current_stock_ratio
                skew = deviation * self.config.adjustment_rate

                # +0.5 makes rung 1 sit a half-spread from mid, so the innermost bid/ask gap equals exactly one spread;
                # each further rung (i) then steps out by one more full spread.
                bid_rungs = []
                ask_rungs = []
                if self.portfolio.get(SYMBOL, 0) > 0:
                    ask_rungs = [(1 + (i + 0.5) * self.config.spread + skew) * mid for i in range(self.config.ladder_levels)]

                if ask_price and self.balance >= ask_price:
                    bid_rungs = [(1 - (i + 0.5) * self.config.spread + skew) * mid for i in range(self.config.ladder_levels)]

                