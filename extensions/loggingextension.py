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
    guild: discord.Guild | None = None,
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

    Notes
    -----
    The embed automatically appends the event ``title`` and the current time as
    additional fields for more verbose logging information.
    """

    embed = discord.Embed(
        title=title,
        description=description,
        color=COLOR_MAP.get(color_type, COLOR_MAP["default"]),
        timestamp=datetime.datetime.utcnow(),
    )

    if user:
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)

    if guild:
        embed.add_field(name="Server", value=f"{guild.name} ({guild.id})", inline=False)

    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

    embed.add_field(
        name="Event",
        value=title,
        inline=False,
    )
    embed.add_field(
        name="Time",
        value=f"<t:{int(embed.timestamp.timestamp())}:F>",
        inline=False,
    )
    embed.set_footer(text=f"Logging System | Guild ID: {guild.id if guild else 'N/A'}")
    return embed
