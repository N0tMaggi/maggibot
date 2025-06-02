from discord.ext import commands
import discord
import datetime
from extensions.statsextension import create_stats_embed
from handlers.debug import LogDebug, LogError
from handlers.config import load_stats, save_stats, MESSAGE_XP_COUNT, ATTACHMENT_XP_COUNT, VOICE_XP_COUNT, load_multiplier_config

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
            embed = create_stats_embed(f"📈 {user.display_name}'s Statistics", color_type="stats")
            embed.set_thumbnail(url=user.display_avatar.url)

            if stats:
                xp = stats.get("xp", 0.0)
                level = stats.get("level", int(xp // 20))
                server_stats = stats.get("servers", {})
                
                embed.add_field(
                    name="🌟 Level",
                    value=f"```yaml\nLevel: {level}```",
                    inline=False
                )
                embed.add_field(
                    name="🌟 Total XP", 
                    value=f"```yaml\n{xp:.2f} XP```", 
                    inline=False
                )

                server_info = []
                for guild_id, data in server_stats.items():
                    guild = self.bot.get_guild(int(guild_id)) or f"Server {guild_id}"
                    server_info.append(
                        f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n"
                        f"**{guild}**\n"
                        f"📨 Messages: {data.get('messages', 0)}\n"
                        f"📎 Media: {data.get('media', 0)}\n"
                        f"🎧 Voice Minutes: {data.get('voiceminutes', 0)}"
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
        await ctx.defer()
        LogDebug(f"Leaderboard viewed by {ctx.author.id}")
        try:
            stats = load_stats()
            embed = create_stats_embed(
                "🌍 Global XP Leaderboard",
                "```diff\n+ Top Performers Across All Servers\n+ Updated: " + datetime.datetime.now().strftime("%Y-%m-%d") + "```",
                "leaderboard"
            )

            if stats:
                leaderboard = sorted(stats.items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]

                for rank, (user_id, data) in enumerate(leaderboard, 1):
                    member = ctx.guild.get_member(int(user_id))
                    xp = data.get("xp", 0)
                    level = data.get("level", int(xp // 20))
                    total_messages = sum(s['messages'] for s in data['servers'].values())
                    total_media = sum(s['media'] for s in data['servers'].values())
                    total_voice = sum(s.get('voiceminutes', 0) for s in data['servers'].values())
                    
                    embed.add_field(
                        name=f"{self.get_rank_emoji(rank)} {getattr(member, 'name', f'User {user_id}')}", 
                        value=f"```yaml\nLevel: {level}\nXP: {xp:.2f}\n"
                              f"Messages: {total_messages}\n"
                              f"Media: {total_media}\n"
                              f"Voice: {total_voice}m```", 
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
    
    @commands.slash_command(name="serverleaderboard", description="🏆 Server-specific XP leaderboard")
    async def server_leaderboard(self, ctx: discord.ApplicationContext):
        """Displays XP rankings within current server"""
        await ctx.defer()
        LogDebug(f"Server leaderboard viewed in {ctx.guild.id}")
        try:
            stats = load_stats()
            current_guild = str(ctx.guild.id)
            embed = create_stats_embed(
                f"📊 {ctx.guild.name} Leaderboard",
                "```diff\n+ Top Members In This Server\n+ Updated: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + "```",
                "server_leaderboard"
            )

            server_stats = []
            for user_id, user_data in stats.items():
                guild_data = user_data.get("servers", {}).get(current_guild)
                if guild_data:
                    server_stats.append((
                        user_id,
                        guild_data.get("messages", 0),
                        guild_data.get("media", 0),
                        guild_data.get("voiceminutes", 0),
                        user_data.get("xp", 0),
                        user_data.get("level", int(user_data.get("xp", 0) // 20))
                    ))

            if server_stats:
                sorted_stats = sorted(server_stats, key=lambda x: x[4], reverse=True)[:10]
                
                for rank, (user_id, messages, media, voice, xp, level) in enumerate(sorted_stats, 1):
                    member = ctx.guild.get_member(int(user_id))
                    display_name = getattr(member, "display_name", f"User {user_id}")
                    
                    embed.add_field(
                        name=f"{self.get_rank_emoji(rank)} {display_name}",
                        value=f"```yaml\nLevel: {level}\nXP: {xp:.2f}\n"
                              f"Messages: {messages}\n" 
                              f"Media: {media}\n"
                              f"Voice: {voice}m```",
                        inline=False
                    )
            else:
                embed.description = "```diff\n- No server statistics available```"

            await ctx.followup.send(embed=embed)
        except Exception as e:
            LogError(f"Server leaderboard error: {str(e)}")
            raise



    @commands.slash_command(name="xp-info", description="ℹ️ Show XP earning system details")
    async def xp_info(self, ctx: discord.ApplicationContext):
        """Displays XP reward system information"""
        try:
            config = load_multiplier_config()
            embed = create_stats_embed("💡 XP System Overview", color_type="info")
            
            base_xp = (
                f"• Messages: {MESSAGE_XP_COUNT} XP\n"
                f"• Attachments: {ATTACHMENT_XP_COUNT} XP each\n"
                f"• Voice: {VOICE_XP_COUNT} XP/min"
            )
            
            multipliers = []
            if config["multipliers"]:
                role_multipliers = "\n".join([f"<@&{rid}>: {mult}x" for rid, mult in config["multipliers"].items()])
                multipliers.append(f"**Role Multipliers:**\n{role_multipliers}")
                
            if config["channels"]:
                channel_boosts = "\n".join([f"<#{cid}>" for cid in config["channels"]])
                multipliers.append(f"**Boosted Channels:**\n{channel_boosts}")
            
            embed.add_field(name="Base Rewards", value=base_xp, inline=False)
            if multipliers:
                embed.add_field(name="Multipliers", value="\n\n".join(multipliers), inline=False)
            
            embed.set_footer(text="XP can stack with multiple multipliers")
            await ctx.respond(embed=embed)
        except Exception as e:
            LogError(f"XP info error: {str(e)}")
            raise

def setup(bot: commands.Bot):
    bot.add_cog(Leaderboards(bot))