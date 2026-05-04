from core.order_book import OrderBook
from core.order import Order
from core.order import Side
from core.trade import Trade
from sortedcontainers import SortedDict
from typing import Callable
from db.repository import Repository

class MatchingEngine():
    
    def __init__(self,order_book: OrderBook, repository: Repository):
        self.order_book = order_book
        self.repository = repository

    def _match_order(self, order: Order, best_price_func: Callable[[], float | None], orders: SortedDict) -> list[Trade]:
        trades = []

        while order.quantity > 0:
            best_price = best_price_func()

            if not best_price:
                self.order_book.add_order(order)
                return []
            
            if order.side == Side.BUY:
                
                if best_price <= order.price:
                    opposing_order = orders[best_price][0]
                    
                    trade_quantity = min(order.quantity, opposing_order.quantity)
                    order.quantity -= trade_quantity
                    opposing_order.quantity -= trade_quantity 
                    
                    if opposing_order.quantity == 0:
                        self.order_book.cancel_order(opposing_order)

                    trade = Trade(order.symbol, best_price, trade_quantity, order.id, opposing_order.id)
                    trades.append(trade)
                else:
                    self.order_book.add_order(order)
                    return [] 
            else:
                
                if best_price >= order.price:
                    opposing_order = orders[best_price][0]
                    
                    trade_quantity = min(order.quantity, opposing_order.quantity)
                    order.quantity -= trade_quantity
                    opposing_order.quantity -= trade_quantity

                    if opposing_order.quantity == 0:
                        self.order_book.cancel_order(opposing_order)

                    trade = Trade(order.symbol, best_price, trade_quantity, opposing_order.id, order.id)
                    trades.append(trade)
                else:
                    self.order_book.add_order(order)
                    return []  
                
        return trades

    def match(self, order: Order):
        
        is_bid = True if order.side == Side.BUY else False

        if is_bid:
            opposing_orders = self.order_book.asks
            best_price = self.order_book.best_ask
        else:
            opposing_orders = self.order_book.bids
            best_price = self.order_book.best_bid
        
        trades_made = self._match_order(order, best_price, opposing_orders)

        for trade in trades_made:
            self.repository.save_trade(trade)

        return trades_made