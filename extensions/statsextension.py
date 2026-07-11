import discord
from utils.components import build_container

def create_stats_embed(title, description="", color_type="stats", author=None) -> discord.ui.Container:
    """Create a standardized stats container (Components V2)."""
    color_map = {
        "system": "status",
        "mod": "mod_action",
    }

    resolved_color = color_map.get(color_type, color_type)
    return build_container(
        title=title,
        description=description,
        color=resolved_color,
        author=author,
        footer_text="Maggi Stats System",
        footer_icon="https://maggi.dev/favicon/favicon.ico",
        timestamp=True,
    )
