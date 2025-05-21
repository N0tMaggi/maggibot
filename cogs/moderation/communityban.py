import discord
from discord.ext import commands
from discord.commands import slash_command
import datetime
from handlers.debug import LogError, LogModeration

class ModCommunityBan(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.embed_colors = {
            'success': 0x2ECC71,
            'error': 0xE74C3C,
            'mod_action': 0x992D22
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

    @slash_command(name="mod-community-ban", description="Start community ban vote (Admin only)")
    @commands.has_permissions(administrator=True)
    async def community_ban(self, ctx, user: discord.Member, reason: str = "Community decision"):
        try:
            if user == ctx.author:
                return await ctx.respond(
                    embed=self.create_embed(
                        "❌ Invalid Target",
                        "You cannot start a ban vote against yourself",
                        'error',
                        ctx.author
                    ), ephemeral=True
                )

            description = (
                f"**Target:** {user.mention}\n"
                f"**Initiated by:** {ctx.author.mention}\n\n"
                "───────────────────────────────\n" 
                f"**Reason:** {reason}\n"
                "───────────────────────────────\n\n" 
                "⚠️ **Action Required:**\n"
                "Any User can click the button below to confirm this ban\n"
                "**Only 1 confirmation needed**"
            )

            embed = self.create_embed(
                "⚠️ Community Ban Vote",
                description,
                'mod_action',
                ctx.author
            )
            embed.set_thumbnail(url=user.display_avatar.url)

            view = self.BanVoteView(self, user, reason, ctx.author)  # [[3]][[4]]
            await ctx.respond(embed=embed, view=view)
            LogModeration(f"Community ban started for {user.id} in {ctx.guild.id}")

        except Exception as e:
            LogError(f"Community ban init error: {str(e)}")
            await ctx.respond("🚨 Failed to start ban vote", ephemeral=True)

    class BanVoteView(discord.ui.View):
        def __init__(self, cog, target, reason, initiator):
            super().__init__(timeout=None)
            self.cog = cog 
            self.target = target
            self.reason = reason
            self.initiator = initiator
            self.confirmed = False

        @discord.ui.button(label="Execute Ban", style=discord.ButtonStyle.danger, emoji="⚠️", custom_id="community_ban:execute")
        async def execute_ban(self, button: discord.ui.Button, interaction: discord.Interaction):
            if self.confirmed:
                return await interaction.response.send_message("⚠️ Ban already executed", ephemeral=True)

            try:
                self.confirmed = True
                button.disabled = True
                button.label = "Ban Executed"
                button.style = discord.ButtonStyle.grey

                await interaction.guild.ban(self.target, reason=f"Community ban: {self.reason}")
                
                spacer = "\u200b" * 10
                new_embed = self.cog.create_embed(  # [[3]][[5]]
                    "✅ Ban Executed",
                    f"{spacer}\n**Target:** {self.target.mention}\n\n"
                    f"**Confirmed by:** {interaction.user.mention}\n\n"
                    f"**Reason:** {self.reason}",
                    'success',
                    interaction.user
                )
                new_embed.set_thumbnail(url=self.target.display_avatar.url)
                
                await interaction.message.edit(embed=new_embed, view=self)
                await interaction.response.send_message(f"✅ Ban confirmed by {interaction.user.mention}!", ephemeral=False)

                try:
                    dm_embed = self.cog.create_embed(  # [[3]][[5]]
                        "🔨 Community Ban",
                        f"You were banned from **{interaction.guild.name}**\n\n"
                        f"**Reason:** {self.reason}\n\n"
                        "───────────────────────────────\n"
                        "This action was community-confirmed",
                        'error'
                    )
                    await self.target.send(embed=dm_embed)
                except:
                    pass

                LogModeration(f"Community ban executed for {self.target.id} by {interaction.user.id}")

            except Exception as e:
                LogError(f"Ban execution failed: {str(e)}")
                await interaction.response.send_message("🚨 Failed to execute ban", ephemeral=True)

def setup(bot: discord.Bot):
    bot.add_cog(ModCommunityBan(bot))