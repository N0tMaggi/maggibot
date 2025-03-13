import discord
from discord.ext import commands
import json
import os
import datetime
from dotenv import load_dotenv
from handlers.debug import LogSystem, LogError, LogDebug, LogNetwork

load_dotenv()
MESSAGE_XP_COUNT = float(os.getenv("MESSAGE_XP_COUNT", 0.2))
ATTACHMENT_XP_COUNT = float(os.getenv("ATTACHMENT_XP_COUNT", 0.5))

STATS_FILE = "data/stats.json"
XP_MULTIPLIER_FILE = "data/xpmultiplier.json"

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

def load_multiplier_config():
    if not os.path.exists(XP_MULTIPLIER_FILE):
        return {"channels": [], "multipliers": {}}
    try:
        with open(XP_MULTIPLIER_FILE, "r") as f:
            data = json.load(f)
            return {
                "channels": data.get("channels", []),
                "multipliers": data.get("multipliers", {})
            }
    except (json.JSONDecodeError, FileNotFoundError):
        return {"channels": [], "multipliers": {}}

def save_multiplier_config(config):
    with open(XP_MULTIPLIER_FILE, "w") as f:
        json.dump(config, f, indent=4)

class XPSetup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_colors = {
            "stats": 0x3498DB,
            "leaderboard": 0xF1C40F,
            "system": 0x2ECC71,
            "error": 0xE74C3C,
            "mod": 0x992D22
        }

    def create_embed(self, title, description="", color_type="stats"):
        embed = discord.Embed(
            title=title,
            description=description,
            color=self.embed_colors.get(color_type, 0x3498DB),
            timestamp=datetime.datetime.now()
        )
        embed.set_footer(
            text="AG7 Stats System",
            icon_url="https://ag7-dev.de/favicon/favicon.ico"
        )
        return embed



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
            
            embed = self.create_embed(
                "⚖️ Multiplier Updated",
                f"Role {role.mention} now grants `{multiplier}x` XP",
                "system"
            )
            await ctx.followup.send(embed=embed)

        except Exception as e:
            LogError(f"Set multiplier error: {str(e)}")
            raise

    @commands.slash_command(name="xp-showmultiplier", description="📜 Show current multipliers")
    @commands.is_owner()
    async def xp_showmultiplier(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        
        try:
            config = load_multiplier_config()
            embed = self.create_embed(
                "📜 Active Multipliers",
                color_type="system"
            )

            if config["multipliers"]:
                for role_id, mult in config["multipliers"].items():
                    role = ctx.guild.get_role(int(role_id))
                    embed.add_field(
                        name=f"⚖️ {role.name if role else 'Deleted Role'}",
                        value=f"`{mult}x` Multiplier",
                        inline=True
                    )
            else:
                embed.description = "```diff\n- No multipliers set```"

            await ctx.followup.send(embed=embed)

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
                embed = self.create_embed(
                    "🗑️ Multiplier Removed",
                    f"Removed multiplier for {role.mention}",
                    "system"
                )
            else:
                embed = self.create_embed(
                    "⚠️ Not Found",
                    f"No multiplier set for {role.mention}",
                    "error"
                )
            
            await ctx.followup.send(embed=embed)

        except Exception as e:
            LogError(f"Remove multiplier error: {str(e)}")
            raise


def setup(bot):
    bot.add_cog(XPSetup(bot))