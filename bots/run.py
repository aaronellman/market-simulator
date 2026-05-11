from typer import Typer
from bots.strategies.random_bot import RandomBot
import asyncio
strategies = {"random": RandomBot}


app = Typer()


async def _run_bots(coroutines):
    await asyncio.gather(*coroutines)


@app.command("start-bots")
def start(count: int, strategy: str, interval: int = 1, starting_balance: float = 1000.00, base_api_url: str = "http://127.0.0.1:8000"):

    bot_instances = []

    bot_class = strategies.get(strategy, "")
        
    if bot_class == "":
        raise ValueError("Invalid bot class provided")
    
    for i in range(count):
        
        bot = bot_class(starting_balance, base_api_url, interval)
        bot_instances.append(bot)

    coroutines = [bot.run() for bot in bot_instances]
    asyncio.run(_run_bots(coroutines))

if __name__ == "__main__":
    app()