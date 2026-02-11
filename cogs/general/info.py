import discord
from discord.ext import commands
import psutil
import time
import platform
import os
from datetime import datetime
from handlers.debug import LogSystem, LogError, LogDebug
from utils.embed_helpers import create_info_embed

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

    class SupportView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.add_item(discord.ui.Button(
                label="Support Server",
                url="https://discord.maggi.dev",
                style=discord.ButtonStyle.link,
                emoji="🌐"
            ))
            self.add_item(discord.ui.Button(
                label="Documentation",
                url="https://maggi.dev/docs",
                style=discord.ButtonStyle.link,
                disabled=True,
                emoji="📚"
            ))
            self.add_item(discord.ui.Button(
                label="GitHub",
                url="https://github.com/ag7dev/maggibot",
                style=discord.ButtonStyle.link,
                emoji="💻"
            ))

    def create_embed(self, title, description, color_name="info"):
        """Create an info embed using centralized utility"""
        return create_info_embed(
            title=title,
            description=description,
            bot_user=self.bot.user
        )

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
                "```diff\n- Important: Official channels only!\n```\n"
                "Use the buttons below to access resources:",
                "info"
            )

            await ctx.followup.send(
                embeds=[main_embed, support_embed],
                view=self.SupportView()
            )

        except Exception as e:
            LogError(f"Info command failed: {str(e)}")
            raise

    @commands.slash_command(name="status", description="📊 Get detailed system status metrics")
    async def status(self, ctx: discord.ApplicationContext):
        """Display detailed system status information"""
        await ctx.defer()
        LogSystem(f"Status check by {ctx.author.id}")

        class RefreshView(discord.ui.View):
            def __init__(self, cog):
                super().__init__(timeout=120)
                self.cog = cog

            @discord.ui.button(label="Refresh", style=discord.ButtonStyle.grey, emoji="🔄")
            async def refresh_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                try:
                    await interaction.response.defer()
                    await self.cog.update_status_embed(interaction)
                except Exception as e:
                    LogError(f"Refresh failed: {str(e)}")
                    await interaction.followup.send("❌ Could not refresh status", ephemeral=True)

            async def on_timeout(self):
                try:
                    self.clear_items()
                    message = await self.message.edit(view=self)
                    await message.edit(view=None)
                except discord.NotFound:
                    LogDebug("Message already deleted in status refresh")
                except Exception as e:
                    LogError(f"Failed to clear status view: {str(e)}")

        try:
            view = RefreshView(self)
            view.message = await ctx.followup.send(
                embed=await self.create_status_embed(),
                view=view
            )

        except Exception as e:
            LogError(f"Status command failed: {str(e)}")
            raise

    async def create_status_embed(self):
        """Helper method to create status embed"""
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
                  f"Pycord: {discord.__version__}\n"
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

        return embed

    async def update_status_embed(self, interaction: discord.Interaction):
        """Update the status embed for refresh"""
        try:
            embed = await self.create_status_embed()
            await interaction.edit_original_response(embed=embed)
        except Exception as e:
            LogError(f"Update status failed: {str(e)}")
            await interaction.followup.send("❌ Could not update status", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(InfoSystem(bot))