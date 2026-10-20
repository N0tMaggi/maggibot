# -*- coding: utf-8 -*-
"""
Pytest configuration and global fixtures for MaggiBot tests.
Provides mocks for Discord entities, guilds, interactions, and temporary database fixtures.
"""

import sys
import os
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import discord


@pytest.fixture
def mock_bot():
    bot = MagicMock(spec=discord.Bot)
    bot.user = MagicMock(spec=discord.ClientUser)
    bot.user.name = "MaggiBot"
    bot.user.id = 999999999999
    bot.user.display_avatar = MagicMock()
    bot.user.display_avatar.url = "https://cdn.discordapp.com/embed/avatars/0.png"
    bot.latency = 0.042
    bot.guilds = []
    bot.users = []
    return bot


@pytest.fixture
def mock_guild():
    guild = MagicMock(spec=discord.Guild)
    guild.id = 123456789012345
    guild.name = "Test Discord Server"
    guild.member_count = 42
    guild.icon = None
    guild.banner = None
    guild.roles = []
    guild.channels = []
    guild.text_channels = []
    guild.voice_channels = []
    guild.categories = []
    guild.emojis = []
    guild.features = ["COMMUNITY", "WELCOME_SCREEN_ENABLED"]
    guild.verification_level = discord.VerificationLevel.low
    guild.premium_tier = 1
    guild.premium_subscription_count = 2

    owner = MagicMock(spec=discord.Member)
    owner.id = 111111111111
    owner.name = "OwnerUser"
    owner.mention = "<@111111111111>"
    guild.owner = owner

    return guild


@pytest.fixture
def mock_member(mock_guild):
    member = MagicMock(spec=discord.Member)
    member.id = 222222222222
    member.name = "TestMember"
    member.display_name = "DisplayMember"
    member.mention = "<@222222222222>"
    member.bot = False
    member.guild = mock_guild
    member.roles = []
    member.top_role = MagicMock(spec=discord.Role)
    member.top_role.mention = "@Member"
    member.display_avatar = MagicMock()
    member.display_avatar.url = "https://cdn.discordapp.com/embed/avatars/1.png"
    member.guild_permissions = discord.Permissions(administrator=True)
    member.send = AsyncMock()
    member.edit = AsyncMock()
    member.move_to = AsyncMock()
    return member


@pytest.fixture
def mock_context(mock_bot, mock_guild, mock_member):
    ctx = MagicMock(spec=discord.ApplicationContext)
    ctx.bot = mock_bot
    ctx.guild = mock_guild
    ctx.author = mock_member
    ctx.user = mock_member
    ctx.channel = MagicMock(spec=discord.TextChannel)
    ctx.channel.id = 333333333333
    ctx.channel.name = "general"
    ctx.channel.mention = "<#333333333333>"

    ctx.respond = AsyncMock()
    ctx.defer = AsyncMock()
    ctx.followup = MagicMock()
    ctx.followup.send = AsyncMock()
    ctx.interaction = MagicMock(spec=discord.Interaction)
    ctx.interaction.user = mock_member
    ctx.interaction.guild = mock_guild
    ctx.interaction.response = MagicMock()
    ctx.interaction.response.send_message = AsyncMock()
    ctx.interaction.response.edit_message = AsyncMock()
    ctx.interaction.response.is_done = MagicMock(return_value=False)
    ctx.response = ctx.interaction.response
    return ctx


@pytest.fixture
def temp_json_env(tmp_path, monkeypatch):
    """Overrides data and config paths to point to a temporary test directory"""
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    config_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("handlers.database.JSON_CONFIG_DIR", str(config_dir))
    monkeypatch.setattr("handlers.database.JSON_DATA_DIR", str(data_dir))
    monkeypatch.setattr("handlers.database.SERVER_CONFIG_JSON", str(config_dir / "serverconfig.json"))

    # Also patch handlers.config file paths
    monkeypatch.setattr("handlers.config.SERVER_CONFIG_FILE", str(config_dir / "serverconfig.json"))
    monkeypatch.setattr("handlers.config.ADMIN_FEEDBACK_FILE", str(config_dir / "adminfeedback.json"))
    monkeypatch.setattr("handlers.config.LOCKDOWN_CONFIG_FILE", str(config_dir / "lockdown.json"))
    monkeypatch.setattr("handlers.config.VOICEGATE_CONFIG_FILE", str(config_dir / "voicegateconfig.json"))
    monkeypatch.setattr("handlers.config.ONLY_IMAGES_FILE", str(config_dir / "onlyimages.json"))
    monkeypatch.setattr("handlers.config.RANDOM_MATH_FILE", str(config_dir / "randommathchannel.json"))
    monkeypatch.setattr("handlers.config.STATS_FILE", str(data_dir / "stats.json"))
    monkeypatch.setattr("handlers.config.TAGS_CONFIG_FILE", str(data_dir / "tags.json"))
    monkeypatch.setattr("handlers.config.XP_MULTIPLIER_FILE", str(data_dir / "xpmultiplier.json"))
    monkeypatch.setattr("handlers.config.COOKIES_FILE", str(data_dir / "cookies.json"))
    monkeypatch.setattr("handlers.config.MAC_FILE", str(data_dir / "mac.json"))
    monkeypatch.setattr("handlers.config.MAC_BYPASS_FILE", str(data_dir / "mac_bypass.json"))
    monkeypatch.setattr("handlers.config.TEMPBANS_FILE", str(data_dir / "tempbans.json"))
    monkeypatch.setattr("handlers.database.TEMPBANS_JSON", str(data_dir / "tempbans.json"))

    # Ensure backend is set to json for temp_json_env
    monkeypatch.setattr("handlers.database.db.backend", "json")
    monkeypatch.setattr("handlers.config.DB_TYPE", "json")

    # Also clear locale cache
    import handlers.locale as loc
    loc._guild_locale_cache.clear()

    return {"config_dir": config_dir, "data_dir": data_dir}
