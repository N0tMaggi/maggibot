import discord
from discord.ext import commands
from datetime import datetime
import os
from handlers.debug import LogDebug, LogError
from typing import Optional
from utils.components import build_container, build_view

class CommandLogging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = int(os.getenv('COMMAND_LOG_CHANNEL_ID', 0))
    async def get_log_channel(self) -> Optional[discord.TextChannel]:
        try:
            return await self.bot.fetch_channel(self.log_channel_id)
        except Exception as e:
            LogError(f"Failed to fetch log channel: {str(e)}")
            return None

    def format_activity(self, user: discord.User) -> str:  
        if not user.activity:
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

    async def create_command_embed(self, ctx: discord.ApplicationContext) -> discord.ui.Container:
        is_dm = isinstance(ctx.channel, discord.DMChannel)
        color = discord.Color.dark_grey().value if is_dm else 'info'

        user = ctx.author
        user_info = (
            f"• Bot: {'✅' if user.bot else '❌'}\n"
            f"• Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"• Status: {str(user.status).title() if hasattr(user, 'status') else 'N/A'}"
        )

        command_info = f"• Name: `/{ctx.command.qualified_name if ctx.command else 'Unknown'}`\n"
        if ctx.selected_options:
            command_info += "• Options: ```json\n" + "\n".join(
                [f"{opt['name']}: {opt['value']}" for opt in ctx.selected_options]
            ) + "```"

        context_info = []
        if ctx.guild:
            context_info.append(f"• Server: {ctx.guild.name} ({ctx.guild.id})")
            if isinstance(user, discord.Member): 
                context_info.append(f"• Joined: {user.joined_at.strftime('%Y-%m-%d %H:%M:%S')}")
                context_info.append(f"• Top Role: {user.top_role.mention}")

        channel_mention = "Direct Message" if isinstance(ctx.channel, discord.DMChannel) else ctx.channel.mention
        channel_id = ctx.channel.id if ctx.channel else 'N/A'

        context_info.append(f"• Channel: {channel_mention} ({channel_id})")
        context_info.append(f"• Shard: {ctx.guild.shard_id if ctx.guild else 0}")

        fields = [
            ("👤 User Info", user_info, False),
            ("⚙️ Command Details", command_info, False),
            ("🌐 Context", "\n".join(context_info), False),
        ]

        if hasattr(user, 'activity') and user.activity:
            fields.append(("🎮 Current Activity", self.format_activity(user), True))

        description = ""
        if ctx.interaction and ctx.interaction.response.is_done():
            description = (
                f"[Jump to Interaction]"
                f"(https://discord.com/channels/{ctx.guild.id if ctx.guild else '@me'}/{ctx.channel.id}/{ctx.interaction.id})"
            )

        container = build_container(
            title="📝 Command Execution Log",
            description=description,
            color=color,
            author=user,
            fields=fields,
            timestamp=True,
            bot_user=self.bot.user,
        )

        if ctx.command:
            container.add_item(discord.ui.TextDisplay(
                f"-# Command ID: {ctx.command.qualified_name} | Cooldown: {ctx.command.cooldown}"
            ))

        return container

    @commands.Cog.listener()
    async def on_application_command(self, ctx: discord.ApplicationContext):
        try:
            log_channel = await self.get_log_channel()
            if not log_channel:
                return

            embed = await self.create_command_embed(ctx)
            
            if log_channel and not log_channel.permissions_for(log_channel.guild.me).send_messages:
                LogError(f"Missing permissions to send messages in {log_channel.name}")
                return

            await log_channel.send(view=build_view(embed))
            
        except Exception as e:
            LogError(f"Failed to log command: {str(e)}")
            raise Exception(f"Failed to log command: {str(e)}") from e

def setup(bot):
    bot.add_cog(CommandLogging(bot))
