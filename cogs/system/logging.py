import discord
from discord.ext import commands
from discord.commands import slash_command
from datetime import datetime
import os
import dotenv
import handlers.debug as DebugHandler

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    def log_embed(self, title, description, colour=discord.Colour.blue()):
        embed = discord.Embed(
            title=title,
            description=description,
            colour=colour,
            timestamp=datetime.utcnow()
        )
        return embed

    @commands.Cog.listener()
    async def on_application_command(self, ctx):
        log_channel = os.getenv('COMMAND_LOG_CHANNEL_ID')
        log_channel = self.bot.get_channel(int(log_channel))

        if log_channel is None:
            DebugHandler.LogDebug("Log Channel not found")
            return

        embed = discord.Embed(
            title="Command Executed",
            colour=discord.Colour.blue(),
            timestamp=datetime.utcnow()
        )

        avatar_url = ctx.author.avatar.url if ctx.author.avatar else "https://www.example.com/default_avatar.png"
        embed.set_thumbnail(url=avatar_url)

        embed.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})" if ctx.author else "Unavailable", inline=True)
        embed.add_field(name="Bot User?", value=str(ctx.author.bot) if ctx.author else "Unavailable", inline=True)

        if isinstance(ctx.author, discord.Member):
            embed.add_field(name="Top Role", value=ctx.author.top_role.mention if ctx.author.top_role else "Unavailable", inline=True)
            embed.add_field(name="Status", value=str(ctx.author.status).title() if ctx.author.status else "Unavailable", inline=True)

            activity_type = str(ctx.author.activity.type).split('.')[-1].title() if ctx.author.activity else "N/A"
            activity_name = ctx.author.activity.name if ctx.author.activity else ""
            embed.add_field(name="Activity", value=f"{activity_type} {activity_name}" if activity_name else "Unavailable", inline=True)

            embed.add_field(name="Joined Server", value=ctx.author.joined_at.strftime("%Y-%m-%d %H:%M:%S") if ctx.author.joined_at else "Unavailable", inline=True)
        else:
            embed.add_field(name="Top Role", value="Unavailable", inline=True)
            embed.add_field(name="Status", value="Unavailable", inline=True)
            embed.add_field(name="Activity", value="Unavailable", inline=True)
            embed.add_field(name="Joined Server", value="Unavailable", inline=True)

        embed.add_field(name="Command", value=ctx.command.name if ctx.command else "Unavailable", inline=True)

        if isinstance(ctx.channel, discord.DMChannel):
            embed.add_field(name="Channel", value="DM", inline=True)
        else:
            embed.add_field(name="Channel", value=f"{ctx.channel.name} ({ctx.channel.id})" if ctx.channel else "Unavailable", inline=True)

        embed.add_field(name="Guild", value=f"{ctx.guild.name} ({ctx.guild.id})" if ctx.guild else "DM", inline=True)
        embed.add_field(name="Time", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), inline=True)

        embed.add_field(name="Account Created", value=ctx.author.created_at.strftime("%Y-%m-%d %H:%M:%S") if ctx.author else "Unavailable", inline=True)

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=avatar_url)
        await log_channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Logging(bot))
