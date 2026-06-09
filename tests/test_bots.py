from bots.strategies.random_bot import RandomBot
from core.order import Side


def test_get_trade_quantity_buy():
    
    #assert for without pending orders
    bot = RandomBot()
    assert bot._get_trade_quantity(100.00, Side.BUY, "TSLA") == 10.00

    #assert for with pending orders
    bot.pending_orders.append({"id": "abc123", "price": 100.0, "quantity": 5, "side": "BUY", "symbol": "AAPL"})

    assert bot._get_trade_quantity(100.00, Side.BUY, "TSLA") == 5.00


def test_get_trade_quantity_sell():
    bot = RandomBot()
    
    #assert for no portfolio
    assert bot._get_trade_quantity(100.00, Side.SELL, "TSLA") == 0
    
    #assert for without pending orders
    bot.portfolio["TSLA"] = 5
    assert bot._get_trade_quantity(100.00, Side.SELL, "TSLA") == 5

    #assert for with pending orders
    bot.pending_orders.append({"id": "abc123", "price": 100.0, "quantity": 3, "side": "SELL", "symbol": "TSLA"})

    assert bot._get_trade_quantity(100.00, Side.SELL, "TSLA") == 2


def test_get_trade_quantity_sell_with_pending_other_symbol():

    bot = RandomBot()
    bot.portfolio["TSLA"] = 5
    bot.portfolio["AAPL"] = 3

    #assert for with pending orders for different symbol
    bot.pending_orders.append({"id": "abc123", "price": 100.0, "quantity": 3, "side": "SELL", "symbol": "AAPL"})

    assert bot._get_trade_quantity(100.00, Side.SELL, "TSLA") == 5


def test_update_state_buy():
    bot = RandomBot()
    bot._update_state("TSLA", 5, Side.BUY, 100.00)

    assert bot.balance == 500.00
    assert bot.portfolio["TSLA"] == 5


def test_update_state_sell():
    bot = RandomBot()
    bot.portfolio["TSLA"] = 5
    bot._update_state("TSLA", 3, Side.SELL, 100.00)

    assert bot.portfolio["TSLA"] == 2
    assert bot.balance == 1300



