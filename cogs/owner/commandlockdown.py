import discord
from discord.ext import commands
import json
import os
import datetime
from handlers.env import get_owner
from handlers.debug import LogSystem, LogError, LogModeration, LogDebug
from handlers.config import load_lockdown_config, save_lockdown_config
from utils.components import build_container, build_view




class LockdownCheckFailure(commands.CheckFailure):
    pass

class CommandLockdown(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lockdown_data = load_lockdown_config()
        self.authorised = get_owner()

    def create_emergency_embed(self, title, description, color):
        return build_container(
            title=f"🚨 {title} 🚨",
            description=description,
            color=color,
            thumbnail="",
            footer_text="Security System v1.0 • Emergency Protocol",
            footer_icon=self.bot.user.avatar.url if self.bot.user and self.bot.user.avatar else None,
            timestamp=True,
            bot_user=self.bot.user,
        )

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
                    'error'
                )
                embed.add_item(discord.ui.TextDisplay(
                    f"**🚫 Security Alert**\nUser: {ctx.user.mention}\nID: `{ctx.user.id}`"
                ))
                await ctx.followup.send(view=build_view(embed))
                LogModeration(f"Unauthorized lockdown attempt by {ctx.user.id}")
                return

            self.lockdown_data = load_lockdown_config()
            new_status = not self.lockdown_data.get("lockdown", False)
            save_lockdown_config(new_status)

            status_word = "ACTIVATED" if new_status else "DEACTIVATED"
            embed_color = 'error' if new_status else 'success'
            
            embed = self.create_emergency_embed(
                f"LOCKDOWN {status_word}",
                "**Global Command Restrictions**\n"
                f"```diff\n{'+' if new_status else '-'} EMERGENCY LOCKDOWN PROTOCOL\n```",
                embed_color
            )
            
            embed.add_item(discord.ui.TextDisplay(
                f"**🔐 System Status**\n```{'🛑 LOCKED DOWN' if new_status else '✅ OPERATIONAL'}```"
            ))
            embed.add_item(discord.ui.TextDisplay(
                f"**🛡️ Authorized Personnel**\n```{ctx.user.display_name}```"
            ))
            embed.add_item(discord.ui.TextDisplay(
                f"**📝 Audit Log**\nAction performed at: {discord.utils.format_dt(datetime.datetime.utcnow(), 'F')}"
            ))
            
            await ctx.followup.send(view=build_view(embed))
            LogSystem(f"Lockdown {'enabled' if new_status else 'disabled'} by {ctx.user.id}")

        except Exception as e:
            LogError(f"Lockdown command failed: {str(e)}")
            raise

async def global_lockdown_check(ctx: commands.Context):
    try:
        lockdown_data = load_lockdown_config()
        locked = lockdown_data.get("lockdown", False)
        
        if locked and ctx.user.id != get_owner():
            embed = build_container(
                title="⛔ EMERGENCY LOCKDOWN ACTIVE",
                description=(
                    "**All non-essential commands have been disabled**\n\n"
                    "The bot is currently in emergency maintenance mode. "
                    "Please check back later or contact the bot owner for assistance."
                ),
                color=discord.Color.dark_red().value,
                thumbnail="",
                footer_text=f"Security Violation Attempt by {ctx.user}",
                footer_icon=ctx.user.avatar.url if ctx.user.avatar else None,
                timestamp=True,
            )
            embed.add_item(discord.ui.TextDisplay("**🔒 Security Level**\n```MAXIMUM ALERT```"))
            embed.add_item(discord.ui.TextDisplay(
                f"**🕒 Active Since**\n```{discord.utils.format_dt(datetime.datetime.utcnow(), 'R')}```"
            ))
            embed.add_item(discord.ui.TextDisplay(f"**📩 Contact Support**\n```{get_owner()}```"))
            
            if hasattr(ctx, "response") and not ctx.response.is_done():
                await ctx.response.send_message(view=build_view(embed), ephemeral=True)
            else:
                await ctx.send(view=build_view(embed))
            
            LogModeration(f"Command blocked during lockdown: {ctx.command} by {ctx.user.id}")
            raise LockdownCheckFailure("Lockdown active")
            
        return True
    except Exception as e:
        LogError(f"Lockdown check failed: {str(e)}")
        raise

def setup(bot: commands.Bot):
    bot.add_cog(CommandLockdown(bot))
    bot.add_check(global_lockdown_check)
