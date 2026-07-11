import discord
from discord.ext import commands
import psutil
import time
import platform
import os
from datetime import datetime
from handlers.debug import LogSystem, LogError, LogDebug
from utils.components import build_info_container, build_view

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

    class SupportView(discord.ui.ActionRow):
        def __init__(self):
            super().__init__()
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

    def create_embed(self, title, description, color_name="info", fields=None, **kwargs):
        """Create an info container using centralized utility"""
        return build_info_container(
            title=title,
            description=description,
            bot_user=self.bot.user,
            fields=fields,
            **kwargs,
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
                "info",
                fields=[
                    (
                        "🔍 Core Details",
                        f"```yaml\n"
                        f"Name: {self.bot.user.name}\n"
                        f"ID: {self.bot.user.id}\n"
                        f"Version: {self.bot.version}```",
                        False,
                    ),
                    (
                        "👑 Ownership",
                        f"```{self.bot.get_user(int(self.owner_id)).name}```\n<@{self.owner_id}>",
                        True,
                    ),
                    (
                        "📆 Creation Date",
                        f"```{self.bot.user.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}```",
                        True,
                    ),
                ],
            )

            support_embed = self.create_embed(
                "🛠️ Support & Resources",
                "```diff\n- Important: Official channels only!\n```\n"
                "Use the buttons below to access resources:",
                "info"
            )

            await ctx.followup.send(
                view=build_view(main_embed, support_embed, self.SupportView(), timeout=None)
            )

        except Exception as e:
            LogError(f"Info command failed: {str(e)}")
            raise

    @commands.slash_command(name="status", description="📊 Get detailed system status metrics")
    async def status(self, ctx: discord.ApplicationContext):
        """Display detailed system status information"""
        await ctx.defer()
        LogSystem(f"Status check by {ctx.author.id}")

        class RefreshView(discord.ui.DesignerView):
            def __init__(self, cog, status_container):
                super().__init__(timeout=120)
                self.cog = cog
                self.status_container = status_container
                self.add_item(self.status_container)

                self.refresh_row = discord.ui.ActionRow()
                self.refresh_button = discord.ui.Button(
                    label="Refresh",
                    style=discord.ButtonStyle.grey,
                    emoji="🔄",
                )
                self.refresh_button.callback = self.refresh_button_callback
                self.refresh_row.add_item(self.refresh_button)
                self.add_item(self.refresh_row)

            async def refresh_button_callback(self, interaction: discord.Interaction):
                try:
                    await interaction.response.defer()
                    await self.cog.update_status_embed(interaction, self)
                except Exception as e:
                    LogError(f"Refresh failed: {str(e)}")
                    await interaction.followup.send("❌ Could not refresh status", ephemeral=True)

            def update_status_container(self, new_container: discord.ui.Container):
                try:
                    self.remove_item(self.status_container)
                except Exception:
                    pass
                self.status_container = new_container
                self.add_item(self.status_container)

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
            status_container = await self.create_status_embed()
            view = RefreshView(self, status_container)
            view.message = await ctx.followup.send(
                view=view
            )

        except Exception as e:
            LogError(f"Status command failed: {str(e)}")
            raise

    async def create_status_embed(self):
        """Helper method to create status container"""
        process = psutil.Process()
        memory_info = process.memory_full_info()

        return self.create_embed(
            "📈 Real-Time System Telemetry",
            "```diff\n+ Live System Metrics\n+ Updated: " + datetime.utcnow().strftime("%H:%M:%S UTC") + "```",
            "status",
            fields=[
                (
                    "🤖 Bot Metrics",
                    f"```yaml\n"
                    f"Uptime: {get_bot_uptime()}\n"
                    f"Latency: {round(self.bot.latency * 1000)}ms\n"
                    f"Guilds: {len(self.bot.guilds)}\n"
                    f"Users: {len(self.bot.users)}```",
                    True,
                ),
                (
                    "🖥️ System Health",
                    f"```yaml\n"
                    f"Host Uptime: {get_host_uptime()}\n"
                    f"CPU Usage: {psutil.cpu_percent()}%\n"
                    f"Memory: {psutil.virtual_memory().percent}%\n"
                    f"Disk: {psutil.disk_usage('/').percent}%```",
                    True,
                ),
                (
                    "⚙️ Technical Specifications",
                    f"```yaml\n"
                    f"Python: {platform.python_version()}\n"
                    f"Pycord: {discord.__version__}\n"
                    f"OS: {platform.system()} {platform.release()}```",
                    False,
                ),
                (
                    "🔍 Process Details",
                    f"```yaml\n"
                    f"Threads: {process.num_threads()}\n"
                    f"Handles: {process.num_handles()}\n"
                    f"Memory: {memory_info.rss / 1024 ** 2:.2f} MB```",
                    True,
                ),
            ],
        )

    async def update_status_embed(self, interaction: discord.Interaction, view: discord.ui.DesignerView):
        """Update the status container for refresh"""
        try:
            container = await self.create_status_embed()
            view.update_status_container(container)
            await interaction.edit_original_response(view=view)
        except Exception as e:
            LogError(f"Update status failed: {str(e)}")
            await interaction.followup.send("❌ Could not update status", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(InfoSystem(bot))
