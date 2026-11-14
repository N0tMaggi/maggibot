# -*- coding: utf-8 -*-
"""
Tests for Stats cogs:
- UserStats (message XP, media attachment bonus, multipliers, level up, voice XP)
- Leaderboards (stats, leaderboard, serverleaderboard, xp-info commands)
- XPSetup (role multiplier management)
"""

import pytest
import discord
import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from cogs.stats.stats import UserStats
from cogs.stats.leaderboard import Leaderboards
from cogs.stats.xp_setup import XPSetup
import handlers.config as config


def bind_cog_commands(cog):
    for attr_name in dir(cog):
        attr = getattr(cog, attr_name, None)
        if hasattr(attr, "cog"):
            attr.cog = cog
    return cog


@pytest.fixture
def stats_cog(mock_bot):
    cog = UserStats(mock_bot)
    return bind_cog_commands(cog)


@pytest.fixture
def leaderboard_cog(mock_bot):
    cog = Leaderboards(mock_bot)
    return bind_cog_commands(cog)


@pytest.fixture
def xp_setup_cog(mock_bot):
    cog = XPSetup(mock_bot)
    return bind_cog_commands(cog)


@pytest.fixture
def mock_message(mock_guild, mock_member):
    msg = MagicMock(spec=discord.Message)
    msg.guild = mock_guild
    msg.author = mock_member
    msg.channel = MagicMock(spec=discord.TextChannel)
    msg.channel.id = 555555555
    msg.channel.name = "general-chat"
    msg.attachments = []
    return msg


class TestUserStatsMessageXP:
    @pytest.mark.asyncio
    async def test_message_xp_gain_basic(self, temp_json_env, stats_cog, mock_message):
        """Test basic message XP gain increments message count and XP."""
        await stats_cog.on_message(mock_message)

        data = config.load_stats()
        uid = str(mock_message.author.id)
        gid = str(mock_message.guild.id)

        assert uid in data
        assert data[uid]["xp"] == pytest.approx(config.MESSAGE_XP_COUNT)
        assert data[uid]["servers"][gid]["messages"] == 1
        assert data[uid]["servers"][gid]["media"] == 0

    @pytest.mark.asyncio
    async def test_ignore_bot_message_and_dms(self, temp_json_env, stats_cog, mock_message):
        """Test bot messages and DM messages are ignored."""
        # Bot message
        mock_message.author.bot = True
        await stats_cog.on_message(mock_message)
        assert config.load_stats() == {}

        # DM message (no guild)
        mock_message.author.bot = False
        mock_message.guild = None
        await stats_cog.on_message(mock_message)
        assert config.load_stats() == {}

    @pytest.mark.asyncio
    async def test_media_attachment_bonus_xp(self, temp_json_env, stats_cog, mock_message):
        """Test image and video attachments award bonus XP."""
        img_att = MagicMock(spec=discord.Attachment)
        img_att.content_type = "image/png"

        vid_att = MagicMock(spec=discord.Attachment)
        vid_att.content_type = "video/mp4"

        doc_att = MagicMock(spec=discord.Attachment)
        doc_att.content_type = "application/pdf"

        mock_message.attachments = [img_att, vid_att, doc_att]

        await stats_cog.on_message(mock_message)

        data = config.load_stats()
        uid = str(mock_message.author.id)
        gid = str(mock_message.guild.id)

        # 2 valid media attachments: MESSAGE_XP_COUNT + 2 * ATTACHMENT_XP_COUNT
        expected_xp = config.MESSAGE_XP_COUNT + (2 * config.ATTACHMENT_XP_COUNT)
        assert data[uid]["xp"] == pytest.approx(expected_xp)
        assert data[uid]["servers"][gid]["messages"] == 1
        assert data[uid]["servers"][gid]["media"] == 2

    @pytest.mark.asyncio
    async def test_xp_multipliers_applied_in_boosted_channel(self, temp_json_env, stats_cog, mock_message):
        """Test XP multiplier is applied when message is sent in boosted channel."""
        cid = str(mock_message.channel.id)
        role1 = MagicMock(spec=discord.Role)
        role1.id = 101010
        role2 = MagicMock(spec=discord.Role)
        role2.id = 202020

        mock_message.author.roles = [role1, role2]

        # Multiplier config: boosted channel and role multipliers (role2 has 2.5x)
        config.save_multiplier_config({
            "channels": [cid],
            "multipliers": {
                str(role1.id): 1.5,
                str(role2.id): 2.5
            }
        })

        await stats_cog.on_message(mock_message)

        data = config.load_stats()
        uid = str(mock_message.author.id)
        expected_xp = config.MESSAGE_XP_COUNT * 2.5
        assert data[uid]["xp"] == pytest.approx(expected_xp)

    @pytest.mark.asyncio
    async def test_xp_multipliers_not_applied_in_unboosted_channel(self, temp_json_env, stats_cog, mock_message):
        """Test XP multiplier is ignored when message is sent outside boosted channels."""
        role = MagicMock(spec=discord.Role)
        role.id = 101010
        mock_message.author.roles = [role]

        # Boosted channel is different channel ID
        config.save_multiplier_config({
            "channels": ["999999999"],
            "multipliers": {str(role.id): 3.0}
        })

        await stats_cog.on_message(mock_message)

        data = config.load_stats()
        uid = str(mock_message.author.id)
        assert data[uid]["xp"] == pytest.approx(config.MESSAGE_XP_COUNT)

    @pytest.mark.asyncio
    async def test_level_up_calculation_and_dm_notification(self, temp_json_env, stats_cog, mock_message):
        """Test level up triggers DM notification with embed."""
        uid = str(mock_message.author.id)
        gid = str(mock_message.guild.id)

        # Prepopulate with 19.95 XP (level 0)
        config.save_stats({
            uid: {
                "xp": 19.95,
                "level": 0,
                "servers": {gid: {"messages": 10, "media": 0, "voiceminutes": 0}}
            }
        })

        await stats_cog.on_message(mock_message)

        data = config.load_stats()
        assert data[uid]["level"] == 1
        assert data[uid]["xp"] >= 20.0

        # Verify DM sent
        mock_message.author.send.assert_awaited_once()
        embed = mock_message.author.send.call_args.kwargs["embed"]
        assert isinstance(embed, discord.Embed)
        assert embed.color == discord.Color.gold()

    @pytest.mark.asyncio
    async def test_level_up_dm_failure_handled_gracefully(self, temp_json_env, stats_cog, mock_message):
        """Test level up handles DM sending exceptions without crashing."""
        uid = str(mock_message.author.id)
        gid = str(mock_message.guild.id)
        config.save_stats({
            uid: {
                "xp": 19.95,
                "level": 0,
                "servers": {gid: {"messages": 5, "media": 0, "voiceminutes": 0}}
            }
        })

        mock_message.author.send.side_effect = discord.Forbidden(MagicMock(), "DMs closed")

        # Must not raise
        await stats_cog.on_message(mock_message)

        data = config.load_stats()
        assert data[uid]["level"] == 1


class TestUserStatsVoiceXP:
    @pytest.mark.asyncio
    async def test_voice_join_and_leave_duration_xp(self, temp_json_env, stats_cog, mock_member):
        """Test voice channel join and leave awards voice XP based on minutes."""
        uid = str(mock_member.id)
        gid = str(mock_member.guild.id)

        vc_before = MagicMock(spec=discord.VoiceChannel)
        vc_before.id = 12345
        vc_before.name = "Talk Room"

        # 1. Join voice
        before_join = MagicMock(spec=discord.VoiceState)
        before_join.channel = None
        after_join = MagicMock(spec=discord.VoiceState)
        after_join.channel = vc_before

        await stats_cog.on_voice_state_update(mock_member, before_join, after_join)
        key = (uid, gid)
        assert key in stats_cog.voice_times

        # 2. Simulate 10 minutes passing
        join_time = stats_cog.voice_times[key]
        stats_cog.voice_times[key] = join_time - datetime.timedelta(minutes=10, seconds=5)

        # 3. Leave voice
        before_leave = MagicMock(spec=discord.VoiceState)
        before_leave.channel = vc_before
        after_leave = MagicMock(spec=discord.VoiceState)
        after_leave.channel = None

        await stats_cog.on_voice_state_update(mock_member, before_leave, after_leave)

        # Verified key cleaned up
        assert key not in stats_cog.voice_times

        data = config.load_stats()
        assert uid in data
        expected_xp = 10 * config.VOICE_XP_COUNT
        assert data[uid]["xp"] == pytest.approx(expected_xp)
        assert data[uid]["servers"][gid]["voiceminutes"] == 10

    @pytest.mark.asyncio
    async def test_voice_less_than_one_minute_no_xp(self, temp_json_env, stats_cog, mock_member):
        """Test leaving voice under 1 minute awards 0 XP."""
        uid = str(mock_member.id)
        gid = str(mock_member.guild.id)

        vc = MagicMock(spec=discord.VoiceChannel)
        vc.id = 12345
        vc.name = "Quick Chat"

        # Join
        before_join = MagicMock(channel=None)
        after_join = MagicMock(channel=vc)
        await stats_cog.on_voice_state_update(mock_member, before_join, after_join)

        # Leave 20 seconds later
        key = (uid, gid)
        stats_cog.voice_times[key] = stats_cog.voice_times[key] - datetime.timedelta(seconds=20)

        before_leave = MagicMock(channel=vc)
        after_leave = MagicMock(channel=None)
        await stats_cog.on_voice_state_update(mock_member, before_leave, after_leave)

        assert key not in stats_cog.voice_times
        assert config.load_stats() == {}

    @pytest.mark.asyncio
    async def test_voice_level_up_and_multiplier(self, temp_json_env, stats_cog, mock_member):
        """Test voice XP respects channel multipliers and triggers level up."""
        uid = str(mock_member.id)
        gid = str(mock_member.guild.id)

        vc = MagicMock(spec=discord.VoiceChannel)
        vc.id = 88888
        vc.name = "Boosted VC"

        role = MagicMock(spec=discord.Role)
        role.id = 77777
        mock_member.roles = [role]

        config.save_multiplier_config({
            "channels": [str(vc.id)],
            "multipliers": {str(role.id): 2.0}
        })

        # Prepopulate with 19.90 XP (level 0) so that 10 mins with 2x multiplier triggers level up
        config.save_stats({
            uid: {
                "xp": 19.90,
                "level": 0,
                "servers": {gid: {"messages": 0, "media": 0, "voiceminutes": 0}}
            }
        })

        # Join
        await stats_cog.on_voice_state_update(mock_member, MagicMock(channel=None), MagicMock(channel=vc))

        # 10 minutes: 10 * VOICE_XP_COUNT * 2.0 multiplier
        key = (uid, gid)
        stats_cog.voice_times[key] = stats_cog.voice_times[key] - datetime.timedelta(minutes=10)

        # Leave
        await stats_cog.on_voice_state_update(mock_member, MagicMock(channel=vc), MagicMock(channel=None))

        data = config.load_stats()
        expected_xp = 19.90 + (10 * config.VOICE_XP_COUNT * 2.0)
        assert data[uid]["xp"] == pytest.approx(expected_xp)
        assert data[uid]["level"] == 1
        mock_member.send.assert_awaited_once()


class TestLeaderboardCommands:
    @pytest.mark.asyncio
    async def test_stats_command_for_self(self, temp_json_env, leaderboard_cog, mock_context):
        """Test /stats command with populated user data."""
        uid = str(mock_context.author.id)
        gid = str(mock_context.guild.id)

        config.save_stats({
            uid: {
                "xp": 45.5,
                "level": 2,
                "servers": {
                    gid: {"messages": 100, "media": 15, "voiceminutes": 60}
                }
            }
        })

        await leaderboard_cog.stats(mock_context, user=None)

        mock_context.defer.assert_awaited_once()
        mock_context.followup.send.assert_awaited_once()
        embed = mock_context.followup.send.call_args.kwargs["embed"]

        assert isinstance(embed, discord.Embed)
        field_names = [f.name for f in embed.fields]
        assert any("level" in name.lower() for name in field_names)
        assert any("xp" in name.lower() for name in field_names)

    @pytest.mark.asyncio
    async def test_stats_command_no_data(self, temp_json_env, leaderboard_cog, mock_context):
        """Test /stats command for user without any recorded stats."""
        await leaderboard_cog.stats(mock_context, user=None)

        mock_context.followup.send.assert_awaited_once()
        embed = mock_context.followup.send.call_args.kwargs["embed"]
        assert embed.description is not None

    @pytest.mark.asyncio
    async def test_leaderboard_global(self, temp_json_env, leaderboard_cog, mock_context):
        """Test /leaderboard displays sorted global rankings."""
        config.save_stats({
            "101": {"xp": 50.0, "level": 2, "servers": {"1": {"messages": 5, "media": 1, "voiceminutes": 0}}},
            "102": {"xp": 120.0, "level": 6, "servers": {"1": {"messages": 20, "media": 5, "voiceminutes": 10}}},
            "103": {"xp": 10.0, "level": 0, "servers": {"1": {"messages": 1, "media": 0, "voiceminutes": 0}}}
        })

        await leaderboard_cog.leaderboard(mock_context)

        mock_context.followup.send.assert_awaited_once()
        embed = mock_context.followup.send.call_args.kwargs["embed"]
        assert len(embed.fields) == 3
        # Top 1 user is 102 (120 XP)
        assert "🥇" in embed.fields[0].name

    @pytest.mark.asyncio
    async def test_server_leaderboard(self, temp_json_env, leaderboard_cog, mock_context):
        """Test /serverleaderboard filters and ranks only for current guild."""
        gid = str(mock_context.guild.id)
        other_gid = "999999"

        config.save_stats({
            "101": {"xp": 500.0, "level": 25, "servers": {other_gid: {"messages": 50, "media": 0, "voiceminutes": 0}}},
            "102": {"xp": 50.0, "level": 2, "servers": {gid: {"messages": 10, "media": 1, "voiceminutes": 5}}}
        })

        await leaderboard_cog.server_leaderboard(mock_context)

        mock_context.followup.send.assert_awaited_once()
        embed = mock_context.followup.send.call_args.kwargs["embed"]
        # Only user 102 belongs to current guild
        assert len(embed.fields) == 1
        assert "🥇" in embed.fields[0].name

    @pytest.mark.asyncio
    async def test_xp_info_command(self, temp_json_env, leaderboard_cog, mock_context):
        """Test /xp-info command outputs system overview and multipliers."""
        config.save_multiplier_config({
            "channels": ["333333333333"],
            "multipliers": {"777888": 2.0}
        })

        await leaderboard_cog.xp_info(mock_context)

        mock_context.respond.assert_awaited_once()
        embed = mock_context.respond.call_args.kwargs["embed"]
        assert isinstance(embed, discord.Embed)
        field_values = " ".join(f.value for f in embed.fields)
        assert str(config.MESSAGE_XP_COUNT) in field_values
        assert "2.0x" in field_values


class TestXPSetupCommands:
    @pytest.mark.asyncio
    async def test_xp_set_and_show_and_remove_multiplier(self, temp_json_env, xp_setup_cog, mock_context):
        """Test /xp-setmultiplier, /xp-showmultiplier, and /xp-removemultiplier."""
        role = MagicMock(spec=discord.Role)
        role.id = 444555
        role.name = "VIP"
        role.mention = "<@&444555>"
        mock_context.guild.get_role.return_value = role

        # Set multiplier
        await xp_setup_cog.xp_setmultiplier(mock_context, role, 2.5)
        mock_context.followup.send.assert_awaited()
        cfg = config.load_multiplier_config()
        assert cfg["multipliers"]["444555"] == 2.5

        # Show multipliers
        mock_context.followup.send.reset_mock()
        await xp_setup_cog.xp_showmultiplier(mock_context)
        embed = mock_context.followup.send.call_args.kwargs["embed"]
        assert any("2.5x" in f.value for f in embed.fields)

        # Remove multiplier
        mock_context.followup.send.reset_mock()
        await xp_setup_cog.xp_removemultiplier(mock_context, role)
        cfg_after = config.load_multiplier_config()
        assert "444555" not in cfg_after["multipliers"]
