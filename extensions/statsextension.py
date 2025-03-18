import discord
import datetime

def create_embed(title, description="", color_type="stats", author=None):
    embed_colors = {
        "stats": 0x3498DB,
        "leaderboard": 0xF1C40F,
        "system": 0x2ECC71,
        "error": 0xE74C3C,
        "mod": 0x992D22
    }

    embed = discord.Embed(
        title=title,
        description=description,
        color=embed_colors.get(color_type, 0x3498DB),
        timestamp=datetime.datetime.now()
    )
    embed.set_footer(
        text="AG7 Stats System",
        icon_url="https://ag7-dev.de/favicon/favicon.ico"
    )

    if author:
        embed.set_author(name=str(author), icon_url=author.avatar.url)
    return embed
