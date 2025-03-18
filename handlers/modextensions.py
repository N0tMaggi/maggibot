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
        log_channel_id = cfg.get_log_channel(guild_id)
        
        if log_channel_id:
            guild = bot.get_guild(guild_id)
            if guild:
                log_channel = guild.get_channel(log_channel_id)
                if log_channel and isinstance(log_channel, discord.TextChannel):
                    embed = create_mod_embed(**embed_data)
                    await log_channel.send(embed=embed)
                    LogModeration(f"Log sent to channel {log_channel.id}")
                else:
                    LogError(f"Channel ID {log_channel_id} is not a valid text channel")
            else:
                LogError(f"Guild with ID {guild_id} not found")
        else:
            LogDebug(f"No log channel set for guild {guild_id}")
    except Exception as e:
        LogError(f"Failed to send mod log: {str(e)}")

