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

        #temporarily using only one stock for simplicity
        SYMBOL = "TSLA"


        async with AsyncClient() as client:
            while True:

                await sleep(self.interval)
                old_pending_orders = [order.copy() for order in self.pending_orders.copy()]
                await self._poll_orders()

                if old_pending_orders != self.pending_orders: 
                    await self._cancel_pending_orders()
                elif old_pending_orders == self.pending_orders and self.pending_orders != []:
                    continue
                    
                prices = await client.get(self.order_book_url)
                asks = prices.json()["asks"]
                bids = prices.json()["bids"]
                
                ask_price = asks[0]["price"] if asks else None
                bid_price = bids[0]["price"] if bids else None

                if ask_price is None or bid_price is None:
                    continue 

                mid = (bid_price + ask_price) / 2

                stock_value = self.portfolio.get(SYMBOL, 0) * mid
                current_stock_ratio = stock_value / (stock_value + self.balance)

                deviation = self.config.target_stock_ratio - current_stock_ratio
                skew = deviation * self.config.adjustment_rate

                # +0.5 makes rung 1 sit a half-spread from mid, so the innermost bid/ask gap equals exactly one spread
                # each further rung (i) then steps out by one more full spread.
                bid_rungs = []
                ask_rungs = []
                if self.portfolio.get(SYMBOL, 0) > 0:
                    ask_rungs = [(1 + (i + 0.5) * self.config.spread + skew) * mid for i in range(self.config.ladder_levels)]

                if self.balance >= ask_price:
                    bid_rungs = [(1 - (i + 0.5) * self.config.spread + skew) * mid for i in range(self.config.ladder_levels)]

                #trade distribution calculation for asks
                trade_quantity = self._get_trade_quantity(mid, Side.SELL, SYMBOL)
                sell_quantities = self._get_quantity_distribution(trade_quantity)
                ask_orders = []
                for ask in zip(ask_rungs, sell_quantities):
                    price = ask[0]
                    qty = ask[1]
                    if qty <= 0:
                        break
                    ask_orders.append(self._place_order(client, price, qty, Side.SELL, SYMBOL))

                await asyncio.gather(*ask_orders)

                #bids
                bid_targets = self._get_quantity_distribution(self.config.quote_quantity * self.config.ladder_levels)

                #getting tradeable amounts at each price on first come, first serve basis
                for bid in zip(bid_rungs, bid_targets):
                    price = bid[0]
                    target = bid[1]
                    affordable = self._get_trade_quantity(price, Side.BUY, SYMBOL)
                    if affordable <= 0:
                        break
                    qty = min(target, affordable)
                    await self._place_order(client, price, qty, Side.BUY, SYMBOL) #placing orders after one another because each subsuquent one relies on the balance that the previous one leaves over

                tnw = await self._get_total_net_worth(client)
                print(f"[{self.bot_id}] TNW: {tnw}")

                print(f"[{self.bot_id}] pending after: {self.pending_orders}")
                print(f"[{self.bot_id}] balance: {self.balance} portfolio: {self.portfolio}")