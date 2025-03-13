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
        serverconfig = config.loadserverconfig()
        serverconfig[str(message.guild.id)] = serverconfig.get(str(message.guild.id), {})
        if not serverconfig[str(message.guild.id)].get("protection"):
            return
        if message.author.guild_permissions.administrator:
            return
        if message.author.bot:
            return
        if message.mentions:
            if len(message.mentions) > 10:
                try:
                    protection_log_channel = await message.guild.fetch_channel(serverconfig[str(message.guild.id)]["protectionlogchannel"])
                    reaction_embed = discord.Embed(
                        title="🚨 Mass Mention Detected 🚨",
                        description=f"{message.author.mention} has sent a message with {len(message.mentions)} mentions. 🚷",
                        color=discord.Color.red()
                    )
                    reaction_embed.add_field(name="Message Content", value=message.content, inline=False)
                    reaction_embed.add_field(name="Message ID", value=message.id, inline=False)
                    reaction_embed.add_field(name="Channel", value=message.channel.mention, inline=False)
                    reaction_embed.timestamp = datetime.datetime.utcnow()
                    await protection_log_channel.send(embed=reaction_embed)
                except Exception as e:
                    DebugHandler.LogError(f"Error while sending message to log channel: {e}")

def setup(bot):
    bot.add_cog(AntiSpam(bot))
