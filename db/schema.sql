CREATE TABLE IF NOT EXISTS trades(
    id UUID PRIMARY KEY,
    symbol TEXT,
    price NUMERIC,
    quantity NUMERIC,
    buyer_order_id UUID NOT NULL,
    seller_order_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
)