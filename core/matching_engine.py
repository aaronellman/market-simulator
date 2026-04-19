from order_book import OrderBook
from order import Order
from order import Side
from sortedcontainers import SortedDict
from typing import Callable

class MatchingEngine():
    
    def __init__(self,order_book: OrderBook):
        self.order_book = order_book

    def _match_order(self, order: Order, best_price_func: Callable[[], float | None], orders: SortedDict) -> bool:
        while order.quantity > 0:
            best_price = best_price_func()

            if not best_price:
                self.order_book.add_order(order)
                return False
            
            if order.side == Side.BUY:
                
                if best_price <= order.price:
                    opposing_order = orders[best_price][0]

                    if order.quantity >= opposing_order.quantity:
                
                        order.quantity -= opposing_order.quantity
                        self.order_book.cancel_order(opposing_order)
                    elif opposing_order.quantity > order.quantity:
                        
                        opposing_order.quantity -= order.quantity
                        break
                else:
                    self.order_book.add_order(order)
                    break
            else:
                
                if best_price >= order.price:
                    opposing_order = orders[best_price][0]

                    if order.quantity >= opposing_order.quantity:
                
                        order.quantity -= opposing_order.quantity
                        self.order_book.cancel_order(opposing_order)
                    elif opposing_order.quantity > order.quantity:
                        
                        opposing_order.quantity -= order.quantity
                        break
                else:
                    self.order_book.add_order(order)
                    break
        
        return True

    def match(self, order: Order):
        
        is_bid = True if order.side == Side.BUY else False

        if is_bid:
            opposing_orders = self.order_book.asks
            best_price = self.order_book.best_ask
        else:
            opposing_orders = self.order_book.bids
            best_price = self.order_book.best_bid

        self._match_order(order, best_price, opposing_orders)