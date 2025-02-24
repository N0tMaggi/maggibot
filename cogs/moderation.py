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
        final_embed.set_footer(text="Permission Check | Moderation Bot", icon_url=ctx.bot.user.avatar.url)


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

def setup(bot: discord.Bot):
    bot.add_cog(Moderation(bot))
