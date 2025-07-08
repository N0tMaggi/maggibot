import discord
from discord.ext import commands
import datetime
import asyncio
from handlers.env import get_mac_banner, get_mac_channel, get_owner
from handlers.config import mac_load_bans, mac_save_bans

AUTHORIZED_ID = int(get_owner())
NOTIFY_CHANNEL_ID = int(get_mac_channel())

def trim_field(value: str, max_length: int = 1024) -> str:
    return value if len(value) <= max_length else value[:max_length-3] + "..."

def is_authorized(ctx: discord.ApplicationContext) -> bool:
    return ctx.author.id == AUTHORIZED_ID

def create_mac_embed(title, description, color=None):
    embed_color = 0x2b2d31
    embed = discord.Embed(
        title=title,
        description=description,
        color=color or embed_color,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text="MAC Global Ban System", icon_url="")
    banner = get_mac_banner()
    if banner:
        embed.set_image(url=banner)
    return embed
