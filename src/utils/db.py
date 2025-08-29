import psycopg2
import os

def get_db_connection(database: str = "srag_brasil"):
    url = os.getenv("POSTGRES_SERVER_URL") + database
    conn = psycopg2.connect(url)
    return conn
