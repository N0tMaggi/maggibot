from discord.ext import commands
import discord
import datetime
from handlers.debug import LogError, LogDebug
from handlers.config import (
    load_stats,
    save_stats,
    MESSAGE_XP_COUNT,
    ATTACHMENT_XP_COUNT,
    VOICE_XP_COUNT,
    load_multiplier_config,
)

class UserStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_times = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return
        try:
            stats = load_stats()
            user_id = str(message.author.id)
            guild_id = str(message.guild.id)

            if user_id not in stats:
                stats[user_id] = {"xp": 0.0, "servers": {}}

            server_stats = stats[user_id]["servers"].setdefault(guild_id, {
                "messages": 0,
                "media": 0,
                "voiceminutes": 0
            })

            xp_gain = MESSAGE_XP_COUNT
            server_stats["messages"] += 1

            media_count = sum(
                1 for att in message.attachments if att.content_type and att.content_type.startswith(("image/", "video/"))
            )
            if media_count:
                xp_gain += ATTACHMENT_XP_COUNT * media_count
                server_stats["media"] += media_count

            config = load_multiplier_config()
            if str(message.channel.id) in config.get("channels", []):
                multipliers = [
                    config["multipliers"].get(str(role.id), 1)
                    for role in message.author.roles
                ]
                max_multiplier = max(multipliers) if multipliers else 1
                xp_gain *= max_multiplier

            stats[user_id]["xp"] += xp_gain
            save_stats(stats)

            # Optional debug
            # LogDebug(f"[XP] {message.author} gained {xp_gain:.2f} XP (msg + media)")

        except Exception as e:
            LogError(f"Message handling error: {str(e)}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot or before.channel == after.channel:
            return

        try:
            guild_id = str(member.guild.id)
            user_id = str(member.id)
            key = (user_id, guild_id)

            if before.channel and key in self.voice_times:
                join_time = self.voice_times[key]
                duration = datetime.datetime.utcnow() - join_time
                minutes = int(duration.total_seconds() // 60)

                if minutes > 0:
                    stats = load_stats()
                    user_stats = stats.setdefault(user_id, {"xp": 0.0, "servers": {}})
                    server_stats = user_stats["servers"].setdefault(guild_id, {
                        "messages": 0,
                        "media": 0,
                        "voiceminutes": 0
                    })

                    server_stats["voiceminutes"] += minutes
                    xp_gain = VOICE_XP_COUNT * minutes

                    config = load_multiplier_config()
                    if str(before.channel.id) in config.get("channels", []):
                        multipliers = [
                            config["multipliers"].get(str(role.id), 1)
                            for role in member.roles
                        ]
                        max_multiplier = max(multipliers) if multipliers else 1
                        xp_gain *= max_multiplier

                    user_stats["xp"] += xp_gain
                    save_stats(stats)

                    # Optional debug
                    LogDebug(f"[XP] {member} gained {xp_gain:.2f} XP from {minutes} voice minutes")

                del self.voice_times[key]

            if after.channel:
                self.voice_times[key] = datetime.datetime.utcnow()

        except Exception as e:
            LogError(f"Voice XP error: {str(e)}")

def setup(bot: commands.Bot):
    bot.add_cog(UserStats(bot))
