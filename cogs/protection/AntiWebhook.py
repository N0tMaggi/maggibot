import discord
from discord.ext import commands

from handlers.config import get_protection_log_channel, loadserverconfig
from handlers.debug import LogDebug, LogError
from utils.audit import find_audit_actor

class WebhookProtectionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        config = loadserverconfig().get(str(guild.id), {})
        protection = config.get("protection", False)
        log_channel = get_protection_log_channel(guild)
        
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
                    
                audit = await find_audit_actor(
                    guild=guild,
                    action=discord.AuditLogAction.webhook_create,
                    target_id=webhook.id,
                )

                actor = audit.user or creator

                embed = discord.Embed(
                    title="Webhook created",
                    description=f"New webhook detected in {channel.mention}",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow(),
                )
                embed.set_thumbnail(url=guild_icon)
                embed.add_field(name="Webhook", value=f"{webhook.name} ({webhook.id})", inline=False)
                embed.add_field(name="Channel", value=f"{channel.name} ({channel.id})", inline=False)
                embed.add_field(
                    name="Actor",
                    value=f"{actor.mention} ({actor.id})" if actor else "Unknown",
                    inline=False,
                )
                embed.add_field(name="Audit reason", value=audit.reason or "None", inline=False)
                embed.set_footer(text=f"Protection System | Guild ID: {guild.id}")

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
        log_channel = get_protection_log_channel(message.guild)

        try:
            webhook = next((w for w in await message.channel.webhooks() if w.id == message.webhook_id), None)
            guild_icon = message.guild.icon.url if message.guild.icon else None

            jump_url = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"

            embed = discord.Embed(
                title="Webhook activity",
                description=f"Message from webhook in {message.channel.mention}",
                color=discord.Color.greyple(),
                timestamp=discord.utils.utcnow(),
            )
            embed.set_thumbnail(url=guild_icon)
            embed.add_field(
                name="Webhook",
                value=f"{webhook.name} ({webhook.id})" if webhook else "Unknown",
                inline=False,
            )
            embed.add_field(name="Jump", value=f"[Open message]({jump_url})", inline=False)
            embed.add_field(
                name="Sent by",
                value=f"{webhook.user} ({webhook.user.id})" if webhook and webhook.user else "Unknown",
                inline=False,
            )
            embed.add_field(name="Content", value=message.content[:1000] or "*No text*", inline=False)
            embed.set_footer(text=f"Protection System | Guild ID: {message.guild.id}")

            if protection and webhook and webhook.user and webhook.user.bot:
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

        except Exception as e:
            LogError(f"Error processing webhook message: {str(e)}")

def setup(bot):
    bot.add_cog(WebhookProtectionCog(bot))