import discord
from discord.ext import commands
from discord.commands import slash_command
import datetime
import asyncio
import os
import handlers.config as cfg
from extensions.modextensions import create_mod_embed, send_mod_log
from handlers.debug import LogDebug, LogError, LogNetwork, LogSystem, LogModeration


class TimeoutSystem(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.slash_command(name="mod-timeout", description="Timeout a user from the server")
    @commands.has_permissions(moderate_members=True)
    async def mod_timeout(self, ctx, user: discord.Member, duration: str, *, reason: str = "No reason provided"):
        try:
            try:
                duration_timedelta = self.convert_duration_to_timedelta(duration)
                if duration_timedelta is None:
                    raise ValueError("Invalid duration format. Use '1m', '1h', '1d', etc.")
            except ValueError as e:
                embed = create_mod_embed("❌ Invalid Duration", str(e), 'error', ctx.author)
                await ctx.respond(embed=embed, ephemeral=True)
                return

            if user == ctx.author:
                embed = create_mod_embed(
                    "❌ Self-Timeout Attempt",
                    "You cannot timeout yourself!",
                    'error',
                    ctx.author
                )
                await ctx.respond(embed=embed, ephemeral=True)
                LogModeration(f"Self-timeout attempt by {ctx.author.id}")
                return

            try:
                user_embed = create_mod_embed(
                    "⏳ Timeout Applied",
                    f"You have been timed out in **{ctx.guild.name}**\n**Duration:** {duration}\n**Reason:** {reason}",
                    'warning'
                )
                await user.send(embed=user_embed)
                LogModeration(f"Timeout notification sent to {user.id}")
            except discord.Forbidden:
                LogError(f"Failed to DM timed-out user {user.id}")

            try:
                await user.timeout_for(duration_timedelta, reason=f"{ctx.author}: {reason}")
                LogModeration(f"Timeout applied to {user.id} in {ctx.guild.id}")
            except discord.Forbidden:
                embed = create_mod_embed(
                    "❌ Permission Denied",
                    "I don't have permission to timeout this user",
                    'error',
                    ctx.author
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            confirm_embed = create_mod_embed(
                "✅ Timeout Successful",
                f"{user.mention} has been timed out for {duration}",
                'success',
                ctx.author
            )
            confirm_embed.add_field(name="User ID", value=user.id)
            confirm_embed.add_field(name="Duration", value=duration)
            confirm_embed.add_field(name="Reason", value=reason)
            confirm_embed.set_thumbnail(url=user.avatar.url)
            await ctx.respond(embed=confirm_embed)

            log_data = {
                "title": "⏳ Timeout Executed",
                "description": f"**User:** {user.mention}\n**Moderator:** {ctx.author.mention}\n**Duration:** {duration}",
                "color_type": 'mod_action',
                "author": ctx.author
            }
            await send_mod_log(ctx.guild.id, log_data)

        except Exception as e:
            LogError(f"Timeout error: {str(e)}")
            await ctx.followup.send(embed=create_mod_embed(
                "⚠️ Error",
                f"An error occurred while applying the timeout: {str(e)}",
                'error', ctx.author), ephemeral=True)

    def convert_duration_to_timedelta(self, duration: str) -> datetime.timedelta:
        """Converts a duration string like '1h', '30m' to a timedelta object"""
        if duration.endswith('m'):
            minutes = int(duration[:-1])
            return datetime.timedelta(minutes=minutes)
        elif duration.endswith('h'):
            hours = int(duration[:-1])
            return datetime.timedelta(hours=hours)
        elif duration.endswith('d'):
            days = int(duration[:-1])
            return datetime.timedelta(days=days)
        else:
            return None 


def setup(bot):
    bot.add_cog(TimeoutSystem(bot))
