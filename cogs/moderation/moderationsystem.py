import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup
from discord.ui import View, Button, button
import datetime
import handlers.config as cfg
from extensions.modextensions import create_mod_embed, send_mod_log
from handlers.debug import LogDebug, LogError, LogModeration
import asyncio
from dateutil.parser import parse as parse_duration

class ModerationView(View):
    def __init__(self, user: discord.Member, moderator: discord.Member):
        super().__init__(timeout=60)
        self.user = user
        self.moderator = moderator
        self.ctx = None

    @button(label="Ban", style=discord.ButtonStyle.red, emoji="🔨", row=0)
    async def ban_button(self, button: Button, interaction: discord.Interaction):
        await self.handle_action(interaction, "ban")

    @button(label="Kick", style=discord.ButtonStyle.primary, emoji="⚠️", row=0)
    async def kick_button(self, button: Button, interaction: discord.Interaction):
        await self.handle_action(interaction, "kick")

    @button(label="Timeout", style=discord.ButtonStyle.grey, emoji="🔇", row=0)
    async def timeout_button(self, button: Button, interaction: discord.Interaction):
        await self.handle_action(interaction, "timeout")

    @button(label="Warn", style=discord.ButtonStyle.primary, emoji="⚠️", row=1)
    async def warn_button(self, button: Button, interaction: discord.Interaction):
        await self.handle_action(interaction, "warn")

    @button(label="History", style=discord.ButtonStyle.secondary, emoji="📚", row=1)
    async def history_button(self, button: Button, interaction: discord.Interaction):
        await self.show_history(interaction)

    @button(label="Refresh", style=discord.ButtonStyle.grey, emoji="🔄", row=1)
    async def refresh_button(self, button: Button, interaction: discord.Interaction):
        await self.refresh_info(interaction)

    @button(label="Close", style=discord.ButtonStyle.red, emoji="✖️", row=2)
    async def close_button(self, button: Button, interaction: discord.Interaction):
        await interaction.message.delete()

    async def handle_action(self, interaction: discord.Interaction, action_type: str):
        if not self.ctx:
            return await interaction.response.send_message("Context not found", ephemeral=True)
            
        required_perms = {
            "ban": "ban_members",
            "kick": "kick_members",
            "timeout": "moderate_members",
            "warn": "moderate_members"
        }.get(action_type)
        
        if not interaction.user.guild_permissions.__getattribute__(required_perms):
            return await interaction.response.send_message(
                embed=create_mod_embed(
                    "❌ Permission Denied",
                    f"You need `{required_perms.replace('_', ' ').title()}` permission",
                    'error',
                    interaction.user
                ), ephemeral=True
            )

        try:
            if action_type == "timeout":
                await interaction.response.send_message(
                    embed=create_mod_embed(
                        "⏱️ Timeout Duration",
                        "Enter duration (e.g., '1h 30m')",
                        'info',
                        interaction.user
                    ), ephemeral=True
                )
                msg = await self.bot.wait_for(
                    'message',
                    check=lambda m: m.author == interaction.user and m.channel == self.ctx.channel,
                    timeout=60
                )
                duration = parse_duration(msg.content)
                await msg.delete()
                
            await interaction.response.send_message(
                embed=create_mod_embed(
                    "📝 Enter Reason",
                    "Please type the reason for this action in the chat",
                    'info',
                    interaction.user
                ), ephemeral=True
            )
            msg = await self.bot.wait_for(
                'message',
                check=lambda m: m.author == interaction.user and m.channel == self.ctx.channel,
                timeout=60
            )
            reason = msg.content
            await msg.delete()
        except asyncio.TimeoutError:
            return await interaction.followup.send("Action timed out", ephemeral=True)

        try:
            if action_type == "ban":
                if self.user.guild_permissions.administrator:
                    return await interaction.followup.send(
                        embed=create_mod_embed(
                            "❌ Safety Lock",
                            "Cannot ban server administrators",
                            'error'
                        ), ephemeral=True
                    )
                await self.user.ban(reason=f"{self.moderator}: {reason}")
                action_text = "banned"
            elif action_type == "kick":
                await self.user.kick(reason=f"{self.moderator}: {reason}")
                action_text = "kicked"
            elif action_type == "timeout":
                await self.user.timeout(duration, reason=reason)
                action_text = "timed out"
            elif action_type == "warn":
                action_text = "warned"
                LogModeration(f"Warned {self.user.id} by {self.moderator.id}: {reason}")

            await self.ctx.send_followup(
                embed=create_mod_embed(
                    f"✅ {action_type.title()} Successful",
                    f"{self.user.mention} has been {action_text}",
                    'success',
                    self.moderator
                ), ephemeral=True
            )
            
            log_data = {
                "title": f"Moderation Action",
                "description": (
                    f"**User:** {self.user.mention}\n"
                    f"**Moderator:** {self.moderator.mention}\n"
                    f"**Action:** {action_type}\n"
                    f"**Reason:** {reason}"
                ),
                "color_type": 'mod_action',
                "author": self.moderator
            }
            await send_mod_log(self.ctx.guild.id, log_data, self.bot)
        except Exception as e:
            LogError(f"Moderation action failed: {str(e)}")
            await interaction.followup.send(
                embed=create_mod_embed(
                    "⚠️ Error",
                    f"Action failed: {str(e)}",
                    'error',
                    interaction.user
                ), ephemeral=True
            )

    async def show_history(self, interaction: discord.Interaction):
        embed = create_mod_embed(
            "📚 Moderation History",
            f"**User:** {self.user.mention}\n"
            "No recent actions found",
            'info'
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def refresh_info(self, interaction: discord.Interaction):
        new_embed = await self.generate_user_embed()
        await interaction.message.edit(embed=new_embed)
        await interaction.response.defer()

    async def generate_user_embed(self):
        embed = discord.Embed(
            title=f"User Information: {self.user}",
            color=0x3498DB,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=self.user.display_avatar.url)
        
        status_emojis = {
            'online': '🟢',
            'idle': '🌙',
            'dnd': '⛔',
            'offline': '⚪'
        }
        status = status_emojis.get(str(self.user.status), '⚪')
        embed.description = f"{status} **Status:** {self.user.status}"
        
        embed.add_field(name="User ID", value=self.user.id, inline=False)
        embed.add_field(name="Nickname", value=self.user.nick or "None", inline=True)
        embed.add_field(name="Bot Account", value="Yes" if self.user.bot else "No", inline=True)
        embed.add_field(name="Pending Verification", value="Yes" if self.user.pending else "No", inline=True)
        embed.add_field(name="Joined Server", value=f"<t:{int(self.user.joined_at.timestamp())}:R>")
        embed.add_field(name="Account Created", value=f"<t:{int(self.user.created_at.timestamp())}:R>")
        
        roles = [role.mention for role in self.user.roles[1:]]
        embed.add_field(name=f"Roles ({len(roles)})", 
                      value=", ".join(roles) if roles else "None", 
                      inline=False)
        
        perms = []
        if self.user.guild_permissions.administrator:
            perms.append("Administrator")
        else:
            if self.user.guild_permissions.manage_messages: perms.append("Manage Messages")
            if self.user.guild_permissions.ban_members: perms.append("Ban Members")
            if self.user.guild_permissions.kick_members: perms.append("Kick Members")
            if self.user.guild_permissions.moderate_members: perms.append("Timeout Members")
        
        embed.add_field(name="Key Permissions", 
                      value=", ".join(perms) if perms else "No special permissions",
                      inline=False)
        return embed

class UserModerationCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot


    @commands.slash_command(name="mod-user", description="View user info and moderation options")
    @commands.has_permissions(moderate_members=True)
    async def mod_user(self, ctx: discord.ApplicationContext, user: discord.Member):
        try:
            view = ModerationView(user, ctx.author)
            view.bot = self.bot
            view.ctx = ctx
            
            embed = await view.generate_user_embed()
            await ctx.respond(embed=embed, view=view)
            LogModeration(f"User info requested for {user.id} by {ctx.author.id}")
        except Exception as e:
            LogError(f"User info command error: {str(e)}")
            await ctx.respond(
                embed=create_mod_embed(
                    "⚠️ Error",
                    f"Failed to retrieve user information: {str(e)}",
                    'error',
                    ctx.author
                ), ephemeral=True
            )

def setup(bot: discord.Bot):
    bot.add_cog(UserModerationCog(bot))