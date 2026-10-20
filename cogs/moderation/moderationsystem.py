import discord
from discord.ext import commands
from discord.ui import View, Button, button
import datetime
import asyncio
from dateutil.parser import parse as parse_duration

import handlers.config as cfg
from extensions.modextensions import send_mod_log
from utils.embed_helpers import (
    create_embed,
    create_mod_embed,
    create_security_embed,
    create_success_embed,
    create_error_embed,
    create_warning_embed,
)
from handlers.debug import LogDebug, LogError, LogModeration

class ModerationView(View):
    def __init__(self, user: discord.Member, moderator: discord.Member):
        super().__init__(timeout=60)
        self.user = user
        self.moderator = moderator
        self.ctx = None
        self.bot = None

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
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        self.stop()

    async def handle_action(self, interaction: discord.Interaction, action_type: str):
        if not self.ctx:
            if not interaction.response.is_done():
                await interaction.response.send_message("Context not found", ephemeral=True)
            else:
                await interaction.followup.send("Context not found", ephemeral=True)
            return

        required_perms = {
            "ban": "ban_members",
            "kick": "kick_members",
            "timeout": "moderate_members",
            "warn": "moderate_members"
        }.get(action_type)

        if not getattr(interaction.user.guild_permissions, required_perms):
            embed = create_error_embed(
                "Permission Denied",
                f"You need `{required_perms.replace('_', ' ').title()}` permission",
                author=interaction.user
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
            return

        duration = None
        duration_text = None
        if action_type == "timeout":
            timeout_embed = create_mod_embed(
                "⏱️ Timeout Duration",
                "Enter duration (e.g., '1h 30m')",
                color_type='info',
                author=interaction.user
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=timeout_embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=timeout_embed, ephemeral=True)
            try:
                msg = await self.bot.wait_for(
                    'message',
                    check=lambda m: m.author == interaction.user and m.channel == self.ctx.channel,
                    timeout=60
                )
                duration = parse_duration(msg.content)
                duration_text = msg.content  
                await msg.delete()
            except asyncio.TimeoutError:
                await interaction.followup.send("Duration input timed out", ephemeral=True)
                return

        reason_embed = create_mod_embed(
            "📝 Enter Reason",
            "Please type the reason for this action in the chat",
            color_type='info',
            author=interaction.user
        )
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=reason_embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=reason_embed, ephemeral=True)
        try:
            msg = await self.bot.wait_for(
                'message',
                check=lambda m: m.author == interaction.user and m.channel == self.ctx.channel,
                timeout=60
            )
            reason = msg.content
            await msg.delete()
        except asyncio.TimeoutError:
            await interaction.followup.send("Reason input timed out", ephemeral=True)
            return

        if action_type == "ban":
            action_text = "banned"
        elif action_type == "kick":
            action_text = "kicked"
        elif action_type == "timeout":
            action_text = f"timed out for {duration_text}"
        elif action_type == "warn":
            action_text = "warned"
        else:
            action_text = action_type

        try:
            dm_description = f"You have been {action_text} for the following reason: {reason}."
            dm_embed = create_mod_embed("Moderation Notice", dm_description, color_type="info", author=self.moderator)
            await self.user.send(embed=dm_embed)
        except Exception as e:
            LogError(f"Failed to send DM to user {self.user.id}: {e}")

        try:
            if action_type == "ban":
                if self.user.guild_permissions.administrator:
                    safety_embed = create_error_embed(
                        "Safety Lock",
                        "Cannot ban server administrators",
                        author=interaction.user
                    )
                    await interaction.followup.send(embed=safety_embed, ephemeral=True)
                    return
                await self.user.ban(reason=f"{self.moderator}: {reason}")
            elif action_type == "kick":
                await self.user.kick(reason=f"{self.moderator}: {reason}")
            elif action_type == "timeout":
                await self.user.timeout(duration, reason=reason)
            elif action_type == "warn":
                LogModeration(f"Warned {self.user.id} by {self.moderator.id}: {reason}")

            success_embed = create_success_embed(
                f"{action_type.title()} Successful",
                f"{self.user.mention} has been {action_text}",
                author=self.moderator
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=success_embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=success_embed, ephemeral=True)

            log_data = {
                "title": "Moderation Action",
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
            error_embed = create_error_embed(
                "Error",
                f"Action failed: {str(e)}",
                author=interaction.user
            )
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
                else:
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
            except discord.errors.NotFound:
                LogError("Webhook not found while sending error message.")

    async def show_history(self, interaction: discord.Interaction):
        history_embed = create_mod_embed(
            "📚 Moderation History",
            f"**User:** {self.user.mention}\nNo recent actions found",
            color_type='info',
            author=interaction.user
        )
        await interaction.response.send_message(embed=history_embed, ephemeral=True)

    async def refresh_info(self, interaction: discord.Interaction):
        new_embed = await self.generate_user_embed()
        await interaction.message.edit(embed=new_embed)
        await interaction.response.defer()

    async def generate_user_embed(self):
        status_emojis = {
            'online': '🟢',
            'idle': '🌙',
            'dnd': '⛔',
            'offline': '⚪'
        }
        status = status_emojis.get(str(self.user.status), '⚪')
        
        roles = [role.mention for role in self.user.roles[1:]]
        
        perms = []
        if self.user.guild_permissions.administrator:
            perms.append("Administrator")
        else:
            if self.user.guild_permissions.manage_messages: perms.append("Manage Messages")
            if self.user.guild_permissions.ban_members: perms.append("Ban Members")
            if self.user.guild_permissions.kick_members: perms.append("Kick Members")
            if self.user.guild_permissions.moderate_members: perms.append("Timeout Members")
        
        fields = [
            ("User ID", str(self.user.id), False),
            ("Nickname", self.user.nick or "None", True),
            ("Bot Account", "Yes" if self.user.bot else "No", True),
            ("Pending Verification", "Yes" if self.user.pending else "No", True),
            ("Joined Server", f"<t:{int(self.user.joined_at.timestamp())}:R>", True),
            ("Account Created", f"<t:{int(self.user.created_at.timestamp())}:R>", True),
            (f"Roles ({len(roles)})", ", ".join(roles) if roles else "None", False),
            ("Key Permissions", ", ".join(perms) if perms else "No special permissions", False),
        ]

        embed = create_embed(
            title=f"User Information: {self.user}",
            description=f"{status} **Status:** {self.user.status}",
            color='info',
            thumbnail=self.user.display_avatar.url,
            footer_text="Maggi Moderation",
            bot_user=self.bot.user if self.bot else None,
            fields=fields
        )
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
            error_embed = create_error_embed(
                "Error",
                f"Failed to retrieve user information: {str(e)}",
                author=ctx.author
            )
            await ctx.respond(embed=error_embed, ephemeral=True)

def setup(bot: discord.Bot):
    bot.add_cog(UserModerationCog(bot))
