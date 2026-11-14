import discord
from discord.ext import commands
from handlers.config import loadserverconfig
from handlers.debug import LogDebug, LogError
from utils.embed_helpers import (
    create_embed,
    create_mod_embed,
    create_security_embed,
    create_success_embed,
    create_error_embed,
    create_warning_embed,
)

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
                    
                bot_icon = self.bot.user.display_avatar.url if self.bot.user else None
                fields = [
                    ("Webhook Name", webhook.name, True),
                    ("Channel", channel.name, True),
                    ("Creator", f"{creator} (`{creator.id}`)" if creator else "Unknown", False)
                ]
                embed = create_security_embed(
                    title="⚠️ SECURITY ALERT: Webhook Created",
                    description=f"New webhook detected in {channel.mention}",
                    color='warning',
                    thumbnail=guild_icon,
                    footer_text=f"Server ID: {guild.id} • Security System",
                    footer_icon=bot_icon,
                    fields=fields
                )

                if protection and creator and creator.bot:
                    try:
                        await webhook.delete(reason="Security: Bot-created webhook")
                        embed.title = "🚫 THREAT NEUTRALIZED: Webhook Deleted"
                        embed.color = discord.Color(0xE74C3C)
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
            webhook = next((w for w in await message.channel.webhooks() if w.id == message.webhook_id), None)
            guild_icon = message.guild.icon.url if message.guild.icon else None
            bot_icon = self.bot.user.display_avatar.url if self.bot.user else None

            fields = [
                ("Webhook", webhook.name if webhook else "Unknown", True),
                ("Message Content", message.content[:1000] or "*No text*", False),
                ("Sent By", f"{webhook.user} (`{webhook.user.id}`)" if webhook and webhook.user else "Unknown", False)
            ]
            embed = create_security_embed(
                title="📡 Webhook Activity Detected",
                description=f"Message from webhook in {message.channel.mention}",
                color='default',
                thumbnail=guild_icon,
                footer_text=f"Server ID: {message.guild.id} • Security System",
                footer_icon=bot_icon,
                fields=fields
            )

            if protection and webhook and webhook.user and webhook.user.bot:
                try:
                    await webhook.delete(reason="Security: Unauthorized bot webhook")
                    embed.title = "🚨 THREAT BLOCKED: Malicious Webhook"
                    embed.color = discord.Color(0xE74C3C)
                    embed.add_field(name="Action Taken", value="Webhook automatically terminated", inline=False)
                    LogDebug(f"Blocked malicious webhook message in {message.guild.name} ({message.guild.id})")
                except Exception as e:
                    LogError(f"Webhook message deletion failed: {str(e)}")
                    embed.add_field(name="Error", value=str(e), inline=False)

            if log_channel:
                await log_channel.send(embed=embed)

        except Exception as e:
            LogError(f"Error processing webhook message: {str(e)}")

def setup(bot):
    bot.add_cog(WebhookProtectionCog(bot))
