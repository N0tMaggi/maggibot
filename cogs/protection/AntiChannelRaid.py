import discord
from discord.ext import commands
from handlers.config import loadserverconfig, get_protection_log_channel
from utils.audit import find_audit_actor
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
            audit = await find_audit_actor(
                guild=guild,
                action=self.get_audit_action(action_type),
                target_id=channel.id,
            )

            actor = audit.user
            if not actor or not getattr(actor, "bot", False):
                return

            bot = actor
            self.action_counter[bot.id] += 1

            if self.action_counter[bot.id] > self.ACTION_THRESHOLD:
                if getattr(bot, "public_flags", None) and bot.public_flags.verified_bot:
                    await self.log_verified_bot_spam(guild, bot, channel, action_type, audit.reason)
                else:
                    await self.handle_unverified_bot_spam(guild, bot, channel, action_type, audit.reason)
                return

            asyncio.create_task(self.reset_counter(bot.id))
        except Exception as e:
            LogError(f"Channel {action_type} audit error in {guild.name}: {str(e)}")

    async def handle_unverified_bot_spam(
        self,
        guild: discord.Guild,
        bot: discord.User,
        channel: discord.abc.GuildChannel,
        action_type: str,
        reason: str | None,
    ):
        try:
            await guild.ban(bot, reason=f"Potential raid: {self.ACTION_THRESHOLD}+ channel {action_type}s")
            await self.log_security_event(
                guild,
                "Unverified bot triggered channel protection",
                {
                    "Bot": f"{bot} ({bot.id})",
                    "Verified": "False",
                    "Action": f"Ban (threshold {self.ACTION_THRESHOLD})",
                    "Channel": f"{channel.name} ({channel.id})",
                    "Audit reason": reason or "None",
                },
                discord.Color.dark_red(),
            )
        except Exception as e:
            LogError(f"Failed to ban bot in {guild.name}: {str(e)}")

    async def log_verified_bot_spam(
        self,
        guild: discord.Guild,
        bot: discord.User,
        channel: discord.abc.GuildChannel,
        action_type: str,
        reason: str | None,
    ):
        await self.log_security_event(
            guild,
            "Verified bot triggered channel protection",
            {
                "Bot": f"{bot} ({bot.id})",
                "Verified": "True",
                "Action": "Log only",
                "Channel": f"{channel.name} ({channel.id})",
                "Audit reason": reason or "None",
            },
            discord.Color.orange(),
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

    async def log_security_event(
        self,
        guild: discord.Guild,
        title: str,
        fields: dict[str, str],
        color: discord.Color,
    ):
        log_channel = get_protection_log_channel(guild)
        if not log_channel:
            return

        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

        for key, value in fields.items():
            embed.add_field(name=key, value=value, inline=False)

        embed.set_footer(text=f"Protection System | Guild ID: {guild.id}")

        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            LogError(f"Failed to send log message: {str(e)}")

def setup(bot):
    bot.add_cog(ChannelProtectionCog(bot))
