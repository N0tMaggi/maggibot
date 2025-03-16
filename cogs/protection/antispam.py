import discord
from discord.ext import commands
import json
import datetime
import handlers.debug as DebugHandler
import handlers.config as config


class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        if message.guild is None:
            return
        
        if message.webhook_id is not None:
            return
        
        serverconfig = config.loadserverconfig()
        server_id = str(message.guild.id)
        
        serverconfig.setdefault(server_id, {})
        
        if not serverconfig[server_id].get("protection"):
            return
        
        if isinstance(message.author, discord.Member) and message.author.guild_permissions.administrator:
            return
        
        if message.author.bot:
            return
        
        if len(message.mentions) > 3:
            try:
                log_channel_id = serverconfig[server_id].get("protectionlogchannel")
                if not log_channel_id:
                    return  
                
                protection_log_channel = await message.guild.fetch_channel(log_channel_id)
                
                embed = discord.Embed(
                    title="🚨 Mass Mention Detected 🚨",
                    description=f"{message.author.mention} mentioned {len(message.mentions)} users. 🚷",
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.utcnow()
                )
                embed.add_field(name="Message Content", value=message.content[:1024], inline=False)
                embed.add_field(name="Message ID", value=message.id, inline=False)
                embed.add_field(name="Channel", value=message.channel.mention, inline=False)
                
                await protection_log_channel.send(embed=embed)
                
            except discord.NotFound:
                DebugHandler.LogError(f"Log channel not found: {log_channel_id}")
            except discord.Forbidden:
                DebugHandler.LogError(f"Permission denied to access log channel: {log_channel_id}")
            except Exception as e:
                DebugHandler.LogError(f"Unexpected error: {e}")


def setup(bot):
    bot.add_cog(AntiSpam(bot))