from core.order_book import OrderBook
from core.order import Order
from core.order import Side

def test_add_buy_order():
    order_book = OrderBook()

    price = 100.25

    order = Order(price=price,side=Side.BUY, quantity=100, symbol="TEST")

    order_book.add_order(order)

    assert order_book.bids[price][0] == order


def test_add_sell_order():
    order_book = OrderBook()

    price = 100.25

    order = Order(price=price,side=Side.SELL, quantity=100, symbol="TEST")

    order_book.add_order(order)

    assert order_book.asks[price][0] == order


def test_cancel_buy_order():
    order_book = OrderBook()

    price = 100.25

    order = Order(price=price,side=Side.BUY, quantity=100, symbol="TEST")

    order_book.add_order(order)
    order_book.cancel_order(order)

    assert price not in order_book.bids


def test_cancel_sell_order():
    order_book = OrderBook()

    price = 100.25

    order = Order(price=price,side=Side.SELL, quantity=100, symbol="TEST")

    order_book.add_order(order)
    order_book.cancel_order(order)

    assert price not in order_book.asks


def test_best_bid():
    order_book = OrderBook()

    order1 = Order(price=100.50, side=Side.BUY, quantity=100, symbol="TEST")
    order2 = Order(price=150.01, side=Side.BUY, quantity=100, symbol="TEST")
    order3 = Order(price=50.0, side=Side.BUY, quantity=100, symbol="TEST")

    order_book.add_order(order1)
    order_book.add_order(order2)
    order_book.add_order(order3)

    best_bid = order_book.best_bid()

    assert best_bid == 150.01


def test_best_ask():
    order_book = OrderBook()

    order1 = Order(price=100.50, side=Side.SELL, quantity=100, symbol="TEST")
    order2 = Order(price=150.01, side=Side.SELL, quantity=100, symbol="TEST")
    order3 = Order(price=50.0, side=Side.SELL, quantity=100, symbol="TEST")

    order_book.add_order(order1)
    order_book.add_order(order2)
    order_book.add_order(order3)

    best_ask = order_book.best_ask()

    assert best_ask == 50.0


def test_best_bid_empty():
    order_book = OrderBook()

    best_bid = order_book.best_bid()

    assert best_bid is None


def test_best_ask_empty():
    order_book = OrderBook()

    best_ask = order_book.best_ask()

    assert best_ask is None