import discord
from discord.ext import commands
from discord.commands import slash_command
import datetime
import random
from handlers.debug import LogError, LogModeration

class ModCommunityMute(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.embed_colors = {
            'success': 0x2ECC71,
            'error': 0xE74C3C,
            'mod_action': 0x992D22,
            'vote': 0xF1C40F
        }

    def create_embed(self, title, description, color_type='mod_action', author=None):
        spacer = "\u200b" * 20  
        divider = "─" * 30
        
        embed = discord.Embed(
            title=title,
            description=f"{description}\n\n{divider}",
            color=self.embed_colors.get(color_type, 0x2b2d31),
            timestamp=datetime.datetime.utcnow()
        )
        
        if author:
            embed.set_author(name=str(author), icon_url=author.display_avatar.url)
            
        embed.set_footer(text="Community ModSystem", icon_url=self.bot.user.display_avatar.url)
        return embed

    @slash_command(name="mod-community-mute", description="Start community mute vote (Admin only)")
    @commands.has_permissions(administrator=True)
    async def community_mute(self, ctx, user: discord.Member, reason: str = "Community decision"):
        try:
            if user == ctx.author:
                return await ctx.respond(
                    embed=self.create_embed(
                        "❌ Invalid Target",
                        "You cannot start a mute vote against yourself",
                        'error',
                        ctx.author
                    ), ephemeral=True
                )
            
            vote_duration = 30  
            vote_end = datetime.datetime.utcnow() + datetime.timedelta(seconds=vote_duration)
            vote_end_str = f"<t:{int(vote_end.timestamp())}:F>"
            
            description = (
                f"**Target:** {user.mention}\n"
                f"**Initiated by:** {ctx.author.mention}\n\n"
                "───────────────────────────────\n" 
                f"**Reason:** {reason}\n"
                "───────────────────────────────\n\n" 
                f"🗳️ **Vote Duration:** {vote_duration} seconds\n"
                "⏰ **Possible Timeouts:**\n"
                "1h | 3h | 6h | 12h | 24h\n"
                f"🕒 **Abstimmungsende:** {vote_end_str}"
            )

            embed = self.create_embed(
                "🗳️ Community Mute Vote",
                description,
                'vote',
                ctx.author
            )
            embed.set_thumbnail(url=user.display_avatar.url)

            view = self.MuteVoteView(user, reason, ctx.author, self.create_embed, vote_end)
            await ctx.respond(embed=embed, view=view)
            view.message = await ctx.interaction.original_response()
            LogModeration(f"Community mute started for {user.id} in {ctx.guild.id}")

        except Exception as e:
            LogError(f"Community mute init error: {str(e)}")
            await ctx.respond("🚨 Failed to start mute vote", ephemeral=True)

    class MuteVoteView(discord.ui.View):
        def __init__(self, target, reason, initiator, create_embed_func, vote_end):
            super().__init__(timeout=30)
            self.target = target
            self.reason = reason
            self.initiator = initiator
            self.create_embed = create_embed_func
            self.vote_end = vote_end
            self.votes = {
                '1h': set(),
                '3h': set(),
                '6h': set(),
                '12h': set(),
                '24h': set()
            }
            self.vote_options = ['1h', '3h', '6h', '12h', '24h']
            
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
                    '24h': 86400
                }[chosen]

                disable_until = datetime.datetime.utcnow() + datetime.timedelta(seconds=duration_seconds)
                await self.target.timeout(
                    until=disable_until,
                    reason=f"Community mute: {self.reason}"
                )

                vote_counts = {option: len(voters) for option, voters in self.votes.items()}
                vote_end_now = f"<t:{int(datetime.datetime.utcnow().timestamp())}:F>"

                new_embed = self.create_embed(
                    "🔇 Mute Executed",
                    f"**Target:** {self.target.mention}\n\n"
                    f"**Duration:** {chosen}\n\n"
                    f"**Voter Counts:**\n"
                    f"1h: {vote_counts['1h']}, 3h: {vote_counts['3h']}, 6h: {vote_counts['6h']}, 12h: {vote_counts['12h']}, 24h: {vote_counts['24h']}\n\n"
                    f"**Vote Ended at:** {vote_end_now}\n\n"
                    f"**Reason:** {self.reason}",
                    'success',
                    self.initiator
                )
                new_embed.set_thumbnail(url=self.target.display_avatar.url)

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
                    dm_embed = self.create_embed(
                        "🔇 Community Mute",
                        f"You were muted in **{guild_name}**\n\n"
                        f"**Duration:** {chosen}\n\n"
                        f"**Reason:** {self.reason}\n\n"
                        "This action was community-voted",
                        'error'
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
