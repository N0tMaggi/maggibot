# -*- coding: utf-8 -*-
"""
Tests for SetupDashboard cog and DashboardView.
"""

import pytest
import discord
from unittest.mock import MagicMock, AsyncMock, patch

from cogs.setup.setup_dashboard import DashboardView, VoiceGateRulesModal, SetupDashboard
import handlers.config as config
from handlers.locale import get_guild_locale, set_guild_locale


@pytest.fixture
def mock_interaction(mock_guild, mock_member):
    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild = mock_guild
    interaction.user = mock_member
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.data = {}
    return interaction


class TestDashboardView:
    @pytest.mark.asyncio
    async def test_initialization_and_config_loading(self, temp_json_env, mock_bot, mock_guild, mock_member):
        """Test DashboardView initializes with default configs and components."""
        view = DashboardView(mock_bot, mock_guild, mock_member)

        assert view.bot == mock_bot
        assert view.guild == mock_guild
        assert view.author == mock_member
        assert view.current_category == "overview"
        assert isinstance(view.server_config, dict)
        assert isinstance(view.voicegate_config, dict)
        assert isinstance(view.onlyimages, dict)
        assert isinstance(view.admin_feedback, dict)
        assert view.lockdown is False
        assert len(view.children) > 0

    @pytest.mark.asyncio
    async def test_build_embed_fields(self, temp_json_env, mock_bot, mock_guild, mock_member):
        """Test build_embed() generates fields for Protection, Logging, Roles, Media, Language, Feedback."""
        # Prepopulate configs
        gid = str(mock_guild.id)
        config.saveserverconfig({
            gid: {
                "protection": True,
                "antispam": True,
                "antiraid": False,
                "antighostping": False,
                "antiwebhook": True,
                "logchannel": 111222333,
                "logging_forum": 444555666,
                "autoroleid": 777888999,
                "tiktok_auto_embed": False,
            }
        })
        config.savevoicegateconfig({
            gid: {
                "gate_channel_id": 121212,
                "final_channel_id": 343434,
                "rules_text": "Rules"
            }
        })
        config.save_onlyimages({"555666": True})
        config.save_admin_feedback({
            "configs": {
                gid: {"team_role": 999111}
            },
            "feedbacks": {}
        })

        view = DashboardView(mock_bot, mock_guild, mock_member)
        embed = view.build_embed()

        assert isinstance(embed, discord.Embed)
        field_names = [f.name for f in embed.fields]

        # Verify all main sections are present in embed fields
        assert any("Protection" in name or "Schutz" in name for name in field_names)
        assert any("Logging" in name or "Protokoll" in name for name in field_names)
        assert any("Roles" in name or "Rollen" in name for name in field_names)
        assert any("Media" in name or "Medien" in name for name in field_names)
        assert any("Language" in name or "Sprache" in name for name in field_names)

        # Check field contents
        protection_field = next(f for f in embed.fields if "Protection" in f.name or "Schutz" in f.name)
        assert "🟢 ON" in protection_field.value
        assert "Anti-Spam: 🟢" in protection_field.value

        logging_field = next(f for f in embed.fields if "Logging" in f.name or "Protokoll" in f.name)
        assert "<#444555666>" in logging_field.value

        roles_field = next(f for f in embed.fields if "Roles" in f.name or "Rollen" in f.name)
        assert "<@&777888999>" in roles_field.value
        assert "<#121212> ➔ <#343434>" in roles_field.value

    @pytest.mark.asyncio
    @pytest.mark.parametrize("category", ["overview", "protection", "logging", "roles", "media", "language"])
    async def test_category_switching(self, temp_json_env, mock_bot, mock_guild, mock_member, mock_interaction, category):
        """Test category switching updates current_category and edits message."""
        view = DashboardView(mock_bot, mock_guild, mock_member)
        mock_interaction.data = {"values": [category]}

        await view._on_category_select(mock_interaction)

        assert view.current_category == category
        mock_interaction.response.edit_message.assert_awaited_once()
        call_kwargs = mock_interaction.response.edit_message.call_args[1]
        assert "embed" in call_kwargs
        assert call_kwargs["view"] == view

    @pytest.mark.asyncio
    async def test_language_switching(self, temp_json_env, mock_bot, mock_guild, mock_member, mock_interaction):
        """Test language switching callback toggles between 'en' and 'de'."""
        view = DashboardView(mock_bot, mock_guild, mock_member)

        # Switch to German
        await view._switch_language(mock_interaction, "de")
        assert get_guild_locale(mock_guild.id) == "de"
        mock_interaction.response.edit_message.assert_awaited_once()

        # Switch to English
        mock_interaction.response.edit_message.reset_mock()
        await view._switch_language(mock_interaction, "en")
        assert get_guild_locale(mock_guild.id) == "en"
        mock_interaction.response.edit_message.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("setting_key", ["protection", "antispam", "antiraid", "tiktok_auto_embed"])
    async def test_toggle_setting(self, temp_json_env, mock_bot, mock_guild, mock_member, mock_interaction, setting_key):
        """Test toggling various settings switches their boolean values and saves to config."""
        view = DashboardView(mock_bot, mock_guild, mock_member)
        initial_val = view.server_config.get(setting_key, False)

        # Toggle on/off
        await view._toggle_setting(mock_interaction, setting_key)
        assert view.server_config[setting_key] == (not initial_val)
        mock_interaction.response.edit_message.assert_awaited_once()

        # Verify saved in storage
        saved_cfg = config.loadserverconfig()
        assert saved_cfg[str(mock_guild.id)][setting_key] == (not initial_val)

        # Toggle back
        mock_interaction.response.edit_message.reset_mock()
        await view._toggle_setting(mock_interaction, setting_key)
        assert view.server_config[setting_key] == initial_val
        saved_cfg = config.loadserverconfig()
        assert saved_cfg[str(mock_guild.id)][setting_key] == initial_val

    @pytest.mark.asyncio
    async def test_toggle_lockdown(self, temp_json_env, mock_bot, mock_guild, mock_member, mock_interaction):
        """Test toggling global lockdown setting."""
        view = DashboardView(mock_bot, mock_guild, mock_member)
        assert view.lockdown is False

        await view._toggle_lockdown(mock_interaction)
        assert view.lockdown is True
        assert config.load_lockdown_config()["lockdown"] is True
        mock_interaction.response.edit_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_logging_channel_select_and_clear(self, temp_json_env, mock_bot, mock_guild, mock_member, mock_interaction):
        """Test selecting text/forum channel and clearing log channel."""
        mock_chan = MagicMock(spec=discord.TextChannel)
        mock_chan.id = 888999111
        mock_chan.type = discord.ChannelType.text
        mock_guild.get_channel = MagicMock(return_value=mock_chan)

        view = DashboardView(mock_bot, mock_guild, mock_member)
        mock_interaction.data = {"values": [str(mock_chan.id)]}

        await view._on_log_channel_select(mock_interaction)
        assert view.server_config["logchannel"] == mock_chan.id

        # Test clear
        mock_interaction.response.edit_message.reset_mock()
        await view._clear_log_channel(mock_interaction)
        assert "logchannel" not in view.server_config
        assert "logging_forum" not in view.server_config

    @pytest.mark.asyncio
    async def test_autorole_select_and_clear(self, temp_json_env, mock_bot, mock_guild, mock_member, mock_interaction):
        """Test selecting and clearing autorole."""
        view = DashboardView(mock_bot, mock_guild, mock_member)
        mock_interaction.data = {"values": ["555444333"]}

        await view._on_autorole_select(mock_interaction)
        assert view.server_config["autoroleid"] == 555444333

        # Clear autorole
        mock_interaction.response.edit_message.reset_mock()
        await view._clear_autorole(mock_interaction)
        assert "autoroleid" not in view.server_config

    @pytest.mark.asyncio
    async def test_onlyimages_toggle_select(self, temp_json_env, mock_bot, mock_guild, mock_member, mock_interaction):
        """Test toggling a channel in onlyimages configuration."""
        view = DashboardView(mock_bot, mock_guild, mock_member)
        mock_interaction.data = {"values": ["777666"]}

        # Add
        await view._on_onlyimages_select(mock_interaction)
        assert "777666" in view.onlyimages
        assert config.load_onlyimages().get("777666") is True

        # Remove
        mock_interaction.response.edit_message.reset_mock()
        await view._on_onlyimages_select(mock_interaction)
        assert "777666" not in view.onlyimages

    @pytest.mark.asyncio
    async def test_navigation_buttons(self, temp_json_env, mock_bot, mock_guild, mock_member, mock_interaction):
        """Test back, refresh, and close buttons."""
        view = DashboardView(mock_bot, mock_guild, mock_member)
        view.current_category = "protection"

        await view._back_to_overview(mock_interaction)
        assert view.current_category == "overview"

        mock_interaction.response.edit_message.reset_mock()
        await view._on_refresh(mock_interaction)
        mock_interaction.response.edit_message.assert_awaited_once()

        mock_interaction.response.edit_message.reset_mock()
        await view._on_close(mock_interaction)
        assert view.is_finished()

    @pytest.mark.asyncio
    async def test_interaction_check(self, temp_json_env, mock_bot, mock_guild, mock_member, mock_interaction):
        """Test that only author or administrator can interact."""
        view = DashboardView(mock_bot, mock_guild, mock_member)

        # Author can interact
        mock_interaction.user = mock_member
        assert await view.interaction_check(mock_interaction) is True

        # Unauthorized user without admin perm is rejected
        other_user = MagicMock(spec=discord.Member)
        other_user.id = 999888777
        other_user.guild_permissions = discord.Permissions(administrator=False)
        mock_interaction.user = other_user

        assert await view.interaction_check(mock_interaction) is False
        mock_interaction.response.send_message.assert_awaited_once()


class TestVoiceGateRulesModal:
    @pytest.mark.asyncio
    async def test_modal_submission_saves_rules(self, temp_json_env, mock_bot, mock_guild, mock_member, mock_interaction):
        """Test VoiceGateRulesModal callback saves rules and updates parent view."""
        view = DashboardView(mock_bot, mock_guild, mock_member)
        modal = VoiceGateRulesModal(parent_view=view)

        modal.rules_input.value = "Rule 1: Be nice.\nRule 2: No spam."
        await modal.callback(mock_interaction)

        gid_str = str(mock_guild.id)
        assert view.voicegate_config[gid_str]["rules_text"] == "Rule 1: Be nice.\nRule 2: No spam."
        assert view.voicegate_config[gid_str]["need_accept_rules"] is True

        saved_vg = config.loadvoicegateconfig()
        assert saved_vg[gid_str]["rules_text"] == "Rule 1: Be nice.\nRule 2: No spam."
        mock_interaction.response.edit_message.assert_awaited_once()


class TestSetupDashboardCog:
    @pytest.mark.asyncio
    async def test_setup_command_execution(self, temp_json_env, mock_bot, mock_context):
        """Test /setup command defers and responds with DashboardView."""
        cog = SetupDashboard(mock_bot)
        cog.setup_command.cog = cog

        await cog.setup_command(mock_context)

        mock_context.defer.assert_awaited_once_with(ephemeral=True)
        mock_context.respond.assert_awaited_once()
        call_kwargs = mock_context.respond.call_args[1]
        assert "embed" in call_kwargs
        assert isinstance(call_kwargs["view"], DashboardView)
        assert call_kwargs["ephemeral"] is True
