from order import Order
from order import Side
from sortedcontainers import SortedDict

class OrderBook:

    def __init__(self):
        self.bids = SortedDict(lambda price: -price) #order by price desc
        self.asks = SortedDict()
    
    def add_order(self, order: Order):
        if order.side == Side.BUY:
            self.bids.setdefault(order.price, []).append(order)
        else:
            self.asks.setdefault(order.price, []).append(order)

    def cancel_order(self, order: Order):
        if order.side == Side.BUY:
            bid_price = self.bids[order.price] 
            bid_price.remove(order)
            
            if len(bid_price) == 0:
                del self.bids[order.price]
        else:
            asks_price = self.asks[order.price] 
            asks_price.remove(order)
            
            if len(asks_price) == 0:
                del self.asks[order.price]
    
    def best_bid(self):
        if len(self.bids) == 0: 
            return None

        return self.bids.peekitem(0)[0]
    
    def best_ask(self):
        if len(self.asks) == 0: 
            return None

        return self.asks.peekitem(0)[0]