from discord.ext import commands
import discord
import datetime
from extensions.statsextension import create_embed
from handlers.debug import LogDebug, LogError
from handlers.config import load_stats, save_stats, MESSAGE_XP_COUNT, ATTACHMENT_XP_COUNT, load_multiplier_config

class Leaderboards(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.slash_command(name="stats", description="📊 Display user statistics")
    async def stats(self, ctx: discord.ApplicationContext, user: discord.User = None):
        await ctx.defer()
        LogDebug(f"Stats command by {ctx.author.id}")
        try:
            user = user or ctx.author
            stats = load_stats().get(str(user.id), {})
            embed = create_embed(f"📈 {user.display_name}'s Statistics", color_type="stats")
            embed.set_thumbnail(url=user.display_avatar.url)

            if stats:
                xp = stats.get("xp", 0.0)
                server_stats = stats.get("servers", {})
                
                embed.add_field(name="🌟 Total XP", value=f"```yaml\n{xp:.2f} XP```", inline=False)

                server_info = []
                for guild_id, data in server_stats.items():
                    guild = self.bot.get_guild(int(guild_id)) or f"Server {guild_id}"
                    server_info.append(f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- \n**{guild}**\n📨 Messages: {data['messages']} \n📎 Media: {data['media']} \n")

                embed.add_field(name="🌐 Server Breakdown \n", value="\n".join(server_info) or "No data", inline=False)
            else:
                embed.description = "```diff\n- No statistics available```"
            
            await ctx.followup.send(embed=embed)
        except Exception as e:
            LogError(f"Stats error: {str(e)}")
            raise

    @commands.slash_command(name="leaderboard", description="🏆 Global XP leaderboard")
    async def leaderboard(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        LogDebug(f"Leaderboard viewed by {ctx.author.id}")
        try:
            stats = load_stats()
            embed = create_embed(
                "🌍 Global XP Leaderboard",
                "```diff\n+ Top Performers Across All Servers\n+ Updated: " + datetime.datetime.now().strftime("%Y-%m-%d") + "```",
                "leaderboard"
            )

            if stats:
                leaderboard = sorted(stats.items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]

                for rank, (user_id, data) in enumerate(leaderboard, 1):
                    member = ctx.guild.get_member(int(user_id))
                    xp = data.get("xp", 0)
                    embed.add_field(name=f"{self.get_rank_emoji(rank)} {getattr(member, 'name', f'User {user_id}')}", 
                                    value=f"```yaml\nXP: {xp:.2f}\nMessages: {sum(s['messages'] for s in data['servers'].values())}\nMedia: {sum(s['media'] for s in data['servers'].values())}```", 
                                    inline=False)
            else:
                embed.description = "```diff\n- No data available```"

            await ctx.followup.send(embed=embed)
        except Exception as e:
            LogError(f"Leaderboard error: {str(e)}")
            raise

    def get_rank_emoji(self, rank):
        return ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][rank-1]

def setup(bot: commands.Bot):
    bot.add_cog(Leaderboards(bot))
