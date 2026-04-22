from core.order_book import OrderBook
from core.order import Order, Side
from core.matching_engine import MatchingEngine

def test_trade_created_bid_quantity_eqals_ask():
    order_book = OrderBook()
    matching_engine = MatchingEngine(order_book)

    quantity = 100
    bid_order = Order(price=100,side=Side.BUY, quantity=quantity, symbol="TEST")
    ask_order = Order(price=100,side=Side.SELL, quantity=quantity, symbol="TEST")

    order_book.add_order(ask_order)
    best_price = order_book.best_ask()

    result = matching_engine._match_order(bid_order, order_book.best_ask, order_book.asks)
    trade = result[0]

    assert result != []
    assert trade.quantity == quantity
    assert trade.buyer_order_id == bid_order.id
    assert trade.seller_order_id == ask_order.id
    assert trade.price == best_price
    assert trade.symbol == "TEST"