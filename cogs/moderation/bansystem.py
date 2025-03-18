import discord
from discord.ext import commands
from discord.commands import slash_command
import datetime
import asyncio
import os
import handlers.config as cfg
from handlers.modextensions import create_mod_embed, send_mod_log
from handlers.debug import LogDebug, LogError, LogNetwork, LogSystem, LogModeration


class BanSystem(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.slash_command(name="mod-ban", description="Ban a user from the server")
    @commands.has_permissions(ban_members=True)
    async def mod_ban(self, ctx, user: discord.Member, *, reason: str = "No reason provided"):
        try:
            if user == ctx.author:
                embed = create_mod_embed(
                    "❌ Self-Ban Attempt",
                    "You cannot ban yourself!",
                    'error',
                    ctx.author
                )
                await ctx.respond(embed=embed, ephemeral=True)
                LogModeration(f"Self-ban attempt by {ctx.author.id}")
                return

            # User notification
            try:
                user_embed = create_mod_embed(
                    "🔨 Account Banned",
                    f"You were banned from **{ctx.guild.name}**\n**Reason:** {reason}",
                    'error'
                )
                await user.send(embed=user_embed)
                LogModeration(f"Ban notification sent to {user.id}")
            except discord.Forbidden:
                LogError(f"Failed to DM banned user {user.id}")

            # Execute ban
            try:
                await user.ban(reason=f"{ctx.author}: {reason}")
                LogModeration(f"Banned {user.id} in {ctx.guild.id}")
            except discord.Forbidden:
                embed = create_mod_embed(
                    "❌ Permission Denied",
                    "I don't have permission to ban this user",
                    'error',
                    ctx.author
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # Response embed
            confirm_embed = create_mod_embed(
                "✅ Ban Successful",
                f"{user.mention} has been banned",
                'success',
                ctx.author
            )
            confirm_embed.add_field(name="User ID", value=user.id)
            confirm_embed.add_field(name="Reason", value=reason)
            confirm_embed.set_thumbnail(url=user.avatar.url)
            await ctx.respond(embed=confirm_embed)

            # Log channel handling
            log_data = {
                "title": "🔨 Ban Executed",
                "description": f"**User:** {user.mention}\n**Moderator:** {ctx.author.mention}",
                "color_type": 'mod_action',
                "author": ctx.author
            }
            await send_mod_log(ctx.guild.id, log_data)

        except Exception as e:
            LogError(f"Ban error: {str(e)}")
            await ctx.followup.send(embed=create_mod_embed(
                "⚠️ Error",
                f"An error occurred while banning the user: {str(e)}",
                'error', ctx.author), ephemeral=True)
            
def setup(bot: discord.Bot):
    bot.add_cog(BanSystem(bot))