# -*- coding: utf-8 -*-
"""
Centralized color definitions for MaggiBot embeds
"""

import discord


class EmbedColors:
    """Standard consistent color scheme for Discord embeds"""

    # Status colors
    SUCCESS = 0x2ECC71      # Vibrant Green
    ERROR = 0xE74C3C        # Crimson Red
    WARNING = 0xF1C40F      # Amber Yellow
    INFO = 0x3498DB         # Deep Blue
    
    # Moderation & Protection
    MOD_ACTION = 0x992D22   # Dark Red
    SECURITY = 0x5865F2     # Blurple / Shield
    VOTE = 0xF39C12         # Orange
    
    # System & General
    STATUS = 0x2ECC71       # Green
    DEFAULT = 0x2B2D31      # Discord Dark Slate
    PRIMARY = 0x5865F2      # Discord Blurple
    
    # Stats & Fun
    STATS = 0x9B59B6        # Purple
    LEADERBOARD = 0xE91E63  # Bright Pink
    VERIFY = 0x2ECC71       # Emerald Green

    @classmethod
    def get(cls, color_name_or_val, default=None):
        """Get color int by name or return value"""
        if isinstance(color_name_or_val, int):
            return color_name_or_val
        if isinstance(color_name_or_val, discord.Color):
            return color_name_or_val.value

        if not isinstance(color_name_or_val, str):
            return default or cls.DEFAULT

        name = color_name_or_val.lower().strip()
        color_map = {
            'success': cls.SUCCESS,
            'green': cls.SUCCESS,
            'error': cls.ERROR,
            'danger': cls.ERROR,
            'red': cls.ERROR,
            'warning': cls.WARNING,
            'yellow': cls.WARNING,
            'info': cls.INFO,
            'blue': cls.INFO,
            'mod_action': cls.MOD_ACTION,
            'mod': cls.MOD_ACTION,
            'security': cls.SECURITY,
            'vote': cls.VOTE,
            'status': cls.STATUS,
            'stats': cls.STATS,
            'purple': cls.STATS,
            'leaderboard': cls.LEADERBOARD,
            'pink': cls.LEADERBOARD,
            'verify': cls.VERIFY,
            'primary': cls.PRIMARY,
            'default': cls.DEFAULT,
        }
        return color_map.get(name, default or cls.DEFAULT)
