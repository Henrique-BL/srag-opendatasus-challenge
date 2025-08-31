import psycopg2
import os

def get_db_connection(database: str = "srag_brasil"):
    url = os.getenv("POSTGRES_SERVER_URL") + database
    conn = psycopg2.connect(url)
    return conn

def verify_data_exists(cursor: psycopg2.extensions.cursor, table: str, 
                        columns: list[str],
                        value: str) -> bool:
    query = f"SELECT COUNT(*) FROM {table} WHERE {columns[0]} = '{value}'"
    for column in columns[1:]:
        query += f" AND {column} = '{value}'"
    cursor.execute(query)
    return cursor.fetchone()[0] > 0