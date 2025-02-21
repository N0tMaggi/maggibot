import discord
from discord.ext import commands
import json
import os
import datetime

STATS_FILE = "data/stats.json"

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

class UserStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Only count messages in guild channels (not DMs)
        if not message.guild:
            return
        # Ignore bot messages
        if message.author.bot:
            return
        stats = load_stats()
        user_id = str(message.author.id)
        guild_id = str(message.guild.id)
        # Create entry for user if not existing
        if user_id not in stats:
            stats[user_id] = {"xp": 0.0, "servers": {}}
        if guild_id not in stats[user_id]["servers"]:
            stats[user_id]["servers"][guild_id] = {"messages": 0, "media": 0}
        # Every message gives 0.2 XP
        xp_gain = 0.2
        stats[user_id]["servers"][guild_id]["messages"] += 1
        # Count attachments that are images/videos (e.g. content_type starts with "image/" or "video/")
        media_count = 0
        for attachment in message.attachments:
            if attachment.content_type and (attachment.content_type.startswith("image/") or attachment.content_type.startswith("video/")):
                media_count += 1
        if media_count > 0:
            xp_gain += 0.5 * media_count
            stats[user_id]["servers"][guild_id]["media"] += media_count
        stats[user_id]["xp"] += xp_gain
        save_stats(stats)

    @commands.slash_command(name="stats", description="Display your stats or a specified user's stats.")
    async def stats(self, ctx: discord.ApplicationContext, user: discord.User = None):
        # If no user specified, default to command author
        if user is None:
            user = ctx.author
        stats = load_stats()
        user_id = str(user.id)
        if user_id not in stats:
            embed = discord.Embed(
                title="User Stats",
                description=f"ℹ️ No stats available for {user.mention}.",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author.name} on {ctx.guild.name}", icon_url=ctx.author.display_avatar.url)
            await ctx.respond(embed=embed)
            return
        user_stats = stats[user_id]
        xp = user_stats.get("xp", 0.0)
        embed = discord.Embed(
            title=f"Stats for {user.name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Total XP", value=f"🌟 {xp:.2f} XP", inline=False)
        server_stats = user_stats.get("servers", {})
        details = ""
        for guild_id, data in server_stats.items():
            # Try to get the server name from cache
            guild = self.bot.get_guild(int(guild_id))
            guild_name = guild.name if guild else f"Server {guild_id}"
            details += f"📈 **{guild_name}**: {data['messages']} messages, {data['media']} media\n"
        if details == "":
            details = "No server stats available."
        embed.add_field(name="Server Stats", value=details, inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.name} on {ctx.guild.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.respond(embed=embed)

    @commands.slash_command(name="leaderboard", description="Display the global XP leaderboard.")
    async def leaderboard(self, ctx: discord.ApplicationContext):
        stats = load_stats()
        if not stats:
            embed = discord.Embed(
                title="Leaderboard",
                description="ℹ️ No stats available yet.",
                color=discord.Color.orange()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name} on {ctx.guild.name}", icon_url=ctx.author.display_avatar.url)
            await ctx.respond(embed=embed)
            return
        # Build a list of tuples (user_id, xp) and sort descending by XP
        leaderboard_list = [(user_id, data.get("xp", 0)) for user_id, data in stats.items()]
        leaderboard_list.sort(key=lambda x: x[1], reverse=True)
        top = leaderboard_list[:10]
        description = ""
        rank = 1
        for user_id, xp in top:
            # Try to get the member from the current guild; if not found, use the ID
            member = ctx.guild.get_member(int(user_id))
            name = member.name if member else f"User {user_id}"
            avatar_url = member.display_avatar.url if member else "https://ag7-dev.de/favicon/favicon.ico"  # Replace with a default avatar URL
            description += f"**{rank}. {name}**  {xp:.2f} XP\n"
            rank += 1
        embed = discord.Embed(
            title="Global XP Leaderboard",
            description=description,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name} on {ctx.guild.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.respond(embed=embed)

    @commands.slash_command(name="serverleaderboard", description="Display the XP leaderboard for this server.")
    async def serverleaderboard(self, ctx: discord.ApplicationContext):
        stats = load_stats()
        server_id = str(ctx.guild.id)
        leaderboard_list = []
        # Calculate server-specific XP for each user (messages * 0.2 + media * 0.5)
        for user_id, data in stats.items():
            server_data = data.get("servers", {}).get(server_id)
            if server_data:
                messages = server_data.get("messages", 0)
                media = server_data.get("media", 0)
                server_xp = messages * 0.2 + media * 0.5
                leaderboard_list.append((user_id, server_xp))
        
        if not leaderboard_list:
            embed = discord.Embed(
                title="Server Leaderboard",
                description="ℹ️ No stats available for this server.",
                color=discord.Color.orange()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name} on {ctx.guild.name}", icon_url=ctx.author.display_avatar.url)
            await ctx.respond(embed=embed)
            return
        leaderboard_list.sort(key=lambda x: x[1], reverse=True)
        top = leaderboard_list[:10]
        description = ""
        rank = 1
        for user_id, xp in top:
            member = ctx.guild.get_member(int(user_id))
            name = member.name if member else f"User {user_id}"
            avatar_url = member.display_avatar.url if member else "https://ag7-dev.de/favicon/favicon.ico"  # Replace with a default avatar URL
            description += f"**{rank}. {name}**  {xp:.2f} XP\n"
            rank += 1
        embed = discord.Embed(
            title=f"Server Leaderboard for {ctx.guild.name}",
            description=description,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name} on {ctx.guild.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.respond(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(UserStats(bot))