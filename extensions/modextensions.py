# -*- coding: utf-8 -*-
import discord
import handlers.config as cfg
from handlers.debug import LogDebug, LogError, LogModeration
from utils.embed_helpers import create_mod_embed


async def send_mod_log(guild_id, embed_data, bot):
    try:
        guild = bot.get_guild(guild_id)
        if not guild:
            LogError(f"Guild {guild_id} not found by bot")
            return

        embed = create_mod_embed(**embed_data)

        # Text channel logging
        log_channel = cfg.get_log_channel(guild)
        if log_channel and isinstance(log_channel, discord.TextChannel):
            try:
                await log_channel.send(embed=embed)
                LogModeration(f"Log sent to channel {log_channel.id}")
            except Exception as e:
                LogError(f"Failed to send log to text channel: {e}")
        else:
            LogDebug(f"No log channel for guild {guild_id}")

        # Forum logging
        forum = cfg.get_logging_forum(guild)
        if forum and isinstance(forum, discord.ForumChannel):
            try:
                await forum.create_thread(
                    name=f"Mod Log - {embed.title[:50]}",
                    embed=embed,
                    reason="Moderation Action Log"
                )
                LogModeration(f"Log thread created in forum {forum.id}")
            except Exception as e:
                LogError(f"Failed to create log thread in forum: {e}")
    except Exception as e:
        LogError(f"send_mod_log failed: {e}")
