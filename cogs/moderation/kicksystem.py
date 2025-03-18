import discord
from discord.ext import commands
from discord.commands import slash_command
import datetime
import asyncio
import os
import handlers.config as cfg
from handlers.modextensions import create_mod_embed, send_mod_log
from handlers.debug import LogDebug, LogError, LogNetwork, LogSystem, LogModeration


class Kicksystem(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.slash_command(name="mod-kick", description="Kick a user from the server")
    @commands.has_permissions(kick_members=True)
    async def mod_kick(self, ctx, user: discord.Member, *, reason: str = "No reason provided"):
        try:
            if user == ctx.author:
                embed = create_mod_embed(
                    "❌ Self-Kick Attempt",
                    "You cannot kick yourself!",
                    'error',
                    ctx.author
                )
                await ctx.respond(embed=embed, ephemeral=True)
                LogModeration(f"Self-kick attempt by {ctx.author.id}")
                return

            try:
                user_embed = create_mod_embed(
                    "👢 Account Kicked",
                    f"You were kicked from **{ctx.guild.name}**\n**Reason:** {reason}",
                    'error'
                )
                await user.send(embed=user_embed)
                LogModeration(f"Kick notification sent to {user.id}")
            except discord.Forbidden:
                LogError(f"Failed to DM kicked user {user.id}")

            try:
                await user.kick(reason=f"{ctx.author}: {reason}")
                LogModeration(f"Kicked {user.id} in {ctx.guild.id}")
            except discord.Forbidden:
                embed = create_mod_embed(
                    "❌ Permission Denied",
                    "I don't have permission to kick this user",
                    'error',
                    ctx.author
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            confirm_embed = create_mod_embed(
                "✅ Kick Successful",
                f"{user.mention} has been kicked",
                'success',
                ctx.author
            )
            confirm_embed.add_field(name="User ID", value=user.id)
            confirm_embed.add_field(name="Reason", value=reason)
            confirm_embed.set_thumbnail(url=user.avatar.url)
            await ctx.respond(embed=confirm_embed)

            log_data = {
                "title": "👢 Kick Executed",
                "description": f"**User:** {user.mention}\n**Moderator:** {ctx.author.mention}",
                "color_type": 'mod_action',
                "author": ctx.author
            }
            await send_mod_log(ctx.guild.id, log_data)

        except Exception as e:
            LogError(f"Kick error: {str(e)}")
            await ctx.followup.send(embed=create_mod_embed(
                "⚠️ Error",
                f"An error occurred while kicking the user: {str(e)}",
                'error', ctx.author), ephemeral=True)

def setup(bot: discord.Bot):
    bot.add_cog(Kicksystem(bot))