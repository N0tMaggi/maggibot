import discord
from discord.ext import commands
from datetime import datetime
import psutil
import time
import platform
import os
from handlers.debug import LogSystem, LogError, LogDebug

def get_host_uptime():
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    return str(uptime).split('.')[0]  

def get_bot_uptime():
    uptime = datetime.now() - datetime.fromtimestamp(time.time() - psutil.Process().create_time())
    return str(uptime).split('.')[0]

class InfoSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.owner_id = os.getenv("OWNER_ID")
        self.bot.version = os.getenv("BOT_VERSION")
        self.embed_colors = {
            "info": 0x3498db,
            "status": 0x2ecc71,
            "error": 0xe74c3c
        }

    def create_embed(self, title, description, color_name="info"):
        embed = discord.Embed(
            title=title,
            description=description,
            color=self.embed_colors.get(color_name, 0x3498db),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(
            text="AG7 Dev System",
            icon_url="https://ag7-dev.de/favicon/favicon.ico"
        )
        return embed

    @commands.slash_command(name="info", description="📚 Get detailed bot information")
    async def info(self, ctx: discord.ApplicationContext):
        """Display bot information and support details"""
        await ctx.defer()
        LogSystem(f"Info command used by {ctx.author.id}")

        try:
            main_embed = self.create_embed(
                "🤖 Advanced Bot Information",
                "```diff\n+ Operational\n+ System Status: Nominal```",
                "info"
            )
            main_embed.add_field(
                name="🔍 Core Details",
                value=f"```yaml\n"
                      f"Name: {self.bot.user.name}\n"
                      f"ID: {self.bot.user.id}\n"
                      f"Version: {self.bot.version}```",
                inline=False
            )
            main_embed.add_field(
                name="👑 Ownership",
                value=f"```{self.bot.get_user(int(self.owner_id)).name}```\n<@{self.owner_id}>",
                inline=True
            )
            main_embed.add_field(
                name="📆 Creation Date",
                value=f"```{self.bot.user.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}```",
                inline=True
            )

            support_embed = self.create_embed(
                "🛠️ Support & Resources",
                "```diff\n- Important: Official channels only!\n```",
                "info"
            )
            support_embed.add_field(
                name="🌐 Support Server",
                value="[Join Now](https://discord.ag7-dev.de)",
                inline=True
            )
            support_embed.add_field(
                name="📚 Documentation (SOON)",
                value="[Read Docs](https://ag7-dev.de/docs)",
                inline=True
            )
            support_embed.add_field(
                name="💻 GitHub Repository",
                value="[View Source](https://github.com/ag7dev/maggibot)",
                inline=True
            )
            support_embed.set_image(url="")

            await ctx.followup.send(embeds=[main_embed, support_embed])

        except Exception as e:
            LogError(f"Info command failed: {str(e)}")
            raise

    @commands.slash_command(name="status", description="📊 Get detailed system status metrics")
    async def status(self, ctx: discord.ApplicationContext):
        """Display detailed system status information"""
        await ctx.defer()
        LogSystem(f"Status check by {ctx.author.id}")

        try:
            process = psutil.Process()
            memory_info = process.memory_full_info()

            embed = self.create_embed(
                "📈 Real-Time System Telemetry",
                "```diff\n+ Live System Metrics\n+ Updated: " + datetime.utcnow().strftime("%H:%M:%S UTC") + "```",
                "status"
            )
            
            embed.add_field(
                name="🤖 Bot Metrics",
                value=f"```yaml\n"
                      f"Uptime: {get_bot_uptime()}\n"
                      f"Latency: {round(self.bot.latency * 1000)}ms\n"
                      f"Guilds: {len(self.bot.guilds)}\n"
                      f"Users: {len(self.bot.users)}```",
                inline=True
            )

            embed.add_field(
                name="🖥️ System Health",
                value=f"```yaml\n"
                      f"Host Uptime: {get_host_uptime()}\n"
                      f"CPU Usage: {psutil.cpu_percent()}%\n"
                      f"Memory: {psutil.virtual_memory().percent}%\n"
                      f"Disk: {psutil.disk_usage('/').percent}%```",
                inline=True
            )

            embed.add_field(
                name="⚙️ Technical Specifications",
                value=f"```yaml\n"
                      f"Python: {platform.python_version()}\n"
                      f"discord.py: {discord.__version__}\n"
                      f"OS: {platform.system()} {platform.release()}```",
                inline=False
            )

            embed.add_field(
                name="🔍 Process Details",
                value=f"```yaml\n"
                      f"Threads: {process.num_threads()}\n"
                      f"Handles: {process.num_handles()}\n"
                      f"Memory: {memory_info.rss / 1024 ** 2:.2f} MB```",
                inline=True
            )

            embed.set_image(url="")
            await ctx.followup.send(embed=embed)

        except Exception as e:
            LogError(f"Status command failed: {str(e)}")
            raise

    @commands.slash_command(name="error-normal", description="⚡ Trigger a controlled test error")
    async def error_normal(self, ctx: discord.ApplicationContext):
        """Generate a test error (Owner only)"""
        await ctx.defer(ephemeral=True)
        
        if ctx.author.id != int(self.owner_id):
            embed = self.create_embed(
                "⛔ Unauthorized Access",
                "```diff\n- Critical Security Alert: Unauthorized error trigger attempt!```",
                "error"
            )
            await ctx.followup.send(embed=embed)
            LogError(f"Unauthorized error trigger by {ctx.author.id}")
            return

        try:
            LogError("⚠️ Test error triggered (normal)")
            raise Exception("🚨 Controlled test error triggered successfully!")
            
        except Exception as e:
            embed = self.create_embed(
                "⚠️ Test Error Generated",
                f"```diff\n- {str(e)}\n+ Error handling working correctly!```",
                "error"
            )
            await ctx.followup.send(embed=embed)
            raise

    @commands.slash_command(name="error-fatal", description="💥 Trigger a critical test error")
    async def error_fatal(self, ctx: discord.ApplicationContext):
        """Generate a fatal test error (Owner only)"""
        await ctx.defer(ephemeral=True)

        if ctx.author.id != int(self.owner_id):
            embed = self.create_embed(
                "⛔ Security Violation",
                "```diff\n- ALERT: Unauthorized critical error trigger attempt!```",
                "error"
            )
            await ctx.followup.send(embed=embed)
            LogError(f"Unauthorized fatal error attempt by {ctx.author.id}")
            return

        try:
            LogError("💥 Fatal test error triggered")
            raise Exception("🔥 CRITICAL TEST ERROR - SYSTEM SIMULATION")
            
        except Exception as e:
            embed = self.create_embed(
                "💥 Fatal Error Simulation",
                f"```diff\n- {str(e)}\n+ Error containment successful!```",
                "error"
            )
            await ctx.followup.send(embed=embed)
            raise

def setup(bot: commands.Bot):
    bot.add_cog(InfoSystem(bot))