import discord
from discord.ext import commands
from handlers.config import loadserverconfig
from handlers.debug import LogDebug, LogError
from utils.components import build_container, build_view

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
    
                if creator and creator.bot and creator.public_flags.verified_bot:
                    LogDebug(f"Verified bot webhook allowed: {webhook.name} by {creator}")
                    continue
                    
                fields = [
                    ("Webhook Name", webhook.name, True),
                    ("Channel", channel.name, True),
                    ("Creator", f"{creator} (`{creator.id}`)" if creator else "Unknown", False),
                ]
                title = "⚠️ SECURITY ALERT: Webhook Created"
                description = f"New webhook detected in {channel.mention}"
                color = 'warning'

                if protection and creator and creator.bot:
                    try:
                        await webhook.delete(reason="Security: Bot-created webhook")
                        title = "🚫 THREAT NEUTRALIZED: Webhook Deleted"
                        color = 'error'
                        fields.append(("Action Taken", "Webhook automatically deleted", False))
                        LogDebug(f"Deleted bot webhook in {guild.name} ({guild.id})")
                    except Exception as e:
                        LogError(f"Webhook deletion failed: {str(e)}")
                        fields.append(("Error", str(e), False))

                container = build_container(
                    title=title,
                    description=description,
                    color=color,
                    thumbnail=guild_icon,
                    fields=fields,
                    footer_text=f"Server ID: {guild.id}",
                    timestamp=True,
                )

                if log_channel:
                    await log_channel.send(view=build_view(container))

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
            webhook = next((w for w in await message.channel.webhooks() if w.id == message.webhook_id), None)
            guild_icon = message.guild.icon.url if message.guild.icon else None

            fields = [
                ("Webhook", webhook.name if webhook else "Unknown", True),
                ("Message Content", message.content[:1000] or "*No text*", False),
                ("Sent By", f"{webhook.user} (`{webhook.user.id}`)" if webhook and webhook.user else "Unknown", False),
            ]
            title = "📡 Webhook Activity Detected"
            description = f"Message from webhook in {message.channel.mention}"
            color = 'info'

            if protection and webhook and webhook.user and webhook.user.bot:
                try:
                    await webhook.delete(reason="Security: Unauthorized bot webhook")
                    title = "🚨 THREAT BLOCKED: Malicious Webhook"
                    color = 'error'
                    fields.append(("Action Taken", "Webhook automatically terminated", False))
                    LogDebug(f"Blocked malicious webhook message in {message.guild.name} ({message.guild.id})")
                except Exception as e:
                    LogError(f"Webhook message deletion failed: {str(e)}")
                    fields.append(("Error", str(e), False))

            container = build_container(
                title=title,
                description=description,
                color=color,
                thumbnail=guild_icon,
                fields=fields,
                footer_text=f"Server ID: {message.guild.id}",
                timestamp=True,
            )

            if log_channel:
                await log_channel.send(view=build_view(container))

        except Exception as e:
            LogError(f"Error processing webhook message: {str(e)}")

def setup(bot):
    bot.add_cog(WebhookProtectionCog(bot))
