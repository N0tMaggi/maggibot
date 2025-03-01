import discord
from discord.ext import commands
from datetime import datetime
import os
import traceback
from cogs.commandlockdown import LockdownCheckFailure

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
            print(f"Error handling another error: {e}")
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
        else:
            await self.handle_error(ctx, error, "❌ Unhandled Slash Command Error")

    async def handle_error(self, ctx, error, error_type):
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
            print("Bot has no permission to send messages in this channel.")
        except discord.HTTPException:
            print("Failed to send error message.")

        if error_log_channel_id:
            log_channel = self.bot.get_channel(int(error_log_channel_id))
            if log_channel:
                await log_channel.send(embed=embed)

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
            print("Bot has no permission to send messages in this channel.")
        except discord.HTTPException:
            print("Failed to send error message.")

def setup(bot: commands.Bot):
    bot.add_cog(ErrorHandling(bot))
