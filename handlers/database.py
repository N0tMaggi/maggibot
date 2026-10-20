# -*- coding: utf-8 -*-
"""
Unified Pluggable Database & Storage Handler for MaggiBot
Supports JSON, SQLite, MySQL, PostgreSQL, and MongoDB backends based on .env
"""

import os
import json
import sqlite3
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from handlers.debug import LogError, LogSystem, LogDebug

load_dotenv()

DB_TYPE = os.getenv("DB_TYPE", "json").lower().strip()
SQLITE_PATH = os.getenv("SQLITE_PATH", "data/maggibot.db")
JSON_DATA_DIR = "data"
JSON_CONFIG_DIR = "config"


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Backend Connector
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.backend = DB_TYPE
        self._init_backend()
        self._initialized = True

    def _init_backend(self):
        os.makedirs(JSON_DATA_DIR, exist_ok=True)
        os.makedirs(JSON_CONFIG_DIR, exist_ok=True)

        if self.backend == "sqlite":
            os.makedirs(os.path.dirname(SQLITE_PATH) if os.path.dirname(SQLITE_PATH) else ".", exist_ok=True)
            self._init_sqlite_tables()
            LogSystem("Initialized SQLite Database backend.")
        elif self.backend == "mysql":
            try:
                import mysql.connector
                conn = self._get_mysql_connection()
                if conn:
                    self._init_mysql_tables(conn)
                    conn.close()
                    LogSystem("Connected & Initialized MySQL Database backend.")
                else:
                    LogDebug("MySQL connection failed, falling back to SQLite.")
                    self.backend = "sqlite"
                    self._init_sqlite_tables()
            except ImportError:
                LogDebug("mysql-connector-python not found. Falling back to SQLite.")
                self.backend = "sqlite"
                self._init_sqlite_tables()
            except Exception as e:
                LogError(f"MySQL initialization failed: {e}. Falling back to SQLite.")
                self.backend = "sqlite"
                self._init_sqlite_tables()
        elif self.backend in ("postgres", "postgresql"):
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    port=int(os.getenv("DB_PORT", 5432)),
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", ""),
                    dbname=os.getenv("DB_NAME", "maggibot"),
                )
                self._init_postgres_tables(conn)
                conn.close()
                LogSystem("Connected & Initialized PostgreSQL Database backend.")
            except Exception as e:
                LogError(f"PostgreSQL initialization failed: {e}. Falling back to SQLite.")
                self.backend = "sqlite"
                self._init_sqlite_tables()
        elif self.backend in ("mongo", "mongodb"):
            try:
                import pymongo
                mongo_uri = os.getenv("MONGO_URI", f"mongodb://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', 27017)}/{os.getenv('DB_NAME', 'maggibot')}")
                self.mongo_client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                self.mongo_db = self.mongo_client[os.getenv("DB_NAME", "maggibot")]
                self.mongo_client.server_info()
                LogSystem("Connected & Initialized MongoDB backend.")
            except Exception as e:
                LogError(f"MongoDB initialization failed: {e}. Falling back to JSON backend.")
                self.backend = "json"
        else:
            self.backend = "json"
            LogSystem("Using JSON file-based storage backend.")

    def _get_mysql_connection(self):
        import mysql.connector
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "maggibot"),
        )

    def _get_sqlite_connection(self):
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite_tables(self):
        with self._get_sqlite_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS guild_configs (
                    guild_id TEXT PRIMARY KEY,
                    config_data TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mac_bans (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    bandate TEXT,
                    reason TEXT,
                    serverid INTEGER,
                    servername TEXT,
                    bannedby TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mac_bypass (
                    user_id INTEGER,
                    server_id INTEGER,
                    PRIMARY KEY (user_id, server_id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    guild_id TEXT,
                    user_id TEXT,
                    xp REAL DEFAULT 0,
                    level INTEGER DEFAULT 0,
                    messages INTEGER DEFAULT 0,
                    voice_seconds INTEGER DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    guild_id TEXT,
                    name TEXT,
                    content TEXT,
                    author_id TEXT,
                    created_at TEXT,
                    PRIMARY KEY (guild_id, name)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tempbans (
                    guild_id TEXT,
                    user_id TEXT,
                    unban_at TEXT,
                    reason TEXT,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            conn.commit()

    def _init_mysql_tables(self, conn):
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS guild_configs (
                guild_id VARCHAR(64) PRIMARY KEY,
                config_data JSON NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mac_bans (
                id BIGINT PRIMARY KEY,
                name VARCHAR(255),
                bandate VARCHAR(255),
                reason TEXT,
                serverid BIGINT,
                servername VARCHAR(255),
                bannedby VARCHAR(255)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mac_bypass (
                user_id BIGINT,
                server_id BIGINT,
                PRIMARY KEY (user_id, server_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                guild_id VARCHAR(64),
                user_id VARCHAR(64),
                xp DOUBLE DEFAULT 0,
                level INT DEFAULT 0,
                messages INT DEFAULT 0,
                voice_seconds INT DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                guild_id VARCHAR(64),
                name VARCHAR(128),
                content TEXT,
                author_id VARCHAR(64),
                created_at VARCHAR(64),
                PRIMARY KEY (guild_id, name)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tempbans (
                guild_id VARCHAR(64),
                user_id VARCHAR(64),
                unban_at VARCHAR(64),
                reason TEXT,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        conn.commit()

    def _init_postgres_tables(self, conn):
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS guild_configs (
                guild_id VARCHAR(64) PRIMARY KEY,
                config_data JSONB NOT NULL
            );
            CREATE TABLE IF NOT EXISTS mac_bans (
                id BIGINT PRIMARY KEY,
                name VARCHAR(255),
                bandate VARCHAR(255),
                reason TEXT,
                serverid BIGINT,
                servername VARCHAR(255),
                bannedby VARCHAR(255)
            );
            CREATE TABLE IF NOT EXISTS mac_bypass (
                user_id BIGINT,
                server_id BIGINT,
                PRIMARY KEY (user_id, server_id)
            );
            CREATE TABLE IF NOT EXISTS user_stats (
                guild_id VARCHAR(64),
                user_id VARCHAR(64),
                xp DOUBLE PRECISION DEFAULT 0,
                level INT DEFAULT 0,
                messages INT DEFAULT 0,
                voice_seconds INT DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS tags (
                guild_id VARCHAR(64),
                name VARCHAR(128),
                content TEXT,
                author_id VARCHAR(64),
                created_at VARCHAR(64),
                PRIMARY KEY (guild_id, name)
            );
            CREATE TABLE IF NOT EXISTS tempbans (
                guild_id VARCHAR(64),
                user_id VARCHAR(64),
                unban_at VARCHAR(64),
                reason TEXT,
                PRIMARY KEY (guild_id, user_id)
            );
        """)
        conn.commit()


db = DatabaseManager()


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Helper Functions for Guild Configuration
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
SERVER_CONFIG_JSON = "config/serverconfig.json"

def _load_all_json_configs() -> Dict[str, Any]:
    if not os.path.exists(SERVER_CONFIG_JSON):
        return {}
    try:
        with open(SERVER_CONFIG_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        LogError(f"Error loading {SERVER_CONFIG_JSON}: {e}")
        return {}

def _save_all_json_configs(data: Dict[str, Any]):
    os.makedirs(os.path.dirname(SERVER_CONFIG_JSON), exist_ok=True)
    with open(SERVER_CONFIG_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def get_guild_config(guild_id: Any) -> Dict[str, Any]:
    gid = str(guild_id)
    if db.backend == "sqlite":
        with db._get_sqlite_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT config_data FROM guild_configs WHERE guild_id = ?", (gid,))
            row = cur.fetchone()
            if row:
                return json.loads(row[0])
            return {}
    elif db.backend == "mysql":
        try:
            conn = db._get_mysql_connection()
            cur = conn.cursor()
            cur.execute("SELECT config_data FROM guild_configs WHERE guild_id = %s", (gid,))
            row = cur.fetchone()
            conn.close()
            if row:
                return json.loads(row[0]) if isinstance(row[0], str) else row[0]
            return {}
        except Exception as e:
            LogError(f"MySQL get_guild_config error: {e}")
    elif db.backend in ("mongo", "mongodb"):
        try:
            doc = db.mongo_db.guild_configs.find_one({"guild_id": gid})
            return doc.get("config", {}) if doc else {}
        except Exception as e:
            LogError(f"MongoDB get_guild_config error: {e}")

    # Fallback to JSON
    configs = _load_all_json_configs()
    return configs.get(gid, {})

def set_guild_config(guild_id: Any, key: str, value: Any):
    gid = str(guild_id)
    cfg = get_guild_config(gid)
    cfg[key] = value
    save_guild_config(gid, cfg)

def save_guild_config(guild_id: Any, config: Dict[str, Any]):
    gid = str(guild_id)
    if db.backend == "sqlite":
        with db._get_sqlite_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO guild_configs (guild_id, config_data)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET config_data=excluded.config_data
            """, (gid, json.dumps(config)))
            conn.commit()
            return
    elif db.backend == "mysql":
        try:
            conn = db._get_mysql_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO guild_configs (guild_id, config_data)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE config_data = VALUES(config_data)
            """, (gid, json.dumps(config)))
            conn.commit()
            conn.close()
            return
        except Exception as e:
            LogError(f"MySQL save_guild_config error: {e}")
    elif db.backend in ("mongo", "mongodb"):
        try:
            db.mongo_db.guild_configs.update_one(
                {"guild_id": gid},
                {"$set": {"config": config}},
                upsert=True
            )
            return
        except Exception as e:
            LogError(f"MongoDB save_guild_config error: {e}")

    # Fallback to JSON
    configs = _load_all_json_configs()
    configs[gid] = config
    _save_all_json_configs(configs)


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Backward Compatibility Database Wrappers
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def get_db_connection():
    if db.backend == "mysql":
        return db._get_mysql_connection()
    elif db.backend == "sqlite":
        return sqlite3.connect(SQLITE_PATH)
    return None

def create_mac_bans_table():
    if db.backend == "sqlite":
        db._init_sqlite_tables()
    elif db.backend == "mysql":
        conn = db._get_mysql_connection()
        db._init_mysql_tables(conn)
        conn.close()

def create_mac_bypass_table():
    create_mac_bans_table()


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Tempbans Database Helpers (Docker / Multi-backend Safe)
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
TEMPBANS_JSON = "data/tempbans.json"

def get_tempbans() -> List[Dict[str, Any]]:
    if db.backend == "sqlite":
        with db._get_sqlite_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT guild_id, user_id, unban_at, reason FROM tempbans")
            rows = cur.fetchall()
            return [{"guild_id": str(r[0]), "user_id": str(r[1]), "unban_at": str(r[2]), "reason": r[3] or ""} for r in rows]
    elif db.backend == "mysql":
        try:
            conn = db._get_mysql_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT guild_id, user_id, unban_at, reason FROM tempbans")
                rows = cur.fetchall()
                conn.close()
                return [{"guild_id": str(r[0]), "user_id": str(r[1]), "unban_at": str(r[2]), "reason": r[3] or ""} for r in rows]
        except Exception as e:
            LogError(f"MySQL get_tempbans error: {e}")
    elif db.backend in ("mongo", "mongodb"):
        try:
            docs = list(db.mongo_db.tempbans.find({}))
            return [{"guild_id": str(d["guild_id"]), "user_id": str(d["user_id"]), "unban_at": str(d["unban_at"]), "reason": d.get("reason", "")} for d in docs]
        except Exception as e:
            LogError(f"MongoDB get_tempbans error: {e}")

    # Fallback to JSON
    if not os.path.exists(TEMPBANS_JSON):
        return []
    try:
        with open(TEMPBANS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        LogError(f"Error loading {TEMPBANS_JSON}: {e}")
        return []

def add_tempban(guild_id: Any, user_id: Any, unban_at: str, reason: str = "") -> bool:
    gid, uid = str(guild_id), str(user_id)
    if db.backend == "sqlite":
        with db._get_sqlite_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO tempbans (guild_id, user_id, unban_at, reason)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id, user_id) DO UPDATE SET unban_at=excluded.unban_at, reason=excluded.reason
            """, (gid, uid, unban_at, reason))
            conn.commit()
            return True
    elif db.backend == "mysql":
        try:
            conn = db._get_mysql_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO tempbans (guild_id, user_id, unban_at, reason)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE unban_at = VALUES(unban_at), reason = VALUES(reason)
                """, (gid, uid, unban_at, reason))
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            LogError(f"MySQL add_tempban error: {e}")
    elif db.backend in ("mongo", "mongodb"):
        try:
            db.mongo_db.tempbans.update_one(
                {"guild_id": gid, "user_id": uid},
                {"$set": {"unban_at": unban_at, "reason": reason}},
                upsert=True
            )
            return True
        except Exception as e:
            LogError(f"MongoDB add_tempban error: {e}")

    # Fallback to JSON
    current = get_tempbans()
    current = [tb for tb in current if not (tb.get("guild_id") == gid and tb.get("user_id") == uid)]
    current.append({"guild_id": gid, "user_id": uid, "unban_at": unban_at, "reason": reason})
    os.makedirs(os.path.dirname(TEMPBANS_JSON), exist_ok=True)
    with open(TEMPBANS_JSON, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=4)
    return True

def remove_tempban(guild_id: Any, user_id: Any) -> bool:
    gid, uid = str(guild_id), str(user_id)
    if db.backend == "sqlite":
        with db._get_sqlite_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM tempbans WHERE guild_id = ? AND user_id = ?", (gid, uid))
            conn.commit()
            return True
    elif db.backend == "mysql":
        try:
            conn = db._get_mysql_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM tempbans WHERE guild_id = %s AND user_id = %s", (gid, uid))
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            LogError(f"MySQL remove_tempban error: {e}")
    elif db.backend in ("mongo", "mongodb"):
        try:
            db.mongo_db.tempbans.delete_one({"guild_id": gid, "user_id": uid})
            return True
        except Exception as e:
            LogError(f"MongoDB remove_tempban error: {e}")

    # Fallback to JSON
    current = get_tempbans()
    filtered = [tb for tb in current if not (tb.get("guild_id") == gid and tb.get("user_id") == uid)]
    os.makedirs(os.path.dirname(TEMPBANS_JSON), exist_ok=True)
    with open(TEMPBANS_JSON, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=4)
    return True

def save_tempbans(tempbans: List[Dict[str, Any]]) -> bool:
    if db.backend == "sqlite":
        with db._get_sqlite_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM tempbans")
            for tb in tempbans:
                cur.execute(
                    "INSERT INTO tempbans (guild_id, user_id, unban_at, reason) VALUES (?, ?, ?, ?)",
                    (str(tb.get("guild_id")), str(tb.get("user_id")), str(tb.get("unban_at")), str(tb.get("reason", "")))
                )
            conn.commit()
            return True
    elif db.backend == "mysql":
        try:
            conn = db._get_mysql_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM tempbans")
                for tb in tempbans:
                    cur.execute(
                        "INSERT INTO tempbans (guild_id, user_id, unban_at, reason) VALUES (%s, %s, %s, %s)",
                        (str(tb.get("guild_id")), str(tb.get("user_id")), str(tb.get("unban_at")), str(tb.get("reason", "")))
                    )
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            LogError(f"MySQL save_tempbans error: {e}")
    elif db.backend in ("mongo", "mongodb"):
        try:
            db.mongo_db.tempbans.delete_many({})
            if tempbans:
                docs = [{"guild_id": str(tb.get("guild_id")), "user_id": str(tb.get("user_id")), "unban_at": str(tb.get("unban_at")), "reason": str(tb.get("reason", ""))} for tb in tempbans]
                db.mongo_db.tempbans.insert_many(docs)
            return True
        except Exception as e:
            LogError(f"MongoDB save_tempbans error: {e}")

    # Fallback to JSON
    os.makedirs(os.path.dirname(TEMPBANS_JSON), exist_ok=True)
    with open(TEMPBANS_JSON, "w", encoding="utf-8") as f:
        json.dump(tempbans, f, indent=4)
    return True

