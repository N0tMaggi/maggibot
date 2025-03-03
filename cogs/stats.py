import discord
from discord.ext import commands
import json
import os
import datetime
from dotenv import load_dotenv

load_dotenv()
MESSAGE_XP_COUNT = float(os.getenv("MESSAGE_XP_COUNT", 0.2))
ATTACHMENT_XP_COUNT = float(os.getenv("ATTACHMENT_XP_COUNT", 0.5))

STATS_FILE = "data/stats.json"
XP_MULTIPLIER_FILE = "data/xpmultiplier.json"

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    with open(STATS_FILE, "r") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

def load_multiplier_config():
    if not os.path.exists(XP_MULTIPLIER_FILE):
        return {"channels": [], "multipliers": {}}
    with open(XP_MULTIPLIER_FILE, "r") as f:
        try:
            data = json.load(f)
            if "channels" not in data:
                data["channels"] = []
            if "multipliers" not in data:
                data["multipliers"] = {}
            return data
        except json.JSONDecodeError:
            return {"channels": [], "multipliers": {}}

def save_multiplier_config(config):
    with open(XP_MULTIPLIER_FILE, "w") as f:
        json.dump(config, f, indent=4)

class UserStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        stats = load_stats()
        user_id = str(message.author.id)
        guild_id = str(message.guild.id)
        
        # Create entries if they don't exist
        stats[user_id] = stats.get(user_id, {"xp": 0.0, "servers": {}})
        stats[user_id]["servers"][guild_id] = stats[user_id]["servers"].get(guild_id, {"messages": 0, "media": 0})
        
        xp_gain = MESSAGE_XP_COUNT
        stats[user_id]["servers"][guild_id]["messages"] += 1
        
        media_count = sum(1 for attachment in message.attachments 
                         if attachment.content_type and 
                         (attachment.content_type.startswith("image/") or 
                          attachment.content_type.startswith("video/")))
        
        if media_count:
            xp_gain += ATTACHMENT_XP_COUNT * media_count
            stats[user_id]["servers"][guild_id]["media"] += media_count

        # Apply multipliers
        config = load_multiplier_config()
        if str(message.channel.id) in config["channels"]:
            applicable = [config["multipliers"].get(str(r.id), 1) for r in message.author.roles]
            xp_gain *= max(applicable) if applicable else 1

        stats[user_id]["xp"] += xp_gain
        save_stats(stats)

    @commands.slash_command(name="stats", description="Display your stats or a specified user's stats.")
    async def stats(self, ctx: discord.ApplicationContext, user: discord.User = None):
        user = user or ctx.author
        stats = load_stats().get(str(user.id), {})
        
        if not stats:
            embed = discord.Embed(
                title="User Stats",
                description=f"ℹ️ No stats available for {user.mention}.",
                color=discord.Color.orange()
            )
        else:
            xp = stats.get("xp", 0.0)
            server_stats = stats.get("servers", {})
            
            embed = discord.Embed(
                title=f"🌟 Stats for {user.name}",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            
            embed.add_field(name="Total XP", value=f"🌟 **{xp:.2f} XP**", inline=False)
            
            details = []
            for guild_id, data in server_stats.items():
                guild = self.bot.get_guild(int(guild_id)) or f"Server {guild_id}"
                details.append(f"📈 **{guild}**: {data['messages']} msgs | 📎 {data['media']} media")
            
            embed.add_field(name="Server Stats", value="\n".join(details) if details else "No server stats", inline=False)
        
        embed.set_footer(
            text=f"Requested by {ctx.author.name} ⏰",
            icon_url=ctx.author.display_avatar.url
        )
        embed.timestamp = datetime.datetime.now()
        await ctx.respond(embed=embed)

    @commands.slash_command(name="leaderboard", description="Display the global XP leaderboard.")
    async def leaderboard(self, ctx: discord.ApplicationContext):
        stats = load_stats()
        
        if not stats:
            return await ctx.respond(embed=discord.Embed(
                title="🏆 Global Leaderboard",
                description="ℹ️ No stats available yet.",
                color=discord.Color.orange()
            ).set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url))
        
        leaderboard = sorted(stats.items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]
        
        embed = discord.Embed(
            title="🏆 Global XP Leaderboard 🏆",
            description="Here are the **top 10 players** with the highest XP! ✨",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url="https://ag7-dev.de/favicon/favicon.ico")
        
        for rank, (user_id, data) in enumerate(leaderboard, 1):
            member = ctx.guild.get_member(int(user_id))
            name = member.name if member else f"User {user_id}"
            avatar = member.display_avatar.url if member else "https://ag7-dev.de/favicon/favicon.ico"
            
            emoji = ["🥇", "🥈", "🥉"][rank-1] if rank <=3 else f"{rank}️⃣"
            
            embed.add_field(
                name=f"**{emoji} {name}**",
                value=f"🌟 **{data.get('xp', 0):.2f} XP**",
                inline=False
            )
        
        embed.set_footer(
            text=f"Requested by {ctx.author.name} on {ctx.guild.name}",
            icon_url=ctx.author.display_avatar.url
        )
        embed.timestamp = datetime.datetime.now()
        await ctx.respond(embed=embed)

    @commands.slash_command(name="serverleaderboard", description="Display the XP leaderboard for this server.")
    async def serverleaderboard(self, ctx: discord.ApplicationContext):
        stats = load_stats()
        guild_id = str(ctx.guild.id)
        
        leaderboard = []
        for user_id, data in stats.items():
            server = data["servers"].get(guild_id, {})
            messages = server.get("messages", 0)
            media = server.get("media", 0)
            xp = messages * MESSAGE_XP_COUNT + media * ATTACHMENT_XP_COUNT
            leaderboard.append((user_id, xp))
        
        if not leaderboard:
            return await ctx.respond(embed=discord.Embed(
                title="📊 Server Leaderboard",
                description="ℹ️ No stats available for this server.",
                color=discord.Color.orange()
            ).set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url))
        
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        top = leaderboard[:10]
        
        embed = discord.Embed(
            title=f"📊 Server Leaderboard for {ctx.guild.name}",
            description="Top contributors in this server! 🔥",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else "https://ag7-dev.de/favicon/favicon.ico")
        
        for rank, (user_id, xp) in enumerate(top, 1):
            member = ctx.guild.get_member(int(user_id))
            name = member.name if member else f"User {user_id}"
            server_data = stats.get(user_id, {}).get("servers", {}).get(guild_id, {})
            
            embed.add_field(
                name=f"**{rank}️⃣ {name}**",
                value=(
                    f"📊 **{xp:.2f} XP**\n"
                    f"💬 **{server_data.get('messages', 0)} msgs**\n"
                    f"📎 **{server_data.get('media', 0)} media**"
                ),
                inline=False
            )
        
        embed.set_footer(
            text=f"Server stats as of {ctx.guild.name}",
            icon_url=ctx.guild.icon.url if ctx.guild.icon else ""
        )
        embed.timestamp = datetime.datetime.now()
        await ctx.respond(embed=embed)

    @commands.slash_command(name="xp-setmultiplier", description="Set XP multiplier for a role (Owner only)")
    @commands.is_owner()
    async def xp_setmultiplier(self, ctx: discord.ApplicationContext, role: discord.Role, multiplier: float):
        config = load_multiplier_config()
        config["multipliers"][str(role.id)] = multiplier
        save_multiplier_config(config)
        embed = discord.Embed(
            title="XP Multiplier Set",
            description=f"Set multiplier for {role.mention} to **{multiplier}**.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name} on {ctx.guild.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.respond(embed=embed)

    @commands.slash_command(name="xp-showmultiplier", description="Show current XP multipliers (Owner only)")
    @commands.is_owner()
    async def xp_showmultiplier(self, ctx: discord.ApplicationContext):
        config = load_multiplier_config()
        multipliers = config.get("multipliers", {})
        channels = config.get("channels", [])
        mult_desc = ""
        if multipliers:
            for role_id, mult in multipliers.items():
                role = ctx.guild.get_role(int(role_id))
                role_name = role.name if role else f"Role {role_id}"
                mult_desc += f"{role_name}: **{mult}**\n"
        else:
            mult_desc = "No multipliers set."
        channels_desc = ""
        if channels:
            for channel_id in channels:
                channel = ctx.guild.get_channel(int(channel_id))
                channel_name = channel.name if channel else f"Channel {channel_id}"
                channels_desc += f"{channel_name}\n"
        else:
            channels_desc = "No channels set for multipliers."
        embed = discord.Embed(title="XP Multipliers", color=discord.Color.blue())
        embed.add_field(name="Multipliers", value=mult_desc, inline=False)
        embed.add_field(name="Channels", value=channels_desc, inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.name} on {ctx.guild.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.respond(embed=embed)

    @commands.slash_command(name="xp-removemultiplier", description="Remove XP multiplier for a role (Owner only)")
    @commands.is_owner()
    async def xp_removemultiplier(self, ctx: discord.ApplicationContext, role: discord.Role):
        config = load_multiplier_config()
        role_id_str = str(role.id)
        if role_id_str in config.get("multipliers", {}):
            del config["multipliers"][role_id_str]
            save_multiplier_config(config)
            embed = discord.Embed(
                title="XP Multiplier Removed",
                description=f"Removed multiplier for {role.mention}.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="XP Multiplier Not Found",
                description=f"No multiplier set for {role.mention}.",
                color=discord.Color.orange()
            )
        embed.set_footer(text=f"Requested by {ctx.author.name} on {ctx.guild.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.respond(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(UserStats(bot))
