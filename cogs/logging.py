import discord
from discord.ext import commands
from discord.commands import slash_command
from datetime import datetime
import os
import dotenv


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

        embed = discord.Embed(
            title="Command Executed",
            colour=discord.Colour.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})", inline=True)
        embed.add_field(name="Bot User?", value=ctx.author.bot, inline=True)
        embed.add_field(name="Top Role", value=ctx.author.top_role.mention, inline=True)
        embed.add_field(name="Command", value=ctx.command.name, inline=True)
        embed.add_field(name="Channel", value=f"{ctx.channel.name} ({ctx.channel.id})", inline=True)
        embed.add_field(name="Guild", value=f"{ctx.guild.name if ctx.guild else 'DM'} ({ctx.guild.id if ctx.guild else 'DM'})", inline=True)
        embed.add_field(name="Time", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="Status", value=str(ctx.author.status).title(), inline=True)
        embed.add_field(name="Activity", value=f"{str(ctx.author.activity.type).split('.')[-1].title() if ctx.author.activity else 'N/A'} {ctx.author.activity.name if ctx.author.activity else ''}", inline=True)
        embed.add_field(name="Account Created", value=ctx.author.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="Joined Server", value=ctx.author.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)

        await log_channel.send(embed=embed)



def setup(bot):
    bot.add_cog(Logging(bot))
