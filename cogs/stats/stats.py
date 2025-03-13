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

class UserStats(commands.Cog):
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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        try:
            stats = load_stats()
            user_id = str(message.author.id)
            guild_id = str(message.guild.id)
            
            if user_id not in stats:
                stats[user_id] = {"xp": 0.0, "servers": {}}
            
            if guild_id not in stats[user_id]["servers"]:
                stats[user_id]["servers"][guild_id] = {"messages": 0, "media": 0}
            
            xp_gain = MESSAGE_XP_COUNT
            stats[user_id]["servers"][guild_id]["messages"] += 1
            
            media_count = sum(1 for att in message.attachments 
                            if att.content_type and 
                            att.content_type.startswith(("image/", "video/")))
            
            if media_count:
                xp_gain += ATTACHMENT_XP_COUNT * media_count
                stats[user_id]["servers"][guild_id]["media"] += media_count

            config = load_multiplier_config()
            if str(message.channel.id) in config["channels"]:
                multipliers = [config["multipliers"].get(str(r.id), 1) 
                              for r in message.author.roles]
                xp_gain *= max(multipliers) if multipliers else 1

            stats[user_id]["xp"] += xp_gain
            save_stats(stats)

        except Exception as e:
            LogError(f"Message handling error: {str(e)}")

    @commands.slash_command(name="stats", description="📊 Display user statistics")
    async def stats(self, ctx: discord.ApplicationContext, user: discord.User = None):
        await ctx.defer()
        LogDebug(f"Stats command by {ctx.author.id}")
        
        try:
            user = user or ctx.author
            stats = load_stats().get(str(user.id), {})
            embed = self.create_embed(
                f"📈 {user.display_name}'s Statistics",
                color_type="stats"
            )
            embed.set_thumbnail(url=user.display_avatar.url)

            if stats:
                xp = stats.get("xp", 0.0)
                server_stats = stats.get("servers", {})
                
                embed.add_field(
                    name="🌟 Total XP",
                    value=f"```yaml\n{xp:.2f} XP```",
                    inline=False
                )
                
                server_info = []
                for guild_id, data in server_stats.items():
                    guild = self.bot.get_guild(int(guild_id)) or f"Server {guild_id}"
                    server_info.append(
                        f"**{guild}**\n"
                        f"📨 Messages: {data['messages']} "
                        f"(+{data['messages']*MESSAGE_XP_COUNT:.2f} XP)\n"
                        f"📎 Media: {data['media']} "
                        f"(+{data['media']*ATTACHMENT_XP_COUNT:.2f} XP)"
                    )
                
                embed.add_field(
                    name="🌐 Server Breakdown",
                    value="\n".join(server_info) or "No data",
                    inline=False
                )
            else:
                embed.description = "```diff\n- No statistics available```"

            await ctx.followup.send(embed=embed)

        except Exception as e:
            LogError(f"Stats error: {str(e)}")
            raise

    @commands.slash_command(name="leaderboard", description="🏆 Global XP leaderboard")
    async def leaderboard(self, ctx: discord.ApplicationContext):
        """Display global leaderboard with advanced metrics"""
        await ctx.defer()
        LogDebug(f"Leaderboard viewed by {ctx.author.id}")

        try:
            stats = load_stats()
            
            embed = self.create_embed(
                "🌍 Global XP Leaderboard",
                "```diff\n+ Top Performers Across All Servers\n+ Updated: " + datetime.datetime.now().strftime("%Y-%m-%d") + "```",
                "leaderboard"
            )
            embed.set_thumbnail(url="")

            if stats:
                leaderboard = sorted(stats.items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]
                
                for rank, (user_id, data) in enumerate(leaderboard, 1):
                    member = ctx.guild.get_member(int(user_id))
                    xp = data.get("xp", 0)
                    
                    embed.add_field(
                        name=f"{self.get_rank_emoji(rank)} {getattr(member, 'name', f'User {user_id}')}",
                        value=(
                            f"```yaml\n"
                            f"XP: {xp:.2f}\n"
                            f"Messages: {sum(s['messages'] for s in data['servers'].values())}\n"
                            f"Media: {sum(s['media'] for s in data['servers'].values())}```"
                        ),
                        inline=False
                    )
            else:
                embed.description = "```diff\n- No data available```"

            await ctx.followup.send(embed=embed)

        except Exception as e:
            LogError(f"Leaderboard error: {str(e)}")
            raise

    def get_rank_emoji(self, rank):
        return ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][rank-1]

    def get_rank_emoji(self, rank):
        return ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][rank-1]

    @commands.slash_command(name="serverleaderboard", description="📊 Server-specific ranking")
    async def serverleaderboard(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        LogDebug(f"Server leaderboard in {ctx.guild.id}")
        
        try:
            stats = load_stats()
            guild_id = str(ctx.guild.id)
            leaderboard = []

            for user_id, data in stats.items():
                server_data = data.get("servers", {}).get(guild_id, {})
                if server_data:
                    xp = (server_data["messages"] +
                         server_data["media"])
                    leaderboard.append((user_id, xp, server_data))

            if not leaderboard:
                embed = self.create_embed(
                    "📊 Server Leaderboard",
                    "```diff\n- No data available```",
                    "stats"
                )
                return await ctx.followup.send(embed=embed)

            leaderboard.sort(key=lambda x: x[1], reverse=True)
            top = leaderboard[:10]

            embed = self.create_embed(
                f"📊 {ctx.guild.name} Leaderboard",
                color_type="leaderboard"
            )
            embed.set_thumbnail(url=ctx.guild.icon.url or discord.Embed.Empty)

            for rank, (user_id, xp, data) in enumerate(top, 1):
                member = ctx.guild.get_member(int(user_id))
                embed.add_field(
                    name=f"{self.get_rank_emoji(rank)} {member.name if member else f'User {user_id}'}",
                    value=(
                        f"```yaml\n"
                        f"XP: {xp:.2f}\n"
                        f"Messages: {data['messages']}\n"
                        f"Media: {data['media']}```"
                    ),
                    inline=False
                )

            await ctx.followup.send(embed=embed)

        except Exception as e:
            LogError(f"Server leaderboard error: {str(e)}")
            raise

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

    @commands.slash_command(name="xp-count", description="📦 Show stats database info")
    async def xp_count(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        
        try:
            stats = load_stats()
            total = len(stats)
            active = sum(1 for u in stats.values() if u.get("xp", 0) > 0)
            
            embed = self.create_embed(
                "📦 Database Statistics",
                color_type="stats"
            )
            embed.add_field(
                name="Total Users",
                value=f"```yaml\n{total}```",
                inline=True
            )
            embed.add_field(
                name="Active Users",
                value=f"```yaml\n{active}```",
                inline=True
            )
            await ctx.followup.send(embed=embed)

        except Exception as e:
            LogError(f"XP count error: {str(e)}")
            raise

def setup(bot: commands.Bot):
    bot.add_cog(UserStats(bot))