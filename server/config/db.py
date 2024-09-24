import os
import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        database=os.environ['DB_DATABASE'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD']
    )
    return conn

# Create tables if they don't exist
def create_tables():
    commands = (
        """
        CREATE TABLE IF NOT EXISTS bots (
            id SERIAL PRIMARY KEY,
            team VARCHAR(1) NOT NULL,
            x FLOAT NOT NULL,
            y FLOAT NOT NULL,
            health FLOAT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS weapons (
            id SERIAL PRIMARY KEY,
            x FLOAT NOT NULL,
            y FLOAT NOT NULL,
            strength FLOAT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS barriers (
            id SERIAL PRIMARY KEY,
            x FLOAT NOT NULL,
            y FLOAT NOT NULL,
            width FLOAT NOT NULL,
            height FLOAT NOT NULL,
            durability FLOAT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL
        )
        """
    )
    conn = get_db_connection()
    cur = conn.cursor()
    for command in commands:
        cur.execute(command)
    cur.close()
    conn.commit()
    conn.close()