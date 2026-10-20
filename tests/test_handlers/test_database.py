# -*- coding: utf-8 -*-
"""
Tests for handlers/database.py.
Verifies singleton pattern, JSON backend operations, SQLite backend initialization,
table schemas, non-existent guild fallback, and backward compatibility functions.
"""

import os
import json
import sqlite3
import pytest
from unittest.mock import MagicMock, patch

import handlers.database as db_mod
from handlers.database import (
    DatabaseManager,
    db,
    get_guild_config,
    set_guild_config,
    save_guild_config,
    get_db_connection,
    create_mac_bans_table,
    create_mac_bypass_table,
    _load_all_json_configs,
    _save_all_json_configs,
)


class TestDatabaseManagerSingleton:
    """Test DatabaseManager singleton behavior and attributes."""

    def test_singleton_instance(self):
        dm1 = DatabaseManager()
        dm2 = DatabaseManager()
        assert dm1 is dm2
        assert dm1 is db

    def test_initialized_flag_prevents_reinit(self):
        assert db._initialized is True
        backend_before = db.backend
        # Calling __init__ again should not re-run _init_backend
        db.__init__()
        assert db.backend == backend_before


class TestJsonBackend:
    """Test JSON file storage backend for guild configurations."""

    @pytest.fixture(autouse=True)
    def ensure_json_backend(self, temp_json_env, monkeypatch):
        monkeypatch.setattr(db, "backend", "json")
        monkeypatch.setattr(db_mod, "DB_TYPE", "json")

    def test_nonexistent_guild_returns_empty_dict(self):
        result = get_guild_config("non_existent_guild_12345")
        assert result == {}
        assert isinstance(result, dict)

    def test_nonexistent_guild_int_id_returns_empty_dict(self):
        result = get_guild_config(999999999999)
        assert result == {}
        assert isinstance(result, dict)

    def test_save_and_get_guild_config(self):
        guild_id = "1001"
        test_data = {
            "prefix": "!",
            "locale": "en",
            "mod_role": 123456,
            "features": ["automod", "welcome"]
        }

        save_guild_config(guild_id, test_data)
        loaded = get_guild_config(guild_id)
        assert loaded == test_data
        assert loaded["prefix"] == "!"
        assert loaded["features"] == ["automod", "welcome"]

    def test_set_guild_config_updates_and_preserves(self):
        guild_id = 1002
        # Set initial key
        set_guild_config(guild_id, "prefix", "$")
        assert get_guild_config(guild_id) == {"prefix": "$"}

        # Set second key, should preserve first
        set_guild_config(guild_id, "locale", "de")
        cfg = get_guild_config(guild_id)
        assert cfg["prefix"] == "$"
        assert cfg["locale"] == "de"

        # Update existing key
        set_guild_config(guild_id, "prefix", "?")
        assert get_guild_config(guild_id)["prefix"] == "?"

    def test_multiple_guilds_isolated(self):
        save_guild_config("guild_a", {"name": "Alpha"})
        save_guild_config("guild_b", {"name": "Beta"})

        assert get_guild_config("guild_a") == {"name": "Alpha"}
        assert get_guild_config("guild_b") == {"name": "Beta"}

    def test_load_all_json_configs_file_missing(self, monkeypatch, tmp_path):
        missing_file = tmp_path / "does_not_exist.json"
        monkeypatch.setattr(db_mod, "SERVER_CONFIG_JSON", str(missing_file))
        assert _load_all_json_configs() == {}

    def test_load_all_json_configs_corrupted_json(self, monkeypatch, tmp_path):
        corrupt_file = tmp_path / "corrupt.json"
        corrupt_file.write_text("{bad json: true", encoding="utf-8")
        monkeypatch.setattr(db_mod, "SERVER_CONFIG_JSON", str(corrupt_file))

        # Should log error and return empty dict without crashing
        assert _load_all_json_configs() == {}


class TestSqliteBackend:
    """Test SQLite storage backend for guild configurations and tables."""

    @pytest.fixture(autouse=True)
    def setup_sqlite(self, tmp_path, monkeypatch):
        sqlite_file = tmp_path / "test_maggibot.db"
        monkeypatch.setattr(db_mod, "SQLITE_PATH", str(sqlite_file))
        monkeypatch.setattr(db, "backend", "sqlite")
        db._init_sqlite_tables()
        return sqlite_file

    def test_sqlite_tables_created(self, setup_sqlite):
        sqlite_file = setup_sqlite
        assert os.path.exists(sqlite_file)

        with sqlite3.connect(sqlite_file) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cur.fetchall()}

        expected_tables = {"guild_configs", "mac_bans", "mac_bypass", "user_stats", "tags"}
        assert expected_tables.issubset(tables)

    def test_sqlite_nonexistent_guild_returns_empty_dict(self):
        result = get_guild_config("999888777")
        assert result == {}
        assert isinstance(result, dict)

    def test_sqlite_save_and_get_guild_config(self):
        guild_id = "5001"
        data = {"locale": "de", "prefix": "!", "volume": 80}

        save_guild_config(guild_id, data)
        loaded = get_guild_config(guild_id)
        assert loaded == data
        assert loaded["locale"] == "de"
        assert loaded["volume"] == 80

    def test_sqlite_upsert_overwrite(self):
        guild_id = "5002"
        save_guild_config(guild_id, {"v": 1})
        assert get_guild_config(guild_id) == {"v": 1}

        # Save new configuration for same guild_id (upsert)
        save_guild_config(guild_id, {"v": 2, "updated": True})
        loaded = get_guild_config(guild_id)
        assert loaded == {"v": 2, "updated": True}

    def test_sqlite_set_guild_config(self):
        guild_id = 5003
        set_guild_config(guild_id, "channel", 123456)
        assert get_guild_config(guild_id) == {"channel": 123456}

        set_guild_config(guild_id, "active", True)
        loaded = get_guild_config(guild_id)
        assert loaded["channel"] == 123456
        assert loaded["active"] is True


class TestDatabaseBackwardCompatibility:
    """Test backward compatibility wrappers and table creation helpers."""

    def test_get_db_connection_sqlite(self, tmp_path, monkeypatch):
        db_path = tmp_path / "compat.db"
        monkeypatch.setattr(db_mod, "SQLITE_PATH", str(db_path))
        monkeypatch.setattr(db, "backend", "sqlite")

        conn = get_db_connection()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_db_connection_json(self, monkeypatch):
        monkeypatch.setattr(db, "backend", "json")
        conn = get_db_connection()
        assert conn is None

    def test_create_mac_tables_sqlite(self, tmp_path, monkeypatch):
        db_path = tmp_path / "mac_test.db"
        monkeypatch.setattr(db_mod, "SQLITE_PATH", str(db_path))
        monkeypatch.setattr(db, "backend", "sqlite")

        create_mac_bans_table()
        create_mac_bypass_table()

        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cur.fetchall()}
            assert "mac_bans" in tables
            assert "mac_bypass" in tables


class TestTempbansDatabase:
    """Test Tempbans database operations across SQLite and JSON backends."""

    def test_sqlite_tempbans_crud(self, tmp_path, monkeypatch):
        db_path = tmp_path / "tempbans_test.db"
        monkeypatch.setattr(db_mod, "SQLITE_PATH", str(db_path))
        monkeypatch.setattr(db, "backend", "sqlite")
        db._init_sqlite_tables()

        # 1. Add tempban
        assert db_mod.add_tempban("123", "456", "2026-10-23T12:00:00", "Spam Honeypot") is True

        bans = db_mod.get_tempbans()
        assert len(bans) == 1
        assert bans[0]["guild_id"] == "123"
        assert bans[0]["user_id"] == "456"
        assert bans[0]["reason"] == "Spam Honeypot"

        # 2. Update existing tempban (upsert)
        db_mod.add_tempban("123", "456", "2026-10-24T12:00:00", "Updated Reason")
        bans = db_mod.get_tempbans()
        assert len(bans) == 1
        assert bans[0]["unban_at"] == "2026-10-24T12:00:00"
        assert bans[0]["reason"] == "Updated Reason"

        # 3. Add second tempban
        db_mod.add_tempban("123", "789", "2026-10-25T12:00:00", "Second Ban")
        assert len(db_mod.get_tempbans()) == 2

        # 4. Remove tempban
        assert db_mod.remove_tempban("123", "456") is True
        bans = db_mod.get_tempbans()
        assert len(bans) == 1
        assert bans[0]["user_id"] == "789"

        # 5. Bulk save_tempbans
        db_mod.save_tempbans([
            {"guild_id": "999", "user_id": "111", "unban_at": "2026-11-01T00:00:00", "reason": "Bulk"}
        ])
        bans = db_mod.get_tempbans()
        assert len(bans) == 1
        assert bans[0]["guild_id"] == "999"

    def test_json_tempbans_crud(self, tmp_path, monkeypatch):
        json_file = tmp_path / "data" / "tempbans.json"
        monkeypatch.setattr(db, "backend", "json")
        monkeypatch.setattr(db_mod, "TEMPBANS_JSON", str(json_file))

        assert db_mod.get_tempbans() == []

        # Add tempban
        db_mod.add_tempban("555", "777", "2026-10-22T00:00:00", "Honeypot Trigger")
        bans = db_mod.get_tempbans()
        assert len(bans) == 1
        assert bans[0]["user_id"] == "777"

        # Remove tempban
        db_mod.remove_tempban("555", "777")
        assert db_mod.get_tempbans() == []

