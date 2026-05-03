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
        sql = "INSERT INTO trades (id, symbol, price, quantity, buyer_order_id, seller_order_id, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        values = (trade.id, trade.symbol, trade.price, trade.quantity, trade.buyer_order_id, trade.seller_order_id, trade.timestamp)
        
        self.cur.execute(sql,values)
        self.conn.commit()


    def get_trades(self, symbol: str | None) -> list[Trade]:
        sql = "SELECT * FROM trades"
        
        if symbol:
            sql = "SELECT * FROM trades WHERE symbol = %s"
            self.cur.execute(sql,(symbol,))
        else:
            self.cur.execute(sql)

        rows = self.cur.fetchall()
        result = []

        for row in rows:
            trade = Trade(id=row[0], symbol=row[1], price=row[2], quantity=row[3], 
                          buyer_order_id=row[4], seller_order_id=row[5], timestamp=row[6])
            
            result.append(trade)
        
        return result
            
