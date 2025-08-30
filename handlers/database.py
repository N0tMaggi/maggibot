
import os
import sqlite3
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_TYPE = os.getenv("DB_TYPE", "json")


def get_db_connection():
    if DB_TYPE == "mysql":
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
    elif DB_TYPE == "sqlite":
        return sqlite3.connect(os.getenv("DB_NAME", "data/mac.db"))
    return None


def create_mac_bans_table():
    conn = get_db_connection()
    if conn is None:
        return

    cursor = conn.cursor()
    if DB_TYPE == "mysql":
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mac_bans (
                id BIGINT PRIMARY KEY,
                name VARCHAR(255),
                bandate VARCHAR(255),
                reason TEXT,
                serverid BIGINT,
                servername VARCHAR(255),
                bannedby VARCHAR(255)
            )
            """
        )
    elif DB_TYPE == "sqlite":
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mac_bans (
                id INTEGER PRIMARY KEY,
                name TEXT,
                bandate TEXT,
                reason TEXT,
                serverid INTEGER,
                servername TEXT,
                bannedby TEXT
            )
            """
        )
    conn.commit()
    conn.close()


def create_mac_bypass_table():
    conn = get_db_connection()
    if conn is None:
        return

    cursor = conn.cursor()
    if DB_TYPE == "mysql":
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mac_bypass (
                user_id BIGINT,
                server_id BIGINT,
                PRIMARY KEY (user_id, server_id)
            )
            """
        )
    elif DB_TYPE == "sqlite":
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mac_bypass (
                user_id INTEGER,
                server_id INTEGER,
                PRIMARY KEY (user_id, server_id)
            )
            """
        )
    conn.commit()
    conn.close()


create_mac_bans_table()
create_mac_bypass_table()
