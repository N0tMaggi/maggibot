# -*- coding: utf-8 -*-
"""
Tests for VoiceGate cog and VoiceGateAcceptView.
"""

import pytest
import discord
from unittest.mock import MagicMock, AsyncMock, patch

from cogs.admin.voicegate import VoiceGate, VoiceGateAcceptView
import handlers.config as config


@pytest.fixture
def voicegate_cog(mock_bot):
    return VoiceGate(mock_bot)


@pytest.fixture
def mock_voice_states(mock_guild):
    before_state = MagicMock(spec=discord.VoiceState)
    before_state.channel = None

    after_state = MagicMock(spec=discord.VoiceState)
    after_channel = MagicMock(spec=discord.VoiceChannel)
    after_channel.id = 9001
    after_channel.name = "Gate Channel"
    after_state.channel = after_channel

    return before_state, after_state


class TestVoiceGateAcceptView:
    @pytest.mark.asyncio
    async def test_accept_button_matching_user(self, temp_json_env):
        """Test accept button clicked by the intended member accepts and stops view."""
        member_id = 12345
        guild_id = 67890
        view = VoiceGateAcceptView(member_id=member_id, guild_id=guild_id)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user = MagicMock()
        interaction.user.id = member_id
        interaction.response = MagicMock()
        interaction.response.edit_message = AsyncMock()

        # Trigger button callback
        button = view.accept_button
        await view.accept_button.callback(interaction)

        assert view.accepted is True
        assert button.disabled is True
        assert view.is_finished()
        interaction.response.edit_message.assert_awaited_once_with(view=view)

    @pytest.mark.asyncio
    async def test_accept_button_non_matching_user(self, temp_json_env):
        """Test accept button clicked by a different member is rejected."""
        member_id = 12345
        guild_id = 67890
        view = VoiceGateAcceptView(member_id=member_id, guild_id=guild_id)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user = MagicMock()
        interaction.user.id = 99999  # Different user
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        button = view.accept_button
        await view.accept_button.callback(interaction)

        assert view.accepted is False
        assert button.disabled is False
        assert not view.is_finished()
        interaction.response.send_message.assert_awaited_once()
        assert interaction.response.send_message.call_args[1].get("ephemeral") is True


class TestVoiceGateListener:
    @pytest.mark.asyncio
    async def test_user_joining_gate_channel_and_accepts(self, temp_json_env, voicegate_cog, mock_member, mock_voice_states):
        """Test user joins gate channel, gets muted, receives DM, accepts rules, and is moved to final channel."""
        before_state, after_state = mock_voice_states
        gid = str(mock_member.guild.id)
        final_chan = MagicMock(spec=discord.VoiceChannel)
        final_chan.id = 9002
        final_chan.name = "Final Lounge"
        mock_member.guild.get_channel = MagicMock(return_value=final_chan)

        config.savevoicegateconfig({
            gid: {
                "gate_channel_id": after_state.channel.id,
                "final_channel_id": final_chan.id,
                "rules_text": "Server Rules"
            }
        })

        mock_dm = MagicMock()
        mock_dm.send = AsyncMock()
        mock_member.create_dm = AsyncMock(return_value=mock_dm)

        # Patch VoiceGateAcceptView so wait() returns with accepted = True
        with patch("cogs.admin.voicegate.VoiceGateAcceptView") as MockViewCls:
            mock_view_instance = MagicMock()
            mock_view_instance.accepted = True
            mock_view_instance.wait = AsyncMock()
            MockViewCls.return_value = mock_view_instance

            await voicegate_cog.on_voice_state_update(mock_member, before_state, after_state)

        # Member should have been muted
        mock_member.edit.assert_any_await(mute=True)
        # DM sent
        mock_member.create_dm.assert_awaited_once()
        mock_dm.send.assert_awaited_once()
        # View waited
        mock_view_instance.wait.assert_awaited_once()
        # Moved to final channel and unmuted
        mock_member.move_to.assert_awaited_once_with(final_chan)
        mock_member.edit.assert_any_await(mute=False)
        mock_member.send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_user_joining_gate_channel_timeout(self, temp_json_env, voicegate_cog, mock_member, mock_voice_states):
        """Test user times out without accepting rules and gets kicked from voice channel."""
        before_state, after_state = mock_voice_states
        gid = str(mock_member.guild.id)
        config.savevoicegateconfig({
            gid: {
                "gate_channel_id": after_state.channel.id,
                "final_channel_id": 9002,
                "rules_text": "Server Rules"
            }
        })

        mock_dm = MagicMock()
        mock_dm.send = AsyncMock()
        mock_member.create_dm = AsyncMock(return_value=mock_dm)

        # Patch VoiceGateAcceptView with accepted = False (timeout)
        with patch("cogs.admin.voicegate.VoiceGateAcceptView") as MockViewCls:
            mock_view_instance = MagicMock()
            mock_view_instance.accepted = False
            mock_view_instance.wait = AsyncMock()
            MockViewCls.return_value = mock_view_instance

            await voicegate_cog.on_voice_state_update(mock_member, before_state, after_state)

        # User is kicked (moved to None) and notified of timeout
        mock_member.move_to.assert_awaited_once_with(None)
        mock_member.send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_user_leaving_gate_channel_gets_unmuted(self, temp_json_env, voicegate_cog, mock_member):
        """Test user leaving the gate channel gets unmuted and cleared from pending verifications."""
        gate_channel = MagicMock(spec=discord.VoiceChannel)
        gate_channel.id = 9001

        before_state = MagicMock(spec=discord.VoiceState)
        before_state.channel = gate_channel

        after_state = MagicMock(spec=discord.VoiceState)
        after_state.channel = None  # Disconnected

        gid = str(mock_member.guild.id)
        config.savevoicegateconfig({
            gid: {
                "gate_channel_id": gate_channel.id,
                "final_channel_id": 9002
            }
        })
        voicegate_cog.pending_verifications.add(mock_member.id)

        await voicegate_cog.on_voice_state_update(mock_member, before_state, after_state)

        mock_member.edit.assert_awaited_once_with(mute=False)
        assert mock_member.id not in voicegate_cog.pending_verifications

    @pytest.mark.asyncio
    async def test_unconfigured_guild_ignored(self, temp_json_env, voicegate_cog, mock_member, mock_voice_states):
        """Test voice update in a guild without voicegate config is ignored."""
        before_state, after_state = mock_voice_states
        config.savevoicegateconfig({})

        await voicegate_cog.on_voice_state_update(mock_member, before_state, after_state)

        mock_member.edit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_non_gate_channel_ignored(self, temp_json_env, voicegate_cog, mock_member):
        """Test joining a non-gate voice channel is ignored."""
        chan = MagicMock(spec=discord.VoiceChannel)
        chan.id = 1111

        before_state = MagicMock(spec=discord.VoiceState)
        before_state.channel = None

        after_state = MagicMock(spec=discord.VoiceState)
        after_state.channel = chan

        gid = str(mock_member.guild.id)
        config.savevoicegateconfig({
            gid: {
                "gate_channel_id": 9999,
                "final_channel_id": 8888
            }
        })

        await voicegate_cog.on_voice_state_update(mock_member, before_state, after_state)

        mock_member.edit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_dm_failure_clears_pending_and_does_not_crash(self, temp_json_env, voicegate_cog, mock_member, mock_voice_states):
        """Test failure when sending DM (e.g. DMs closed) is logged and cleans up pending set."""
        before_state, after_state = mock_voice_states
        gid = str(mock_member.guild.id)
        config.savevoicegateconfig({
            gid: {
                "gate_channel_id": after_state.channel.id,
                "final_channel_id": 9002
            }
        })

        mock_member.create_dm = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "DMs closed"))

        await voicegate_cog.on_voice_state_update(mock_member, before_state, after_state)

        assert mock_member.id not in voicegate_cog.pending_verifications

    @pytest.mark.asyncio
    async def test_target_channel_missing_handles_gracefully(self, temp_json_env, voicegate_cog, mock_member, mock_voice_states):
        """Test that if the final channel is deleted/missing from guild, error is handled."""
        before_state, after_state = mock_voice_states
        gid = str(mock_member.guild.id)
        mock_member.guild.get_channel = MagicMock(return_value=None)

        config.savevoicegateconfig({
            gid: {
                "gate_channel_id": after_state.channel.id,
                "final_channel_id": 999999
            }
        })

        mock_dm = MagicMock()
        mock_dm.send = AsyncMock()
        mock_member.create_dm = AsyncMock(return_value=mock_dm)

        with patch("cogs.admin.voicegate.VoiceGateAcceptView") as MockViewCls:
            mock_view_instance = MagicMock()
            mock_view_instance.accepted = True
            mock_view_instance.wait = AsyncMock()
            MockViewCls.return_value = mock_view_instance

            await voicegate_cog.on_voice_state_update(mock_member, before_state, after_state)

        mock_member.send.assert_awaited_once()
        mock_member.move_to.assert_not_awaited()
