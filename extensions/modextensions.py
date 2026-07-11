import discord
import handlers.config as cfg
from handlers.debug import LogDebug, LogError, LogModeration
from utils.components import build_mod_container, build_view

def create_mod_embed(title, description, color_type='info', author=None) -> discord.ui.Container:
    """Create a standardized moderation container (Components V2)."""
    return build_mod_container(
        title=title,
        description=description,
        color_type=color_type,
        author=author,
    )

async def send_mod_log(guild_id, embed_data, bot):
    try:
        guild = bot.get_guild(guild_id)
        if not guild:
            LogError(f"Guild {guild_id} not found by bot")
            return

        # Text channel logging
        log_channel = cfg.get_log_channel(guild)
        if log_channel and isinstance(log_channel, discord.TextChannel):
            try:
                container = create_mod_embed(**embed_data)
                await log_channel.send(view=build_view(container))
                LogModeration(f"Log sent to channel {log_channel.id}")
            except Exception as e:
                LogError(f"Failed to send log to text channel: {e}")
        else:
            LogDebug(f"No log channel for guild {guild_id}")

        # Forum logging
        forum = cfg.get_logging_forum(guild)
        if forum and isinstance(forum, discord.ForumChannel):
            try:
                container = create_mod_embed(**embed_data)
                thread_name = embed_data.get('title', 'Log')
                await forum.create_thread(name=thread_name, view=build_view(container))
            except Exception as e:
                LogError(f"Failed to create log thread: {e}")
    except Exception as e:
        LogError(f"Failed to send mod log: {str(e)}")

