import discord
from discord.ext import commands
from discord.commands import slash_command
import random
import datetime
from handlers.debug import LogError, LogModeration
from extensions.modextensions import create_mod_embed
from utils.components import build_view

class ModCommunityMute(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    def create_embed(self, title, description, color_type='mod_action', author=None):
        """Create a moderation container using centralized utility"""
        return create_mod_embed(
            title=title,
            description=description,
            color_type=color_type,
            author=author
        )

    @slash_command(name="mod-community-mute", description="Start community mute vote (Admin only)")
    @commands.has_permissions(administrator=True)
    async def community_mute(self, ctx, user: discord.Member, reason: str = "Community decision"):
        try:
            if user == ctx.author:
                return await ctx.respond(
                    view=build_view(self.create_embed(
                        "❌ Invalid Target",
                        "You cannot start a mute vote against yourself",
                        'error',
                        ctx.author
                    )), ephemeral=True
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
                "1h | 3h | 6h | 12h | 24h | 1d | 3d | 7d\n"
                f"🕒 **Vote End:** {vote_end_str}"
            )

            embed = self.create_embed(
                "🗳️ Community Mute Vote",
                description,
                'vote',
                ctx.author
            )
            embed.add_item(
                discord.ui.Section(
                    discord.ui.TextDisplay("\u200b"),
                    accessory=discord.ui.Thumbnail(user.display_avatar.url),
                )
            )

            panel = self.MuteVotePanel(user, reason, ctx.author, self.create_embed, vote_end)
            row_top = self.VoteActionRow(['1h', '3h', '6h', '12h', '24h'], panel)
            row_bottom = self.VoteActionRow(['1d', '3d', '7d'], panel)
            designer_view = self.MuteVoteDesignerView(panel, row_top, row_bottom, timeout=30)
            designer_view.add_item(embed)
            designer_view.add_item(row_top)
            designer_view.add_item(row_bottom)
            await ctx.respond(view=designer_view)
            message = await ctx.interaction.original_response()
            designer_view.message = message
            panel.message = message
            panel.designer_view = designer_view
            LogModeration(f"Community mute started for {user.id} in {ctx.guild.id}")

        except Exception as e:
            LogError(f"Community mute init error: {str(e)}")
            await ctx.respond("🚨 Failed to start mute vote", ephemeral=True)

    class MuteVotePanel:
        def __init__(self, target, reason, initiator, create_embed_func, vote_end):
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
                '24h': set(),
                '1d': set(),
                '3d': set(),
                '7d': set()
            }
            self.vote_options = ['1h', '3h', '6h', '12h', '24h', '1d', '3d', '7d']
            self.message = None
            self.designer_view = None

        async def finalize_vote(self):
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

            disable_until = datetime.datetime.utcnow() + datetime.timedelta(seconds=duration_seconds)
            await self.target.timeout(
                until=disable_until,
                reason=f"Community mute: {self.reason}"
            )

            vote_counts = {option: len(self.votes[option]) for option in self.vote_options}
            vote_end_now = f"<t:{int(datetime.datetime.utcnow().timestamp())}:F>"

            new_embed = self.create_embed(
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
                'success',
                self.initiator
            )
            new_embed.add_item(
                discord.ui.Section(
                    discord.ui.TextDisplay("\u200b"),
                    accessory=discord.ui.Thumbnail(self.target.display_avatar.url),
                )
            )

            if self.designer_view:
                for child in self.designer_view.children:
                    if hasattr(child, "disabled"):
                        child.disabled = True

            if self.message:
                disabled_view = build_view(
                    new_embed,
                    self.designer_view.top_row if self.designer_view else None,
                    self.designer_view.bottom_row if self.designer_view else None,
                    timeout=None,
                ) if self.designer_view else build_view(new_embed)
                if self.designer_view:
                    for child in (self.designer_view.top_row.children + self.designer_view.bottom_row.children):
                        child.disabled = True
                    disabled_view = build_view(new_embed, self.designer_view.top_row, self.designer_view.bottom_row, timeout=None)
                await self.message.edit(view=disabled_view)
                if self.message.channel:
                    await self.message.channel.send(
                        f"✅ {self.target.mention} has been muted for {chosen} by community vote!",
                        allowed_mentions=discord.AllowedMentions(users=False)
                    )
            else:
                await self.initiator.send(view=build_view(new_embed))

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
                await self.target.send(view=build_view(dm_embed))
            except Exception as dm_error:
                LogError(f"DM sending failed: {str(dm_error)}")

            LogModeration(f"Community mute executed for {self.target.id}: {chosen}")


    class MuteVoteDesignerView(discord.ui.DesignerView):
        def __init__(self, panel, top_row, bottom_row, timeout=30):
            super().__init__(timeout=timeout)
            self.panel = panel
            self.top_row = top_row
            self.bottom_row = bottom_row
            self.message = None

        async def on_timeout(self):
            try:
                await self.panel.finalize_vote()
            except Exception as e:
                LogError(f"Mute execution failed: {str(e)}")
                if self.message and self.message.channel:
                    await self.message.channel.send("🚨 Failed to apply mute", delete_after=10)
                else:
                    await self.panel.initiator.send("🚨 Failed to apply mute")


    class VoteActionRow(discord.ui.ActionRow):
        def __init__(self, options, panel):
            super().__init__()
            self.panel = panel
            for option in options:
                self.add_item(ModCommunityMute.VoteButton(option, panel))

    class VoteButton(discord.ui.Button):
        def __init__(self, duration, panel):
            super().__init__(
                label=duration,
                style=discord.ButtonStyle.primary,
                emoji="🗳️",
                custom_id=f"vote_{duration}"
            )
            self.panel = panel
            self.duration = duration

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id in self.panel.votes[self.duration]:
                return await interaction.response.send_message(
                    "You already voted for this option", 
                    ephemeral=True
                )

            for vote_list in self.panel.votes.values():
                if interaction.user.id in vote_list:
                    vote_list.remove(interaction.user.id)

            self.panel.votes[self.duration].add(interaction.user.id)
            await interaction.response.send_message(
                f"Your vote for {self.duration} has been recorded", 
                ephemeral=True
            )

def setup(bot: discord.Bot):
    bot.add_cog(ModCommunityMute(bot))
