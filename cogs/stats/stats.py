from discord.ext import commands
import discord
import datetime
from extensions.statsextension import create_embed
from handlers.debug import LogDebug, LogError
from handlers.config import load_stats, save_stats, MESSAGE_XP_COUNT, ATTACHMENT_XP_COUNT, load_multiplier_config

class UserStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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

            if guild_id not in stats[user_id]["servers"]:
                stats[user_id]["servers"][guild_id] = {"messages": 0, "media": 0}

            xp_gain = MESSAGE_XP_COUNT
            stats[user_id]["servers"][guild_id]["messages"] += 1

            media_count = sum(1 for att in message.attachments if att.content_type and att.content_type.startswith(("image/", "video/")))
            if media_count:
                xp_gain += ATTACHMENT_XP_COUNT * media_count
                stats[user_id]["servers"][guild_id]["media"] += media_count

            config = load_multiplier_config()
            if str(message.channel.id) in config["channels"]:
                multipliers = [config["multipliers"].get(str(r.id), 1) for r in message.author.roles]
                xp_gain *= max(multipliers) if multipliers else 1

            stats[user_id]["xp"] += xp_gain
            save_stats(stats)
        except Exception as e:
            LogError(f"Message handling error: {str(e)}")


def setup(bot: commands.Bot):
    bot.add_cog(UserStats(bot))
