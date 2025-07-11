import discord
import datetime


COLOR_MAP = {
    "join": discord.Color.green(),
    "leave": discord.Color.red(),
    "ban": discord.Color.dark_red(),
    "kick": discord.Color.orange(),
    "warn": discord.Color.orange(),
    "message_delete": discord.Color.orange(),
    "default": discord.Color.blue(),
}


def create_log_embed(title: str, description: str, color_type: str = "default", user: discord.abc.User | None = None) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=COLOR_MAP.get(color_type, COLOR_MAP["default"]),
        timestamp=datetime.datetime.utcnow(),
    )
    if user:
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    embed.set_footer(text="Logging System")
    return embed
