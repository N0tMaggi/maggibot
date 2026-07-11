import discord
from utils.components import build_container


COLOR_MAP = {
    "join": "success",
    "leave": "error",
    "ban": "mod_action",
    "kick": "warning",
    "warn": "warning",
    "message_delete": "warning",
    "default": "info",
}


def create_log_embed(
    title: str,
    description: str,
    color_type: str = "default",
    user: discord.abc.User | None = None,
    fields: list[tuple[str, str, bool]] | None = None,
    guild: discord.Guild | None = None,
) -> discord.ui.Container:
    """Create a standardized log container (Components V2).

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
    The container automatically appends the event ``title`` and the current time as
    additional fields for more verbose logging information.
    """

    timestamp_unix = int(discord.utils.utcnow().timestamp())
    container_fields = []

    if guild:
        container_fields.append(("Server", f"{guild.name} ({guild.id})", False))

    if fields:
        for name, value, inline in fields:
            container_fields.append((name, value, inline))

    container_fields.append(("Event", title, False))
    container_fields.append(("Time", f"<t:{timestamp_unix}:F>", False))

    return build_container(
        title=title,
        description=description,
        color=COLOR_MAP.get(color_type, COLOR_MAP["default"]),
        author=user,
        thumbnail=user.display_avatar.url if user else None,
        fields=container_fields,
        footer_text=f"Logging System | Guild ID: {guild.id if guild else 'N/A'}",
        timestamp=True,
    )
