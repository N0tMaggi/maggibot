import discord
from discord.ext import commands
from discord.commands import slash_command
from datetime import datetime
import os
import dotenv

error_log_channel_id = os.getenv("ERROR_LOG_CHANNEL_ID")

class ErrorHandling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            error_embed = discord.Embed(
                title="Command Not Found",
                description=f"The command {ctx.command.name}` was not found. Please check the command name and try again.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Error",
                value=f"{error}"
            )
            error_embed.add_field(
                name="User",
                value=f"{ctx.author} ({ctx.author.id})"
            )
            error_embed.add_field(
                name="Channel",
                value=f"{ctx.channel} ({ctx.channel.id})"
            )
            error_embed.add_field(
                name="Guild",
                value=f"{ctx.guild} ({ctx.guild.id})"
            )
            error_embed.set_footer(
                text=f"Error in command {ctx.command.name}"
            )
            await ctx.send(embed=error_embed)
            log_channel = self.bot.get_channel(error_log_channel_id)
            await log_channel.send(embed=error_embed)

        elif isinstance(error, commands.MissingRequiredArgument):
            error_embed = discord.Embed(
                title="Missing Required Argument",
                description=f"You are missing the required argument `{error.param.name}`. Please check the command usage and try again.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Error",
                value=f"{error}"
            )
            error_embed.add_field(
                name="User",
                value=f"{ctx.author} ({ctx.author.id})"
            )
            error_embed.add_field(
                name="Channel",
                value=f"{ctx.channel} ({ctx.channel.id})"
            )
            error_embed.add_field(
                name="Guild",
                value=f"{ctx.guild} ({ctx.guild.id})"
            )
            error_embed.set_footer(
                text=f"Error in command {ctx.command.name}"
            )
            await ctx.send(embed=error_embed)
            log_channel = self.bot.get_channel(error_log_channel_id)
            await log_channel.send(embed=error_embed)
        
        elif isinstance(error, commands.MissingPermissions):
            error_embed = discord.Embed(
                title="Missing Permissions",
                description=f"You are missing the required permissions to run the command `{ctx.command.name}`.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Error",
                value=f"{error}"
            )
            error_embed.add_field(
                name="User",
                value=f"{ctx.author} ({ctx.author.id})"
            )
            error_embed.add_field(
                name="Channel",
                value=f"{ctx.channel} ({ctx.channel.id})"
            )
            error_embed.add_field(
                name="Guild",
                value=f"{ctx.guild} ({ctx.guild.id})"
            )
            error_embed.set_footer(
                text=f"Error in command {ctx.command.name}"
            )
            await ctx.send(embed=error_embed)
            log_channel = self.bot.get_channel(error_log_channel_id)
            await log_channel.send(embed=error_embed)

        elif isinstance(error, commands.BotMissingPermissions):
            error_embed = discord.Embed(
                title="Missing Permissions",
                description=f"The bot is missing the required permissions to run the command `{ctx.command.name}`.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Error",
                value=f"{error}"
            )
            error_embed.add_field(
                name="User",
                value=f"{ctx.author} ({ctx.author.id})"
            )
            error_embed.add_field(
                name="Channel",
                value=f"{ctx.channel} ({ctx.channel.id})"
            )
            error_embed.add_field(
                name="Guild",
                value=f"{ctx.guild} ({ctx.guild.id})"
            )
            error_embed.set_footer(
                text=f"Error in command {ctx.command.name}"
            )
            await ctx.send(embed=error_embed)
            log_channel = self.bot.get_channel(error_log_channel_id)
            await log_channel.send(embed=error_embed)

        elif isinstance(error, commands.CommandOnCooldown):
            error_embed = discord.Embed(
                title="Command on Cooldown",
                description=f"The command `{ctx.command.name}` is on cooldown. Please wait `{error.retry_after:.2f}` seconds before trying again.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Error",
                value=f"{error}"
            )
            error_embed.add_field(
                name="User",
                value=f"{ctx.author} ({ctx.author.id})"
            )
            error_embed.add_field(
                name="Channel",
                value=f"{ctx.channel} ({ctx.channel.id})"
            )
            error_embed.add_field(
                name="Guild",
                value=f"{ctx.guild} ({ctx.guild.id})"
            )
            error_embed.set_footer(
                text=f"Error in command {ctx.command.name}"
            )
            await ctx.send(embed=error_embed)
            log_channel = self.bot.get_channel(error_log_channel_id)
            await log_channel.send(embed=error_embed)
        
        elif isinstance(error, commands.CheckFailure):
            error_embed = discord.Embed(
                title="Check Failure",
                description=f"A check failed on the command `{ctx.command.name}`.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Error",
                value=f"{error}"
            )
            error_embed.add_field(
                name="User",
                value=f"{ctx.author} ({ctx.author.id})"
            )
            error_embed.add_field(
                name="Channel",
                value=f"{ctx.channel} ({ctx.channel.id})"
            )
            error_embed.add_field(
                name="Guild",
                value=f"{ctx.guild} ({ctx.guild.id})"
            )
            error_embed.set_footer(
                text=f"Error in command {ctx.command.name}"
            )
            await ctx.send(embed=error_embed)
            log_channel = self.bot.get_channel(error_log_channel_id)
            await log_channel.send(embed=error_embed)
        
        elif isinstance(error, commands.ExtensionError):
            error_embed = discord.Embed(
                title="Extension Error",
                description=f"An error occurred in the extension `{ctx.command.name}`.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Error",
                value=f"{error}"
            )
            error_embed.add_field(
                name="User",
                value=f"{ctx.author} ({ctx.author.id})"
            )
            error_embed.add_field(
                name="Channel",
                value=f"{ctx.channel} ({ctx.channel.id})"
            )
            error_embed.add_field(
                name="Guild",
                value=f"{ctx.guild} ({ctx.guild.id})"
            )
            error_embed.set_footer(
                text=f"Error in extension {ctx.command.name}"
            )
            await ctx.send(embed=error_embed)
            log_channel = self.bot.get_channel(error_log_channel_id)
            await log_channel.send(embed=error_embed)

        elif isinstance(error, commands.CommandInvokeError):
            error_embed = discord.Embed(
                title="Command Invoke Error",
                description=f"An error occurred while invoking the command `{ctx.command.name}`.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Error",
                value=f"{error}"
            )
            error_embed.add_field(
                name="User",
                value=f"{ctx.author} ({ctx.author.id})"
            )
            error_embed.add_field(
                name="Channel",
                value=f"{ctx.channel} ({ctx.channel.id})"
            )
            error_embed.add_field(
                name="Guild",
                value=f"{ctx.guild} ({ctx.guild.id})"
            )
            error_embed.set_footer(
                text=f"Error in command {ctx.command.name}"
            )
            await ctx.send(embed=error_embed)
            log_channel = self.bot.get_channel(error_log_channel_id)
            await log_channel.send(embed=error_embed)
        
        # Handling general errors in python code
        elif isinstance(error, Exception):
            error_embed = discord.Embed(
                title="Error",
                description=f"An error occurred while running the command `{ctx.command.name}`.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Error",
                value=f"{error}"
            )
            error_embed.add_field(
                name="User",
                value=f"{ctx.author} ({ctx.author.id})"
            )
            error_embed.add_field(
                name="Channel",
                value=f"{ctx.channel} ({ctx.channel.id})"
            )
            error_embed.add_field(
                name="Guild",
                value=f"{ctx.guild} ({ctx.guild.id})"
            )
            error_embed.set_footer(
                text=f"Error in command {ctx.command.name}"
            )
            await ctx.send(embed=error_embed)
            log_channel = self.bot.get_channel(error_log_channel_id)
            await log_channel.send(embed=error_embed)
        
        #handling any other errors
        else:
            error_embed = discord.Embed(
                title="Error",
                description=f"An error occurred while running the command `{ctx.command.name}`.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            error_embed.add_field(
                name="Error",
                value=f"{error}"
            )
            error_embed.add_field(
                name="User",
                value=f"{ctx.author} ({ctx.author.id})"
            )
            error_embed.add_field(
                name="Channel",
                value=f"{ctx.channel} ({ctx.channel.id})"
            )
            error_embed.add_field(
                name="Guild",
                value=f"{ctx.guild} ({ctx.guild.id})"
            )
            error_embed.set_footer(
                text=f"Error in command {ctx.command.name}"
            )
            await ctx.send(embed=error_embed)
            log_channel = self.bot.get_channel(error_log_channel_id)
            await log_channel.send(embed=error_embed)


    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        error_embed = discord.Embed(
            title="Error",
            description=f"An error occurred in the event `{event}`. Please check the error and try again.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        error_embed.add_field(
            name="Error",
            value=f"{args[0]}"
        )
        error_embed.set_footer(
            text=f"Error in event {event}"
        )
        log_channel = self.bot.get_channel(error_log_channel_id)
        await log_channel.send(embed=error_embed)


def setup(bot):
    bot.add_cog(ErrorHandling(bot))
            