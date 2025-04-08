import discord
from discord.ext import commands
import datetime
from handlers.debug import LogDebug, LogError
import handlers.config as config
from extensions.protectionextension import create_alert_embed

class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        if not message.guild or message.webhook_id:
            return

        serverconfig = config.loadserverconfig()
        server_id = str(message.guild.id)
        
        if not serverconfig.get(server_id, {}).get("protection"):
            return

        if (isinstance(message.author, discord.Member) and \
           (message.author.guild_permissions.administrator or message.author.bot)):
            return

        mention_count = len(message.mentions)
        if mention_count <= 3:
            return

        try:
            log_channel_id = serverconfig[server_id].get("protectionlogchannel")
            if not log_channel_id:
                LogDebug(f"No log channel set in {message.guild.name}")
                return

            log_channel = await message.guild.fetch_channel(log_channel_id)
            if not log_channel.permissions_for(message.guild.me).send_messages:
                LogError(f"No send permissions in {log_channel.name}")
                return

            embed = await create_alert_embed(message, mention_count)
            await log_channel.send(embed=embed)
            LogDebug(f"Logged mass mention by {message.author} ({mention_count} mentions)")

        except discord.NotFound:
            LogError(f"Log channel not found: {log_channel_id}")
        except discord.Forbidden:
            LogError(f"Missing permissions for log channel: {log_channel_id}")
        except Exception as e:
            LogError(f"Mass mention handling error: {str(e)}")
            try:
                LogError(f"⚠️ Failed to handle mass mention by {message.author.mention}: {str(e)}")
                await message.guild.owner.send(
                    f"⚠️ Failed to handle mass mention by {message.author.mention}: {str(e)}")
                
            except Exception as owner_error:
                LogError(f"Critical failure: {owner_error}")

def setup(bot):
    bot.add_cog(AntiSpam(bot))