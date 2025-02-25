import discord
from discord.ext import commands
from discord.ext.commands import Cog
from discord import Interaction
import json
import datetime
import os
from handlers.env import get_owner

lockdown_config_file = "config/lockdown.json"

def load_lockdown_config():
    """Load the lockdown status from the file."""
    try:
        with open(lockdown_config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # If the file doesn't exist, create it with default values ("lockdown": false)
        with open(lockdown_config_file, "w") as f:
            json.dump({"lockdown": False}, f)
        return {"lockdown": False}
    except json.JSONDecodeError:
        # Delete the file and create a new one in case of corruption
        os.remove(lockdown_config_file)
        with open(lockdown_config_file, "w") as f:
            json.dump({"lockdown": False}, f)
        return {"lockdown": False}

def save_lockdown_config(lockdown_status):
    """Save the lockdown status to the config file."""
    with open(lockdown_config_file, "w") as f:
        json.dump({"lockdown": lockdown_status}, f)

# This is a cog for locking down the bot from commands
# This is useful when you want to prevent users from using commands
# It prevents any user from using commands until it's unlocked

class CommandLockdown(Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load the current lockdown state from the file
        self.lockdown_data = load_lockdown_config()
        self.locked = self.lockdown_data.get("lockdown", False)
        self.authorised = get_owner()

    @commands.slash_command(name="lockdown", description="Locks down the bot from commands")
    async def lockdown(self, ctx):
        if ctx.user.id != self.authorised:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="**You do not have permission to lock down the bot.**\nOnly the bot owner can execute this command.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Requested by {ctx.user}", icon_url=ctx.user.avatar.url)
            await ctx.response.send_message(embed=embed)
            return

        # Toggle the lockdown state
        self.locked = not self.locked
        save_lockdown_config(self.locked)

        # Send a confirmation message
        status = "🔒 Locked" if self.locked else "🔓 Unlocked"
        embed_color = discord.Color.green() if self.locked else discord.Color.blue()

        embed = discord.Embed(
            title=f"{status} Down",
            description=f"**The bot has been {status.lower()} successfully.**",
            color=embed_color,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Current Status", value=f"The bot is now {'in lockdown' if self.locked else 'active'}.", inline=False)
        embed.add_field(name="Action Taken By", value=f"{ctx.user.mention}", inline=False)
        embed.set_footer(text=f"Lockdown toggled by {ctx.user}", icon_url=ctx.user.avatar.url)

        await ctx.response.send_message(embed=embed)

    async def cog_check(self, ctx):
        """Override cog_check to prevent commands when the bot is locked down."""
        # Reload the lockdown status each time the check is performed
        self.lockdown_data = load_lockdown_config()
        self.locked = self.lockdown_data.get("lockdown", False)

        if self.locked and ctx.user.id != self.authorised:
            embed = discord.Embed(
                title="⚠️ Bot in Lockdown",
                description="**The bot is currently in lockdown mode and cannot process commands.**\nPlease contact the bot owner for more information.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Lockdown Status", value="Active", inline=False)
            embed.add_field(name="Reason", value="The bot owner has restricted command usage.", inline=False)
            embed.add_field(name="Note", value="This lockdown does not affect the bot owner.", inline=False)
            embed.set_footer(text=f"Attempted by {ctx.user}", icon_url=ctx.user.avatar.url)

            await ctx.response.send_message(embed=embed)
            return False
        return True

def setup(bot):
    bot.add_cog(CommandLockdown(bot))
