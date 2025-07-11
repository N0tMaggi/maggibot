import discord
from discord.ext import commands
from datetime import datetime
import os
from handlers.debug import LogDebug, LogError
from typing import Optional

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = int(os.getenv('COMMAND_LOG_CHANNEL_ID', 0))
        self.colors = {
            'normal': discord.Color.blue(),
            'dm': discord.Color.dark_grey(),
            'error': discord.Color.red()
        }

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

    async def create_command_embed(self, ctx: discord.ApplicationContext) -> discord.Embed:
        is_dm = isinstance(ctx.channel, discord.DMChannel)
        color = self.colors['dm'] if is_dm else self.colors['normal']

        embed = discord.Embed(
            title="📝 Command Execution Log",
            color=color,
            timestamp=datetime.utcnow()
        )

        user = ctx.author
        embed.set_author(
            name=f"{user} ({user.id})",
            icon_url=user.display_avatar.url
        )

        embed.add_field(
            name="👤 User Info",
            value=f"• Bot: {'✅' if user.bot else '❌'}\n"
                 f"• Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                 f"• Status: {str(user.status).title() if hasattr(user, 'status') else 'N/A'}",
            inline=False
        )

        command_info = f"• Name: `/{ctx.command.qualified_name if ctx.command else 'Unknown'}`\n"
        if ctx.selected_options:
            command_info += "• Options: ```json\n" + "\n".join(
                [f"{opt['name']}: {opt['value']}" for opt in ctx.selected_options]
            ) + "```"

        embed.add_field(
            name="⚙️ Command Details",
            value=command_info,
            inline=False
        )

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

        embed.add_field(
            name="🌐 Context",
            value="\n".join(context_info),
            inline=False
        )

        if ctx.command:
            embed.set_footer(
                text=f"Command ID: {ctx.command.qualified_name} | Cooldown: {ctx.command.cooldown}",
                icon_url=self.bot.user.display_avatar.url
            )

        if hasattr(user, 'activity') and user.activity:
            embed.add_field(
                name="🎮 Current Activity",
                value=self.format_activity(user),
                inline=True
            )

        if ctx.interaction and ctx.interaction.response.is_done():
            embed.description = f"[Jump to Interaction](https://discord.com/channels/{ctx.guild.id if ctx.guild else '@me'}/{ctx.channel.id}/{ctx.interaction.id})"

        return embed

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

            await log_channel.send(embed=embed)
            
        except Exception as e:
            LogError(f"Failed to log command: {str(e)}")
            raise Exception(f"Failed to log command: {str(e)}") from e

def setup(bot):
    bot.add_cog(Logging(bot))