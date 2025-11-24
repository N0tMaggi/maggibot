"""
Centralized color definitions for embeds
"""


class EmbedColors:
    """Standard colors for Discord embeds"""
    
    # Status colors
    SUCCESS = 0x2ECC71  # Green
    ERROR = 0xE74C3C    # Red
    WARNING = 0xF1C40F  # Yellow
    INFO = 0x3498DB     # Blue
    
    # Moderation colors
    MOD_ACTION = 0x992D22  # Dark red
    VOTE = 0xF1C40F        # Yellow
    
    # System colors
    STATUS = 0x2ECC71   # Green
    DEFAULT = 0x2b2d31  # Discord dark
    
    # Stats colors
    STATS = 0x9B59B6    # Purple
    LEADERBOARD = 0xE91E63  # Pink
    
    # Verification colors
    VERIFY = 0x2ECC71   # Green
    
    @classmethod
    def get(cls, color_name, default=None):
        """Get color by name, returns default if not found"""
        color_map = {
            'success': cls.SUCCESS,
            'error': cls.ERROR,
            'warning': cls.WARNING,
            'info': cls.INFO,
            'mod_action': cls.MOD_ACTION,
            'vote': cls.VOTE,
            'status': cls.STATUS,
            'stats': cls.STATS,
            'leaderboard': cls.LEADERBOARD,
            'verify': cls.VERIFY,
        }
        return color_map.get(color_name.lower(), default or cls.DEFAULT)
