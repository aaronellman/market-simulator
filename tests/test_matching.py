from core.order_book import OrderBook
from core.order import Order
from core.order import Side
from core.matching_engine import MatchingEngine


def test_match_order_bid_quantity_greater_than_ask():
    order_book = OrderBook()
    matching_engine = MatchingEngine(order_book)

    price = 100.0

    bid_order = Order(price=price,side=Side.BUY, quantity=100, symbol="TEST")
    ask_order = Order(price=price,side=Side.SELL, quantity=80, symbol="TEST")

    order_book.add_order(ask_order)

    matching_engine._match_order(bid_order, order_book.best_ask, order_book.asks)

    assert price not in order_book.asks
    assert price in order_book.bids 
    assert bid_order.quantity == 20


def test_match_order_bid_quantity_less_than_ask():
    order_book = OrderBook()
    matching_engine = MatchingEngine(order_book)

    price = 100.0

    bid_order = Order(price=price,side=Side.BUY, quantity=80, symbol="TEST")
    ask_order = Order(price=price,side=Side.SELL, quantity=100, symbol="TEST")

    order_book.add_order(ask_order)

    matching_engine._match_order(bid_order, order_book.best_ask, order_book.asks)

    assert price in order_book.asks
    assert price not in order_book.bids 
    assert ask_order.quantity == 20


def test_match_order_bid_quantity_equals_ask():
    order_book = OrderBook()
    matching_engine = MatchingEngine(order_book)

    price = 100.0

    bid_order = Order(price=price,side=Side.BUY, quantity=100, symbol="TEST")
    ask_order = Order(price=price,side=Side.SELL, quantity=100, symbol="TEST")

    order_book.add_order(ask_order)

    matching_engine._match_order(bid_order, order_book.best_ask, order_book.asks)

    assert price not in order_book.asks
    assert price not in order_book.bids 


def test_match_order_no_match():
    order_book = OrderBook()
    matching_engine = MatchingEngine(order_book)

    bid_order = Order(price=80,side=Side.BUY, quantity=100, symbol="TEST")
    ask_order = Order(price=100,side=Side.SELL, quantity=100, symbol="TEST")

    order_book.add_order(ask_order)

    result = matching_engine._match_order(bid_order, order_book.best_ask, order_book.asks)

    assert result == []


def test_match_order_empty_book():
    order_book = OrderBook()
    matching_engine = MatchingEngine(order_book)

    price = 80

    bid_order = Order(price=price,side=Side.BUY, quantity=100, symbol="TEST")

    result = matching_engine._match_order(bid_order, order_book.best_ask, order_book.asks)

    assert result == []
    assert price in order_book.bids


def test_match_order_ask_quantity_equals_bid():
    order_book = OrderBook()
    matching_engine = MatchingEngine(order_book)

    price = 100.0

    bid_order = Order(price=price,side=Side.BUY, quantity=100, symbol="TEST")
    ask_order = Order(price=price,side=Side.SELL, quantity=100, symbol="TEST")

    order_book.add_order(bid_order)

    matching_engine._match_order(ask_order, order_book.best_bid, order_book.bids)

    assert price not in order_book.asks
    assert price not in order_book.bids 


def test_match_bid_equals_ask():
    order_book = OrderBook()
    matching_engine = MatchingEngine(order_book)

    price = 100.0

    bid_order = Order(price=price,side=Side.BUY, quantity=100, symbol="TEST")
    ask_order = Order(price=price,side=Side.SELL, quantity=100, symbol="TEST")

    order_book.add_order(ask_order)

    matching_engine.match(bid_order)

    assert price not in order_book.asks
    assert price not in order_book.bids 


def test_match_ask_equals_bid():
    order_book = OrderBook()
    matching_engine = MatchingEngine(order_book)

    price = 100.0

    bid_order = Order(price=price,side=Side.BUY, quantity=100, symbol="TEST")
    ask_order = Order(price=price,side=Side.SELL, quantity=100, symbol="TEST")

    order_book.add_order(bid_order)

    matching_engine.match(ask_order)

    assert price not in order_book.asks
    assert price not in order_book.bids 

