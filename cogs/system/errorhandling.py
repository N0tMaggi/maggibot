import discord
from discord.ext import commands
from datetime import datetime
import os
import traceback
from cogs.owner.commandlockdown import LockdownCheckFailure
import sys
from colorama import Fore, Style, init
import handlers.debug as DebugHandler
from handlers.env import get_owner
import uuid 

init(autoreset=True)

error_log_channel_id = os.getenv("ERROR_LOG_CHANNEL_ID")

class ErrorHandling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = get_owner()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # Check if error message contains "fatal" or "critical"
        error_message = str(error).lower()
        if "fatal" in error_message or "critical" in error_message:
            await self.fatal_error("FATAL ERROR encountered in: " + ctx.command.name, error, ctx)
            return

        if isinstance(error, LockdownCheckFailure):
            return
        try:
            await self.handle_error(ctx, error, "❌ Command Error")
        except Exception as e:
            await self.fatal_error("Error handling command error", e)
            traceback.print_exc()

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        error_message = str(error).lower()
        if "fatal" in error_message or "critical" in error_message:
            await self.fatal_error("FATAL ERROR encountered in application command error", error)
            return

        original_error = getattr(error, "original", error)
        if isinstance(original_error, LockdownCheckFailure):
            return
        if isinstance(error, discord.ApplicationCommandInvokeError):
            await self.handle_error(ctx, error, "⚠️ Application Command Invoke Error ⚠️")
            return
        if isinstance(original_error, commands.NoPrivateMessage):
            await self.handle_error_without_log(ctx, original_error, "🚫 No Private Message 🚫")
        elif isinstance(error, commands.CommandOnCooldown):
            await self.handle_error_without_log(ctx, error, "⏰ Command on cooldown")
        elif isinstance(error, commands.MissingPermissions):
            await self.handle_missing_permissions_error(ctx, error, "🚫 Missing Permissions 🚫")
        elif isinstance(error, commands.CommandError):
            await self.handle_error_without_log(ctx, error, "❌ Command Error ❌ ")
        else:
            await self.handle_error(ctx, error, "❌ Unhandled Slash Command Error ❌")

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        error = sys.exc_info()[1]
        DebugHandler.LogError(f"Unhandled error in event '{event}': {error}")
        traceback_text = traceback.format_exc()
        error_uid = str(uuid.uuid4())
        
        embed = discord.Embed(
            title="Unhandled Global Exception",
            description=f"An unhandled error occurred in event `{event}`.",
            color=discord.Color.brand_red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Error Details", value=f"```\n{error.__class__.__name__}: {error}\n```", inline=False)
        embed.add_field(name="Error ID", value=f"`{error_uid}`", inline=True)
        
        if len(traceback_text) > 1024:
            traceback_file = await self.create_traceback_file(traceback_text)
            embed.add_field(name="🔍 Traceback", value="See attached file", inline=False)
            try:
                if error_log_channel_id:
                    log_channel = self.bot.get_channel(int(error_log_channel_id))
                    if log_channel:
                        await log_channel.send(embed=embed, file=traceback_file)
            except Exception as e:
                print(Fore.RED + Style.BRIGHT + f"Error logging global error: {e}")
                traceback.print_exc()
        else:
            embed.add_field(name="🔍 Traceback", value=traceback_text, inline=False)
            try:
                if error_log_channel_id:
                    log_channel = self.bot.get_channel(int(error_log_channel_id))
                    if log_channel:
                        await log_channel.send(embed=embed)
            except Exception as e:
                print(Fore.RED + Style.BRIGHT + f"Error logging global error: {e}")
                traceback.print_exc()

    async def handle_error(self, ctx, error, error_type):
        DebugHandler.LogError(f"Handling error for command: {ctx.command.name if ctx.command else 'Unknown'}")
        
        error_uid = str(uuid.uuid4())
        DebugHandler.LogError(f"Generated error UID: {error_uid}")

        error_info = f"{error.__class__.__name__}: {error}"
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        traceback_text = "".join(tb_lines)

        embed = discord.Embed(
            title=error_type,
            description=f"An error occurred while executing the command **{ctx.command.name if ctx.command else 'Unknown'}**.",
            color=discord.Color.brand_red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Error Details", value=f"```\n{error_info}\n```", inline=False)
        embed.add_field(name="Error ID", value=f"`{error_uid}`", inline=True)  
        embed.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})", inline=True)
        embed.add_field(name="Channel", value=f"{ctx.channel} ({ctx.channel.id})", inline=True)
        guild_info = f"{ctx.guild} ({ctx.guild.id})" if ctx.guild else "Direct Message"
        embed.add_field(name="Server", value=guild_info, inline=True)
        embed.set_footer(
            text=f"Error in command: {ctx.command.name if ctx.command else 'Unknown'}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )

        try:
            if isinstance(ctx, discord.ApplicationContext):
                try:
                    if not ctx.response.is_done():
                        await ctx.response.send_message(embed=embed, ephemeral=True)
                    else:
                        await ctx.followup.send(embed=embed, ephemeral=True)
                except (discord.NotFound, discord.HTTPException) as e:
                    DebugHandler.LogError(f"Interaction expired for error response: {str(e)}")
            else:
                await ctx.send(embed=embed)
        except Exception as e:
            await self.fatal_error(f"Failed to send error response: {str(e)}", e)
            return

        if len(traceback_text) > 1024:
            traceback_file = await self.create_traceback_file(traceback_text)
            log_embed = embed.copy()
            log_embed.add_field(name="🔍 Traceback", value="See attached file", inline=False)
            await self.log_error(ctx, error, log_embed, traceback_file, error_uid)
        else:
            log_embed = embed.copy()
            log_embed.add_field(name="🔍 Traceback", value=traceback_text, inline=False)
            await self.log_error(ctx, error, log_embed, error_uid=error_uid)

    async def handle_error_without_log(self, ctx, error, error_type):
        error_uid = str(uuid.uuid4())  
        DebugHandler.LogError(f"Generated error UID: {error_uid}")

        error_info = f"{error.__class__.__name__}: {error}"

        embed = discord.Embed(
            title=error_type,
            description=f"An error occurred while executing the command **{ctx.command.name if ctx.command else 'Unknown'}**.",
            color=discord.Color.brand_red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Error Details", value=f"```\n{error_info}\n```", inline=False)
        embed.add_field(name="Error ID", value=f"`{error_uid}`", inline=True)  
        embed.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})", inline=True)
        embed.add_field(name="Channel", value=f"{ctx.channel} ({ctx.channel.id})", inline=True)
        guild_info = f"{ctx.guild} ({ctx.guild.id})" if ctx.guild else "Direct Message"
        embed.add_field(name="Server", value=guild_info, inline=True)
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
            await self.fatal_error("Bot has no permission to send messages in this channel.", "ForbiddenError")
        except discord.HTTPException:
            await self.fatal_error("Failed to send error message.", "HTTPError")

    async def handle_missing_permissions_error(self, ctx, error, error_type):
        error_uid = str(uuid.uuid4())   
        DebugHandler.LogError(f"Generated error UID: {error_uid}")

        missing_perms = ", ".join(error.missing_permissions)  
        error_info = f"Missing Permissions: `{missing_perms}`"

        embed = discord.Embed(
            title=error_type,
            description=f"You are missing the required permissions to execute this command.",
            color=discord.Color.brand_red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Error Details", value=f"```\n{error_info}\n```", inline=False)
        embed.add_field(name="Error ID", value=f"`{error_uid}`", inline=True)  
        embed.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})", inline=True)
        embed.add_field(name="Channel", value=f"{ctx.channel} ({ctx.channel.id})", inline=True)
        guild_info = f"{ctx.guild} ({ctx.guild.id})" if ctx.guild else "Direct Message"
        embed.add_field(name="Server", value=guild_info, inline=True)
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
            await self.fatal_error("Bot has no permission to send messages in this channel.", "ForbiddenError")
        except discord.HTTPException:
            await self.fatal_error("Failed to send error message.", "HTTPError")

    async def log_error(self, ctx, error, embed, traceback_file=None, error_uid=None):
        if not error_log_channel_id:
            await self.fatal_error("No error log channel ID set.", "MissingConfig")
            return

        try:
            log_channel = self.bot.get_channel(int(error_log_channel_id))
            if log_channel:
                if error_uid:
                    embed.add_field(name="Error ID", value=f"`{error_uid}`", inline=False)  
                if traceback_file:
                    await log_channel.send(embed=embed, file=traceback_file)
                else:
                    await log_channel.send(embed=embed)
            else:
                await self.fatal_error(f"Could not find the log channel with ID: {error_log_channel_id}", "InvalidChannel")
        except Exception as e:
            await self.fatal_error("Error logging the error", e)
            traceback.print_exc()

    async def create_traceback_file(self, traceback_text):
        file_name = f"traceback_{datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        file_path = os.path.join("logs/traceback", file_name)  
        os.makedirs("logs/traceback", exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(traceback_text)

        return discord.File(file_path, filename=file_name)

    async def fatal_error(self, error_message, error):
        DebugHandler.LogError(f"FATAL ERROR: {error_message} | Details: {error}")
        print(Fore.RED + Style.BRIGHT + f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        print(Fore.RED + Style.BRIGHT + f"FATAL ERROR: {error_message}")
        print(Fore.RED + Style.BRIGHT + f"Error details: {error}")
        print(Fore.RED + Style.BRIGHT + f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        traceback.print_exc()

        fatal_embed = discord.Embed(
            title="FATAL EXCEPTION",
            description=f"A **FATAL** error occurred in the system: {error_message}",
            color=discord.Color.brand_red(),
            timestamp=datetime.utcnow()
        )
        fatal_embed.add_field(name="📝 Error Details", value=f"{error.__class__.__name__}: {error}\n", inline=False)
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

    def create_embed(self, title, description, style):
        return discord.Embed(
            title=title,
            description=description,
            color=discord.Color.brand_red(),
            timestamp=datetime.utcnow()
        )

def setup(bot: commands.Bot):
    bot.add_cog(ErrorHandling(bot))
