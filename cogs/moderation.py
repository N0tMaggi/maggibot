import discord
from discord.ext import commands
from discord.commands import slash_command
import json
import requests
import datetime
import re
import asyncio
import os
import dotenv
import handlers.config as cfg

emoji_success = os.getenv("emoji_success") or "✅"
emoji_error = os.getenv("emoji_error") or "❌"
emoji_warning = os.getenv("emoji_warning") or "⚠️"

class Moderation(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.slash_command(name="checkperms", description="Check if the bot has every required permission")
    @commands.has_permissions(administrator=True)
    async def checkperms(self, ctx):


        # Send an initial scanning animation embed
        scanning_embed = discord.Embed(
            title="Scanning Bot Permissions",
            description="⏳ Scanning for required permissions...",
            color=discord.Color.blue()
        )
        await ctx.respond(embed=scanning_embed)

        # Simulate a scanning delay for animation effect
        await asyncio.sleep(2)

        # Check for required permissions (currently only 'administrator' is required)
        required_permissions = ["administrator"]
        missing_permissions = []
        for permission in required_permissions:
            if not getattr(ctx.guild.me.guild_permissions, permission):
                missing_permissions.append(permission)

        if missing_permissions:
            result_message = (
                f"🚨 **Permission Check Failed** 🚨\n\n"
                f"Hey {ctx.author.mention},\n"
                f"I checked my permissions on this server, and it looks like I'm **missing** some required permissions.\n\n"
                f"🔴 **Missing Permissions:**\n"
                f"➜ `{', '.join(missing_permissions)}`\n\n"
                "Please update my permissions to ensure I can function properly."
            )
            color = discord.Color.red()
        else:
            result_message = (
                f"✅ **Permission Check Passed** ✅\n\n"
                f"Hey {ctx.author.mention},\n"
                "I have **all** the required permissions to function properly on this server. 🎉\n\n"
                "If you ever need to check again, just use this command!"
            )
            color = discord.Color.green()
        
        final_embed = discord.Embed(
            title="🔍 Bot Permissions Check",
            description=result_message,
            color=color
        )
        final_embed.set_footer(text="Permission Check | ModSystem | Maggi", icon_url=ctx.bot.user.avatar.url)


        # Generate a detailed permissions report for the server owner
        bot_perms = ctx.guild.me.guild_permissions
        perms_dict = {perm: getattr(bot_perms, perm) for perm in discord.Permissions.VALID_FLAGS}
        enabled_perms = [perm.replace("_", " ").title() for perm, value in perms_dict.items() if value]
        disabled_perms = [perm.replace("_", " ").title() for perm, value in perms_dict.items() if not value]

        owner_report = (
            f"**Server:** {ctx.guild.name}\n"
            f"**Bot Administrator:** {'Yes' if bot_perms.administrator else 'No'}\n\n"
            f"**Enabled Permissions:**\n" + ", ".join(enabled_perms) + "\n\n"
            f"**Disabled Permissions:**\n" + ", ".join(disabled_perms)
        )

        owner_embed = discord.Embed(
            title="Bot Permissions Report",
            description=owner_report,
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )
        owner_embed.set_footer(text="This report is for the server owner only.")

        # Attempt to send a DM with the detailed report to the server owner
        owner = ctx.guild.owner
        dm_success = True
        try:
            await owner.send(embed=owner_embed)
        except discord.Forbidden:
            dm_success = False

        # Update the original scanning embed with the final result
        await ctx.interaction.edit_original_response(embed=final_embed)

        # If sending the DM failed, send a follow-up message that pings the owner
        if not dm_success:
            error_embed = discord.Embed(
                title="Privacy Settings Error",
                description=(
                    f"{emoji_warning} I couldn't send a DM to the server owner ({owner.mention}). "
                    f"Please ask them to check their DM settings."
                ),
                color=discord.Color.orange()
            )
            await ctx.followup.send(embed=error_embed)



    @commands.slash_command(name="mod-ban", description="Ban a user from the server")
    @commands.has_permissions(ban_members=True)
    async def mod_ban(self, ctx, user: discord.Member, *, reason: str = "No reason provided."):
        if user == ctx.author:
            return_embed = discord.Embed(
                title="Error: Self-Ban",
                description="You can't ban yourself from the server!",
                color=discord.Color.red()
            )
            await ctx.respond(embed=return_embed)
            return
        else:
            try:
                #dm user
                user_embed = discord.Embed(
                    title="You've been banned from the server",
                    description=f"You've been banned from {ctx.guild.name} for the following reason:\n\n{reason}",
                    color=discord.Color.red()
                )
                user_embed.set_footer(text="Ban Reason | ModSystem | Maggi")
                user_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
                user_embed.timestamp = datetime.datetime.utcnow()
                await user.send(embed=user_embed)
            except discord.Forbidden:
                pass

            try:
                await ctx.guild.ban(user, reason=reason)
                return_embed = discord.Embed(
                    title="User Banned",
                    description=f"{user.mention} has been banned from the server.",
                    color=discord.Color.green()
                )
                return_embed.set_footer(text=f"Reason: {reason}")
                return_embed.set_thumbnail(url=user.avatar.url)
                return_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
                return_embed.timestamp = datetime.datetime.utcnow()
                return_embed.add_field(name="User ID", value=user.id, inline=True)
                return_embed.add_field(name="Banned By", value=ctx.author.mention, inline=True)
                return_embed.add_field(name="Banned At", value=return_embed.timestamp, inline=True)
                await ctx.respond(embed=return_embed)
                logchannel = cfg.get_log_channel(ctx.guild.id)
                if logchannel:
                    log_embed = discord.Embed(
                        title="User Banned",
                        description=f"A User has been banned from the server.",
                        color=discord.Color.red()
                    )
                    log_embed.set_thumbnail(url=user.avatar.url)
                    log_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
                    log_embed.add_field(name="User ID", value=user.id, inline=True)
                    log_embed.add_field(name="Banned By", value=ctx.author.mention, inline=True)
                    log_embed.add_field(name="Banned At", value=return_embed.timestamp, inline=True)
                    await logchannel.send(embed=log_embed)
                else:
                    return_embed = discord.Embed(
                        title="INFO: Log Channel Missing",
                        description="No log channel has been set for this server. Please set one using `/setup-logchannel`",
                        color=discord.Color.yellow()
                    )
                    return_embed.set_footer(text="Log Channel Missing | ModSystem | Maggi")
                    return_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
                    return_embed.timestamp = datetime.datetime.utcnow()
                    await ctx.respond(embed=return_embed)
            except discord.Forbidden:
                return_embed = discord.Embed(
                    title="Error",
                    description="I don't have permission to ban this user.",
                    color=discord.Color.red()
                    )
                return_embed.set_footer(text="Permission Error | ModSystem | Maggi")
                return_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
                return_embed.timestamp = datetime.datetime.utcnow()
                return_embed.add_field(name="User ID", value=user.id, inline=True)
                await ctx.respond(embed=return_embed)
            
        
    @commands.slash_command(name="mod-kick", description="Kick a user from the server")
    @commands.has_permissions(kick_members=True)
    async def mod_kick(self, ctx, user: discord.Member, *, reason: str = "No reason provided."):
        if user == ctx.author:
            return_embed = discord.Embed(
                title="Error: Self-Kick",
                description="You can't kick yourself from the server.",
                color=discord.Color.red()
            )
            return_embed.set_footer(text="Self-Kick Error | ModSystem | Maggi")
            return_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
            return_embed.timestamp = datetime.datetime.utcnow()
            await ctx.respond(embed=return_embed)
        else:
            try:
                user_embed = discord.Embed(
                    title="You've been kicked from the server",
                    description=f"You've been kicked from {ctx.guild.name} for the following reason:\n\n{reason}",
                    color=discord.Color.red()
                )
                user_embed.set_footer(text="Kick Reason | ModSystem | Maggi")
                user_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
                user_embed.timestamp = datetime.datetime.utcnow()
                await user.send(embed=user_embed)
                await user.kick(reason=reason)
                log_channel = cfg.get_log_channel(ctx.guild.id)
                if log_channel:
                    log_embed = discord.Embed(
                        title="Kick Log",
                        description=f"{user.mention} has been kicked from {ctx.guild.name} by {ctx.author.mention}",
                        color=discord.Color.red()
                    )
                    log_embed.set_thumbnail(url=user.avatar.url)
                    log_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
                    log_embed.add_field(name="User ID", value=user.id, inline=True)
                    log_embed.add_field(name="Reason", value=reason, inline=True)
                    log_embed.timestamp = datetime.datetime.utcnow()
                    await log_channel.send(embed=log_embed)
                else:
                    return_embed = discord.Embed(
                        title="INFO: Log Channel Missing",
                        description="No log channel has been set for this server. Please set one using `/setup-logchannel`",
                        color=discord.Color.yellow()
                    )
                    return_embed.set_footer(text="Log Channel Missing | ModSystem | Maggi")
                    return_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
                    return_embed.timestamp = datetime.datetime.utcnow()
                    await ctx.respond(embed=return_embed)
            except discord.Forbidden:
                return_embed = discord.Embed(
                    title="Error",
                    description="I don't have permission to kick this user.",
                    color=discord.Color.red()
                    )
                return_embed.set_footer(text="Permission Error | ModSystem | Maggi")
                return_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
                return_embed.timestamp = datetime.datetime.utcnow()
                return_embed.add_field(name="User ID", value=user.id, inline=True)
                await ctx.respond(embed=return_embed)



    @commands.slash_command(name="mod-showbanlist", description="Show the list of banned users")
    @commands.has_permissions(ban_members=True)
    async def mod_showbanlist(self, ctx):
        """Show the list of banned users"""
        
        banned_users = ctx.guild.bans()  # Get the BanIterator
        banned_user_list = []
    
        async for entry in banned_users:
            user = entry.user
            if user is not None and hasattr(user, 'id'):
                user_info = f"{user} ({user.id})"
            else:
                user_info = "Unknown User (ID not available)"
            banned_user_list.append(user_info)
    
        if not banned_user_list:
            return_embed = discord.Embed(
                title="INFO: No Banned Users",
                description="There are no banned users in this server.",
                color=discord.Color.yellow()
            )
            return_embed.set_footer(text="No Banned Users | ModSystem | Maggi")
            return_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
            return_embed.timestamp = datetime.datetime.utcnow()
            await ctx.respond(embed=return_embed)
        else:
            with open("banned_users.txt", "w", encoding="utf-8", errors='replace') as f:
                for user_info in banned_user_list:
                    f.write(f"{user_info}\n")
    
            await ctx.respond(file=discord.File("banned_users.txt"))
            os.remove("banned_users.txt")
    
            log_channel = cfg.get_log_channel(ctx.guild.id)
            if log_channel:
                log_embed = discord.Embed(
                    title="INFO: Banned Users List",
                    description="The list of banned users has been sent as a file.",
                    color=discord.Color.green()
                )
                log_embed.set_footer(text="Banned Users List | ModSystem | Maggi")
                log_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
                log_embed.timestamp = datetime.datetime.utcnow()
                await log_channel.send(embed=log_embed)
            else:
                await ctx.respond(embed=discord.Embed(
                    title="INFO: Log Channel Missing",
                    description="No log channel has been set for this server. Please set one using /setup-logchannel",
                    color=discord.Color.yellow()
                ))



def setup(bot: discord.Bot):
    bot.add_cog(Moderation(bot))
