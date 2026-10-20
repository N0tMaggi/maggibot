# -*- coding: utf-8 -*-
"""
Tests for handlers/config.py.
Verifies generic data loader/saver, config loaders/savers (serverconfig, voicegate,
admin feedback, onlyimages, lockdown, stats, etc.), MAC helpers, and guild channel lookups.
"""

import os
import json
import pytest
from unittest.mock import MagicMock

import handlers.config as cfg_mod
from handlers.config import (
    load_data,
    save_data,
    loadserverconfig,
    saveserverconfig,
    loadvoicegateconfig,
    savevoicegateconfig,
    load_admin_feedback,
    save_admin_feedback,
    load_onlyimages,
    save_onlyimages,
    load_lockdown_config,
    save_lockdown_config,
    load_stats,
    save_stats,
    load_multiplier_config,
    save_multiplier_config,
    load_randommath,
    save_randommath,
    load_cookies,
    save_cookies,
    load_tags,
    save_tags,
    get_server_config,
    set_server_config,
    get_log_channel,
    get_logging_forum,
    get_json_files,
    get_config_files,
    get_data_files,
    mac_load_bans,
    mac_save_bans,
    mac_load_bypasses,
    mac_save_bypasses,
)


class TestGenericDataHelpers:
    """Test generic load_data and save_data utility functions."""

    def test_load_data_file_missing_value_default(self, tmp_path):
        missing = tmp_path / "missing.json"
        assert load_data(str(missing), default={"default": 1}) == {"default": 1}

    def test_load_data_file_missing_callable_default(self, tmp_path):
        missing = tmp_path / "missing.json"
        result = load_data(str(missing), default=dict)
        assert result == {}
        assert isinstance(result, dict)

    def test_load_data_invalid_json(self, tmp_path):
        invalid = tmp_path / "invalid.json"
        invalid.write_text("{corrupt json:", encoding="utf-8")
        assert load_data(str(invalid), default={"fallback": True}) == {"fallback": True}

    def test_load_data_with_transform_function(self, tmp_path):
        valid = tmp_path / "numbers.json"
        valid.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        result = load_data(str(valid), transform_fn=lambda arr: [x * 2 for x in arr])
        assert result == [2, 4, 6]

    def test_save_data_creates_file(self, tmp_path):
        target = tmp_path / "output.json"
        success = save_data(str(target), {"key": "value"})
        assert success is True
        assert target.exists()

        with open(target, "r", encoding="utf-8") as f:
            assert json.load(f) == {"key": "value"}

    def test_save_data_with_mkdir(self, tmp_path):
        nested = tmp_path / "sub" / "folder" / "nested.json"
        success = save_data(str(nested), {"nested": True}, mkdir=True)
        assert success is True
        assert nested.exists()


class TestServerConfig:
    """Test serverconfig loading and saving."""

    def test_loadserverconfig_default_empty(self, temp_json_env):
        config = loadserverconfig()
        assert config == {}

    def test_saveserverconfig_roundtrip(self, temp_json_env):
        test_config = {
            "123456789": {
                "prefix": "!",
                "locale": "de",
                "log_channel": 999111
            }
        }
        saveserverconfig(test_config)
        loaded = loadserverconfig()
        assert loaded == test_config
        assert loaded["123456789"]["locale"] == "de"


class TestVoicegateConfig:
    """Test voicegate configuration loading and saving."""

    def test_loadvoicegateconfig_default_empty(self, temp_json_env):
        assert loadvoicegateconfig() == {}

    def test_savevoicegateconfig_roundtrip(self, temp_json_env):
        vg_data = {
            "guild_123": {
                "gate_channel": 555111,
                "verified_role": 555222,
                "min_account_age_days": 7
            }
        }
        savevoicegateconfig(vg_data)
        assert loadvoicegateconfig() == vg_data


class TestAdminFeedback:
    """Test admin feedback configuration loading and saving."""

    def test_load_admin_feedback_default_structure(self, temp_json_env):
        default_fb = load_admin_feedback()
        assert default_fb == {"configs": {}, "feedbacks": {}}

    def test_save_admin_feedback_roundtrip(self, temp_json_env):
        fb_data = {
            "configs": {"guild_1": {"enabled": True, "channel_id": 444333}},
            "feedbacks": {"guild_1": [{"id": 1, "text": "Great bot!"}]}
        }
        save_admin_feedback(fb_data)
        assert load_admin_feedback() == fb_data


class TestOnlyImages:
    """Test onlyimages configuration loading with transformation and saving."""

    def test_load_onlyimages_default_empty(self, temp_json_env):
        assert load_onlyimages() == {}

    def test_load_onlyimages_transform_list_to_dict(self, temp_json_env):
        # If the file stores a legacy list of channel IDs, it should transform to a dict
        channel_list = ["111222", "333444", "555666"]
        save_data(cfg_mod.ONLY_IMAGES_FILE, channel_list, mkdir=True)

        loaded = load_onlyimages()
        assert isinstance(loaded, dict)
        assert loaded == {"111222": True, "333444": True, "555666": True}

    def test_save_onlyimages_roundtrip(self, temp_json_env):
        data = {"111222": True, "333444": True}
        save_onlyimages(data)
        assert load_onlyimages() == data


class TestLockdownConfig:
    """Test lockdown configuration loading and saving."""

    def test_load_lockdown_config_default(self, temp_json_env):
        assert load_lockdown_config() == {"lockdown": False}

    def test_save_lockdown_config_boolean(self, temp_json_env):
        save_lockdown_config(True)
        assert load_lockdown_config() == {"lockdown": True}

        save_lockdown_config(False)
        assert load_lockdown_config() == {"lockdown": False}

    def test_load_lockdown_config_heals_invalid_data(self, temp_json_env):
        # Save invalid content without "lockdown" key
        save_data(cfg_mod.LOCKDOWN_CONFIG_FILE, {"unknown_key": 123}, mkdir=True)
        healed = load_lockdown_config()
        assert healed == {"lockdown": False}


class TestStatsConfig:
    """Test user and server statistics configuration loading and saving."""

    def test_load_stats_default_empty(self, temp_json_env):
        assert load_stats() == {}

    def test_save_stats_roundtrip(self, temp_json_env):
        stats_data = {
            "guild_1": {
                "user_1": {
                    "xp": 150.5,
                    "level": 3,
                    "messages": 42
                }
            }
        }
        save_stats(stats_data)
        assert load_stats() == stats_data


class TestAdditionalConfigHandlers:
    """Test remaining configuration loaders and savers."""

    def test_multiplier_config_roundtrip_and_defaults(self, temp_json_env):
        default_cfg = load_multiplier_config()
        assert "channels" in default_cfg
        assert "multipliers" in default_cfg

        custom = {"channels": ["ch1"], "multipliers": {"ch1": 2.0}}
        save_multiplier_config(custom)
        loaded = load_multiplier_config()
        assert loaded["channels"] == ["ch1"]
        assert loaded["multipliers"]["ch1"] == 2.0

    def test_randommath_roundtrip(self, temp_json_env):
        assert load_randommath() == {}
        save_randommath({"channel_id": 999})
        assert load_randommath() == {"channel_id": 999}

    def test_cookies_roundtrip(self, temp_json_env):
        assert load_cookies() == {}
        save_cookies({"user_1": 15})
        assert load_cookies() == {"user_1": 15}

    def test_tags_roundtrip(self, temp_json_env):
        assert load_tags() == {}
        tags_data = {"help": {"content": "Help info", "author": 123}}
        save_tags(tags_data)
        assert load_tags() == tags_data

    def test_get_and_set_server_config(self, temp_json_env):
        guild_id = 999888
        set_server_config(guild_id, "test_key", "test_val")
        cfg = get_server_config(guild_id)
        assert cfg["test_key"] == "test_val"


class TestChannelResolvers:
    """Test get_log_channel and get_logging_forum."""

    def test_get_log_channel_found(self, mock_guild, temp_json_env):
        mock_channel = MagicMock()
        mock_channel.id = 888777
        mock_guild.get_channel = MagicMock(return_value=mock_channel)

        saveserverconfig({str(mock_guild.id): {"log_channel": 888777}})
        ch = get_log_channel(mock_guild)
        assert ch is mock_channel
        mock_guild.get_channel.assert_called_once_with(888777)

    def test_get_log_channel_not_configured(self, mock_guild, temp_json_env):
        saveserverconfig({str(mock_guild.id): {}})
        assert get_log_channel(mock_guild) is None

    def test_get_logging_forum_found(self, mock_guild, temp_json_env):
        mock_forum = MagicMock()
        mock_forum.id = 777666
        mock_guild.get_channel = MagicMock(return_value=mock_forum)

        saveserverconfig({str(mock_guild.id): {"logging_forum": 777666}})
        forum = get_logging_forum(mock_guild)
        assert forum is mock_forum
        mock_guild.get_channel.assert_called_once_with(777666)


class TestFileListHelpers:
    """Test categorised file lists getters."""

    def test_file_lists(self):
        json_files = get_json_files()
        config_files = get_config_files()
        data_files = get_data_files()

        assert len(json_files) == len(config_files) + len(data_files)
        assert cfg_mod.SERVER_CONFIG_FILE in config_files
        assert cfg_mod.STATS_FILE in data_files


class TestMacBanHelpersJson:
    """Test mac_load_bans, mac_save_bans, mac_load_bypasses, mac_save_bypasses in JSON mode."""

    def test_mac_bans_json_roundtrip(self, temp_json_env):
        bans = {
            "123": {
                "id": 123,
                "name": "BannedUser",
                "bandate": "2026-10-20",
                "reason": "Raid",
                "serverid": 999,
                "servername": "ServerName",
                "bannedby": "Admin"
            }
        }
        mac_save_bans(bans)
        loaded = mac_load_bans()
        assert "123" in loaded
        assert loaded["123"]["name"] == "BannedUser"

    def test_mac_bypasses_json_roundtrip(self, temp_json_env):
        bypasses = {"123": [999, 888]}
        mac_save_bypasses(bypasses)
        loaded = mac_load_bypasses()
        assert loaded == {"123": [999, 888]}
