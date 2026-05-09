from typer import Typer
from bots.strategies.random_bot import RandomBot
from asyncio import run, gather
strategies = {"random": RandomBot}

app = Typer()

@app.command("start-bots")
def start(count: int, strategy, interval: int = 1, starting_balance: float = 1000.00, base_api_url: str = "http://127.0.0.1:8000"):

    bot_instances = []

    bot_class = strategies.get(strategy, "")
        
    if bot_class == "":
        raise ValueError("Invalid bot class provided")
    
    for i in range(count):
        
        bot = bot_class(base_api_url, starting_balance, interval)
        bot_instances.append(bot)

    coroutines = [bot.run() for bot in bot_instances]
    run(gather(*coroutines))

if __name__ == "__main__":
    app()