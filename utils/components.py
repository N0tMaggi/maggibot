"""
Centralized Components V2 creation utilities.

Dieses Modul ersetzt ``utils/embed_helpers.py`` im Zuge der Migration auf
Discord Components V2 (erfordert ``py-cord>=2.7.0``).

Verwendung:
    ``container = build_container(...)``
    ``await ctx.respond(view=build_view(container))``
anstatt ``await ctx.respond(embed=embed)``.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence, Tuple, Union

import discord

from .colors import EmbedColors

FieldTuple = Tuple[str, str, bool]


def _resolve_color(value: Optional[Union[int, str]]) -> int:
    """Resolve int/string color values using EmbedColors naming."""
    if isinstance(value, str):
        return EmbedColors.get(value, EmbedColors.INFO)
    if value is None:
        return EmbedColors.INFO
    return value


def _get_display_name(subject: Any) -> str:
    """Best-effort display name for user/member/guild-like objects."""
    return str(getattr(subject, "name", None) or subject)


def _get_icon_url(subject: Any) -> Optional[str]:
    """Best-effort avatar/icon URL for user/member/guild-like objects."""
    display_avatar = getattr(subject, "display_avatar", None)
    if display_avatar and hasattr(display_avatar, "url"):
        return display_avatar.url

    icon = getattr(subject, "icon", None)
    if icon and hasattr(icon, "url"):
        return icon.url

    avatar = getattr(subject, "avatar", None)
    if avatar and hasattr(avatar, "url"):
        return avatar.url

    return None


def _append_footer_metadata(
    container: discord.ui.Container,
    *,
    footer_text: Optional[str],
    footer_icon: Optional[str],
    timestamp: bool,
    bot_user: Optional[discord.User],
) -> None:
    """Append Footer/Timestamp as TextDisplay lines (Components V2 style)."""
    footer_base: Optional[str] = None
    if footer_text or footer_icon:
        footer_base = footer_text or ""
    elif bot_user:
        footer_base = "MaggiBot"

    timestamp_part = None
    if timestamp:
        unix_ts = int(discord.utils.utcnow().timestamp())
        timestamp_part = f"<t:{unix_ts}:R>"

    line: Optional[str] = None
    if footer_base and timestamp_part:
        line = f"-# {footer_base} • {timestamp_part}"
    elif footer_base:
        if footer_base.strip():
            line = f"-# {footer_base}"
    elif timestamp_part:
        line = f"-# {timestamp_part}"

    if line:
        container.add_item(discord.ui.TextDisplay(line))


def _build_media_gallery(image_url: str) -> discord.ui.MediaGallery:
    """Create a one-item MediaGallery for image URLs."""
    gallery = discord.ui.MediaGallery()
    gallery.add_item(image_url)
    return gallery


def build_container(
    title: Optional[str] = None,
    description: str = "",
    color: Optional[Union[int, str]] = None,
    author: Optional[Any] = None,
    thumbnail: Optional[str] = None,
    footer_text: Optional[str] = None,
    footer_icon: Optional[str] = None,
    timestamp: bool = True,
    bot_user: Optional[discord.User] = None,
    fields: Optional[Sequence[FieldTuple]] = None,
    image: Optional[str] = None,
    **kwargs: Any,
) -> discord.ui.Container:
    """
    Build a Discord Components V2 container as replacement for create_embed().

    Notes:
        - ``inline`` values from ``fields`` are accepted for migration compatibility,
          but are ignored because inline field layout is not supported by Components V2.
        - If both ``author`` and ``thumbnail`` are provided, the author avatar/icon is
          used and ``thumbnail`` is ignored.
        - ``footer_icon`` is accepted for signature compatibility, but cannot be
          rendered directly in Components V2 footer text.
        - Only known Container kwargs (``spoiler``, ``id``, ``colour``/``color``) are
          forwarded; unknown kwargs are ignored.
    """
    raw_color = color
    if raw_color is None:
        raw_color = kwargs.pop("color", kwargs.pop("colour", None))

    container_kwargs: dict[str, Any] = {
        "color": _resolve_color(raw_color),
    }
    for allowed_key in ("spoiler", "id"):
        if allowed_key in kwargs:
            container_kwargs[allowed_key] = kwargs[allowed_key]

    container = discord.ui.Container(**container_kwargs)

    if author is not None:
        author_text = discord.ui.TextDisplay(_get_display_name(author))
        author_icon_url = _get_icon_url(author)
        if author_icon_url:
            container.add_item(
                discord.ui.Section(
                    author_text,
                    accessory=discord.ui.Thumbnail(author_icon_url),
                )
            )
        else:
            container.add_item(author_text)
    elif thumbnail:
        container.add_item(
            discord.ui.Section(
                discord.ui.TextDisplay("\u200b"),
                accessory=discord.ui.Thumbnail(thumbnail),
            )
        )

    if title:
        container.add_item(discord.ui.TextDisplay(f"### {title}"))

    if description:
        container.add_item(discord.ui.TextDisplay(description))

    if fields:
        for field in fields:
            try:
                name, value, _inline = field
            except ValueError:
                name, value = field[0], field[1]
            container.add_item(discord.ui.TextDisplay(f"**{name}**\n{value}"))

    if image:
        gallery = _build_media_gallery(image)
        container.add_item(gallery)

    _append_footer_metadata(
        container,
        footer_text=footer_text,
        footer_icon=footer_icon,
        timestamp=timestamp,
        bot_user=bot_user,
    )

    return container


def build_mod_container(
    title: str,
    description: str,
    color_type: str = "mod_action",
    author: Optional[Any] = None,
    bot_user: Optional[discord.User] = None,
    fields: Optional[Sequence[FieldTuple]] = None,
    **kwargs: Any,
) -> discord.ui.Container:
    """
    Build moderation-styled Components V2 container (replacement for create_mod_embed()).
    """
    timestamp = kwargs.pop("timestamp", True)

    container = build_container(
        title=title,
        description=description,
        color=color_type,
        author=author,
        bot_user=None,
        fields=fields,
        footer_text=None,
        footer_icon=None,
        timestamp=False,
        **kwargs,
    )

    container.add_item(discord.ui.Separator())
    _append_footer_metadata(
        container,
        footer_text="Community ModSystem",
        footer_icon=None,
        timestamp=timestamp,
        bot_user=bot_user,
    )
    return container


def build_info_container(
    title: str,
    description: str,
    bot_user: Optional[discord.User] = None,
    **kwargs: Any,
) -> discord.ui.Container:
    """
    Build info-styled Components V2 container (replacement for create_info_embed()).

    Note:
        The previous embed helper used a footer icon URL. Components V2 does not
        support footer icons, so this helper intentionally omits it.
    """
    author = kwargs.get("author")
    thumbnail = kwargs.get("thumbnail")
    if not author and not thumbnail and bot_user:
        bot_avatar = _get_icon_url(bot_user)
        if bot_avatar:
            kwargs["thumbnail"] = bot_avatar

    footer_text = kwargs.pop("footer_text", "Maggi Dev System")

    return build_container(
        title=title,
        description=description,
        color="info",
        bot_user=bot_user,
        footer_text=footer_text,
        footer_icon=None,
        **kwargs,
    )


def build_view(
    *containers_or_items: discord.ui.Item,
    timeout: Optional[float] = 180.0,
    disable_on_timeout: bool = False,
) -> discord.ui.DesignerView:
    """
    Build a DesignerView and add one/many Components V2 items.

    Important:
        Send this view without ``content=`` and without ``embed(s)=`` in the same
        message call, because V2 component messages do not allow mixed content/embed
        payloads.
    """
    try:
        view = discord.ui.DesignerView(
            timeout=timeout,
            disable_on_timeout=disable_on_timeout,
        )
    except TypeError:
        view = discord.ui.DesignerView(timeout=timeout)
        if hasattr(view, "disable_on_timeout"):
            view.disable_on_timeout = disable_on_timeout

    for item in containers_or_items:
        view.add_item(item)

    return view
