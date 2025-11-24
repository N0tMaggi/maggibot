"""
Centralized embed creation utilities
"""

import discord
from datetime import datetime, timezone
from typing import Optional, Union

from .colors import EmbedColors


def create_embed(
    title: str,
    description: str = "",
    color: Optional[Union[int, str]] = None,
    author: Optional[discord.User] = None,
    thumbnail: Optional[str] = None,
    footer_text: Optional[str] = None,
    footer_icon: Optional[str] = None,
    timestamp: bool = True,
    bot_user: Optional[discord.User] = None,
    **kwargs
) -> discord.Embed:
    """
    Create a standardized Discord embed with common patterns.
    
    Args:
        title: Embed title
        description: Embed description
        color: Either a color int or color name string (e.g., 'success', 'error', 'info')
        author: If provided, sets the embed author with their avatar
        thumbnail: URL for embed thumbnail
        footer_text: Custom footer text
        footer_icon: Custom footer icon URL
        timestamp: Whether to include timestamp (default: True)
        bot_user: Bot user object for default footer icon
        **kwargs: Additional arguments passed to discord.Embed()
    
    Returns:
        discord.Embed: Configured embed object
    """
    # Handle color
    if isinstance(color, str):
        embed_color = EmbedColors.get(color)
    elif color is None:
        embed_color = EmbedColors.INFO
    else:
        embed_color = color
    
    # Create embed
    embed = discord.Embed(
        title=title,
        description=description,
        color=embed_color,
        timestamp=discord.utils.utcnow() if timestamp else None,
        **kwargs
    )
    
    # Set author if provided
    if author:
        embed.set_author(
            name=str(author),
            icon_url=author.display_avatar.url if hasattr(author, 'display_avatar') else None
        )
    
    # Set thumbnail if provided
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    # Set footer
    if footer_text or footer_icon:
        embed.set_footer(
            text=footer_text or discord.Embed.Empty,
            icon_url=footer_icon or discord.Embed.Empty
        )
    elif bot_user:
        # Default footer with bot icon
        embed.set_footer(
            text="MaggiBot",
            icon_url=bot_user.display_avatar.url if hasattr(bot_user, 'display_avatar') else None
        )
    
    return embed


def create_mod_embed(
    title: str,
    description: str,
    color_type: str = 'mod_action',
    author: Optional[discord.User] = None,
    bot_user: Optional[discord.User] = None,
    **kwargs
) -> discord.Embed:
    """
    Create a moderation-specific embed with consistent styling.
    
    Args:
        title: Embed title
        description: Embed description
        color_type: Color type (mod_action, success, error, etc.)
        author: User who triggered the action
        bot_user: Bot user for footer
        **kwargs: Additional arguments
    
    Returns:
        discord.Embed: Configured moderation embed
    """
    # Add divider to description
    divider = "─" * 30
    description_with_divider = f"{description}\n\n{divider}"
    
    embed = create_embed(
        title=title,
        description=description_with_divider,
        color=color_type,
        author=author,
        bot_user=bot_user,
        **kwargs
    )
    
    # Override footer for mod embeds
    if bot_user:
        embed.set_footer(
            text="Community ModSystem",
            icon_url=bot_user.display_avatar.url if hasattr(bot_user, 'display_avatar') else None
        )
    
    return embed


def create_info_embed(
    title: str,
    description: str,
    bot_user: Optional[discord.User] = None,
    **kwargs
) -> discord.Embed:
    """
    Create an info embed with AG7 Dev styling.
    
    Args:
        title: Embed title
        description: Embed description
        bot_user: Bot user for thumbnail and footer
        **kwargs: Additional arguments
    
    Returns:
        discord.Embed: Configured info embed
    """
    embed = create_embed(
        title=title,
        description=description,
        color='info',
        thumbnail=bot_user.display_avatar.url if bot_user and hasattr(bot_user, 'display_avatar') else None,
        footer_text="AG7 Dev System",
        footer_icon="https://ag7-dev.de/favicon/favicon.ico",
        **kwargs
    )
    
    return embed
