import discord
from discord.ext import commands
from handlers.config import loadserverconfig
from handlers.debug import LogDebug, LogError
from collections import defaultdict
import asyncio

class ChannelProtectionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.action_counter = defaultdict(int)
        self.COOLDOWN = 60
        self.ACTION_THRESHOLD = 3

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        await self.check_bot_action(channel, "create")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self.check_bot_action(channel, "delete")

    async def check_bot_action(self, channel: discord.abc.GuildChannel, action_type: str):
        guild = channel.guild
        config = loadserverconfig().get(str(guild.id), {})

        if not config.get("protection", False):
            return

        try:
            async for entry in guild.audit_logs(limit=1, action=self.get_audit_action(action_type)):
                if entry.target.id != channel.id or not entry.user.bot:
                    return

                bot = entry.user
                self.action_counter[bot.id] += 1

                if self.action_counter[bot.id] > self.ACTION_THRESHOLD:
                    if bot.public_flags.verified_bot:
                        await self.log_verified_bot_spam(guild, bot, channel, action_type)
                    else:
                        await self.handle_unverified_bot_spam(guild, bot, channel, action_type)
                    return

                asyncio.create_task(self.reset_counter(bot.id))
        except Exception as e:
            LogError(f"Channel {action_type} audit error in {guild.name}: {str(e)}")

    async def handle_unverified_bot_spam(self, guild: discord.Guild, bot: discord.User, channel: discord.abc.GuildChannel, action_type: str):
        try:
            await guild.ban(bot, reason=f"Potential raid: {self.ACTION_THRESHOLD}+ channel {action_type}s")
            await self.log_security_event(
                guild,
                "🚨 Unverified Bot Detected",
                f"Bot {bot} (`{bot.id}`) triggered a threshold of {self.ACTION_THRESHOLD}+ channel {action_type}s.\n"
                f"Channel: {channel.name}\nAction: Banned",
                discord.Color.dark_red()
            )
        except Exception as e:
            LogError(f"Failed to ban bot in {guild.name}: {str(e)}")

    async def log_verified_bot_spam(self, guild: discord.Guild, bot: discord.User, channel: discord.abc.GuildChannel, action_type: str):
        await self.log_security_event(
            guild,
            "⚠️ Verified Bot Triggered Channel Protection",
            f"Verified bot {bot} (`{bot.id}`) exceeded the channel {action_type} threshold.\n"
            f"Channel: {channel.name}\nAction: Logged only (not banned)",
            discord.Color.orange()
        )
        LogDebug(f"Verified bot {bot} exceeded channel action threshold in {guild.name}")

    async def reset_counter(self, bot_id: int):
        await asyncio.sleep(self.COOLDOWN)
        self.action_counter[bot_id] = 0

    def get_audit_action(self, action_type: str):
        return {
            "create": discord.AuditLogAction.channel_create,
            "delete": discord.AuditLogAction.channel_delete
        }[action_type]

    async def log_security_event(self, guild: discord.Guild, title: str, description: str, color: discord.Color):
        config = loadserverconfig().get(str(guild.id), {})
        log_channel_id = config.get("logchannel")

        if not log_channel_id:
            return

        log_channel = self.bot.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="Server", value=guild.name, inline=True)
        embed.add_field(name="Server ID", value=guild.id, inline=True)

        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            LogError(f"Failed to send log message: {str(e)}")

def setup(bot):
    bot.add_cog(ChannelProtectionCog(bot))
