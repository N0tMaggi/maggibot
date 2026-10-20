# -*- coding: utf-8 -*-
"""
Tests for Cog Extension Loading:
- Discovers all extensions in the cogs directory
- Verifies exact extension count (37 extensions)
- Verifies every individual cog loads into a fresh discord.Bot instance with 0 errors
- Verifies all 37 cogs load together into a single discord.Bot instance without conflicts
"""

import os
import asyncio
import pytest
import discord


def get_all_cog_extensions(directory: str = "cogs"):
    """Walks the cogs directory and returns sorted dot-separated extension names."""
    extensions = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                ext_path = os.path.join(root, file)[:-3].replace(os.sep, ".")
                extensions.append(ext_path)
    return sorted(extensions)


ALL_EXTENSIONS = get_all_cog_extensions("cogs")


def test_cog_extension_count():
    """Verify that all 37 cog extensions exist in the cogs directory."""
    assert len(ALL_EXTENSIONS) == 37, (
        f"Expected 37 cogs, but found {len(ALL_EXTENSIONS)}: {ALL_EXTENSIONS}"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("extension_name", ALL_EXTENSIONS)
async def test_individual_cog_extension_loads(extension_name):
    """Verify that each individual extension loads into a clean discord.Bot instance."""
    bot = discord.Bot(intents=discord.Intents.all())
    try:
        bot.load_extension(extension_name)
    except Exception as e:
        pytest.fail(f"Failed to load extension '{extension_name}': {e}")


@pytest.mark.asyncio
async def test_all_cogs_load_together_into_single_bot():
    """Verify that all 37 cogs can be loaded together into a single bot without collisions."""
    bot = discord.Bot(intents=discord.Intents.all())
    loaded = 0
    errors = []

    for ext in ALL_EXTENSIONS:
        try:
            bot.load_extension(ext)
            loaded += 1
        except Exception as e:
            errors.append((ext, str(e)))

    assert len(errors) == 0, f"Errors loading cogs together: {errors}"
    assert loaded == 37
