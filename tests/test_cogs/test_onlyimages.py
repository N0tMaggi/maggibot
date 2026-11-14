# -*- coding: utf-8 -*-
"""
Tests for OnlyImages cog.
"""

import pytest
import discord
from unittest.mock import MagicMock, AsyncMock, patch

from cogs.server.onlyimages import OnlyImages
import handlers.config as config


@pytest.fixture
def onlyimages_cog(mock_bot):
    cog = OnlyImages(mock_bot)
    cog.enableonlyimages.cog = cog
    cog.disableonlyimages.cog = cog
    return cog


@pytest.fixture
def mock_message(mock_guild, mock_member):
    msg = MagicMock(spec=discord.Message)
    msg.guild = mock_guild
    msg.author = mock_member
    msg.author.bot = False
    msg.type = discord.MessageType.default
    msg.channel = MagicMock(spec=discord.TextChannel)
    msg.channel.id = 555666777
    msg.channel.send = AsyncMock()
    msg.delete = AsyncMock()
    msg.attachments = []
    return msg


class TestOnlyImagesCommands:
    @pytest.mark.asyncio
    async def test_enable_onlyimages_success(self, temp_json_env, onlyimages_cog, mock_context):
        """Test enabling onlyimages in an unconfigured channel."""
        mock_context.channel.id = 12345
        mock_context.channel.mention = "<#12345>"

        await onlyimages_cog.enableonlyimages(mock_context)

        stored = config.load_onlyimages()
        assert "12345" in stored
        mock_context.respond.assert_awaited_once()
        call_kwargs = mock_context.respond.call_args[1]
        assert "embed" in call_kwargs

    @pytest.mark.asyncio
    async def test_enable_onlyimages_already_enabled(self, temp_json_env, onlyimages_cog, mock_context):
        """Test enabling onlyimages in an already enabled channel sends warning."""
        mock_context.channel.id = 12345
        mock_context.channel.mention = "<#12345>"
        config.save_onlyimages({"12345": True})

        await onlyimages_cog.enableonlyimages(mock_context)

        mock_context.respond.assert_awaited_once()
        call_kwargs = mock_context.respond.call_args[1]
        assert "embed" in call_kwargs
        assert call_kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_disable_onlyimages_success(self, temp_json_env, onlyimages_cog, mock_context):
        """Test disabling onlyimages in an active channel."""
        mock_context.channel.id = 12345
        mock_context.channel.mention = "<#12345>"
        config.save_onlyimages({"12345": True})

        await onlyimages_cog.disableonlyimages(mock_context)

        stored = config.load_onlyimages()
        assert "12345" not in stored
        mock_context.respond.assert_awaited_once()
        call_kwargs = mock_context.respond.call_args[1]
        assert "embed" in call_kwargs

    @pytest.mark.asyncio
    async def test_disable_onlyimages_not_active(self, temp_json_env, onlyimages_cog, mock_context):
        """Test disabling onlyimages in a channel where it is not active sends warning."""
        mock_context.channel.id = 12345
        mock_context.channel.mention = "<#12345>"
        config.save_onlyimages({})

        await onlyimages_cog.disableonlyimages(mock_context)

        mock_context.respond.assert_awaited_once()
        call_kwargs = mock_context.respond.call_args[1]
        assert "embed" in call_kwargs
        assert call_kwargs.get("ephemeral") is True


class TestOnlyImagesListener:
    @pytest.mark.asyncio
    async def test_message_without_attachments_deleted_and_warned(self, temp_json_env, onlyimages_cog, mock_message):
        """Test that a message without attachments in an only-images channel is deleted and warned."""
        chan_id = str(mock_message.channel.id)
        config.save_onlyimages({chan_id: True})
        mock_message.attachments = []

        await onlyimages_cog.on_message(mock_message)

        mock_message.delete.assert_awaited_once()
        mock_message.channel.send.assert_awaited_once()
        call_kwargs = mock_message.channel.send.call_args[1]
        assert "embed" in call_kwargs
        assert call_kwargs.get("delete_after") == 10

    @pytest.mark.asyncio
    async def test_message_with_attachments_permitted(self, temp_json_env, onlyimages_cog, mock_message):
        """Test that a message with attachments in an only-images channel is permitted."""
        chan_id = str(mock_message.channel.id)
        config.save_onlyimages({chan_id: True})
        mock_attachment = MagicMock(spec=discord.Attachment)
        mock_message.attachments = [mock_attachment]

        await onlyimages_cog.on_message(mock_message)

        mock_message.delete.assert_not_awaited()
        mock_message.channel.send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_bot_messages_ignored(self, temp_json_env, onlyimages_cog, mock_message):
        """Test that bot messages are ignored even without attachments."""
        chan_id = str(mock_message.channel.id)
        config.save_onlyimages({chan_id: True})
        mock_message.author.bot = True
        mock_message.attachments = []

        await onlyimages_cog.on_message(mock_message)

        mock_message.delete.assert_not_awaited()
        mock_message.channel.send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_non_default_message_type_ignored(self, temp_json_env, onlyimages_cog, mock_message):
        """Test that non-default messages (e.g. pin notification) are ignored."""
        chan_id = str(mock_message.channel.id)
        config.save_onlyimages({chan_id: True})
        mock_message.type = discord.MessageType.pins_add
        mock_message.attachments = []

        await onlyimages_cog.on_message(mock_message)

        mock_message.delete.assert_not_awaited()
        mock_message.channel.send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_non_onlyimages_channel_ignored(self, temp_json_env, onlyimages_cog, mock_message):
        """Test that messages in channels not configured for onlyimages are ignored."""
        config.save_onlyimages({"999888": True})
        mock_message.channel.id = 111222
        mock_message.attachments = []

        await onlyimages_cog.on_message(mock_message)

        mock_message.delete.assert_not_awaited()
        mock_message.channel.send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_forbidden_delete_handled_gracefully(self, temp_json_env, onlyimages_cog, mock_message):
        """Test that discord.Forbidden on delete is logged and does not crash the listener."""
        chan_id = str(mock_message.channel.id)
        config.save_onlyimages({chan_id: True})
        mock_message.attachments = []
        mock_message.delete.side_effect = discord.Forbidden(MagicMock(), "Missing Permissions")

        await onlyimages_cog.on_message(mock_message)

        mock_message.delete.assert_awaited_once()
        mock_message.channel.send.assert_awaited_once()
