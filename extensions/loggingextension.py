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


def create_log_embed(
    title: str,
    description: str,
    color_type: str = "default",
    user: discord.abc.User | None = None,
    fields: list[tuple[str, str, bool]] | None = None,
) -> discord.Embed:
    """Create a standardized log embed.

    Parameters
    ----------
    title: str
        Title of the embed.
    description: str
        Description text.
    color_type: str, optional
        Key for ``COLOR_MAP``.
    user: discord.abc.User | None, optional
        User associated with the event.
    fields: list[tuple[str, str, bool]] | None, optional
        Extra fields to append. Each entry is ``(name, value, inline)``.
    """

    embed = discord.Embed(
        title=title,
        description=description,
        color=COLOR_MAP.get(color_type, COLOR_MAP["default"]),
        timestamp=datetime.datetime.utcnow(),
    )

    if user:
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)

    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

    embed.set_footer(text="Logging System")
    return embed
