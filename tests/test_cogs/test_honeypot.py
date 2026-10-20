# -*- coding: utf-8 -*-
"""
Tests for Honeypot Protection Cog:
- Setup and creation of honeypot channel with warning embed
- Removal of honeypot with/without channel deletion
- Detection of messages in honeypot channel
- Message deletion, DM notification, and 3-day ban execution
- Tempban record persistence and background unban loop
- Administrator and self-bot bypass verification
"""

import pytest
import datetime
from unittest.mock import MagicMock, AsyncMock, patch

import discord
from cogs.protection.honeypot import Honeypot
import handlers.config as config


@pytest.fixture
def honeypot_cog(mock_bot):
    with patch.object(discord.ext.tasks.Loop, "start"):
        cog = Honeypot(mock_bot)
        return cog


@pytest.mark.asyncio
async def test_honeypot_setup_auto_create(honeypot_cog, mock_context, temp_json_env):
    """Test auto-creating a new honeypot channel when none specified."""
    mock_new_channel = MagicMock(spec=discord.TextChannel)
    mock_new_channel.id = 888888888888
    mock_new_channel.name = "🍯・honeypot"
    mock_new_channel.mention = "<#888888888888>"
    mock_new_channel.send = AsyncMock()

    mock_msg = MagicMock(spec=discord.Message)
    mock_msg.pin = AsyncMock()
    mock_new_channel.send.return_value = mock_msg

    mock_context.guild.create_text_channel = AsyncMock(return_value=mock_new_channel)

    await honeypot_cog._setup_honeypot(mock_context, channel=None)

    # Verifies channel creation
    mock_context.guild.create_text_channel.assert_called_once()
    args, kwargs = mock_context.guild.create_text_channel.call_args
    assert kwargs["name"] == "🍯・honeypot"

    # Verifies warning embed was sent and pinned
    mock_new_channel.send.assert_called_once()
    mock_msg.pin.assert_called_once()

    # Verifies configuration saved
    cfg = config.loadserverconfig()
    assert cfg[str(mock_context.guild.id)]["honeypot_channel"] == 888888888888

    # Verifies response sent to admin
    mock_context.respond.assert_called_once()
    _, res_kwargs = mock_context.respond.call_args
    embed = res_kwargs["embed"]
    assert "Erfolg" in embed.title or "Success" in embed.title


@pytest.mark.asyncio
async def test_honeypot_setup_existing_channel(honeypot_cog, mock_context, temp_json_env):
    """Test configuring an existing channel as a honeypot."""
    mock_target = MagicMock(spec=discord.TextChannel)
    mock_target.id = 777777777777
    mock_target.name = "security-trap"
    mock_target.mention = "<#777777777777>"
    mock_msg = MagicMock(spec=discord.Message)
    mock_msg.pin = AsyncMock()
    mock_target.send = AsyncMock(return_value=mock_msg)

    await honeypot_cog._setup_honeypot(mock_context, channel=mock_target)

    # Verifies warning embed sent
    mock_target.send.assert_called_once()
    cfg = config.loadserverconfig()
    assert cfg[str(mock_context.guild.id)]["honeypot_channel"] == 777777777777


@pytest.mark.asyncio
async def test_honeypot_remove_keep_channel(honeypot_cog, mock_context, temp_json_env):
    """Test removing honeypot without deleting Discord channel."""
    cfg = {str(mock_context.guild.id): {"honeypot_channel": 777777777777}}
    config.saveserverconfig(cfg)

    await honeypot_cog._remove_honeypot(mock_context, delete_channel=False)

    saved_cfg = config.loadserverconfig()
    assert "honeypot_channel" not in saved_cfg.get(str(mock_context.guild.id), {})

    mock_context.respond.assert_called_once()
    _, res_kwargs = mock_context.respond.call_args
    assert res_kwargs["embed"].color.value == 0x2ECC71  # Success color


@pytest.mark.asyncio
async def test_honeypot_remove_delete_channel(honeypot_cog, mock_context, temp_json_env):
    """Test removing honeypot and deleting the channel."""
    chan_id = 777777777777
    cfg = {str(mock_context.guild.id): {"honeypot_channel": chan_id}}
    config.saveserverconfig(cfg)

    mock_chan = MagicMock(spec=discord.TextChannel)
    mock_chan.delete = AsyncMock()
    mock_context.guild.get_channel.return_value = mock_chan

    await honeypot_cog._remove_honeypot(mock_context, delete_channel=True)

    mock_chan.delete.assert_called_once()
    saved_cfg = config.loadserverconfig()
    assert "honeypot_channel" not in saved_cfg.get(str(mock_context.guild.id), {})


@pytest.mark.asyncio
async def test_honeypot_remove_when_not_active(honeypot_cog, mock_context, temp_json_env):
    """Test removing when no honeypot is configured returns warning."""
    config.saveserverconfig({})

    await honeypot_cog._remove_honeypot(mock_context, delete_channel=False)

    mock_context.respond.assert_called_once()
    _, res_kwargs = mock_context.respond.call_args
    assert "Warnung" in res_kwargs["embed"].title or "Warning" in res_kwargs["embed"].title


@pytest.mark.asyncio
async def test_honeypot_combined_command(honeypot_cog, mock_context, temp_json_env):
    """Test /honeypot command delegating to setup and remove."""
    with patch.object(honeypot_cog, "_setup_honeypot", new_callable=AsyncMock) as mock_setup:
        await honeypot_cog.honeypot_cmd.callback(honeypot_cog, mock_context, action="setup", channel=None, delete_channel=False)
        mock_setup.assert_called_once()

    with patch.object(honeypot_cog, "_remove_honeypot", new_callable=AsyncMock) as mock_remove:
        await honeypot_cog.honeypot_cmd.callback(honeypot_cog, mock_context, action="remove", channel=None, delete_channel=True)
        mock_remove.assert_called_once_with(mock_context, True)


@pytest.mark.asyncio
async def test_on_message_ignored_if_no_guild_or_own_bot(honeypot_cog, temp_json_env):
    """Test messages in DMs or by the bot itself are ignored."""
    msg = MagicMock(spec=discord.Message)
    msg.guild = None
    await honeypot_cog.on_message(msg)

    msg.guild = MagicMock()
    msg.author.id = honeypot_cog.bot.user.id
    await honeypot_cog.on_message(msg)

    # Guild ban should never be called
    msg.guild.ban.assert_not_called()


@pytest.mark.asyncio
async def test_on_message_ignored_in_normal_channels(honeypot_cog, temp_json_env):
    """Test messages outside the honeypot channel are ignored."""
    guild_id = 123456789
    cfg = {str(guild_id): {"honeypot_channel": 888888}}
    config.saveserverconfig(cfg)

    msg = MagicMock(spec=discord.Message)
    msg.guild = MagicMock()
    msg.guild.id = guild_id
    msg.channel.id = 999999  # Different channel
    msg.author.id = 555555
    msg.author.guild_permissions = discord.Permissions(send_messages=True)

    await honeypot_cog.on_message(msg)
    msg.guild.ban.assert_not_called()


@pytest.mark.asyncio
async def test_on_message_ignored_for_administrator(honeypot_cog, temp_json_env):
    """Test server administrators are not banned even if they type in honeypot."""
    guild_id = 123456789
    chan_id = 888888
    cfg = {str(guild_id): {"honeypot_channel": chan_id}}
    config.saveserverconfig(cfg)

    msg = MagicMock(spec=discord.Message)
    msg.guild = MagicMock()
    msg.guild.id = guild_id
    msg.channel.id = chan_id
    msg.author = MagicMock(spec=discord.Member)
    msg.author.id = 444444
    msg.author.guild_permissions = discord.Permissions(administrator=True)

    await honeypot_cog.on_message(msg)
    msg.guild.ban.assert_not_called()


@pytest.mark.asyncio
async def test_on_message_triggers_ban_and_tempban_record(honeypot_cog, temp_json_env):
    """Test a spammer/hacked account is banned for 3 days and recorded."""
    guild_id = 123456789
    chan_id = 888888
    log_chan_id = 444444

    cfg = {str(guild_id): {"honeypot_channel": chan_id, "logchannel": log_chan_id}}
    config.saveserverconfig(cfg)

    log_channel = MagicMock(spec=discord.TextChannel)
    log_channel.send = AsyncMock()

    guild = MagicMock(spec=discord.Guild)
    guild.id = guild_id
    guild.name = "Target Guild"
    guild.get_channel.return_value = log_channel
    guild.ban = AsyncMock()

    spammer = MagicMock(spec=discord.Member)
    spammer.id = 666666
    spammer.mention = "<@666666>"
    spammer.guild_permissions = discord.Permissions(send_messages=True)
    spammer.send = AsyncMock()

    msg = MagicMock(spec=discord.Message)
    msg.id = 111111
    msg.guild = guild
    msg.channel.id = chan_id
    msg.channel.name = "honeypot"
    msg.channel.mention = f"<#{chan_id}>"
    msg.author = spammer
    msg.content = "FREE DISCORD NITRO: https://scam-link.ru"
    msg.delete = AsyncMock()

    await honeypot_cog.on_message(msg)

    # 1. Message deleted
    msg.delete.assert_called_once()

    # 2. DM sent to spammer
    spammer.send.assert_called_once()
    _, dm_kwargs = spammer.send.call_args
    assert "3-Day" in dm_kwargs["embed"].title or "3-Tage" in dm_kwargs["embed"].title

    # 3. Guild ban executed with 1 day message history purge
    guild.ban.assert_called_once()
    b_args, b_kwargs = guild.ban.call_args
    assert b_args[0] == spammer
    assert "Honeypot Triggered" in b_kwargs["reason"]
    assert b_kwargs["delete_message_days"] == 1

    # 4. Tempban saved with 3-day duration
    tempbans = config.load_tempbans()
    assert len(tempbans) == 1
    record = tempbans[0]
    assert record["guild_id"] == str(guild_id)
    assert record["user_id"] == str(spammer.id)

    unban_dt = datetime.datetime.fromisoformat(record["unban_at"])
    now = discord.utils.utcnow()
    # Should be approximately 3 days in the future (+- 10 seconds)
    diff = (unban_dt - now).total_seconds()
    assert 259100 < diff < 259300

    # 5. Incident logged to audit/log channel
    log_channel.send.assert_called_once()


@pytest.mark.asyncio
async def test_check_unbans_task_loop(honeypot_cog, mock_bot, temp_json_env):
    """Test background task unbanning expired tempbans."""
    guild_id = 123456789
    expired_user_id = 111111
    active_user_id = 222222

    now = discord.utils.utcnow()
    expired_time = (now - datetime.timedelta(hours=1)).isoformat()
    future_time = (now + datetime.timedelta(days=2)).isoformat()

    tempbans = [
        {"guild_id": str(guild_id), "user_id": str(expired_user_id), "unban_at": expired_time, "reason": "Honeypot"},
        {"guild_id": str(guild_id), "user_id": str(active_user_id), "unban_at": future_time, "reason": "Honeypot"}
    ]
    config.save_tempbans(tempbans)

    mock_guild = MagicMock(spec=discord.Guild)
    mock_guild.unban = AsyncMock()
    mock_bot.get_guild.return_value = mock_guild

    # Call unban check iteration
    await honeypot_cog.check_unbans.coro(honeypot_cog)

    # Expired user unbanned
    mock_guild.unban.assert_called_once()
    unban_args, _ = mock_guild.unban.call_args
    assert unban_args[0].id == expired_user_id

    # Active user stays in database
    remaining = config.load_tempbans()
    assert len(remaining) == 1
    assert remaining[0]["user_id"] == str(active_user_id)
