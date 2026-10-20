# -*- coding: utf-8 -*-
"""
Tests for Moderation cogs:
- ModCommunityBan (vote start, self-target, execute ban, button callback, DM notification)
- ModCommunityMute (vote start, self-target, timeout execution, permissions check, vote casting)
"""

import pytest
import discord
import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from discord.ext import commands
from cogs.moderation.communityban import ModCommunityBan
from cogs.moderation.communitymute import ModCommunityMute


def bind_cog_commands(cog):
    for attr_name in dir(cog):
        attr = getattr(cog, attr_name, None)
        if hasattr(attr, "cog"):
            attr.cog = cog
    return cog


@pytest.fixture
def ban_cog(mock_bot):
    cog = ModCommunityBan(mock_bot)
    return bind_cog_commands(cog)


@pytest.fixture
def mute_cog(mock_bot):
    cog = ModCommunityMute(mock_bot)
    return bind_cog_commands(cog)


@pytest.fixture
def target_member(mock_guild):
    target = MagicMock(spec=discord.Member)
    target.id = 888111222
    target.name = "TargetUser"
    target.display_name = "TargetUser"
    target.mention = "<@888111222>"
    target.display_avatar = MagicMock()
    target.display_avatar.url = "https://cdn.discordapp.com/embed/avatars/2.png"
    target.guild = mock_guild
    target.send = AsyncMock()
    target.timeout = AsyncMock()
    return target


@pytest.fixture
def mock_interaction(mock_guild, mock_member):
    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild = mock_guild
    interaction.user = mock_member
    interaction.message = MagicMock(spec=discord.Message)
    interaction.message.edit = AsyncMock()
    interaction.message.channel = MagicMock(spec=discord.TextChannel)
    interaction.message.channel.send = AsyncMock()
    interaction.message.guild = mock_guild
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)
    return interaction


class TestCommunityBan:
    @pytest.mark.asyncio
    async def test_start_ban_vote_success(self, ban_cog, mock_context, target_member):
        """Test starting a valid community ban vote creates embed and BanVoteView."""
        await ban_cog.community_ban(mock_context, target_member, reason="Griefing")

        mock_context.respond.assert_awaited_once()
        call_kwargs = mock_context.respond.call_args.kwargs
        assert "embed" in call_kwargs
        assert isinstance(call_kwargs["view"], ModCommunityBan.BanVoteView)
        assert target_member.mention in call_kwargs["embed"].description

    @pytest.mark.asyncio
    async def test_ban_vote_self_target_prevented(self, ban_cog, mock_context):
        """Test user cannot initiate a ban vote against themselves."""
        await ban_cog.community_ban(mock_context, mock_context.author, reason="Self ban")

        mock_context.respond.assert_awaited_once()
        call_kwargs = mock_context.respond.call_args.kwargs
        assert call_kwargs.get("ephemeral") is True
        embed = call_kwargs["embed"]
        assert "Invalid Target" in embed.title

    @pytest.mark.asyncio
    async def test_ban_vote_permissions_check(self, ban_cog, mock_context):
        """Test community ban command enforces administrator permissions."""
        assert len(ban_cog.community_ban.checks) > 0
        check = ban_cog.community_ban.checks[0]

        # Author with admin passes check
        mock_context.channel.permissions_for = MagicMock(return_value=discord.Permissions(administrator=True))
        assert check(mock_context) is True

        # Non-admin author raises MissingPermissions
        mock_context.channel.permissions_for = MagicMock(return_value=discord.Permissions(administrator=False))
        with pytest.raises(commands.MissingPermissions):
            check(mock_context)

    @pytest.mark.asyncio
    async def test_execute_ban_button_callback_and_dm(self, ban_cog, target_member, mock_interaction):
        """Test clicking execute ban button bans target, edits message, and sends DM."""
        view = ban_cog.BanVoteView(ban_cog, target_member, "Rule violations", mock_interaction.user)
        button = view.children[0]

        mock_interaction.guild.ban = AsyncMock()

        await button.callback(mock_interaction)

        # Ban executed on guild
        mock_interaction.guild.ban.assert_awaited_once_with(
            target_member,
            reason="Community ban: Rule violations"
        )

        # Message edited and confirmation response sent
        mock_interaction.message.edit.assert_awaited_once()
        mock_interaction.response.send_message.assert_awaited_once()
        assert "Ban confirmed" in mock_interaction.response.send_message.call_args.args[0]

        # Target received DM
        target_member.send.assert_awaited_once()
        dm_embed = target_member.send.call_args.kwargs["embed"]
        assert "Community Ban" in dm_embed.title

        # Button state updated
        assert view.confirmed is True
        assert button.disabled is True
        assert button.label == "Ban Executed"

    @pytest.mark.asyncio
    async def test_execute_ban_already_confirmed_prevented(self, ban_cog, target_member, mock_interaction):
        """Test clicking execute ban again after confirmation is rejected."""
        view = ban_cog.BanVoteView(ban_cog, target_member, "Spam", mock_interaction.user)
        view.confirmed = True
        button = view.children[0]

        mock_interaction.guild.ban = AsyncMock()

        await button.callback(mock_interaction)

        mock_interaction.guild.ban.assert_not_awaited()
        mock_interaction.response.send_message.assert_awaited_once_with(
            "⚠️ Ban already executed",
            ephemeral=True
        )

    @pytest.mark.asyncio
    async def test_execute_ban_dm_forbidden_handled(self, ban_cog, target_member, mock_interaction):
        """Test target DM Forbidden exception does not crash ban execution."""
        view = ban_cog.BanVoteView(ban_cog, target_member, "Griefing", mock_interaction.user)
        button = view.children[0]

        mock_interaction.guild.ban = AsyncMock()
        target_member.send.side_effect = discord.Forbidden(MagicMock(), "DMs disabled")

        # Must not raise
        await button.callback(mock_interaction)

        mock_interaction.guild.ban.assert_awaited_once()
        assert view.confirmed is True


class TestCommunityMute:
    @pytest.mark.asyncio
    async def test_start_mute_vote_success(self, mute_cog, mock_context, target_member):
        """Test starting a valid community mute vote sets up MuteVoteView."""
        mock_orig_response = MagicMock(spec=discord.InteractionMessage)
        mock_context.interaction.original_response = AsyncMock(return_value=mock_orig_response)

        await mute_cog.community_mute(mock_context, target_member, reason="Excessive noise")

        mock_context.respond.assert_awaited_once()
        call_kwargs = mock_context.respond.call_args.kwargs
        assert "embed" in call_kwargs
        assert isinstance(call_kwargs["view"], ModCommunityMute.MuteVoteView)
        assert target_member.mention in call_kwargs["embed"].description

    @pytest.mark.asyncio
    async def test_mute_vote_self_target_prevented(self, mute_cog, mock_context):
        """Test user cannot initiate a mute vote against themselves."""
        await mute_cog.community_mute(mock_context, mock_context.author, reason="Self mute")

        mock_context.respond.assert_awaited_once()
        call_kwargs = mock_context.respond.call_args.kwargs
        assert call_kwargs.get("ephemeral") is True
        embed = call_kwargs["embed"]
        assert "Invalid Target" in embed.title

    @pytest.mark.asyncio
    async def test_mute_vote_permissions_check(self, mute_cog, mock_context):
        """Test community mute command enforces administrator permissions."""
        assert len(mute_cog.community_mute.checks) > 0
        check = mute_cog.community_mute.checks[0]

        # Author with admin passes check
        mock_context.channel.permissions_for = MagicMock(return_value=discord.Permissions(administrator=True))
        assert check(mock_context) is True

        # Non-admin author raises MissingPermissions
        mock_context.channel.permissions_for = MagicMock(return_value=discord.Permissions(administrator=False))
        with pytest.raises(commands.MissingPermissions):
            check(mock_context)

    @pytest.mark.asyncio
    async def test_vote_button_callback_voting_and_switching(self, mute_cog, target_member, mock_interaction):
        """Test VoteButton records votes and handles switching choices without duplicate votes."""
        vote_end = discord.utils.utcnow() + datetime.timedelta(seconds=30)
        view = mute_cog.MuteVoteView(target_member, "Spamming", mock_interaction.user, vote_end)

        # 1. Vote for 1h
        button_1h = next(btn for btn in view.children if getattr(btn, 'duration', None) == '1h')
        await button_1h.callback(mock_interaction)

        assert mock_interaction.user.id in view.votes['1h']
        assert "Your vote for 1h has been recorded" in mock_interaction.response.send_message.call_args.args[0]

        # 2. Duplicate vote for 1h rejected
        mock_interaction.response.send_message.reset_mock()
        await button_1h.callback(mock_interaction)
        assert "already voted for this option" in mock_interaction.response.send_message.call_args.args[0]

        # 3. Switch vote to 3h
        mock_interaction.response.send_message.reset_mock()
        button_3h = next(btn for btn in view.children if getattr(btn, 'duration', None) == '3h')
        await button_3h.callback(mock_interaction)

        assert mock_interaction.user.id not in view.votes['1h']
        assert mock_interaction.user.id in view.votes['3h']

    @pytest.mark.asyncio
    async def test_mute_view_timeout_execution(self, mute_cog, target_member, mock_guild):
        """Test on_timeout calculates winner, timeouts target member, and sends DM."""
        vote_end = discord.utils.utcnow() + datetime.timedelta(seconds=30)
        initiator = MagicMock(spec=discord.Member)
        initiator.id = 111111
        initiator.mention = "<@111111>"

        view = mute_cog.MuteVoteView(target_member, "Chat flooding", initiator, vote_end)
        # Pre-populate votes: '6h' has 2 votes, others have 0
        view.votes['6h'].add(12345)
        view.votes['6h'].add(67890)

        # Set up mock message
        mock_msg = MagicMock(spec=discord.Message)
        mock_msg.guild = mock_guild
        mock_msg.edit = AsyncMock()
        mock_msg.channel = MagicMock(spec=discord.TextChannel)
        mock_msg.channel.send = AsyncMock()
        view.message = mock_msg

        await view.on_timeout()

        # Target member was timed out
        target_member.timeout.assert_awaited_once()
        timeout_kwargs = target_member.timeout.call_args.kwargs
        assert "until" in timeout_kwargs
        assert timeout_kwargs["reason"] == "Community mute: Chat flooding"

        # Message edited and announcement sent in channel
        mock_msg.edit.assert_awaited_once()
        mock_msg.channel.send.assert_awaited_once()
        assert "muted for 6h" in mock_msg.channel.send.call_args.args[0]

        # Target received DM
        target_member.send.assert_awaited_once()
        dm_embed = target_member.send.call_args.kwargs["embed"]
        assert "Community Mute" in dm_embed.title
        assert "6h" in dm_embed.description

        # All buttons disabled
        assert all(child.disabled is True for child in view.children)
