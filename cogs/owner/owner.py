import discord
from discord.ext import commands
import datetime
import handlers.debug as DH
import os


class OwnerCommands(commands.Cog):
        def __init__(self, bot):
            self.bot = bot


        @commands.slash_command(name= "stop", description="[Owner only] Stop the bot 🛑")
        async def stop(self, ctx):
            authorised = int(os.getenv('OWNER_ID'))
            if ctx.author.id == authorised:
                embed = discord.Embed(
                    title="🛑 Bot Shutdown",
                    description="The bot is shutting down... Please wait a moment.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Shutdown Reason", value="Manual shutdown initiated by the owner.", inline=False)
                embed.add_field(name="Time of Shutdown", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
                embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
                await ctx.respond(embed=embed)
                DH.LogDebug(f"Bot shutdown initiated by {ctx.author} ({ctx.author.id})")
                await self.bot.close()
            else:
                embed = discord.Embed(
                    title="🚫 Permission Denied",
                    description="You do not have permission to stop the bot. Please contact the owner for assistance.",
                    color=discord.Color.orange()
                )
                embed.add_field(name="Owner ID", value=os.getenv('OWNER_ID'), inline=True)
                embed.add_field(name="Your ID", value=ctx.author.id, inline=True)
                embed.add_field(name="Contact Method", value="Please send a direct message to the owner.", inline=False)
                embed.set_footer(text=f"Requested by {ctx.author} | ID: {ctx.author.id}", icon_url=ctx.author.avatar.url)
                DH.LogDebug(f" Stop Permission denied for {ctx.author} | ID: {ctx.author.id}") 
                await ctx.respond(embed=embed)


        @commands.slash_command(name= "reboot", description="[Owner only] Reboot the bot 🔄")
        async def reboot(self, ctx):
            authorised = int(os.getenv('OWNER_ID'))
            if ctx.author.id == authorised:
                embed = discord.Embed(
                    title="🤖 Bot Reboot",
                    description="The bot is rebooting... Please wait a moment. ⏰",
                    color=discord.Color.blue()
                )
                embed.add_field(name="🔧 Reboot Reason", value="Manual reboot initiated by the owner.", inline=False)
                embed.add_field(name="🔄 Reboot Status", value="In Progress...", inline=False)
                embed.set_footer(text=f"Requested by {ctx.author} | Rebooting...", icon_url=ctx.author.avatar.url)
                await ctx.respond(embed=embed)
                DH.LogDebug(f"Reboot initiated by {ctx.author} | ID: {ctx.author.id}")
                await self.bot.close()
            else:
                embed = discord.Embed(
                    title="🚫 Permission Denied",
                    description="You do not have permission to reboot the bot. Please contact the owner for assistance.",
                    color=discord.Color.orange()
                )
                embed.add_field(name="Owner ID", value=os.getenv('OWNER_ID'), inline=True)
                embed.add_field(name="Your ID", value=ctx.author.id, inline=True)
                embed.add_field(name="Contact Method", value="Please send a direct message to the owner.", inline=False)
                embed.set_footer(text=f"Requested by {ctx.author} | ID: {ctx.author.id}", icon_url=ctx.author.avatar.url)
                DH.LogDebug(f" Reboot Permission denied for {ctx.author} | ID: {ctx.author.id}") 
                await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(OwnerCommands(bot))