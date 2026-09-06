from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import pool
import logging
from core.trade import Trade

logger = logging.getLogger(__name__)

class Repository:


    def __init__(self):
        load_dotenv()

        self.conn_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=50,
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            database=os.getenv("POSTGRES_DB"),
            options='-c search_path=public'
        )

        logger.info("PostgreSQL connection is open")


    def save_trade(self, trade: Trade):
    
        try:
            conn = self.conn_pool.getconn()
            with conn:
                with conn.cursor() as cur:

                    sql = "INSERT INTO trades (id, symbol, price, quantity, buyer_order_id, seller_order_id, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)"

                    values = (str(trade.id), trade.symbol, trade.price, trade.quantity, str(trade.buyer_order_id), str(trade.seller_order_id), trade.timestamp)

                    cur.execute(sql,values)  

        except Exception as e: 

            logger.error(e)
            raise Exception(e)
        
        finally:
            if conn:
                self.conn_pool.putconn(conn)


    def get_trades(self, symbol: str | None) -> list[Trade]:
        
        try:
            conn = self.conn_pool.getconn()
            with conn:
                with conn.cursor() as cur:

                    sql = "SELECT * FROM trades"
                    
                    if symbol:
                        sql = "SELECT * FROM trades WHERE symbol = %s"
                        cur.execute(sql,(symbol,))
                    else:
                        cur.execute(sql)
        

                    rows = cur.fetchall()
        except Exception as e:

            logger.error(e)
            raise Exception(e)
        
        finally:
            if conn:
                self.conn_pool.putconn(conn)
        
        result = []

        for row in rows:
            trade = Trade(id=row[0], symbol=row[1], price=row[2], quantity=row[3], 
                          buyer_order_id=row[4], seller_order_id=row[5], timestamp=row[6])
            
            result.append(trade)
        
        return result
    
    
    def get_last_price(self, symbol: str) -> float | None:
        
        try:
            conn = self.conn_pool.getconn()
            with conn:
                with conn.cursor() as cur:

                    sql = "SELECT price FROM trades WHERE symbol = %s ORDER BY created_at DESC LIMIT 1"

                    cur.execute(sql, (symbol,))
                    result = cur.fetchone()

        except Exception as e:

            logger.error(e)
            raise Exception(e)
        
        finally:
            if conn:
                self.conn_pool.putconn(conn)
        
        return float(result[0]) if result else None
