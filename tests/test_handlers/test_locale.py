# -*- coding: utf-8 -*-
"""
Tests for handlers/locale.py (i18n engine).
Verifies default locale, German translations, dot notation, interpolations,
fallbacks, caching, and guild/context resolution.
"""

import os
import json
import pytest
from unittest.mock import MagicMock, patch

import handlers.locale as loc
from handlers.locale import (
    t,
    get_guild_locale,
    set_guild_locale,
    load_locales,
    _get_nested,
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
)


@pytest.fixture(autouse=True)
def reset_locale_state():
    """Ensure clean locale cache and guild locale cache for every test."""
    loc._guild_locale_cache.clear()
    load_locales()
    yield
    loc._guild_locale_cache.clear()
    load_locales()


class TestLocaleBasics:
    """Test default locale and basic translations."""

    def test_default_locale_is_english(self):
        assert DEFAULT_LOCALE == "en"
        assert "en" in SUPPORTED_LOCALES
        assert "de" in SUPPORTED_LOCALES

    def test_default_translation_english(self):
        # Default without guild or lang should be English
        assert t("common.yes") == "Yes"
        assert t("common.no") == "No"
        assert t("common.success") == "Success"
        assert t("common.error") == "Error"

    def test_german_translation_explicit(self):
        # Explicit lang='de'
        assert t("common.yes", lang="de") == "Ja"
        assert t("common.no", lang="de") == "Nein"
        assert t("common.success", lang="de") == "Erfolg"
        assert t("common.error", lang="de") == "Fehler"


class TestDotNotationAndNesting:
    """Test retrieval of keys using dot notation."""

    def test_nested_keys_retrieval(self):
        assert t("setup.categories.overview", lang="en") == "Overview (Dashboard)"
        assert t("setup.categories.overview", lang="de") == "Übersicht (Dashboard)"
        assert t("setup.categories.protection", lang="en") == "Protection & Security"
        assert t("setup.categories.protection", lang="de") == "Schutz & Automod"

    def test_get_nested_helper_direct(self):
        data = {
            "a": {
                "b": {
                    "c": "deep_value"
                },
                "number": 42,
                "null_val": None
            }
        }
        assert _get_nested(data, "a.b.c") == "deep_value"
        assert _get_nested(data, "a.number") == 42
        assert _get_nested(data, "a.null_val") is None
        assert _get_nested(data, "a.b.nonexistent") is None
        assert _get_nested(data, "nonexistent.key") is None
        # Traversing into a non-dict should return None safely
        assert _get_nested(data, "a.number.subfield") is None


class TestStringInterpolation:
    """Test keyword formatting and error resilience."""

    def test_format_kwargs_success(self):
        # en: "setup.title": "{guild_name} • Server Control Center"
        rendered_en = t("setup.title", lang="en", guild_name="TestServer")
        assert rendered_en == "TestServer • Server Control Center"

        # de: "setup.title": "{guild_name} • Server Control Center"
        rendered_de = t("setup.title", lang="de", guild_name="DeutscheGilde")
        assert rendered_de == "DeutscheGilde • Server Control Center"

    def test_format_kwargs_with_custom_template(self, monkeypatch):
        mock_cache = {
            "en": {"test": {"greet": "Hello {name}, you have {count} messages!"}},
            "de": {"test": {"greet": "Hallo {name}, du hast {count} Nachrichten!"}}
        }
        monkeypatch.setattr(loc, "_locale_cache", mock_cache)

        result_en = t("test.greet", lang="en", name="Alice", count=5)
        assert result_en == "Hello Alice, you have 5 messages!"

        result_de = t("test.greet", lang="de", name="Bob", count=10)
        assert result_de == "Hallo Bob, du hast 10 Nachrichten!"

    def test_format_kwargs_missing_key_in_template_returns_raw(self, monkeypatch):
        # If kwargs format fails (e.g. KeyError due to missing required placeholder), returns unformatted string
        mock_cache = {
            "en": {"test": {"broken": "Hello {name}, code: {code}"}}
        }
        monkeypatch.setattr(loc, "_locale_cache", mock_cache)

        # Missing 'code' keyword argument
        result = t("test.broken", lang="en", name="Alice")
        assert result == "Hello {name}, code: {code}"


class TestFallbackMechanisms:
    """Test fallback when keys are missing in German or in all locales."""

    def test_fallback_to_english_when_missing_in_german(self, monkeypatch):
        mock_cache = {
            "en": {
                "unique": {"feature": "English Only Feature"},
                "shared": {"key": "English Shared"}
            },
            "de": {
                "shared": {"key": "German Shared"}
                # "unique.feature" is absent
            }
        }
        monkeypatch.setattr(loc, "_locale_cache", mock_cache)

        # Present in DE -> returns German
        assert t("shared.key", lang="de") == "German Shared"
        # Missing in DE -> falls back to EN
        assert t("unique.feature", lang="de") == "English Only Feature"

    def test_fallback_to_default_parameter_when_missing_everywhere(self):
        assert t("non.existent.key", default="Custom Fallback") == "Custom Fallback"
        assert t("non.existent.key", lang="de", default="Deutscher Fallback") == "Deutscher Fallback"

    def test_fallback_to_key_name_when_missing_everywhere_without_default(self):
        assert t("some.totally.missing.key") == "some.totally.missing.key"
        assert t("some.totally.missing.key", lang="de") == "some.totally.missing.key"


class TestGuildLocaleAndCaching:
    """Test get_guild_locale, set_guild_locale, and in-memory caching."""

    def test_get_guild_locale_default_and_none(self):
        assert get_guild_locale(None) == "en"
        assert get_guild_locale("") == "en"

    def test_set_guild_locale_invalid_language(self):
        success = set_guild_locale(12345, "fr")
        assert success is False
        assert get_guild_locale(12345) == "en"

    def test_set_and_get_guild_locale_success(self, temp_json_env):
        guild_id = 987654321
        success = set_guild_locale(guild_id, "de")
        assert success is True
        assert get_guild_locale(guild_id) == "de"
        assert loc._guild_locale_cache[str(guild_id)] == "de"

    def test_guild_locale_cache_hits_without_db(self, monkeypatch):
        guild_id = 55555
        loc._guild_locale_cache[str(guild_id)] = "de"

        # Mock get_guild_config to ensure it's NOT called when cache has the key
        mock_get_cfg = MagicMock()
        monkeypatch.setattr("handlers.locale.get_guild_config", mock_get_cfg)

        assert get_guild_locale(guild_id) == "de"
        mock_get_cfg.assert_not_called()

    def test_get_guild_locale_db_fetch_and_cache(self, monkeypatch):
        guild_id = 77777
        loc._guild_locale_cache.clear()

        # Database returns language "de"
        monkeypatch.setattr(
            "handlers.locale.get_guild_config",
            lambda gid: {"locale": "de"}
        )

        assert get_guild_locale(guild_id) == "de"
        assert loc._guild_locale_cache[str(guild_id)] == "de"

    def test_get_guild_locale_database_exception_returns_default(self, monkeypatch):
        def raise_err(gid):
            raise RuntimeError("Database disconnected")

        monkeypatch.setattr("handlers.locale.get_guild_config", raise_err)
        loc._guild_locale_cache.clear()

        assert get_guild_locale(88888) == "en"

    def test_set_guild_locale_database_exception(self, monkeypatch):
        def raise_err(gid, key, val):
            raise RuntimeError("Write failed")

        monkeypatch.setattr("handlers.locale.set_guild_config", raise_err)
        success = set_guild_locale(88888, "de")
        assert success is False


class TestContextResolution:
    """Test passing guild_id, guild object, or ctx object to t()."""

    def test_t_with_guild_id_int(self, temp_json_env):
        set_guild_locale(123, "de")
        assert t("common.yes", guild_id=123) == "Ja"

    def test_t_with_guild_id_str(self, temp_json_env):
        set_guild_locale("456", "de")
        assert t("common.yes", guild_id="456") == "Ja"

    def test_t_with_guild_object(self, mock_guild, temp_json_env):
        set_guild_locale(mock_guild.id, "de")
        assert t("common.yes", guild=mock_guild) == "Ja"

    def test_t_with_mock_context(self, mock_context, temp_json_env):
        set_guild_locale(mock_context.guild.id, "de")
        assert t("common.yes", ctx=mock_context) == "Ja"

    def test_t_with_context_without_guild(self):
        ctx_no_guild = MagicMock()
        ctx_no_guild.guild = None
        # Should fallback to default 'en'
        assert t("common.yes", ctx=ctx_no_guild) == "Yes"

    def test_t_explicit_lang_overrides_guild(self, mock_guild, temp_json_env):
        # Guild is set to German, but explicit lang='en' overrides it
        set_guild_locale(mock_guild.id, "de")
        assert t("common.yes", guild=mock_guild, lang="en") == "Yes"


class TestLoadLocalesHandling:
    """Test edge cases for loading locale files."""

    def test_load_locales_file_not_found(self, monkeypatch, tmp_path):
        monkeypatch.setattr(loc, "LOCALES_DIR", str(tmp_path / "empty_locales"))
        load_locales()
        assert loc._locale_cache.get("en") == {}
        assert loc._locale_cache.get("de") == {}

    def test_load_locales_invalid_json(self, monkeypatch, tmp_path):
        bad_dir = tmp_path / "bad_locales"
        bad_dir.mkdir(parents=True, exist_ok=True)
        bad_file = bad_dir / "en.json"
        bad_file.write_text("{invalid_json: true,", encoding="utf-8")

        monkeypatch.setattr(loc, "LOCALES_DIR", str(bad_dir))
        load_locales()
        assert loc._locale_cache.get("en") == {}
