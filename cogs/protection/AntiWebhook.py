import discord
from discord.ext import commands
from handlers.config import loadserverconfig
from handlers.debug import LogDebug, LogError

class WebhookProtectionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        config = loadserverconfig().get(str(guild.id), {})
        protection = config.get("protection", False)
        log_channel = self.bot.get_channel(config.get("logchannel")) if config.get("logchannel") else None
        
        try:
            webhooks = await channel.webhooks()
            if not webhooks:
                return

            for webhook in webhooks:
                creator = webhook.user
                guild_icon = guild.icon.url if guild.icon else None

                embed = discord.Embed(
                    title="⚠️ SECURITY ALERT: Webhook Created",
                    description=f"New webhook detected in {channel.mention}",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_thumbnail(url=guild_icon)
                embed.add_field(name="Webhook Name", value=webhook.name, inline=True)
                embed.add_field(name="Channel", value=channel.name, inline=True)
                embed.add_field(name="Creator", value=f"{creator} (`{creator.id}`)" if creator else "Unknown", inline=False)
                embed.set_footer(text=f"Server ID: {guild.id}", icon_url=self.bot.user.avatar.url)

                if protection and creator and creator.bot:
                    try:
                        await webhook.delete(reason="Security: Bot-created webhook")
                        embed.title = "🚫 THREAT NEUTRALIZED: Webhook Deleted"
                        embed.color = discord.Color.red()
                        embed.add_field(name="Action Taken", value="Webhook automatically deleted", inline=False)
                        LogDebug(f"Deleted bot webhook in {guild.name} ({guild.id})")
                    except Exception as e:
                        LogError(f"Webhook deletion failed: {str(e)}")
                        embed.add_field(name="Error", value=str(e), inline=False)

                if log_channel:
                    await log_channel.send(embed=embed)

        except Exception as e:
            LogError(f"Webhook update handler error: {str(e)}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author == self.bot.user or not message.webhook_id:
            return

        config = loadserverconfig().get(str(message.guild.id), {})
        protection = config.get("protection", False)
        log_channel = self.bot.get_channel(config.get("logchannel")) if config.get("logchannel") else None

        try:
            webhook = await message.guild.fetch_webhook(message.webhook_id)
            guild_icon = message.guild.icon.url if message.guild.icon else None

            embed = discord.Embed(
                title="📡 Webhook Activity Detected",
                description=f"Message from webhook in {message.channel.mention}",
                color=discord.Color.greyple(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=guild_icon)
            embed.add_field(name="Webhook", value=webhook.name, inline=True)
            embed.add_field(name="Message Content", value=message.content[:1000] or "*No text*", inline=False)
            embed.add_field(name="Sent By", value=f"{webhook.user} (`{webhook.user.id}`)" if webhook.user else "Unknown", inline=False)
            embed.set_footer(text=f"Server ID: {message.guild.id}", icon_url=self.bot.user.avatar.url)

            if protection and webhook.user and webhook.user.bot:
                try:
                    await webhook.delete(reason="Security: Unauthorized bot webhook")
                    embed.title = "🚨 THREAT BLOCKED: Malicious Webhook"
                    embed.color = discord.Color.red()
                    embed.add_field(name="Action Taken", value="Webhook automatically terminated", inline=False)
                    LogDebug(f"Blocked malicious webhook message in {message.guild.name} ({message.guild.id})")
                except Exception as e:
                    LogError(f"Webhook message deletion failed: {str(e)}")
                    embed.add_field(name="Error", value=str(e), inline=False)

            if log_channel:
                await log_channel.send(embed=embed)

        except discord.NotFound:
            LogDebug("Webhook not found (already deleted?)")
        except Exception as e:
            LogError(f"Error processing webhook message: {str(e)}")

def setup(bot):
    bot.add_cog(WebhookProtectionCog(bot))