# -*- coding: utf-8 -*-
"""
Tests for ErrorHandling cog and on_application_command_error listener:
- MissingPermissions -> sends localized warning embed
- CommandOnCooldown -> sends cooldown embed
- NoPrivateMessage -> sends server-only embed
- Generic errors -> creates traceback file and logs
- LockdownCheckFailure -> ignored cleanly without logging duplicate errors
- Fatal / critical errors handling
"""

import pytest
import discord
from discord.ext import commands
import os
from unittest.mock import MagicMock, AsyncMock, patch

from cogs.system.errorhandling import ErrorHandling
from cogs.owner.commandlockdown import LockdownCheckFailure


@pytest.fixture
def error_cog(mock_bot, monkeypatch):
    monkeypatch.setattr("cogs.system.errorhandling.get_owner", lambda: 111222333)
    cog = ErrorHandling(mock_bot)
    return cog


class TestApplicationCommandErrorHandling:
    @pytest.mark.asyncio
    async def test_lockdown_check_failure_ignored_cleanly(self, error_cog, mock_context):
        """Test LockdownCheckFailure is cleanly ignored without sending messages or logging."""
        mock_context.response.is_done.return_value = False
        error = LockdownCheckFailure("Lockdown active")

        with patch("cogs.system.errorhandling.LogError") as mock_log:
            await error_cog.on_application_command_error(mock_context, error)

            # Neither response nor followup send should be called
            mock_context.response.send_message.assert_not_awaited()
            mock_context.followup.send.assert_not_awaited()
            mock_log.assert_not_called()

    @pytest.mark.asyncio
    async def test_wrapped_lockdown_check_failure_ignored_cleanly(self, error_cog, mock_context):
        """Test LockdownCheckFailure wrapped inside discord command invoke error is ignored."""
        inner = LockdownCheckFailure("Lockdown active")
        wrapped = discord.ApplicationCommandInvokeError(inner)

        with patch("cogs.system.errorhandling.LogError") as mock_log:
            await error_cog.on_application_command_error(mock_context, wrapped)

            mock_context.response.send_message.assert_not_awaited()
            mock_context.followup.send.assert_not_awaited()
            mock_log.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_permissions_sends_warning_embed(self, error_cog, mock_context):
        """Test MissingPermissions error sends localized warning embed with permission names."""
        mock_context.response.is_done.return_value = False
        error = commands.MissingPermissions(["manage_messages", "ban_members"])

        await error_cog.on_application_command_error(mock_context, error)

        mock_context.response.send_message.assert_awaited_once()
        embed = mock_context.response.send_message.call_args.kwargs["embed"]
        assert isinstance(embed, discord.Embed)
        assert mock_context.response.send_message.call_args.kwargs.get("ephemeral") is True
        # Check permissions mentioned in description
        assert "manage_messages" in embed.description
        assert "ban_members" in embed.description

    @pytest.mark.asyncio
    async def test_missing_permissions_uses_followup_when_done(self, error_cog, mock_context):
        """Test MissingPermissions error uses followup if interaction response was deferred."""
        mock_context.response.is_done.return_value = True
        error = commands.MissingPermissions(["administrator"])

        await error_cog.on_application_command_error(mock_context, error)

        mock_context.followup.send.assert_awaited_once()
        embed = mock_context.followup.send.call_args.kwargs["embed"]
        assert "administrator" in embed.description

    @pytest.mark.asyncio
    async def test_command_on_cooldown_sends_cooldown_embed(self, error_cog, mock_context):
        """Test CommandOnCooldown sends warning embed without developer logging."""
        mock_context.response.is_done.return_value = False
        cooldown = commands.Cooldown(1, 10)
        error = commands.CommandOnCooldown(cooldown, retry_after=7.4, type=commands.BucketType.user)

        with patch("cogs.system.errorhandling.LogError") as mock_log:
            await error_cog.on_application_command_error(mock_context, error)

            mock_context.response.send_message.assert_awaited_once()
            embed = mock_context.response.send_message.call_args.kwargs["embed"]
            assert "7.4" in str(embed.description)
            mock_log.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_private_message_sends_guild_only_embed(self, error_cog, mock_context):
        """Test NoPrivateMessage sends guild-only warning embed without developer logging."""
        mock_context.response.is_done.return_value = False
        error = commands.NoPrivateMessage()

        with patch("cogs.system.errorhandling.LogError") as mock_log:
            await error_cog.on_application_command_error(mock_context, error)

            mock_context.response.send_message.assert_awaited_once()
            embed = mock_context.response.send_message.call_args.kwargs["embed"]
            assert isinstance(embed, discord.Embed)
            mock_log.assert_not_called()

    @pytest.mark.asyncio
    async def test_generic_error_creates_traceback_file_and_logs(self, error_cog, mock_context, tmp_path, monkeypatch):
        """Test generic unhandled error creates traceback file when long, logs, and alerts user."""
        mock_context.response.is_done.return_value = False
        mock_context.command = MagicMock()
        mock_context.command.name = "test-bugged-command"

        # Redirect traceback files to tmp_path
        tb_dir = tmp_path / "traceback"
        tb_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr("cogs.system.errorhandling.os.path.join", lambda *args: str(tb_dir / args[-1]))
        monkeypatch.setattr("cogs.system.errorhandling.os.makedirs", lambda *args, **kwargs: None)

        # Mock developer log channel
        mock_log_chan = MagicMock(spec=discord.TextChannel)
        mock_log_chan.send = AsyncMock()
        error_cog.bot.get_channel = MagicMock(return_value=mock_log_chan)
        monkeypatch.setattr("cogs.system.errorhandling.error_log_channel_id", "999888777")

        # Raise an exception with a deeply nested traceback so length > 1024 characters
        def deep_call(n):
            if n <= 0:
                raise ValueError("Deep nested simulated exception for testing traceback file generation " * 10)
            return deep_call(n - 1)

        try:
            deep_call(15)
        except Exception as exc:
            error = exc

        with patch("cogs.system.errorhandling.LogError") as mock_log:
            await error_cog.on_application_command_error(mock_context, error)

            # User alerted
            mock_context.response.send_message.assert_awaited_once()
            user_embed = mock_context.response.send_message.call_args.kwargs["embed"]
            assert "test-bugged-command" in user_embed.description

            # Logged to console
            mock_log.assert_called()

            # Sent to developer error channel with traceback file attached
            mock_log_chan.send.assert_awaited_once()
            dev_call_kwargs = mock_log_chan.send.call_args.kwargs
            assert "file" in dev_call_kwargs
            assert isinstance(dev_call_kwargs["file"], discord.File)

    @pytest.mark.asyncio
    async def test_fatal_error_handler(self, error_cog, mock_context, monkeypatch):
        """Test fatal/critical error triggers fatal_error workflow."""
        mock_log_chan = MagicMock(spec=discord.TextChannel)
        mock_log_chan.send = AsyncMock()
        error_cog.bot.get_channel = MagicMock(return_value=mock_log_chan)
        monkeypatch.setattr("cogs.system.errorhandling.error_log_channel_id", "999888777")

        fatal_exc = RuntimeError("critical fatal system failure detected")

        with patch("cogs.system.errorhandling.LogError") as mock_log:
            await error_cog.on_application_command_error(mock_context, fatal_exc)

            mock_log.assert_called()
            mock_log_chan.send.assert_awaited_once()
            embed = mock_log_chan.send.call_args.kwargs["embed"]
            assert "System Failure Protocol" in embed.footer.text
