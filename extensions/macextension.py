# -*- coding: utf-8 -*-
import discord
from handlers.env import get_mac_banner
from utils.embed_helpers import create_embed


def trim_field(value: str, max_length: int = 1024) -> str:
    """Trims a string to a maximum length, adding '...' if truncated."""
    return value if len(value) <= max_length else value[:max_length-3] + "..."


def create_mac_embed(title: str, description: str, color=None, **kwargs) -> discord.Embed:
    """Creates a standardized embed for the MAC system."""
    banner = get_mac_banner()
    return create_embed(
        title=title,
        description=description,
        color=color or "security",
        image=banner if banner else None,
        footer_text="MAC™ Global Ban System",
        **kwargs
    )
