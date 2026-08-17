from bots.strategies.random_bot import RandomBot
from core.order import Side
import respx
import httpx
import asyncio


def test_get_trade_quantity_buy():
    
    #assert for without pending orders
    bot = RandomBot()
    starting_balance = bot.balance
    assert bot._get_trade_quantity(100.00, Side.BUY, "TSLA") == starting_balance / 100.00

    #assert for with pending orders
    bot.pending_orders.append({"id": "abc123", "price": 100.0, "quantity": 5, "side": "BUY", "symbol": "AAPL"})

    assert bot._get_trade_quantity(100.00, Side.BUY, "TSLA") == (starting_balance - 500) / 100.00


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
    starting_balance = bot.balance
    bot._update_state("TSLA", 5, Side.BUY, 100.00)

    assert bot.balance == starting_balance - 500.00
    assert bot.portfolio["TSLA"] == 5


def test_update_state_sell():
    bot = RandomBot()
    starting_balance = bot.balance
    bot.portfolio["TSLA"] = 5
    bot._update_state("TSLA", 3, Side.SELL, 100.00)

    assert bot.portfolio["TSLA"] == 2
    assert bot.balance == starting_balance + 300.00


def test_bot_portfolio_recovery(respx_mock):
    """Tests cancel_pending_orders() to ensure correct recovery of 
    portfolio upon full use of stocks owned"""
    
    bot = RandomBot()
    bot.portfolio["TSLA"] = 5
    bot.pending_orders.append({"id": "abc123", "price": 100.0, "quantity": 5, "side": "SELL", "symbol": "TSLA"})

    #precondition
    assert bot._get_trade_quantity(100.00, Side.SELL, "TSLA") == 0

    respx_mock.delete("http://127.0.0.1:8000/orders/abc123").return_value = httpx.Response(200, json={"message": "order cancelled"})
    
    result = asyncio.run(bot._cancel_pending_orders())

    #postcondition
    assert bot.pending_orders == []
    assert result[0] == "abc123"
