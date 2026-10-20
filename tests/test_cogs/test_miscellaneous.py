# -*- coding: utf-8 -*-
"""
Tests for Miscellaneous cog:
- /serverinfo output and fields
- /userinfo for bots, guild members, and outside users
- /ping latency calculation and embed color assignment
"""

import pytest
import discord
import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from cogs.misc.miscellaneous import Miscellaneous
from utils.colors import EmbedColors


def bind_cog_commands(cog):
    for attr_name in dir(cog):
        attr = getattr(cog, attr_name, None)
        if hasattr(attr, "cog"):
            attr.cog = cog
    return cog


@pytest.fixture
def misc_cog(mock_bot):
    cog = Miscellaneous(mock_bot)
    return bind_cog_commands(cog)


class TestServerInfo:
    @pytest.mark.asyncio
    async def test_serverinfo_basic_fields(self, misc_cog, mock_context):
        """Test /serverinfo defers and responds with detailed embed fields."""
        guild = mock_context.guild
        guild.description = "A wonderful community"
        guild.created_at = datetime.datetime(2021, 5, 20, 12, 0, 0, tzinfo=datetime.timezone.utc)
        guild.text_channels = [MagicMock(spec=discord.TextChannel) for _ in range(3)]
        guild.voice_channels = [MagicMock(spec=discord.VoiceChannel) for _ in range(2)]
        guild.categories = [MagicMock(spec=discord.CategoryChannel)]
        guild.roles = [MagicMock(spec=discord.Role) for _ in range(5)]
        guild.emojis = [MagicMock(spec=discord.Emoji) for _ in range(10)]
        guild.features = ["COMMUNITY", "VANITY_URL"]
        guild.icon = MagicMock()
        guild.icon.url = "https://cdn.discordapp.com/icons/123/icon.png"
        guild.banner = MagicMock()
        guild.banner.url = "https://cdn.discordapp.com/banners/123/banner.png"

        await misc_cog.serverinfo(mock_context)

        mock_context.defer.assert_awaited_once()
        mock_context.respond.assert_awaited_once()

        embed = mock_context.respond.call_args.kwargs["embed"]
        assert isinstance(embed, discord.Embed)
        assert guild.name in embed.title
        assert embed.description == "A wonderful community"
        assert embed.thumbnail.url == guild.icon.url
        assert embed.image.url == guild.banner.url

        field_names = [f.name for f in embed.fields]
        field_values = " ".join(f.value for f in embed.fields)

        assert str(guild.id) in field_values
        assert str(guild.member_count) in field_values
        assert "Community, Vanity Url" in field_values

    @pytest.mark.asyncio
    async def test_serverinfo_long_features_truncation(self, misc_cog, mock_context):
        """Test features exceeding 500 characters are safely truncated."""
        guild = mock_context.guild
        guild.description = None
        guild.created_at = datetime.datetime(2021, 1, 1, tzinfo=datetime.timezone.utc)
        guild.icon = None
        guild.banner = None
        # Long list of features
        guild.features = [f"FEATURE_NUMBER_{i}_VERY_LONG_NAME" for i in range(40)]

        await misc_cog.serverinfo(mock_context)

        embed = mock_context.respond.call_args.kwargs["embed"]
        features_field = next(f for f in embed.fields if "feature" in f.name.lower())
        assert features_field.value.endswith("...```")


class TestUserInfo:
    @pytest.mark.asyncio
    async def test_userinfo_for_guild_member(self, misc_cog, mock_context):
        """Test /userinfo includes joined_at, roles, and highest_role for server members."""
        now = datetime.datetime(2023, 6, 1, tzinfo=datetime.timezone.utc)
        target = MagicMock(spec=discord.Member)
        target.id = 123456789
        target.name = "NormalUser"
        target.display_name = "NormalUser"
        target.mention = "<@123456789>"
        target.bot = False
        target.created_at = now
        target.joined_at = now + datetime.timedelta(days=10)
        target.display_avatar = MagicMock()
        target.display_avatar.url = "https://cdn.discordapp.com/avatars/target.png"

        role1 = MagicMock(spec=discord.Role)
        role1.mention = "<@&111>"
        role2 = MagicMock(spec=discord.Role)
        role2.mention = "<@&222>"
        target.roles = [MagicMock(spec=discord.Role), role1, role2]  # first is @everyone
        target.top_role = role2

        mock_context.guild.get_member.return_value = target

        await misc_cog.userinfo(mock_context, target=target)

        mock_context.defer.assert_awaited_once()
        mock_context.respond.assert_awaited_once()

        embed = mock_context.respond.call_args.kwargs["embed"]
        assert target.display_name in embed.title
        assert embed.thumbnail.url == target.display_avatar.url

        field_names = [f.name for f in embed.fields]
        field_values = " ".join(f.value for f in embed.fields)

        assert str(target.id) in field_values
        assert role1.mention in field_values
        assert role2.mention in field_values

    @pytest.mark.asyncio
    async def test_userinfo_for_bot_account(self, misc_cog, mock_context):
        """Test /userinfo indicates bot status when target is a bot."""
        bot_target = MagicMock(spec=discord.Member)
        bot_target.id = 999111
        bot_target.name = "RobotUser"
        bot_target.display_name = "RobotUser"
        bot_target.mention = "<@999111>"
        bot_target.bot = True
        bot_target.created_at = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
        bot_target.joined_at = None
        bot_target.roles = [MagicMock(spec=discord.Role)]
        bot_target.top_role = None
        bot_target.display_avatar = MagicMock()
        bot_target.display_avatar.url = "https://cdn.discordapp.com/avatars/bot.png"

        mock_context.guild.get_member.return_value = bot_target

        await misc_cog.userinfo(mock_context, target=bot_target)

        embed = mock_context.respond.call_args.kwargs["embed"]
        # Find bot account field
        bot_field = next(f for f in embed.fields if "bot" in f.name.lower())
        assert bot_field.value.lower() in ["ja", "yes", "true"]

    @pytest.mark.asyncio
    async def test_userinfo_for_outside_user(self, misc_cog, mock_context):
        """Test /userinfo handles outside user (not in current guild) without member fields."""
        outside_user = MagicMock(spec=discord.User)
        outside_user.id = 555444333
        outside_user.name = "OutsideUser"
        outside_user.display_name = "OutsideUser"
        outside_user.mention = "<@555444333>"
        outside_user.bot = False
        outside_user.created_at = datetime.datetime(2022, 3, 15, tzinfo=datetime.timezone.utc)
        outside_user.display_avatar = MagicMock()
        outside_user.display_avatar.url = "https://cdn.discordapp.com/avatars/outside.png"

        # Not in guild
        mock_context.guild.get_member.return_value = None

        await misc_cog.userinfo(mock_context, target=outside_user)

        embed = mock_context.respond.call_args.kwargs["embed"]
        field_names = [f.name.lower() for f in embed.fields]

        # Should NOT contain joined or roles fields
        assert not any("joined" in name for name in field_names)
        assert not any("role" in name for name in field_names)

    @pytest.mark.asyncio
    async def test_userinfo_more_than_15_roles_truncation(self, misc_cog, mock_context):
        """Test user with > 15 roles truncates display cleanly."""
        target = MagicMock(spec=discord.Member)
        target.id = 112233
        target.name = "ManyRolesUser"
        target.display_name = "ManyRolesUser"
        target.mention = "<@112233>"
        target.bot = False
        target.created_at = datetime.datetime(2021, 1, 1, tzinfo=datetime.timezone.utc)
        target.joined_at = datetime.datetime(2021, 2, 1, tzinfo=datetime.timezone.utc)
        target.display_avatar = MagicMock()
        target.display_avatar.url = "https://cdn.discordapp.com/avatars/many.png"

        # 20 roles plus @everyone
        roles = [MagicMock(spec=discord.Role)]
        for i in range(20):
            r = MagicMock(spec=discord.Role)
            r.mention = f"<@&role_{i}>"
            roles.append(r)
        target.roles = roles
        target.top_role = roles[-1]

        mock_context.guild.get_member.return_value = target

        await misc_cog.userinfo(mock_context, target=target)

        embed = mock_context.respond.call_args.kwargs["embed"]
        roles_field = next(f for f in embed.fields if "roll" in f.name.lower() or "role" in f.name.lower())
        assert "more" in roles_field.value.lower() or "weitere" in roles_field.value.lower() or "5" in roles_field.value


class TestPing:
    @pytest.mark.asyncio
    async def test_ping_low_latency_green(self, misc_cog, mock_context):
        """Test /ping with latency < 150ms assigns success (green) color."""
        misc_cog.bot.latency = 0.042  # 42ms

        await misc_cog.ping(mock_context)

        mock_context.respond.assert_awaited_once()
        embed = mock_context.respond.call_args.kwargs["embed"]
        assert isinstance(embed, discord.Embed)
        assert "42" in embed.description
        assert embed.color.value == EmbedColors.SUCCESS

    @pytest.mark.asyncio
    async def test_ping_medium_latency_warning(self, misc_cog, mock_context):
        """Test /ping with 150ms <= latency < 300ms assigns warning (yellow) color."""
        misc_cog.bot.latency = 0.220  # 220ms

        await misc_cog.ping(mock_context)

        embed = mock_context.respond.call_args.kwargs["embed"]
        assert "220" in embed.description
        assert embed.color.value == EmbedColors.WARNING

    @pytest.mark.asyncio
    async def test_ping_high_latency_error(self, misc_cog, mock_context):
        """Test /ping with latency >= 300ms assigns error (red) color."""
        misc_cog.bot.latency = 0.450  # 450ms

        await misc_cog.ping(mock_context)

        embed = mock_context.respond.call_args.kwargs["embed"]
        assert "450" in embed.description
        assert embed.color.value == EmbedColors.ERROR
