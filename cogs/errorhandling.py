import discord
from discord.ext import commands
from datetime import datetime
import os
import traceback
from cogs.commandlockdown import LockdownCheckFailure
import sys
from colorama import Fore, Style, init
import handlers.debug as DebugHandler

init(autoreset=True)

error_log_channel_id = os.getenv("ERROR_LOG_CHANNEL_ID")

class ErrorHandling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, LockdownCheckFailure):
            return
        try:
            await self.handle_error(ctx, error, "❌ Command Error")
        except Exception as e:
            self.fatal_error("Error handling command error", e)
            traceback.print_exc()

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        original_error = getattr(error, "original", error)
        if isinstance(original_error, LockdownCheckFailure):
            return
        if isinstance(error, discord.ApplicationCommandInvokeError):
            await self.handle_error(ctx, error, "⚠️ Application Command Invoke Error")
        elif isinstance(error, commands.CommandOnCooldown):
            await self.handle_error_without_log(ctx, error, "⏰ Command on cooldown")
        elif isinstance(error, commands.MissingPermissions):
            await self.handle_error_without_log(ctx, error, "🚫 Missing Permissions")  
        elif isinstance(error, commands.CommandError):
            await self.handle_error_without_log(ctx, error, "❌ Command Error")
        else:
            await self.handle_error(ctx, error, "❌ Unhandled Slash Command Error")

    async def handle_error(self, ctx, error, error_type):
        DebugHandler.LogDebug(f"Handling error for command: {ctx.command.name if ctx.command else 'Unknown'}")

        if "Fatal" in str(error):
            await self.fatal_error("A fatal error occurred in the command.", error)
            return  

        embed = discord.Embed(
            title=error_type,
            description=f"An error occurred while executing the command **{ctx.command.name if ctx.command else 'Unknown'}**.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📝 Error Details", value=f"```py\n{error}\n```", inline=False)
        embed.add_field(name="👤 User", value=f"{ctx.author} ({ctx.author.id})", inline=True)
        embed.add_field(name="💬 Channel", value=f"{ctx.channel} ({ctx.channel.id})", inline=True)
        guild_info = f"{ctx.guild} ({ctx.guild.id})" if ctx.guild else "Direct Message"
        embed.add_field(name="🏰 Server", value=guild_info, inline=True)
        embed.set_footer(
            text=f"Error in command: {ctx.command.name if ctx.command else 'Unknown'}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )

        try:
            if isinstance(ctx, discord.ApplicationContext):
                if ctx.response.is_done():
                    await ctx.followup.send(embed=embed, ephemeral=True)
                else:
                    await ctx.response.send_message(embed=embed, ephemeral=True)
            else:
                await ctx.send(embed=embed)
        except discord.Forbidden:
            DebugHandler.LogDebug(f"Permission error while sending message in channel: {ctx.channel.id}")  # Log debug message

            owner = ctx.guild.owner if ctx.guild else None
            if owner:
                try:
                    await owner.send(f"The bot doesn't have permission to send messages in the channel `{ctx.channel.name}`.")
                except discord.Forbidden:
                    DebugHandler.LogDebug(f"Failed to notify server owner about permission issue in channel {ctx.channel.id}.")

            pass
        except discord.HTTPException:
            DebugHandler.LogDebug(f"HTTP error while sending error message in channel: {ctx.channel.id}")  # Log debug message
            self.fatal_error("Failed to send error message.", "HTTPError")

        await self.log_error(ctx, error, embed)


    async def handle_error_without_log(self, ctx, error, error_type):
        embed = discord.Embed(
            title=error_type,
            description=f"An error occurred while executing the command **{ctx.command.name if ctx.command else 'Unknown'}**.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📝 Error Details", value=f"```py\n{error}\n```", inline=False)
        embed.add_field(name="👤 User", value=f"{ctx.author} ({ctx.author.id})", inline=True)
        embed.add_field(name="💬 Channel", value=f"{ctx.channel} ({ctx.channel.id})", inline=True)
        guild_info = f"{ctx.guild} ({ctx.guild.id})" if ctx.guild else "Direct Message"
        embed.add_field(name="🏰 Server", value=guild_info, inline=True)
        embed.set_footer(
            text=f"Error in command: {ctx.command.name if ctx.command else 'Unknown'}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )

        try:
            if isinstance(ctx, discord.ApplicationContext):
                if ctx.response.is_done():
                    await ctx.followup.send(embed=embed, ephemeral=True)
                else:
                    await ctx.response.send_message(embed=embed, ephemeral=True)
            else:
                await ctx.send(embed=embed)
        except discord.Forbidden:
            self.fatal_error("Bot has no permission to send messages in this channel.", "ForbiddenError")
        except discord.HTTPException:
            self.fatal_error("Failed to send error message.", "HTTPError")

    async def log_error(self, ctx, error, embed):
        if not error_log_channel_id:
            self.fatal_error("No error log channel ID set.", "MissingConfig")
            return

        try:
            log_channel = self.bot.get_channel(int(error_log_channel_id))
            if log_channel:
                await log_channel.send(embed=embed)
            else:
                self.fatal_error(f"Could not find the log channel with ID: {error_log_channel_id}", "InvalidChannel")
        except Exception as e:
            self.fatal_error("Error logging the error", e)
            traceback.print_exc()

    async def fatal_error(self, error_message, error):
        print(Fore.RED + Style.BRIGHT + f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        print(Fore.RED + Style.BRIGHT + f"FATAL ERROR: {error_message}")
        print(Fore.RED + Style.BRIGHT + f"Error details: {error}")
        print(Fore.RED + Style.BRIGHT + f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        traceback.print_exc()

        fatal_embed = discord.Embed(
            title="FATAL EXCEPTION",
            description=f"A **FATAL** error occurred in the system: {error_message}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        fatal_embed.add_field(name="📝 Error Details", value=f"```py\n{error}\n```", inline=False)
        fatal_embed.set_footer(text="FATAL System Failure")

        try:
            if error_log_channel_id:
                log_channel = self.bot.get_channel(int(error_log_channel_id))
                if log_channel:
                    await log_channel.send(embed=fatal_embed)
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
            print(Fore.RED + Style.BRIGHT + "FATAL ERROR while logging fatal error")
            print(Fore.RED + Style.BRIGHT + f"Error details: {e}")
            print(Fore.RED + Style.BRIGHT + f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
            traceback.print_exc()
            self.shutdown_system()

    def shutdown_system(self):
        print(Fore.RED + Style.BRIGHT + f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        print(Fore.RED + Style.BRIGHT + "Shutting down bot due to critical error.")
        print(Fore.RED + Style.BRIGHT + f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        sys.exit()

def setup(bot: commands.Bot):
    bot.add_cog(ErrorHandling(bot))
