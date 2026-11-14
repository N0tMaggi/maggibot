# -*- coding: utf-8 -*-
"""
Centralized embed creation utilities for MaggiBot
Ensures clean, modern, and unified embed designs across all cogs and modules.
"""

import discord
from typing import Optional, Union, Any

from .colors import EmbedColors


def create_embed(
    title: str,
    description: str = "",
    color: Optional[Union[int, str, discord.Color]] = None,
    author: Optional[Union[discord.User, discord.Member]] = None,
    thumbnail: Optional[str] = None,
    image: Optional[str] = None,
    footer_text: Optional[str] = None,
    footer_icon: Optional[str] = None,
    timestamp: bool = True,
    bot_user: Optional[Union[discord.User, discord.ClientUser]] = None,
    fields: Optional[list] = None,
    **kwargs
) -> discord.Embed:
    """
    Create a standardized Discord embed with consistent styling.
    """
    embed_color = EmbedColors.get(color, default=EmbedColors.INFO)
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=embed_color,
        timestamp=discord.utils.utcnow() if timestamp else None,
        **kwargs
    )

    if author:
        avatar_url = author.display_avatar.url if hasattr(author, 'display_avatar') else None
        embed.set_author(name=str(author.display_name if hasattr(author, 'display_name') else author), icon_url=avatar_url)

    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    if image:
        embed.set_image(url=image)

    # Footer handling
    if footer_text or footer_icon:
        embed.set_footer(text=footer_text or "", icon_url=footer_icon or None)
    elif bot_user and hasattr(bot_user, 'display_avatar'):
        embed.set_footer(text="MaggiBot", icon_url=bot_user.display_avatar.url)
    else:
        embed.set_footer(text="MaggiBot")

    if fields:
        for f in fields:
            if isinstance(f, (list, tuple)) and len(f) >= 2:
                inline = f[2] if len(f) > 2 else False
                embed.add_field(name=str(f[0]), value=str(f[1]), inline=inline)
            elif isinstance(f, dict):
                embed.add_field(
                    name=str(f.get("name", "")),
                    value=str(f.get("value", "")),
                    inline=bool(f.get("inline", False))
                )

    return embed


def create_success_embed(
    title: str,
    description: str = "",
    author: Optional[Union[discord.User, discord.Member]] = None,
    **kwargs
) -> discord.Embed:
    """Standard success embed (Green, checkmark)"""
    icon = "✅ " if not any(title.startswith(p) for p in ("✅", "🎉", "✓")) else ""
    return create_embed(
        title=f"{icon}{title}",
        description=description,
        color=EmbedColors.SUCCESS,
        author=author,
        **kwargs
    )


def create_error_embed(
    title: str,
    description: str = "",
    author: Optional[Union[discord.User, discord.Member]] = None,
    **kwargs
) -> discord.Embed:
    """Standard error embed (Red, cross mark)"""
    icon = "❌ " if not any(title.startswith(p) for p in ("❌", "🚫", "⚠️", "✗")) else ""
    return create_embed(
        title=f"{icon}{title}",
        description=description,
        color=EmbedColors.ERROR,
        author=author,
        **kwargs
    )


def create_warning_embed(
    title: str,
    description: str = "",
    author: Optional[Union[discord.User, discord.Member]] = None,
    **kwargs
) -> discord.Embed:
    """Standard warning embed (Yellow, warning sign)"""
    icon = "⚠️ " if not any(title.startswith(p) for p in ("⚠️", "❗", "⚡")) else ""
    return create_embed(
        title=f"{icon}{title}",
        description=description,
        color=EmbedColors.WARNING,
        author=author,
        **kwargs
    )


def create_info_embed(
    title: str,
    description: str = "",
    bot_user: Optional[Union[discord.User, discord.ClientUser]] = None,
    **kwargs
) -> discord.Embed:
    """Standard info embed (Blue)"""
    icon = "ℹ️ " if not any(title.startswith(p) for p in ("ℹ️", "📚", "🤖", "📈", "🔍", "⚙️")) else ""
    return create_embed(
        title=f"{icon}{title}",
        description=description,
        color=EmbedColors.INFO,
        bot_user=bot_user,
        **kwargs
    )


def create_mod_embed(
    title: str,
    description: str = "",
    color_type: str = 'mod_action',
    author: Optional[Union[discord.User, discord.Member]] = None,
    bot_user: Optional[Union[discord.User, discord.ClientUser]] = None,
    footer_text: Optional[str] = None,
    **kwargs
) -> discord.Embed:
    """Moderation-specific embed with consistent styling"""
    return create_embed(
        title=title,
        description=description,
        color=color_type,
        author=author,
        bot_user=bot_user,
        footer_text=footer_text or "Maggi Moderation",
        **kwargs
    )


def create_security_embed(
    title: str,
    description: str = "",
    color: str = 'security',
    footer_text: Optional[str] = None,
    **kwargs
) -> discord.Embed:
    """Security and protection embed (Shield, Blurple/Red)"""
    icon = "🛡️ " if not any(title.startswith(p) for p in ("🛡️", "🚨", "🔒", "⚡", "⚠️")) else ""
    return create_embed(
        title=f"{icon}{title}",
        description=description,
        color=color,
        footer_text=footer_text or "MaggiBot Security System",
        **kwargs
    )
