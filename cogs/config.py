import discord
from discord.ext import commands
from discord.ext.commands import Cog
import os
import json
import asyncio
import datetime
import logging
import handlers.config as config
import handlers.debug as DebugHandler


class Server(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.serverconfig = config.loadserverconfig()

    @commands.slash_command(name="setup-logchannel", description="Set the log channel for the server")
    @commands.has_permissions(administrator=True)
    async def settings_logchannel(self, ctx, channel: discord.TextChannel):
        try:
            guild_id = str(ctx.guild.id)
            
            DebugHandler.LogDebug(f"Current server config for guild {guild_id}: {self.serverconfig}")

            if guild_id not in self.serverconfig:
                self.serverconfig[guild_id] = {}

            self.serverconfig[guild_id]["logchannel"] = channel.id
            DebugHandler.LogDebug(f"Updated server config for guild {guild_id}: {self.serverconfig[guild_id]}")

            config.saveserverconfig(self.serverconfig)

            embed = discord.Embed(
                title="Success",
                description=f"Log channel has been set to {channel.mention}",
                color=0x00ff00
            )
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
            embed.timestamp = datetime.datetime.utcnow()
            embed.set_thumbnail(url=ctx.guild.icon.url)
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            embed.add_field(name="Channel", value=channel.mention, inline=False)
            embed.add_field(name="Channel ID", value=channel.id, inline=False)
            embed.add_field(name="Guild ID", value=ctx.guild.id, inline=False)

            await ctx.respond(embed=embed)

        except Exception as e:
            DebugHandler.LogDebug(f"An error occurred while setting the log channel: {e}")
            await ctx.respond(f"An error occurred while setting the log channel: {e}")


    @commands.slash_command(name="setup-showconfig", description="Show the current server configuration")
    @commands.has_permissions(administrator=True)
    async def settings_showconfig(self, ctx):
        try:
            guild_id = str(ctx.guild.id)
            config_data = self.serverconfig.get(guild_id, None)
            embed = discord.Embed(
                title="Server Configuration",
                description="Current server configuration",
                color=0x00ff00
            )
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
            embed.timestamp = datetime.datetime.utcnow()
            embed.set_thumbnail(url=ctx.guild.icon.url)
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            if config_data is not None:
                for key, value in config_data.items():
                    embed.add_field(name=key, value=value, inline=False)
            else:
                embed.add_field(name="Error", value="No configuration found", inline=False)
            await ctx.respond(embed=embed)
        except Exception as e:
            DebugHandler.LogDebug(f"An error occurred while showing the server configuration: {e}")
        
        
def setup(bot):
    bot.add_cog(Server(bot))
