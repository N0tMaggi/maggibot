import discord
from discord.ext import commands
from discord.ext.commands import Cog
import datetime
import handlers.config as config
import handlers.debug as DebugHandler

class Server(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.serverconfig = config.loadserverconfig()

    @commands.slash_command(name="setup-logchannel", description="Set the log channel for the server")
    @commands.has_permissions(administrator=True)
    async def settings_logchannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        try:
            guild_id = str(ctx.guild.id)
            DebugHandler.LogDebug(f"Current server config for guild {guild_id}: {self.serverconfig}")

            if guild_id not in self.serverconfig:
                self.serverconfig[guild_id] = {}

            self.serverconfig[guild_id]["logchannel"] = channel.id
            DebugHandler.LogDebug(f"Updated server config for guild {guild_id}: {self.serverconfig[guild_id]}")

            config.saveserverconfig(self.serverconfig)

            embed = discord.Embed(
                title="📁 Log Channel Configuration",
                description=f"**Successfully configured logging system!**",
                color=0x3498DB,
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_author(
                name=f"{ctx.guild.name} Settings",
                icon_url=ctx.guild.icon.url if ctx.guild.icon else self.bot.user.avatar.url
            )
            embed.add_field(
                name="⚙️ Setting Updated",
                value=f"```diff\n+ Log Channel: #{channel.name}\n```",
                inline=False
            )
            embed.add_field(
                name="📝 Details",
                value=f"• Channel: {channel.mention}\n• ID: `{channel.id}`\n• Server: `{ctx.guild.id}`",
                inline=True
            )
            embed.set_footer(
                text=f"Configured by {ctx.author.display_name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else self.bot.user.avatar.url
            )
            await ctx.respond(embed=embed)

        except Exception as e:
            DebugHandler.LogError(f"An error occurred while setting the log channel: {e}")
            raise Exception(f"An error occurred while setting the log channel: {e}")

    @commands.slash_command(name="setup-showconfig", description="Show the current server configuration")
    @commands.has_permissions(administrator=True)
    async def settings_showconfig(self, ctx: discord.ApplicationContext):
        try:
            guild_id = str(ctx.guild.id)
            self.serverconfig = config.loadserverconfig()
            config_data = self.serverconfig.get(guild_id, None)

            embed = discord.Embed(
                title="🔧 Server Configuration",
                description=f"**Current settings for {ctx.guild.name}**",
                color=0x9B59B6,
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_author(
                name=f"{ctx.guild.name} System Settings",
                icon_url=ctx.guild.icon.url if ctx.guild.icon else self.bot.user.avatar.url
            )
            if config_data:
                config_list = "\n".join([f"• **{key}:** `{value}`" for key, value in config_data.items()])
                embed.add_field(name="📜 Active Settings", value=config_list, inline=False)
            else:
                embed.add_field(name="❌ No Configuration Found", value="This server hasn't set up any custom settings yet!", inline=False)
            embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else self.bot.user.avatar.url
            )
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            DebugHandler.LogError(f"An error occurred while showing the server configuration: {e}")
            raise Exception(f"An error occurred while showing the server configuration: {e}")

def setup(bot):
    bot.add_cog(Server(bot))