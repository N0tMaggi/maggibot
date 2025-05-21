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
                stats[user_id] = {"xp": 0.0, "servers": {}, "level": 0}

            # Initialize level if not present (for old users)
            if "level" not in stats[user_id]:
                stats[user_id]["level"] = int(stats[user_id]["xp"] // 20)

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
                LogDebug(f"[MSG] {message.author} sent {media_count} media attachment(s) in #{message.channel.name}")

            # Load config for XP multipliers
            config = load_multiplier_config()
            if str(message.channel.id) in config.get("channels", []):
                multipliers = [
                    config["multipliers"].get(str(role.id), 1)
                    for role in message.author.roles
                ]
                max_multiplier = max(multipliers) if multipliers else 1
                if max_multiplier > 1:
                    LogDebug(f"[XP-MULTI] {message.author} has XP multiplier {max_multiplier} in #{message.channel.name}")
                xp_gain *= max_multiplier

            stats[user_id]["xp"] += xp_gain

            # Level-Up logic
            old_level = stats[user_id]["level"]
            new_level = int(stats[user_id]["xp"] // 20)
            if new_level > old_level:
                stats[user_id]["level"] = new_level
                try:
                    embed = discord.Embed(
                        title="🎉 Level Up!",
                        description=f"Congratulations, **{message.author.display_name}**!\n\nYou have reached **Level {new_level}**!",
                        color=discord.Color.gold()
                    )
                    embed.add_field(name="Total XP", value=f"{stats[user_id]['xp']:.2f} XP", inline=False)
                    embed.add_field(name="Keep it up!", value="Stay active and climb even higher!", inline=False)
                    embed.set_thumbnail(url=message.author.display_avatar.url)
                    embed.set_footer(text="Maggibot Level System", icon_url=message.guild.icon.url if message.guild.icon else discord.Embed.Empty)
                    await message.author.send(embed=embed)
                except Exception as dm_error:
                    LogError(f"[LEVEL-UP] Could not send DM to {message.author}: {dm_error}")

            save_stats(stats)

            LogDebug(f"[XP] {message.author} gained {xp_gain:.2f} XP from message in #{message.channel.name} (Guild: {message.guild.name})")

        except Exception as e:
            LogError(f"[ERROR] Message handling error: {str(e)}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot or before.channel == after.channel:
            return

        try:
            guild_id = str(member.guild.id)
            user_id = str(member.id)
            key = (user_id, guild_id)
            now = datetime.datetime.utcnow()

            # Log leaving a voice channel
            if before.channel:
                LogDebug(f"[VOICE-LEAVE] {member} left voice channel '{before.channel.name}' (ID: {before.channel.id}) at {now.isoformat()} UTC")

                if key in self.voice_times:
                    join_time = self.voice_times[key]
                    duration = now - join_time
                    minutes = int(duration.total_seconds() // 60)

                    LogDebug(f"[VOICE-DURATION] {member} was in voice channel for {minutes} minute(s)")

                    if minutes > 0:
                        stats = load_stats()
                        user_stats = stats.setdefault(user_id, {"xp": 0.0, "servers": {}, "level": 0})
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
                            if max_multiplier > 1:
                                LogDebug(f"[XP-MULTI] {member} has voice XP multiplier {max_multiplier} in '{before.channel.name}'")
                            xp_gain *= max_multiplier

                        user_stats["xp"] += xp_gain

                        # Level-Up logic for voice XP
                        old_level = user_stats.get("level", int(user_stats["xp"] // 20))
                        new_level = int(user_stats["xp"] // 20)
                        if new_level > old_level:
                            user_stats["level"] = new_level
                            try:
                                embed = discord.Embed(
                                    title="🎉 Level Up!",
                                    description=f"Congratulations, **{member.display_name}**!\n\nYou have reached **Level {new_level}**!",
                                    color=discord.Color.gold()
                                )
                                embed.add_field(name="Total XP", value=f"{user_stats['xp']:.2f} XP", inline=False)
                                embed.add_field(name="Keep it up!", value="Stay active and climb even higher!", inline=False)
                                embed.set_thumbnail(url=member.display_avatar.url)
                                embed.set_footer(text="Maggibot Level System", icon_url=member.guild.icon.url if member.guild.icon else discord.Embed.Empty)
                                await member.send(embed=embed)
                            except Exception as dm_error:
                                LogError(f"[LEVEL-UP] Could not send DM to {member}: {dm_error}")

                        save_stats(stats)

                        LogDebug(f"[XP] {member} gained {xp_gain:.2f} XP from {minutes} voice minutes in '{before.channel.name}' (Guild: {member.guild.name})")

                    del self.voice_times[key]

            # Log joining a voice channel
            if after.channel:
                self.voice_times[key] = now
                LogDebug(f"[VOICE-JOIN] {member} joined voice channel '{after.channel.name}' (ID: {after.channel.id}) at {now.isoformat()} UTC")

        except Exception as e:
            LogError(f"[ERROR] Voice XP error: {str(e)}")

def setup(bot: commands.Bot):
    bot.add_cog(UserStats(bot))
