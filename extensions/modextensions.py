import discord
import datetime
import handlers.config as cfg
from handlers.debug import LogDebug, LogError, LogModeration

def create_mod_embed(title, description, color_type='info', author=None):
    embed_colors = {
        'success': 0x2ECC71,
        'error': 0xE74C3C,
        'warning': 0xF1C40F,
        'info': 0x3498DB,
        'mod_action': 0x992D22
    }
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=embed_colors.get(color_type, 0x3498DB),
        timestamp=datetime.datetime.utcnow()
    )
    
    if author:
        embed.set_author(name=str(author), icon_url=author.avatar.url)
        
    embed.set_footer(text="ModSystem | Maggi", icon_url="")  
    return embed

async def send_mod_log(guild_id, embed_data, bot):
    try:
        guild = bot.get_guild(guild_id)
        if not guild:
            LogError(f"Guild {guild_id} not found by bot")
            return

        embed = create_mod_embed(**embed_data)

        # Text channel logging
        log_channel = cfg.get_log_channel(guild)
        if log_channel and isinstance(log_channel, discord.TextChannel):
            try:
                await log_channel.send(embed=embed)
                LogModeration(f"Log sent to channel {log_channel.id}")
            except Exception as e:
                LogError(f"Failed to send log to text channel: {e}")
        else:
            LogDebug(f"No log channel for guild {guild_id}")

        # Forum logging
        forum = cfg.get_logging_forum(guild)
        if forum and isinstance(forum, discord.ForumChannel):
            try:
                await forum.create_thread(name=embed.title, embed=embed)
            except Exception as e:
                LogError(f"Failed to create log thread: {e}")
    except Exception as e:
        LogError(f"Failed to send mod log: {str(e)}")

