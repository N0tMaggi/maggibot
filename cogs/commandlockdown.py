import discord
from discord.ext import commands
import json
import os
import datetime
from handlers.env import get_owner

lockdown_config_file = "config/lockdown.json"

def load_lockdown_config():
    try:
        with open(lockdown_config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(lockdown_config_file, "w") as f:
            json.dump({"lockdown": False}, f)
        return {"lockdown": False}
    except json.JSONDecodeError:
        os.remove(lockdown_config_file)
        with open(lockdown_config_file, "w") as f:
            json.dump({"lockdown": False}, f)
        return {"lockdown": False}

def save_lockdown_config(lockdown_status):
    with open(lockdown_config_file, "w") as f:
        json.dump({"lockdown": lockdown_status}, f)

class LockdownCheckFailure(commands.CheckFailure):
    pass

class CommandLockdown(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lockdown_data = load_lockdown_config()
        self.authorised = get_owner()

    @commands.slash_command(name="lockdown", description="Locks down the bot from commands")
    async def lockdown(self, ctx: discord.ApplicationContext):
        if ctx.user.id != self.authorised:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You do not have permission to lock down the bot.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_thumbnail(url="")
            embed.set_footer(text=f"Requested by {ctx.user}", icon_url=ctx.user.avatar.url)
            await ctx.response.send_message(embed=embed)
            return

        self.lockdown_data = load_lockdown_config()
        new_status = not self.lockdown_data.get("lockdown", False)
        save_lockdown_config(new_status)

        status = "🔒 Locked" if new_status else "🔓 Unlocked"
        embed_color = discord.Color.green() if new_status else discord.Color.blue()
        embed = discord.Embed(
            title=f"{status}",
            description=f"The bot has been {status.lower()} successfully.",
            color=embed_color,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url="")
        embed.add_field(name="Current Status", value=f"{'Lockdown' if new_status else 'Active'}", inline=True)
        embed.add_field(name="Action Taken By", value=f"{ctx.user.mention}", inline=True)
        embed.set_footer(text=f"Lockdown toggled by {ctx.user}", icon_url=ctx.user.avatar.url)
        await ctx.response.send_message(embed=embed)

async def global_lockdown_check(ctx: commands.Context):
    lockdown_data = load_lockdown_config()
    locked = lockdown_data.get("lockdown", False)
    if locked and ctx.user.id != get_owner():
        embed = discord.Embed(
            title="⚠️ Bot in Lockdown",
            description="The bot is currently in lockdown mode and cannot process commands.\nContact the bot owner for more info.",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url="")
        embed.add_field(name="Lockdown Status", value="Active", inline=False)
        embed.add_field(name="Reason", value="The bot owner has restricted command usage.", inline=False)
        embed.add_field(name="Note", value="This lockdown does not affect the bot owner.", inline=False)
        embed.set_footer(text=f"Attempted by {ctx.user}", icon_url=ctx.user.avatar.url)
        if hasattr(ctx, "response") and not ctx.response.is_done():
            await ctx.response.send_message(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed)
        raise LockdownCheckFailure("Bot in lockdown. Command execution prevented.")
    return True

def setup(bot: commands.Bot):
    bot.add_cog(CommandLockdown(bot))
    bot.add_check(global_lockdown_check)
