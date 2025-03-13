import discord
from discord.ext import commands
import json
import os
import datetime
from handlers.env import get_owner
from handlers.debug import LogSystem, LogError, LogModeration, LogDebug

lockdown_config_file = "config/lockdown.json"

def load_lockdown_config():
    try:
        with open(lockdown_config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        LogDebug("Lockdown config created")
        with open(lockdown_config_file, "w") as f:
            json.dump({"lockdown": False}, f)
        return {"lockdown": False}
    except json.JSONDecodeError as e:
        LogError(f"Corrupted lockdown config: {str(e)}")
        os.remove(lockdown_config_file)
        with open(lockdown_config_file, "w") as f:
            json.dump({"lockdown": False}, f)
        return {"lockdown": False}

def save_lockdown_config(lockdown_status):
    try:
        with open(lockdown_config_file, "w") as f:
            json.dump({"lockdown": lockdown_status}, f)
        LogSystem(f"Lockdown status updated to {lockdown_status}")
    except Exception as e:
        LogError(f"Failed to save lockdown config: {str(e)}")
        raise

class LockdownCheckFailure(commands.CheckFailure):
    pass

class CommandLockdown(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lockdown_data = load_lockdown_config()
        self.authorised = get_owner()

    def create_emergency_embed(self, title, description, color):
        embed = discord.Embed(
            title=f"🚨 {title} 🚨",
            description=description,
            color=color,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url="https://i.imgur.com/3JxW7Hc.png")
        embed.set_footer(
            text="Security System v1.0 • Emergency Protocol",
            icon_url=self.bot.user.avatar.url
        )
        return embed

    @commands.slash_command(name="lockdown", description="🔒 Emergency command lockdown system")
    async def lockdown(self, ctx: discord.ApplicationContext):
        """Toggle emergency command lockdown"""
        await ctx.defer()
        
        try:
            if ctx.user.id != self.authorised:
                embed = self.create_emergency_embed(
                    "ACCESS DENIED",
                    "**Unauthorized lockdown attempt detected!**\n\n"
                    "This incident has been logged and reported.",
                    discord.Color.red()
                )
                embed.add_field(
                    name="🚫 Security Alert",
                    value=f"User: {ctx.user.mention}\nID: `{ctx.user.id}`",
                    inline=False
                )
                await ctx.followup.send(embed=embed)
                LogModeration(f"Unauthorized lockdown attempt by {ctx.user.id}")
                return

            self.lockdown_data = load_lockdown_config()
            new_status = not self.lockdown_data.get("lockdown", False)
            save_lockdown_config(new_status)

            status_word = "ACTIVATED" if new_status else "DEACTIVATED"
            embed_color = discord.Color.red() if new_status else discord.Color.green()
            
            embed = self.create_emergency_embed(
                f"LOCKDOWN {status_word}",
                "**Global Command Restrictions**\n"
                f"```diff\n{'+' if new_status else '-'} EMERGENCY LOCKDOWN PROTOCOL\n```",
                embed_color
            )
            
            embed.add_field(
                name="🔐 System Status",
                value=f"```{'🛑 LOCKED DOWN' if new_status else '✅ OPERATIONAL'}```",
                inline=True
            )
            embed.add_field(
                name="🛡️ Authorized Personnel",
                value=f"```{ctx.user.display_name}```",
                inline=True
            )
            embed.add_field(
                name="📝 Audit Log",
                value=f"Action performed at: {discord.utils.format_dt(datetime.datetime.utcnow(), 'F')}",
                inline=False
            )
            
            await ctx.followup.send(embed=embed)
            LogSystem(f"Lockdown {'enabled' if new_status else 'disabled'} by {ctx.user.id}")

        except Exception as e:
            LogError(f"Lockdown command failed: {str(e)}")
            raise

async def global_lockdown_check(ctx: commands.Context):
    try:
        lockdown_data = load_lockdown_config()
        locked = lockdown_data.get("lockdown", False)
        
        if locked and ctx.user.id != get_owner():
            embed = discord.Embed(
                title="⛔ EMERGENCY LOCKDOWN ACTIVE",
                description=(
                    "**All non-essential commands have been disabled**\n\n"
                    "The bot is currently in emergency maintenance mode. "
                    "Please check back later or contact the bot owner for assistance."
                ),
                color=discord.Color.dark_red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_thumbnail(url="https://i.imgur.com/5Q4z4hD.png")
            embed.add_field(
                name="🔒 Security Level",
                value="```MAXIMUM ALERT```",
                inline=True
            )
            embed.add_field(
                name="🕒 Active Since",
                value=f"```{discord.utils.format_dt(datetime.datetime.utcnow(), 'R')}```",
                inline=True
            )
            embed.add_field(
                name="📩 Contact Support",
                value=f"```{get_owner()}```",
                inline=False
            )
            embed.set_footer(
                text=f"Security Violation Attempt by {ctx.user}",
                icon_url=ctx.user.avatar.url
            )
            
            if hasattr(ctx, "response") and not ctx.response.is_done():
                await ctx.response.send_message(embed=embed, ephemeral=True)
            else:
                await ctx.send(embed=embed)
            
            LogModeration(f"Command blocked during lockdown: {ctx.command} by {ctx.user.id}")
            raise LockdownCheckFailure("Lockdown active")
            
        return True
    except Exception as e:
        LogError(f"Lockdown check failed: {str(e)}")
        raise

def setup(bot: commands.Bot):
    bot.add_cog(CommandLockdown(bot))
    bot.add_check(global_lockdown_check)