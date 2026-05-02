from dotenv import load_dotenv
import os
import psycopg2
import logging
from core.trade import Trade

logger = logging.getLogger(__name__)

class Repository:

    def __init__(self):
        load_dotenv()

        self.conn = psycopg2.connect(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            database=os.getenv("POSTGRES_DB")
        )

        self.cur = self.conn.cursor()
        logger.info("PostgreSQL connection is open")
        
    def save_trade(self, trade: Trade):
        sql = "INSERT INTO trades (symbol, price, quantity, buyer_order_id, seller_order_id) VALUES (%s, %s, %s, %s, %s)"
        values = (trade.symbol, trade.price, trade.quantity, trade.buyer_order_id, trade.seller_order_id)
        
        self.cur.execute(sql,values)
        self.conn.commit()