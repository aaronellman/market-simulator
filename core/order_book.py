from core.order import Order
from core.order import Side
from sortedcontainers import SortedDict
import uuid

class OrderBook:

    def __init__(self):
        self.bids = SortedDict(lambda price: -price) #order by price desc
        self.asks = SortedDict()
        self.lookup = {}
    
    def get_order_by_id(self, id: uuid.UUID):
        return self.lookup.get(id, None)
    
    def add_order(self, order: Order):
        self.lookup[order.id] = order

        if order.side == Side.BUY:
            self.bids.setdefault(order.price, []).append(order)
        else:
            self.asks.setdefault(order.price, []).append(order)

    def cancel_order(self, order: Order):
        del self.lookup[order.id]

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
    
    def format_price_levels(self, orders: SortedDict):
        result = []
        
        for price in orders:
            orders_at_price = orders[price]
            quantity_at_price = sum(order.quantity for order in orders_at_price)
            
            result.append({"price": price, "quantity": quantity_at_price})
            
        return result
