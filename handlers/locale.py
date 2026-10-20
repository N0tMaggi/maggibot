# -*- coding: utf-8 -*-
"""
MaggiBot Localization (i18n) Engine
Handles dynamic multi-language translations (English & German) per-server.
English is the default. Configurable per server via /setup.
"""

import os
import json
from typing import Any, Dict, Optional, Union

from handlers.debug import LogDebug, LogError
from handlers.database import get_guild_config, set_guild_config

LOCALES_DIR = "locales"
DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = ["en", "de"]

_locale_cache: Dict[str, Dict[str, Any]] = {}
_guild_locale_cache: Dict[str, str] = {}


def load_locales():
    """Load all JSON translation files from locales/"""
    global _locale_cache
    os.makedirs(LOCALES_DIR, exist_ok=True)
    _locale_cache.clear()

    for lang in SUPPORTED_LOCALES:
        file_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    _locale_cache[lang] = json.load(f)
                LogDebug(f"Loaded locale: {lang}")
            except Exception as e:
                LogError(f"Failed to load locale file {file_path}: {e}")
                _locale_cache[lang] = {}
        else:
            _locale_cache[lang] = {}


def get_guild_locale(guild_id: Optional[Union[int, str]]) -> str:
    """Get the configured language code for a server with memory caching (default: 'en')"""
    if not guild_id:
        return DEFAULT_LOCALE
    gid_str = str(guild_id)
    if gid_str in _guild_locale_cache:
        return _guild_locale_cache[gid_str]

    try:
        cfg = get_guild_config(gid_str)
        lang = cfg.get("locale") or cfg.get("language") or DEFAULT_LOCALE
        lang = lang if lang in SUPPORTED_LOCALES else DEFAULT_LOCALE
        _guild_locale_cache[gid_str] = lang
        return lang
    except Exception as e:
        LogDebug(f"Error fetching locale for guild {guild_id}: {e}")
        return DEFAULT_LOCALE


def set_guild_locale(guild_id: Union[int, str], lang: str) -> bool:
    """Sets the language code for a server and updates cache"""
    if lang not in SUPPORTED_LOCALES:
        return False
    gid_str = str(guild_id)
    _guild_locale_cache[gid_str] = lang
    try:
        set_guild_config(gid_str, "locale", lang)
        return True
    except Exception as e:
        LogError(f"Error setting locale for guild {guild_id}: {e}")
        return False


def _get_nested(data: Dict[str, Any], path: str) -> Optional[Any]:
    """Retrieve value from nested dictionary using dot notation"""
    keys = path.split(".")
    curr = data
    for k in keys:
        if isinstance(curr, dict) and k in curr:
            curr = curr[k]
        else:
            return None
    return curr


def t(
    key: str,
    guild_id: Optional[Union[int, str]] = None,
    guild: Optional[Any] = None,
    ctx: Optional[Any] = None,
    lang: Optional[str] = None,
    default: Optional[str] = None,
    **kwargs
) -> str:
    """
    Translates a translation key with optional interpolation.
    
    Args:
        key: Dot-separated translation key (e.g., 'setup.title', 'common.yes')
        guild_id: Server ID to resolve language
        guild: Guild object (alternative to guild_id)
        ctx: Context / Interaction object (alternative to guild_id)
        lang: Explicit language override ('en' or 'de')
        default: Fallback string if key not found
        **kwargs: Values to interpolate into the translated string
    """
    if not _locale_cache:
        load_locales()

    gid = guild_id
    if gid is None and guild is not None:
        gid = getattr(guild, "id", None)
    if gid is None and ctx is not None:
        g = getattr(ctx, "guild", None)
        gid = getattr(g, "id", None) if g else None

    target_lang = lang or get_guild_locale(gid)
    lang_dict = _locale_cache.get(target_lang, {})

    # Try requested language
    val = _get_nested(lang_dict, key)

    # Fallback to English if not found in target language
    if val is None and target_lang != DEFAULT_LOCALE:
        val = _get_nested(_locale_cache.get(DEFAULT_LOCALE, {}), key)

    # If still not found, fallback to default argument or the key itself
    if val is None:
        val = default if default is not None else key

    if isinstance(val, str) and kwargs:
        try:
            return val.format(**kwargs)
        except Exception as e:
            LogDebug(f"Locale format error for key '{key}': {e}")
            return val

    return str(val) if val is not None else key


# Initial load
load_locales()
