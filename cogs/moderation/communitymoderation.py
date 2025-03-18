import discord
from discord.ext import commands
from discord.commands import slash_command
import datetime
import handlers.config as cfg
from handlers.modextensions import send_mod_log
from handlers.debug import LogError, LogModeration

class ModCommunityBan(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.embed_colors = {
            'success': 0x2ECC71,
            'error': 0xE74C3C,
            'mod_action': 0x992D22
        }
        self.persistent_views_added = False

    def create_embed(self, title, description, color_type='mod_action', author=None):
        embed = discord.Embed(
            title=title,
            description=description,
            color=self.embed_colors.get(color_type, 0x2b2d31),
            timestamp=datetime.datetime.utcnow()
        )
        if author:
            embed.set_author(name=str(author), icon_url=author.avatar.url)
        embed.set_footer(text="Community ModSystem", icon_url=self.bot.user.avatar.url)
        return embed



    @slash_command(name="mod-community-ban", description="Initiate a community ban vote")
    @commands.has_permissions(ban_members=True)
    async def community_ban(self, ctx, 
                          user: discord.Member,
                          reason: str = "Community consensus"):
        try:
            if user == ctx.author:
                embed = self.create_embed(
                    "❌ Self-Ban Attempt",
                    "Self-initiated community bans are forbidden!",
                    'error',
                    ctx.author
                )
                await ctx.respond(embed=embed, ephemeral=True)
                LogModeration(f"Self-ban attempt blocked for {ctx.author.id}")
                return

            embed = self.create_embed(
                "🔨 Community Ban Initiated",
                f"{ctx.author.mention} initiated ban for {user.mention}\n**Reason:** {reason}",
                'mod_action',
                ctx.author
            )
            embed.add_field(name="Voting", value="Click below to confirm ban", inline=False)
            embed.set_thumbnail(url=user.avatar.url)
            
            view = self.BanVoteView(self, user, reason)
            await ctx.respond(embed=embed, view=view)
            LogModeration(f"Community ban started for {user.id} in {ctx.guild.id}")

        except Exception as e:
            LogError(f"Community ban init error: {str(e)}")
            await ctx.respond("🚨 Failed to initialize community ban!", ephemeral=True)

    class BanVoteView(discord.ui.View):
        def __init__(self, cog, target, reason):
            super().__init__(timeout=None)
            self.cog = cog
            self.target = target
            self.reason = reason
            self.confirmed = False

        @discord.ui.button(label="Confirm Ban", style=discord.ButtonStyle.danger, 
                         emoji="🔨", custom_id="persist:community_ban")
        async def confirm_callback(self, button, interaction):
            try:
                if self.confirmed:
                    await interaction.response.send_message("⏳ Ban already executed!", ephemeral=True)
                    return

                if interaction.user == self.target:
                    await interaction.response.send_message("❌ Cannot self-ban!", ephemeral=True)
                    return

                # Updated line: Use guild.ban instead of self.target.ban
                await interaction.guild.ban(self.target, reason=f"Community ban by {interaction.user}: {self.reason}")
                self.confirmed = True
                button.disabled = True

                new_embed = self.cog.create_embed(
                    "✅ Ban Executed",
                    f"{self.target.mention} banned by community\n**Confirmed by:** {interaction.user.mention}",
                    'success',
                    interaction.user
                )
                new_embed.add_field(name="Original Reason", value=self.reason)
                new_embed.set_thumbnail(url=self.target.avatar.url)
                await interaction.message.edit(embed=new_embed, view=self)

                try:
                    dm_embed = self.cog.create_embed(
                        "🔨 Community Ban",
                        f"Banned from {interaction.guild.name}\n**Reason:** {self.reason}",
                        'error'
                    )
                    await self.target.send(embed=dm_embed)
                except discord.Forbidden:
                    LogError(f"Failed DM to {self.target.id}")

                log_data = {
                    "title": "🔨 Community Ban Finalized",
                    "description": f"**Target:** {self.target.mention}\n**By:** {interaction.user.mention}\n**Reason:** {self.reason}",
                    "color_type": 'mod_action',
                    "author": interaction.user
                }
                await self.cog.send_mod_log(interaction.guild.id, log_data)

                await interaction.response.send_message(f"✅ {interaction.user.mention} confirmed ban!", ephemeral=False)

            except discord.Forbidden:
                await interaction.response.send_message("❌ Missing permissions!", ephemeral=True)
                LogError(f"Ban failed for {self.target.id}")
            except Exception as e:
                await interaction.response.send_message("⚠️ Critical ban error!", ephemeral=True)
                LogError(f"Community ban error: {str(e)}")

def setup(bot: discord.Bot):
    cog = ModCommunityBan(bot)
    bot.add_cog(cog)
