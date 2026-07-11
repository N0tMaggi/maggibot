import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
from handlers.debug import LogSystem, LogError, LogDebug, LogNetwork
from handlers.config import load_stats, save_stats, load_multiplier_config, save_multiplier_config
from utils.components import build_container, build_view

load_dotenv()
MESSAGE_XP_COUNT = float(os.getenv("MESSAGE_XP_COUNT", 0.2))
ATTACHMENT_XP_COUNT = float(os.getenv("ATTACHMENT_XP_COUNT", 0.5))

STATS_FILE = "data/stats.json"
XP_MULTIPLIER_FILE = "data/xpmultiplier.json"

class XPSetup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def create_embed(self, title, description="", color_type="stats"):
        """Helper to create stats containers"""
        color_map = {
            "system": "status",
        }
        resolved_color = color_map.get(color_type, color_type)
        container = build_container(
            title=title,
            description=description,
            color=resolved_color,
            bot_user=self.bot.user,
            footer_text="Maggi Stats System",
            footer_icon="https://maggi.dev/favicon/favicon.ico"
        )
        return container



    @commands.slash_command(name="xp-setmultiplier", description="⚖️ Set role XP multiplier")
    @commands.is_owner()
    async def xp_setmultiplier(self, ctx: discord.ApplicationContext, 
                              role: discord.Role, multiplier: float):
        await ctx.defer(ephemeral=True)
        LogDebug(f"Multiplier set for {role.id} by {ctx.author.id}")
        
        try:
            config = load_multiplier_config()
            config["multipliers"][str(role.id)] = multiplier
            save_multiplier_config(config)
            
            container = self.create_embed(
                "⚖️ Multiplier Updated",
                f"Role {role.mention} now grants `{multiplier}x` XP",
                "system"
            )
            await ctx.followup.send(view=build_view(container))

        except Exception as e:
            LogError(f"Set multiplier error: {str(e)}")
            raise

    @commands.slash_command(name="xp-showmultiplier", description="📜 Show current multipliers")
    @commands.is_owner()
    async def xp_showmultiplier(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        
        try:
            config = load_multiplier_config()
            container = self.create_embed(
                "📜 Active Multipliers",
                color_type="system"
            )

            if config["multipliers"]:
                for role_id, mult in config["multipliers"].items():
                    role = ctx.guild.get_role(int(role_id))
                    container.add_item(
                        discord.ui.TextDisplay(
                            f"**⚖️ {role.name if role else 'Deleted Role'}**\n`{mult}x` Multiplier"
                        )
                    )
            else:
                container.add_item(discord.ui.TextDisplay("```diff\n- No multipliers set```"))

            await ctx.followup.send(view=build_view(container))

        except Exception as e:
            LogError(f"Show multipliers error: {str(e)}")
            raise

    @commands.slash_command(name="xp-removemultiplier", description="🗑️ Remove role multiplier")
    @commands.is_owner()
    async def xp_removemultiplier(self, ctx: discord.ApplicationContext, role: discord.Role):
        await ctx.defer(ephemeral=True)
        LogDebug(f"Multiplier removed for {role.id} by {ctx.author.id}")
        
        try:
            config = load_multiplier_config()
            role_id = str(role.id)
            
            if role_id in config["multipliers"]:
                del config["multipliers"][role_id]
                save_multiplier_config(config)
                container = self.create_embed(
                    "🗑️ Multiplier Removed",
                    f"Removed multiplier for {role.mention}",
                    "system"
                )
            else:
                container = self.create_embed(
                    "⚠️ Not Found",
                    f"No multiplier set for {role.mention}",
                    "error"
                )
            
            await ctx.followup.send(view=build_view(container))

        except Exception as e:
            LogError(f"Remove multiplier error: {str(e)}")
            raise


    @commands.slash_command(name="xp-count", description="📦 Show stats database info")
    async def xp_count(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        
        try:
            stats = load_stats()
            total = len(stats)
            active = sum(1 for u in stats.values() if u.get("xp", 0) > 0)
            
            container = self.create_embed(
                "📦 Database Statistics",
                color_type="stats"
            )
            container.add_item(discord.ui.TextDisplay(f"**Total Users**\n```yaml\n{total}```"))
            container.add_item(discord.ui.TextDisplay(f"**Active Users**\n```yaml\n{active}```"))
            await ctx.followup.send(view=build_view(container))

        except Exception as e:
            LogError(f"XP count error: {str(e)}")
            raise

def setup(bot):
    bot.add_cog(XPSetup(bot))
