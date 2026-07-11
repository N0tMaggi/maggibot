import discord
from discord.ext import commands
from handlers.env import get_mac_banner
from utils.components import build_container

def trim_field(value: str, max_length: int = 1024) -> str:
    """Trims a string to a maximum length, adding '...' if truncated."""
    return value if len(value) <= max_length else value[:max_length-3] + "..."

def create_mac_embed(title, description, color=None):
    """Creates a standardized container for the MAC system (Components V2)."""
    container_color = color or 0x2b2d31  # Default embed color
    banner = get_mac_banner()
    return build_container(
        title=title,
        description=description,
        color=container_color,
        footer_text="MAC™ Global Ban System",
        footer_icon="",
        timestamp=True,
        image=banner,
    )
