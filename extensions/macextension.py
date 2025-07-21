import discord
from discord.ext import commands
import datetime
from handlers.env import get_mac_banner

def trim_field(value: str, max_length: int = 1024) -> str:
    """Trims a string to a maximum length, adding '...' if truncated."""
    return value if len(value) <= max_length else value[:max_length-3] + "..."

def create_mac_embed(title, description, color=None):
    """Creates a standardized embed for the MAC system."""
    embed_color = color or 0x2b2d31 # Default embed color
    embed = discord.Embed(
        title=title,
        description=description,
        color=embed_color,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text="MAC™ Global Ban System", icon_url="") # Removed the placeholder icon_url
    
    banner = get_mac_banner()
    if banner:
        embed.set_image(url=banner)
        
    return embed
