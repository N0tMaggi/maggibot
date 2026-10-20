# -*- coding: utf-8 -*-
"""
Tests for AdminFeedback cog.
"""

import pytest
import discord
from unittest.mock import MagicMock, AsyncMock

from cogs.admin.adminfeedback import AdminFeedback
import handlers.config as config


@pytest.fixture
def adminfeedback_cog(mock_bot):
    cog = AdminFeedback(mock_bot)
    cog.feedback.cog = cog
    cog.view_feedbacks.cog = cog
    cog.view_feedbacks_from.cog = cog
    cog.owner_deletefeedback.cog = cog
    return cog


@pytest.fixture
def mock_admin(mock_guild):
    admin = MagicMock(spec=discord.Member)
    admin.id = 888888888
    admin.name = "AdminUser"
    admin.display_name = "AdminUser"
    admin.mention = "<@888888888>"
    admin.send = AsyncMock()
    return admin


@pytest.fixture
def team_role_setup(mock_guild, mock_admin):
    role = MagicMock(spec=discord.Role)
    role.id = 777777777
    role.members = [mock_admin]
    mock_guild.get_role = MagicMock(side_effect=lambda rid: role if rid == role.id else None)
    return role


class TestFeedbackSending:
    @pytest.mark.asyncio
    async def test_send_feedback_to_admin_success(self, temp_json_env, adminfeedback_cog, mock_context, mock_admin, team_role_setup):
        """Test successfully sending feedback to an admin in the team role."""
        gid = str(mock_context.guild.id)
        adminfeedback_cog.admin_feedback["configs"][gid] = {"team_role": team_role_setup.id}

        await adminfeedback_cog.feedback(mock_context, mock_admin, feedback="Great server!")

        # DM sent to admin
        mock_admin.send.assert_awaited_once()
        dm_embed = mock_admin.send.call_args[1]["embed"]
        assert "Great server!" in dm_embed.description

        # Saved in feedback storage
        saved_feedbacks = adminfeedback_cog.admin_feedback["feedbacks"]
        assert len(saved_feedbacks) == 1
        feedback_id, entry = next(iter(saved_feedbacks.items()))
        assert len(feedback_id) == 8
        assert entry["from"] == str(mock_context.author.id)
        assert entry["to"] == str(mock_admin.id)
        assert entry["feedback"] == "Great server!"
        assert entry["server"] == gid

        # Saved on disk
        stored_disk = config.load_admin_feedback()
        assert feedback_id in stored_disk["feedbacks"]

        # Response to user
        mock_context.respond.assert_awaited_once()
        resp_kwargs = mock_context.respond.call_args[1]
        assert "embed" in resp_kwargs
        assert resp_kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_self_feedback_error(self, temp_json_env, adminfeedback_cog, mock_context, team_role_setup):
        """Test sending feedback to oneself produces self_error."""
        gid = str(mock_context.guild.id)
        adminfeedback_cog.admin_feedback["configs"][gid] = {"team_role": team_role_setup.id}
        # Author is also in team_role
        team_role_setup.members.append(mock_context.author)

        await adminfeedback_cog.feedback(mock_context, mock_context.author, feedback="Testing self feedback")

        mock_context.respond.assert_awaited_once()
        resp_kwargs = mock_context.respond.call_args[1]
        assert "embed" in resp_kwargs
        assert resp_kwargs.get("ephemeral") is True
        assert len(adminfeedback_cog.admin_feedback["feedbacks"]) == 0

    @pytest.mark.asyncio
    async def test_not_in_team_error(self, temp_json_env, adminfeedback_cog, mock_context, team_role_setup):
        """Test sending feedback to a member who is not in the team role."""
        gid = str(mock_context.guild.id)
        adminfeedback_cog.admin_feedback["configs"][gid] = {"team_role": team_role_setup.id}

        regular_member = MagicMock(spec=discord.Member)
        regular_member.id = 999123
        regular_member.send = AsyncMock()

        await adminfeedback_cog.feedback(mock_context, regular_member, feedback="Hello there")

        regular_member.send.assert_not_awaited()
        mock_context.respond.assert_awaited_once()
        resp_kwargs = mock_context.respond.call_args[1]
        assert "embed" in resp_kwargs
        assert resp_kwargs.get("ephemeral") is True
        assert len(adminfeedback_cog.admin_feedback["feedbacks"]) == 0

    @pytest.mark.asyncio
    async def test_unconfigured_feedback_error(self, temp_json_env, adminfeedback_cog, mock_context, mock_admin):
        """Test sending feedback when the server has no configured team_role."""
        adminfeedback_cog.admin_feedback["configs"].clear()

        await adminfeedback_cog.feedback(mock_context, mock_admin, feedback="Hello")

        mock_admin.send.assert_not_awaited()
        mock_context.respond.assert_awaited_once()
        resp_kwargs = mock_context.respond.call_args[1]
        assert "embed" in resp_kwargs
        assert resp_kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_dm_disabled_error(self, temp_json_env, adminfeedback_cog, mock_context, mock_admin, team_role_setup):
        """Test sending feedback when admin user has DMs disabled (Forbidden)."""
        gid = str(mock_context.guild.id)
        adminfeedback_cog.admin_feedback["configs"][gid] = {"team_role": team_role_setup.id}
        mock_admin.send.side_effect = discord.Forbidden(MagicMock(), "DMs blocked")

        await adminfeedback_cog.feedback(mock_context, mock_admin, feedback="Hello admin")

        mock_admin.send.assert_awaited_once()
        mock_context.respond.assert_awaited_once()
        resp_kwargs = mock_context.respond.call_args[1]
        assert "embed" in resp_kwargs
        assert resp_kwargs.get("ephemeral") is True
        # Ensure feedback was not stored
        assert len(adminfeedback_cog.admin_feedback["feedbacks"]) == 0


class TestViewFeedbacks:
    @pytest.mark.asyncio
    async def test_view_feedbacks_for_admin_empty(self, temp_json_env, adminfeedback_cog, mock_context, mock_admin):
        """Test view_feedbacks when no feedback has been sent to the admin."""
        adminfeedback_cog.admin_feedback["feedbacks"].clear()

        await adminfeedback_cog.view_feedbacks(mock_context, mock_admin)

        mock_context.respond.assert_awaited_once()
        resp_kwargs = mock_context.respond.call_args[1]
        assert "embed" in resp_kwargs
        assert resp_kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_view_feedbacks_for_admin_populated(self, temp_json_env, adminfeedback_cog, mock_context, mock_admin):
        """Test view_feedbacks retrieves feedback directed to the admin."""
        adminfeedback_cog.admin_feedback["feedbacks"] = {
            "fb101": {
                "server": str(mock_context.guild.id),
                "channel": "333333333333",
                "time": "2026-10-20 12:00:00",
                "from": "222222222222",
                "to": str(mock_admin.id),
                "feedback": "Outstanding bot performance"
            }
        }

        await adminfeedback_cog.view_feedbacks(mock_context, mock_admin)

        mock_context.respond.assert_awaited_once()
        resp_kwargs = mock_context.respond.call_args[1]
        embed = resp_kwargs["embed"]
        assert "fb101" in embed.description
        assert "Outstanding bot performance" in embed.description

    @pytest.mark.asyncio
    async def test_view_feedbacks_from_user(self, temp_json_env, adminfeedback_cog, mock_context, mock_admin):
        """Test view_feedbacks_from retrieves feedback submitted by a specific user."""
        adminfeedback_cog.admin_feedback["feedbacks"] = {
            "fb202": {
                "server": str(mock_context.guild.id),
                "channel": "333333333333",
                "time": "2026-10-20 13:00:00",
                "from": str(mock_context.author.id),
                "to": str(mock_admin.id),
                "feedback": "Feature request details"
            }
        }

        await adminfeedback_cog.view_feedbacks_from(mock_context, mock_context.author)

        mock_context.respond.assert_awaited_once()
        resp_kwargs = mock_context.respond.call_args[1]
        embed = resp_kwargs["embed"]
        assert "fb202" in embed.description
        assert "Feature request details" in embed.description


class TestOwnerDeleteFeedback:
    @pytest.mark.asyncio
    async def test_owner_deletefeedback_success(self, temp_json_env, adminfeedback_cog, mock_context):
        """Test deleting an existing feedback ID as owner."""
        adminfeedback_cog.admin_feedback["feedbacks"] = {
            "del123": {
                "server": str(mock_context.guild.id),
                "time": "2026-10-20",
                "from": "111",
                "to": "222",
                "feedback": "Spam message"
            }
        }

        await adminfeedback_cog.owner_deletefeedback(mock_context, "del123")

        assert "del123" not in adminfeedback_cog.admin_feedback["feedbacks"]
        stored_disk = config.load_admin_feedback()
        assert "del123" not in stored_disk["feedbacks"]

        mock_context.respond.assert_awaited_once()
        resp_kwargs = mock_context.respond.call_args[1]
        assert "embed" in resp_kwargs
        assert resp_kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_owner_deletefeedback_not_found(self, temp_json_env, adminfeedback_cog, mock_context):
        """Test deleting a non-existent feedback ID returns error embed."""
        adminfeedback_cog.admin_feedback["feedbacks"] = {}

        await adminfeedback_cog.owner_deletefeedback(mock_context, "nonexistent_id")

        mock_context.respond.assert_awaited_once()
        resp_kwargs = mock_context.respond.call_args[1]
        assert "embed" in resp_kwargs
        assert resp_kwargs.get("ephemeral") is True
