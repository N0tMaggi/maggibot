# -*- coding: utf-8 -*-
"""
Tests for utils/embed_helpers.py and utils/colors.py.
Verifies create_embed options, specialized embed functions, author/footer/thumbnail/field
handling, Discord embed limit safety, and EmbedColors resolution.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock
import discord

from utils.embed_helpers import (
    create_embed,
    create_success_embed,
    create_error_embed,
    create_warning_embed,
    create_info_embed,
    create_mod_embed,
    create_security_embed,
)
from utils.colors import EmbedColors


class TestEmbedColors:
    """Test EmbedColors constants and resolution helper."""

    def test_color_constants_values(self):
        assert EmbedColors.SUCCESS == 0x2ECC71
        assert EmbedColors.ERROR == 0xE74C3C
        assert EmbedColors.WARNING == 0xF1C40F
        assert EmbedColors.INFO == 0x3498DB
        assert EmbedColors.MOD_ACTION == 0x992D22
        assert EmbedColors.SECURITY == 0x5865F2
        assert EmbedColors.DEFAULT == 0x2B2D31

    def test_get_with_int(self):
        assert EmbedColors.get(0xFF0000) == 0xFF0000
        assert EmbedColors.get(123456) == 123456

    def test_get_with_discord_color(self):
        dc = discord.Color.teal()
        assert EmbedColors.get(dc) == dc.value

    def test_get_with_named_strings(self):
        assert EmbedColors.get("success") == EmbedColors.SUCCESS
        assert EmbedColors.get("green") == EmbedColors.SUCCESS
        assert EmbedColors.get("error") == EmbedColors.ERROR
        assert EmbedColors.get("danger") == EmbedColors.ERROR
        assert EmbedColors.get("red") == EmbedColors.ERROR
        assert EmbedColors.get("warning") == EmbedColors.WARNING
        assert EmbedColors.get("yellow") == EmbedColors.WARNING
        assert EmbedColors.get("info") == EmbedColors.INFO
        assert EmbedColors.get("blue") == EmbedColors.INFO
        assert EmbedColors.get("mod_action") == EmbedColors.MOD_ACTION
        assert EmbedColors.get("mod") == EmbedColors.MOD_ACTION
        assert EmbedColors.get("security") == EmbedColors.SECURITY
        assert EmbedColors.get("vote") == EmbedColors.VOTE
        assert EmbedColors.get("status") == EmbedColors.STATUS
        assert EmbedColors.get("stats") == EmbedColors.STATS
        assert EmbedColors.get("purple") == EmbedColors.STATS
        assert EmbedColors.get("leaderboard") == EmbedColors.LEADERBOARD
        assert EmbedColors.get("pink") == EmbedColors.LEADERBOARD
        assert EmbedColors.get("verify") == EmbedColors.VERIFY
        assert EmbedColors.get("primary") == EmbedColors.PRIMARY
        assert EmbedColors.get("default") == EmbedColors.DEFAULT

    def test_get_case_insensitive_and_whitespace(self):
        assert EmbedColors.get("  SUCCESS  ") == EmbedColors.SUCCESS
        assert EmbedColors.get("ErRoR") == EmbedColors.ERROR
        assert EmbedColors.get("  bLuE ") == EmbedColors.INFO

    def test_get_fallback_behavior(self):
        # Unknown string with default
        assert EmbedColors.get("nonexistent_color", default=0x111111) == 0x111111
        # Unknown string without default
        assert EmbedColors.get("nonexistent_color") == EmbedColors.DEFAULT
        # Non-string invalid type (e.g., None, list, dict)
        assert EmbedColors.get(None, default=0x222222) == 0x222222
        assert EmbedColors.get(None) == EmbedColors.DEFAULT
        assert EmbedColors.get([]) == EmbedColors.DEFAULT


class TestCreateEmbedCore:
    """Test create_embed functionality, parameters, and defaults."""

    def test_create_embed_minimal(self):
        embed = create_embed(title="Test Title")
        assert embed.title == "Test Title"
        assert embed.description == ""
        assert embed.color.value == EmbedColors.INFO
        assert embed.footer.text == "MaggiBot"
        assert embed.timestamp is not None

    def test_create_embed_full(self, mock_member, mock_bot):
        fields = [
            ("Field 1", "Value 1", True),
            ("Field 2", "Value 2", False),
            {"name": "Field 3", "value": "Value 3", "inline": True}
        ]

        embed = create_embed(
            title="Full Embed",
            description="Testing full properties",
            color="success",
            author=mock_member,
            thumbnail="https://example.com/thumb.png",
            image="https://example.com/image.png",
            footer_text="Custom Footer",
            footer_icon="https://example.com/icon.png",
            timestamp=False,
            fields=fields
        )

        assert embed.title == "Full Embed"
        assert embed.description == "Testing full properties"
        assert embed.color.value == EmbedColors.SUCCESS
        assert embed.author.name == mock_member.display_name
        assert embed.author.icon_url == mock_member.display_avatar.url
        assert embed.thumbnail.url == "https://example.com/thumb.png"
        assert embed.image.url == "https://example.com/image.png"
        assert embed.footer.text == "Custom Footer"
        assert embed.footer.icon_url == "https://example.com/icon.png"
        assert embed.timestamp is None
        assert len(embed.fields) == 3
        assert embed.fields[0].name == "Field 1"
        assert embed.fields[0].value == "Value 1"
        assert embed.fields[0].inline is True
        assert embed.fields[1].inline is False
        assert embed.fields[2].name == "Field 3"
        assert embed.fields[2].inline is True

    def test_footer_fallback_to_bot_user(self, mock_bot):
        embed = create_embed(title="Bot Footer", bot_user=mock_bot.user)
        assert embed.footer.text == "MaggiBot"
        assert embed.footer.icon_url == mock_bot.user.display_avatar.url

    def test_fields_tuple_variations(self):
        fields = [
            ("Two Element", "Only name and val"),
            ("Three Element", "With inline", True),
        ]
        embed = create_embed(title="Fields", fields=fields)
        assert len(embed.fields) == 2
        assert embed.fields[0].inline is False
        assert embed.fields[1].inline is True

    def test_author_without_display_avatar(self):
        author = MagicMock(spec=[])
        author.display_name = "SimpleUser"
        embed = create_embed(title="Author Test", author=author)
        assert embed.author.name == "SimpleUser"
        assert embed.author.icon_url is None


class TestSpecializedEmbeds:
    """Test specialized embed helpers: success, error, warning, info, mod, security."""

    def test_create_success_embed(self, mock_member):
        embed = create_success_embed("Operation Completed", "All good", author=mock_member)
        assert embed.title == "✅ Operation Completed"
        assert embed.color.value == EmbedColors.SUCCESS
        assert embed.description == "All good"
        assert embed.author.name == mock_member.display_name

    def test_create_success_embed_no_duplicate_icon(self):
        embed1 = create_success_embed("✅ Already has icon")
        assert embed1.title == "✅ Already has icon"

        embed2 = create_success_embed("🎉 Celebratory success")
        assert embed2.title == "🎉 Celebratory success"

        embed3 = create_success_embed("✓ Checkmark success")
        assert embed3.title == "✓ Checkmark success"

    def test_create_error_embed(self):
        embed = create_error_embed("Failed to execute", "Invalid permissions")
        assert embed.title == "❌ Failed to execute"
        assert embed.color.value == EmbedColors.ERROR
        assert embed.description == "Invalid permissions"

    def test_create_error_embed_no_duplicate_icon(self):
        embed1 = create_error_embed("❌ Already has cross")
        assert embed1.title == "❌ Already has cross"

        embed2 = create_error_embed("🚫 Forbidden access")
        assert embed2.title == "🚫 Forbidden access"

        embed3 = create_error_embed("⚠️ Warning used as error")
        assert embed3.title == "⚠️ Warning used as error"

    def test_create_warning_embed(self):
        embed = create_warning_embed("High Latency Detected", "Check network")
        assert embed.title == "⚠️ High Latency Detected"
        assert embed.color.value == EmbedColors.WARNING
        assert embed.description == "Check network"

    def test_create_warning_embed_no_duplicate_icon(self):
        embed1 = create_warning_embed("⚠️ Warning here")
        assert embed1.title == "⚠️ Warning here"

        embed2 = create_warning_embed("⚡ Alert notice")
        assert embed2.title == "⚡ Alert notice"

    def test_create_info_embed(self, mock_bot):
        embed = create_info_embed("Bot Statistics", "Running smooth", bot_user=mock_bot.user)
        assert embed.title == "ℹ️ Bot Statistics"
        assert embed.color.value == EmbedColors.INFO
        assert embed.footer.icon_url == mock_bot.user.display_avatar.url

    def test_create_info_embed_no_duplicate_icon(self):
        embed1 = create_info_embed("ℹ️ Info title")
        assert embed1.title == "ℹ️ Info title"

        embed2 = create_info_embed("🤖 Bot status")
        assert embed2.title == "🤖 Bot status"

        embed3 = create_info_embed("⚙️ System settings")
        assert embed3.title == "⚙️ System settings"

    def test_create_mod_embed(self, mock_member):
        embed = create_mod_embed("User Banned", "Banned for spam", author=mock_member)
        assert embed.title == "User Banned"
        assert embed.color.value == EmbedColors.MOD_ACTION
        assert embed.footer.text == "Maggi Moderation"

    def test_create_security_embed(self):
        embed = create_security_embed("Raid Mode Activated", "Lockdown initiated")
        assert embed.title == "🛡️ Raid Mode Activated"
        assert embed.color.value == EmbedColors.SECURITY
        assert embed.footer.text == "MaggiBot Security System"

    def test_create_security_embed_no_duplicate_icon(self):
        embed1 = create_security_embed("🛡️ Protection on")
        assert embed1.title == "🛡️ Protection on"

        embed2 = create_security_embed("🔒 Channel locked")
        assert embed2.title == "🔒 Channel locked"


class TestEmbedLimitsAndSafety:
    """Test safety handling under maximum Discord embed constraints."""

    def test_maximum_allowed_title_length(self):
        # Discord limit for embed title is 256 characters
        title_256 = "A" * 256
        embed = create_embed(title=title_256)
        assert len(embed.title) == 256

    def test_maximum_allowed_description_length(self):
        # Discord limit for embed description is 4096 characters
        desc_4096 = "B" * 4096
        embed = create_embed(title="Desc Test", description=desc_4096)
        assert len(embed.description) == 4096

    def test_maximum_allowed_field_lengths(self):
        # Field name max 256, Field value max 1024
        name_256 = "N" * 256
        val_1024 = "V" * 1024
        fields = [(name_256, val_1024)]
        embed = create_embed(title="Field Limit Test", fields=fields)
        assert len(embed.fields[0].name) == 256
        assert len(embed.fields[0].value) == 1024

    def test_maximum_25_fields_handling(self):
        # Discord allows up to 25 fields
        fields = [(f"Field {i}", f"Value {i}") for i in range(25)]
        embed = create_embed(title="25 Fields", fields=fields)
        assert len(embed.fields) == 25

    def test_footer_text_length_safety(self):
        footer_2048 = "F" * 2048
        embed = create_embed(title="Footer Limit", footer_text=footer_2048)
        assert len(embed.footer.text) == 2048

    def test_fields_with_non_string_types(self):
        # Numbers, booleans, or objects should safely convert to str without raising exceptions
        fields = [
            (12345, 67890, True),
            {"name": 999, "value": False, "inline": False}
        ]
        embed = create_embed(title="Type Safety", fields=fields)
        assert embed.fields[0].name == "12345"
        assert embed.fields[0].value == "67890"
        assert embed.fields[1].name == "999"
        assert embed.fields[1].value == "False"
