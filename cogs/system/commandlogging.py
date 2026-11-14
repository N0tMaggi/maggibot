# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
from typing import Optional
from handlers.debug import LogDebug, LogError
from utils.embed_helpers import create_embed


class CommandLogging(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.log_channel_id = int(os.getenv('COMMAND_LOG_CHANNEL_ID', 0) or 0)

    async def get_log_channel(self) -> Optional[discord.TextChannel]:
        if not self.log_channel_id:
            return None
        try:
            return self.bot.get_channel(self.log_channel_id) or await self.bot.fetch_channel(self.log_channel_id)
        except Exception as e:
            LogDebug(f"Could not fetch command log channel: {e}")
            return None

    def format_activity(self, user: discord.User) -> str:
        if not hasattr(user, 'activity') or not user.activity:
            return "N/A"
        activity = user.activity
        activity_type = str(activity.type).split('.')[-1].title()
        if isinstance(activity, discord.Spotify):
            return f"🎵 {activity.title} - {activity.artist}"
        elif isinstance(activity, discord.CustomActivity):
            return f"📝 {activity.name}"
        elif isinstance(activity, discord.Game):
            return f"🎮 {activity.name}"
        return f"{activity_type}: {activity.name}" if activity.name else activity_type

    async def create_command_embed(self, ctx: discord.ApplicationContext) -> discord.Embed:
        is_dm = isinstance(ctx.channel, discord.DMChannel)
        user = ctx.author

        cmd_name = ctx.command.qualified_name if ctx.command else "Unknown"
        options_str = ""
        if hasattr(ctx, "selected_options") and ctx.selected_options:
            options_str = "```json\n" + "\n".join(
                [f"{opt['name']}: {opt['value']}" for opt in ctx.selected_options]
            ) + "\n```"

        fields = [
            ("👤 User Info", f"• Nutzer: {user.mention} (`{user.id}`)\n• Bot: {'✅' if user.bot else '❌'}", False),
            ("⚙️ Command Details", f"• Name: `/{cmd_name}`" + (f"\n• Optionen:\n{options_str}" if options_str else ""), False),
            ("🌐 Kontext", f"• Server: {ctx.guild.name if ctx.guild else 'Direct Message'}\n• Channel: {ctx.channel.mention if hasattr(ctx.channel, 'mention') else 'DM'}", False)
        ]

        if hasattr(user, 'activity') and user.activity:
            fields.append(("🎮 Aktivität", self.format_activity(user), True))

        embed = create_embed(
            title="📝 Command Execution Log",
            color="default" if is_dm else "primary",
            author=user,
            footer_text=f"Command: {cmd_name}",
            fields=fields
        )

        return embed

    @commands.Cog.listener()
    async def on_application_command(self, ctx: discord.ApplicationContext):
        try:
            log_channel = await self.get_log_channel()
            if not log_channel:
                return

            embed = await self.create_command_embed(ctx)
            if log_channel.permissions_for(log_channel.guild.me).send_messages:
                await log_channel.send(embed=embed)
        except Exception as e:
            LogDebug(f"Command log send failed: {e}")


def setup(bot: discord.Bot):
    bot.add_cog(CommandLogging(bot))
