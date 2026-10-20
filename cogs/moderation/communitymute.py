import discord
from discord.ext import commands
from discord.commands import slash_command
import random
import datetime
from handlers.debug import LogError, LogModeration
from utils.embed_helpers import (
    create_embed,
    create_mod_embed,
    create_security_embed,
    create_success_embed,
    create_error_embed,
    create_warning_embed,
)

class ModCommunityMute(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @slash_command(name="mod-community-mute", description="Start community mute vote (Admin only)")
    @commands.has_permissions(administrator=True)
    async def community_mute(self, ctx, user: discord.Member, reason: str = "Community decision"):
        try:
            if user == ctx.author:
                return await ctx.respond(
                    embed=create_error_embed(
                        "Invalid Target",
                        "You cannot start a mute vote against yourself",
                        author=ctx.author
                    ), ephemeral=True
                )
            
            vote_duration = 30  
            vote_end = discord.utils.utcnow() + datetime.timedelta(seconds=vote_duration)
            vote_end_str = f"<t:{int(vote_end.timestamp())}:F>"
            
            description = (
                f"**Target:** {user.mention}\n"
                f"**Initiated by:** {ctx.author.mention}\n\n"
                "───────────────────────────────\n" 
                f"**Reason:** {reason}\n"
                "───────────────────────────────\n\n" 
                f"🗳️ **Vote Duration:** {vote_duration} seconds\n"
                "⏰ **Possible Timeouts:**\n"
                "1h | 3h | 6h | 12h | 24h | 1d | 3d | 7d\n"
                f"🕒 **Vote End:** {vote_end_str}"
            )

            embed = create_mod_embed(
                "🗳️ Community Mute Vote",
                description,
                color_type='vote',
                author=ctx.author,
                bot_user=self.bot.user,
                thumbnail=user.display_avatar.url
            )

            view = self.MuteVoteView(user, reason, ctx.author, vote_end, bot_user=self.bot.user)
            await ctx.respond(embed=embed, view=view)
            view.message = await ctx.interaction.original_response()
            LogModeration(f"Community mute started for {user.id} in {ctx.guild.id}")

        except Exception as e:
            LogError(f"Community mute init error: {str(e)}")
            await ctx.respond("🚨 Failed to start mute vote", ephemeral=True)

    class MuteVoteView(discord.ui.View):
        def __init__(self, target, reason, initiator, vote_end, bot_user=None):
            super().__init__(timeout=30)
            self.target = target
            self.reason = reason
            self.initiator = initiator
            self.vote_end = vote_end
            self.bot_user = bot_user
            self.votes = {
                '1h': set(),
                '3h': set(),
                '6h': set(),
                '12h': set(),
                '24h': set(),
                '1d': set(),
                '3d': set(),
                '7d': set()
            }
            self.vote_options = ['1h', '3h', '6h', '12h', '24h', '1d', '3d', '7d']
            
            for option in self.vote_options:
                self.add_item(self.VoteButton(option, self))
            
            self.message = None

        async def on_timeout(self):
            try:
                total_votes = sum(len(v) for v in self.votes.values())
                if total_votes == 0:
                    chosen = random.choice(self.vote_options)
                else:
                    max_votes = max(len(v) for v in self.votes.values())
                    candidates = [k for k, v in self.votes.items() if len(v) == max_votes]
                    chosen = random.choice(candidates) if len(candidates) > 1 else candidates[0]

                duration_seconds = {
                    '1h': 3600,
                    '3h': 10800,
                    '6h': 21600,
                    '12h': 43200,
                    '24h': 86400,
                    '1d': 86400,
                    '3d': 259200,
                    '7d': 604800
                }[chosen]

                disable_until = discord.utils.utcnow() + datetime.timedelta(seconds=duration_seconds)
                await self.target.timeout(
                    until=disable_until,
                    reason=f"Community mute: {self.reason}"
                )

                vote_counts = {option: len(self.votes[option]) for option in self.vote_options}
                vote_end_now = f"<t:{int(discord.utils.utcnow().timestamp())}:F>"

                new_embed = create_mod_embed(
                    "🔇 Mute Executed",
                    f"**Target:** {self.target.mention}\n\n"
                    f"**Duration:** {chosen}\n\n"
                    f"**Voter Counts:**\n"
                    f"1h: {vote_counts['1h']}, "
                    f"3h: {vote_counts['3h']}, "
                    f"6h: {vote_counts['6h']}, "
                    f"12h: {vote_counts['12h']}, "
                    f"24h: {vote_counts['24h']}, "
                    f"1d: {vote_counts['1d']}, "
                    f"3d: {vote_counts['3d']}, "
                    f"7d: {vote_counts['7d']}\n\n"
                    f"**Vote Ended at:** {vote_end_now}\n\n"
                    f"**Reason:** {self.reason}",
                    color_type='success',
                    author=self.initiator,
                    bot_user=self.bot_user,
                    thumbnail=self.target.display_avatar.url
                )

                for child in self.children:
                    child.disabled = True

                if self.message:
                    await self.message.edit(embed=new_embed, view=self)
                    if self.message.channel:
                        await self.message.channel.send(
                            f"✅ {self.target.mention} has been muted for {chosen} by community vote!",
                            allowed_mentions=discord.AllowedMentions(users=False)
                        )
                else:
                    await self.initiator.send(embed=new_embed)

                try:
                    guild_name = self.message.guild.name if self.message and self.message.guild else 'the server'
                    dm_embed = create_mod_embed(
                        "🔇 Community Mute",
                        f"You were muted in **{guild_name}**\n\n"
                        f"**Duration:** {chosen}\n\n"
                        f"**Reason:** {self.reason}\n\n"
                        "This action was community-voted",
                        color_type='error',
                        bot_user=self.bot_user
                    )
                    await self.target.send(embed=dm_embed)
                except Exception as dm_error:
                    LogError(f"DM sending failed: {str(dm_error)}")

                LogModeration(f"Community mute executed for {self.target.id}: {chosen}")

            except Exception as e:
                LogError(f"Mute execution failed: {str(e)}")
                if self.message and self.message.channel:
                    await self.message.channel.send("🚨 Failed to apply mute", delete_after=10)
                else:
                    await self.initiator.send("🚨 Failed to apply mute")

        class VoteButton(discord.ui.Button):
            def __init__(self, duration, parent_view):
                super().__init__(
                    label=duration,
                    style=discord.ButtonStyle.primary,
                    emoji="🗳️",
                    custom_id=f"vote_{duration}"
                )
                self.parent = parent_view
                self.duration = duration

            async def callback(self, interaction: discord.Interaction):
                if interaction.user.id in self.parent.votes[self.duration]:
                    return await interaction.response.send_message(
                        "You already voted for this option", 
                        ephemeral=True
                    )

                for vote_list in self.parent.votes.values():
                    if interaction.user.id in vote_list:
                        vote_list.remove(interaction.user.id)

                self.parent.votes[self.duration].add(interaction.user.id)
                await interaction.response.send_message(
                    f"Your vote for {self.duration} has been recorded", 
                    ephemeral=True
                )

def setup(bot: discord.Bot):
    bot.add_cog(ModCommunityMute(bot))
