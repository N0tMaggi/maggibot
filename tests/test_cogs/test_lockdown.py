# -*- coding: utf-8 -*-
"""
Tests for CommandLockdown cog and global_lockdown_check:
- Toggle /lockdown command (owner vs non-owner)
- Lockdown state persistence in configuration
- global_lockdown_check blocking non-owners when active and passing when inactive
"""

import pytest
import discord
from unittest.mock import MagicMock, AsyncMock, patch

from cogs.owner.commandlockdown import CommandLockdown, LockdownCheckFailure, global_lockdown_check
import handlers.config as config


def bind_cog_commands(cog):
    for attr_name in dir(cog):
        attr = getattr(cog, attr_name, None)
        if hasattr(attr, "cog"):
            attr.cog = cog
    return cog


@pytest.fixture
def lockdown_cog(mock_bot):
    cog = CommandLockdown(mock_bot)
    return bind_cog_commands(cog)


OWNER_ID = 111222333444
NON_OWNER_ID = 999888777666


class TestLockdownCommand:
    @pytest.mark.asyncio
    async def test_non_owner_lockdown_attempt_denied(self, temp_json_env, lockdown_cog, mock_context, monkeypatch):
        """Test non-owner user attempting /lockdown is denied and lockdown is not toggled."""
        monkeypatch.setattr("cogs.owner.commandlockdown.get_owner", lambda: OWNER_ID)
        mock_context.user.id = NON_OWNER_ID

        # Ensure initial state is False
        config.save_lockdown_config(False)

        await lockdown_cog.lockdown(mock_context)

        mock_context.defer.assert_awaited_once_with(ephemeral=True)
        mock_context.followup.send.assert_awaited_once()

        embed = mock_context.followup.send.call_args.kwargs["embed"]
        assert isinstance(embed, discord.Embed)
        # Verify denial embed
        assert embed.color.value in [0xE74C3C, 0x992D22]

        # Verify lockdown state unchanged
        assert config.load_lockdown_config()["lockdown"] is False

    @pytest.mark.asyncio
    async def test_owner_lockdown_toggle_on_and_off(self, temp_json_env, lockdown_cog, mock_context, monkeypatch):
        """Test bot owner successfully toggles lockdown ON, then OFF."""
        monkeypatch.setattr("cogs.owner.commandlockdown.get_owner", lambda: OWNER_ID)
        mock_context.user.id = OWNER_ID

        config.save_lockdown_config(False)

        # 1. Toggle ON
        await lockdown_cog.lockdown(mock_context)

        mock_context.followup.send.assert_awaited_once()
        embed1 = mock_context.followup.send.call_args.kwargs["embed"]
        assert config.load_lockdown_config()["lockdown"] is True
        # Activated status embed
        field_values1 = " ".join(f.value for f in embed1.fields)
        assert "gesperrt" in field_values1.lower() or "locked" in field_values1.lower()

        # 2. Toggle OFF
        mock_context.followup.send.reset_mock()
        await lockdown_cog.lockdown(mock_context)

        mock_context.followup.send.assert_awaited_once()
        embed2 = mock_context.followup.send.call_args.kwargs["embed"]
        assert config.load_lockdown_config()["lockdown"] is False
        field_values2 = " ".join(f.value for f in embed2.fields)
        assert "betriebsbereit" in field_values2.lower() or "operational" in field_values2.lower()

    @pytest.mark.asyncio
    async def test_lockdown_state_persistence(self, temp_json_env, mock_bot):
        """Test lockdown state persists across cog reload / separate instances."""
        config.save_lockdown_config(True)

        cog1 = CommandLockdown(mock_bot)
        assert cog1.lockdown_data.get("lockdown") is True

        config.save_lockdown_config(False)
        cog2 = CommandLockdown(mock_bot)
        assert cog2.lockdown_data.get("lockdown") is False


class TestGlobalLockdownCheck:
    @pytest.mark.asyncio
    async def test_lockdown_inactive_allows_all(self, temp_json_env, mock_context, monkeypatch):
        """Test global_lockdown_check passes for both owner and non-owner when inactive."""
        monkeypatch.setattr("cogs.owner.commandlockdown.get_owner", lambda: OWNER_ID)
        config.save_lockdown_config(False)

        # Non-owner passes
        mock_context.user.id = NON_OWNER_ID
        assert await global_lockdown_check(mock_context) is True

        # Owner passes
        mock_context.user.id = OWNER_ID
        assert await global_lockdown_check(mock_context) is True

    @pytest.mark.asyncio
    async def test_lockdown_active_allows_owner(self, temp_json_env, mock_context, monkeypatch):
        """Test global_lockdown_check allows bot owner even when lockdown is active."""
        monkeypatch.setattr("cogs.owner.commandlockdown.get_owner", lambda: OWNER_ID)
        config.save_lockdown_config(True)

        mock_context.user.id = OWNER_ID
        assert await global_lockdown_check(mock_context) is True

    @pytest.mark.asyncio
    async def test_lockdown_active_blocks_non_owner(self, temp_json_env, mock_context, monkeypatch):
        """Test global_lockdown_check blocks non-owner with LockdownCheckFailure and warning embed."""
        monkeypatch.setattr("cogs.owner.commandlockdown.get_owner", lambda: OWNER_ID)
        config.save_lockdown_config(True)

        mock_context.user.id = NON_OWNER_ID
        mock_context.response.is_done.return_value = False

        with pytest.raises(LockdownCheckFailure) as exc_info:
            await global_lockdown_check(mock_context)

        assert "Lockdown active" in str(exc_info.value)
        mock_context.response.send_message.assert_awaited_once()
        embed = mock_context.response.send_message.call_args.kwargs["embed"]
        assert isinstance(embed, discord.Embed)
        assert mock_context.response.send_message.call_args.kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_lockdown_active_blocks_non_owner_when_response_done(self, temp_json_env, mock_context, monkeypatch):
        """Test global_lockdown_check uses followup if response is already done."""
        monkeypatch.setattr("cogs.owner.commandlockdown.get_owner", lambda: OWNER_ID)
        config.save_lockdown_config(True)

        mock_context.user.id = NON_OWNER_ID
        mock_context.response.is_done.return_value = True

        with pytest.raises(LockdownCheckFailure):
            await global_lockdown_check(mock_context)

        mock_context.followup.send.assert_awaited_once()
        embed = mock_context.followup.send.call_args.kwargs["embed"]
        assert isinstance(embed, discord.Embed)
