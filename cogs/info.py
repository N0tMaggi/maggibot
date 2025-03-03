import discord
from discord.ext import commands
from datetime import datetime
import psutil
import time
import platform
import os

def get_host_uptime():
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    return uptime

def get_bot_uptime():
    uptime = datetime.now() - datetime.fromtimestamp(time.time() - psutil.Process().create_time())
    return uptime
class InfoSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.owner_id = os.getenv("OWNER_ID")
        self.bot.version = os.getenv("BOT_VERSION")

    @commands.slash_command(
        name="info", 
        description="Get information about the bot"
    )
    async def info(self, ctx: discord.ApplicationContext):
        main_embed = discord.Embed(
            title="🤖 Bot Information",
            description="This bot was developed by AG7. 🚀",
            color=discord.Color.blue()
        )
        main_embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        main_embed.set_image(url="https://ag7-dev.de/favicon/favicon.ico")  
        main_embed.add_field(name="🤖 Bot Name", value=self.bot.user.name, inline=True)
        main_embed.add_field(name="📝 Bot ID", value=self.bot.user.id, inline=True)
        main_embed.add_field(name="👑 Bot Owner", value=f"<@{self.owner_id}>", inline=True)
        main_embed.set_footer(text="AG7 Dev Team", icon_url="https://ag7-dev.de/favicon/favicon.ico")  
        main_embed.timestamp = discord.utils.utcnow()
    
        support_embed = discord.Embed(
            title="🤝 Support Server",
            description="Join the support server for the bot here: [Support Server](https://discord.ag7-dev.de)\nIf you need help with the bot, you can ask in the support server or DM the bot owner. 🤔",
            color=discord.Color.green()
        )
        support_embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        support_embed.set_image(url="https://ag7-dev.de/favicon/favicon.ico")  
        support_embed.add_field(name="👑 Bot Owner", value=f"<@{self.owner_id}>", inline=True)
        support_embed.add_field(name="📚 Documentation", value="[Documentation](https://ag7-dev.de/docs)", inline=True)
        support_embed.set_footer(text="AG7 Dev Team", icon_url="https://ag7-dev.de/favicon/favicon.ico")  
        support_embed.timestamp = discord.utils.utcnow()
    
        await ctx.respond(embeds=[main_embed, support_embed])


    @commands.slash_command(
        name="status", 
        description="Gest the bot's status. eg. uptime, latency, etc."
    )
    async def status(self, ctx: discord.ApplicationContext):
        try:
            embed = discord.Embed(
                title="Bot Status",
                description="Here is the current status of the bot.",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_image(url="https://ag7-dev.de/favicon/favicon.ico")

            embed.add_field(name="🖥️ Host Uptime", value=get_host_uptime(), inline=True)
            embed.add_field(name="⏱️ Bot Uptime", value=get_bot_uptime(), inline=True)
            embed.add_field(name="🌐 Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
            embed.add_field(name="🏰 Guilds", value=len(self.bot.guilds), inline=True)
            embed.add_field(name="👥 Users", value=len(self.bot.users), inline=True)
            embed.add_field(name="🛠️ Commands", value=len(self.bot.commands), inline=True)
            embed.add_field(name="⚙️ Cogs", value=len(self.bot.cogs), inline=True)
            embed.add_field(name="💻 CPU Usage", value=f"{psutil.cpu_percent()}%", inline=True)
            embed.add_field(name="🧠 Memory Usage", value=f"{psutil.virtual_memory().percent}%", inline=True)
            embed.add_field(name="🐍 Python Version", value=platform.python_version(), inline=True)
            embed.add_field(name="💬 Discord.py Version", value=discord.__version__, inline=True)
            embed.add_field(name="🔢 Bot Version", value=self.bot.version, inline=True)
            embed.add_field(name="👑 Bot Owner", value=f"<@{self.owner_id}>", inline=True)
            embed.add_field(name="💬 Support Server", value="[Support Server](https://discord.ag7-dev.de)", inline=True)
            embed.set_footer(text="AG7 Dev Team", icon_url="https://ag7-dev.de/favicon/favicon.ico")
            embed.timestamp = discord.utils.utcnow()

            await ctx.respond(embed=embed)
        
        except Exception as e:
            raise Exception("An error occurred while fetching the bot's status." + str(e)) 


    @commands.slash_command(name="error-normal", description="Trigger An Error")
    async def error_normal(self, ctx: discord.ApplicationContext):
        if ctx.author.id == int(self.owner_id):
            raise Exception("This is a test error!")
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            embed.set_footer(text="AG7 Dev Team", icon_url="https://ag7-dev.de/favicon/favicon.ico")
            embed.timestamp = discord.utils.utcnow()
            await ctx.respond(embed=embed)

    @commands.slash_command(name="error-fatal", description="Trigger A Fatal Error")
    async def error_fatal(self, ctx: discord.ApplicationContext):
        if ctx.author.id == int(self.owner_id):  
            raise Exception("This is a Fatal error triggered for testing purposes!")  
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            embed.set_footer(text="AG7 Dev Team", icon_url="https://ag7-dev.de/favicon/favicon.ico")
            embed.timestamp = discord.utils.utcnow()
            await ctx.respond(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(InfoSystem(bot))