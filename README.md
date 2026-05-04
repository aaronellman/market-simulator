# market-simulator

A simulated financial exchange engine built in Python. Features a limit order book with price-time priority matching, a REST API, and a configurable bot framework for stress testing at scale.

> **Status:** In active development - bot framework with active decision making and bot number choice for load testing.

---

## Features

- **Limit order book** - bids and asks maintained in price-time priority order using `SortedDict`
- **Matching engine** - partial fills supported, walks the book until the incoming order is fully filled or no match is possible
- **Multiple instruments** - each symbol maintains its own independent order book
- **REST API** - place orders, cancel orders, query the order book and trade history *(in progress)*
- **Bot framework** - configurable bots with pluggable strategies *(planned)*
- **Trade persistence** - full trade history stored in PostgreSQL *(planned)*
- **Load testing** - spin up N bots and observe throughput metrics in real time *(planned)*

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.13 |
| API | FastAPI |
| Database | PostgreSQL (Docker) |
| Validation | Pydantic |
| Concurrency | asyncio |
| Testing | pytest |

---

## Project Structure

```
market-simulator/
├── core/
│   ├── order.py            # Order dataclass, Side enum
│   ├── order_book.py       # OrderBook - manages bids and asks
│   └── matching_engine.py  # MatchingEngine - price-time priority matching
├── api/
│   ├── main.py             # FastAPI app entry point
│   └── routes.py           # Route definitions
├── bots/
│   ├── base.py             # Base Bot class with run loop
│   └── strategies/         # Bot strategy implementations
├── db/
│   └── repository.py       # PostgreSQL persistence layer
├── tests/
│   ├── test_order_book.py  # OrderBook unit tests
│   └── test_matching.py    # MatchingEngine unit tests
├── .env.example            # Required environment variables
├── docker-compose.yml      # PostgreSQL container
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.13+
- Docker

### Setup

```bash
# Clone the repository
git clone https://github.com/aaronellman/market-simulator
cd market-simulator

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Fill in your values in .env

# Start PostgreSQL
docker compose up -d

# Run the API
uvicorn api.main:app --reload
```

### Running Tests

```bash
pytest
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `POSTGRES_USER` | PostgreSQL username |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_DB` | Database name |
| `POSTGRES_HOST` | Database host (default: localhost) |
| `POSTGRES_PORT` | Database port (default: 5432) |

---

## How It Works

### Order Matching

When an order is placed it is matched against the opposite side of the book using price-time priority:

- A **buy order** matches against the lowest available ask, as long as the ask price is ≤ the bid price
- A **sell order** matches against the highest available bid, as long as the bid price is ≥ the ask price
- If an order is only partially filled, the remainder stays in the book
- If no match is possible, the order is added to the book and waits

### Order Book

- Bids are stored in a `SortedDict` ordered by price descending - highest bid first
- Asks are stored in a `SortedDict` ordered by price ascending - lowest ask first
- Each price level holds a list of orders in FIFO order for time priority

---

## Roadmap

- [ ] REST API endpoints
- [ ] PostgreSQL trade persistence
- [ ] Bot framework with random and market maker strategies
- [ ] Load testing script - spin up N bots, log throughput metrics
- [ ] Live leaderboard for bot performance