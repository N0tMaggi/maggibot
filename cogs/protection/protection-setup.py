import discord
from discord.ext import commands
import json
import datetime
import handlers.debug as DebugHandler
import handlers.config as config
import time

mention_count = {}



class Protection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def is_authorized(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        else:
            raise commands.CommandError(f"User {ctx.author} is not authorized to use this command")

    @commands.slash_command(name="setup-protectionlog", description="Set the protection log channel")
    @commands.check(is_authorized)
    async def setprotectionlogchannel(self, ctx, channel: discord.TextChannel):
        serverconfig = config.loadserverconfig()
        serverconfig[str(ctx.guild.id)] = serverconfig.get(str(ctx.guild.id), {})
        serverconfig[str(ctx.guild.id)]["protectionlogchannel"] = channel.id
        config.saveserverconfig(serverconfig)

        reaction_embed = discord.Embed(
            title="Protection Log Channel",
            description=f"Protection log channel has been set to {channel.mention}",
            color=discord.Color.green()
        )
        reaction_embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        reaction_embed.timestamp = datetime.datetime.utcnow()

        await ctx.respond(embed=reaction_embed)

    @commands.slash_command(name="setup-protection", description="Enable or disable the protection system")
    @commands.check(is_authorized)
    async def antiraid(self, ctx, enabled: bool):
        serverconfig = config.loadserverconfig()
        serverconfig[str(ctx.guild.id)] = serverconfig.get(str(ctx.guild.id), {})
        serverconfig[str(ctx.guild.id)]["protection"] = enabled
        config.saveserverconfig(serverconfig)

        reaction_embed = discord.Embed(
            title="🔒 Protection System",
            description=f"Maggi Protection system has been {'✅ Enabled' if enabled else '❌ Disabled'}",
            color=discord.Color.green() if enabled else discord.Color.red()
        )

        reaction_embed.add_field(name="Status", value="Enabled" if enabled else "Disabled", inline=True)
        reaction_embed.add_field(name="Requested By", value=f"{ctx.author.mention}", inline=True)
        reaction_embed.add_field(name="Server", value=ctx.guild.name, inline=True)

        reaction_embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        reaction_embed.timestamp = datetime.datetime.utcnow()

        if ctx.guild.icon:
            reaction_embed.set_thumbnail(url=ctx.guild.icon.url)

        await ctx.respond(embed=reaction_embed)



    
def setup(bot):
    bot.add_cog(Protection(bot))
