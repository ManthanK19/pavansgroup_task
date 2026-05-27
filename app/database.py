import os
from mysql.connector.pooling import MySQLConnectionPool
from dotenv import load_dotenv

load_dotenv()

pool = MySQLConnectionPool(
    pool_name="product_api_pool",
    pool_size=5,
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "product_api"),
)


def get_db():
    """Borrow a connection from the pool. The finally block returns it automatically."""
    conn = pool.get_connection()
    try:
        yield conn
    finally:
        conn.close()
