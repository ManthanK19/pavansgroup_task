import os
from mysql.connector.pooling import MySQLConnectionPool
from dotenv import load_dotenv

# Load the .env file into environment variables
load_dotenv()

# ─── Connection Pool ──────────────────────────────────────────────────────────
# Creates 5 persistent MySQL connections at startup.
# Each request BORROWS one and RETURNS it when done — no create/destroy per request.
# Think of it as a waiter pool: 5 waiters always ready, shared across all customers.
pool = MySQLConnectionPool(
    pool_name="product_api_pool",
    pool_size=5,
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "product_api"),
)


def get_db():
    """
    FastAPI dependency that borrows a connection from the pool per request.
    `yield` ensures the finally block always runs — returning the connection
    to the pool even if the request throws an error.
    Note: conn.close() here does NOT close the TCP connection —
    it just returns it to the pool for the next request.
    """
    conn = pool.get_connection()
    try:
        yield conn
    finally:
        conn.close()  # Returns to pool, does NOT drop the TCP connection
