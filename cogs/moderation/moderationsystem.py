import discord
from discord.ext import commands
from discord.ui import ActionRow, Button, button
import datetime
import asyncio
from dateutil.parser import parse as parse_duration

import handlers.config as cfg
from extensions.modextensions import create_mod_embed, send_mod_log
from handlers.debug import LogDebug, LogError, LogModeration
from utils.components import build_container, build_view

class ModerationView:
    def __init__(self, user: discord.Member, moderator: discord.Member):
        self.user = user
        self.moderator = moderator
        self.ctx = None
        self.bot = None
        self.rows = []
        self.designer_view = None

    def set_panel(self, designer_view: discord.ui.DesignerView, rows):
        self.designer_view = designer_view
        self.rows = rows

    def disable_rows(self):
        for row in self.rows:
            for child in row.children:
                child.disabled = True

    async def refresh_info(self, interaction: discord.Interaction):
        new_container = await self.generate_user_embed()
        row_one = ModerationPrimaryRow(self)
        row_two = ModerationSecondaryRow(self)
        row_three = ModerationCloseRow(self)
        new_view = build_view(new_container, row_one, row_two, row_three, timeout=60)
        self.set_panel(new_view, [row_one, row_two, row_three])
        await interaction.response.edit_message(view=new_view)

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
            embed = create_mod_embed(
                "❌ Permission Denied",
                f"You need `{required_perms.replace('_', ' ').title()}` permission",
                'error',
                interaction.user
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(view=build_view(embed), ephemeral=True)
            else:
                await interaction.followup.send(view=build_view(embed), ephemeral=True)
            return

        duration = None
        duration_text = None
        if action_type == "timeout":
            timeout_embed = create_mod_embed(
                "⏱️ Timeout Duration",
                "Enter duration (e.g., '1h 30m')",
                'info',
                interaction.user
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(view=build_view(timeout_embed), ephemeral=True)
            else:
                await interaction.followup.send(view=build_view(timeout_embed), ephemeral=True)
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
            'info',
            interaction.user
        )
        if not interaction.response.is_done():
            await interaction.response.send_message(view=build_view(reason_embed), ephemeral=True)
        else:
            await interaction.followup.send(view=build_view(reason_embed), ephemeral=True)
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
            dm_embed = create_mod_embed("Moderation Notice", dm_description, "info", self.moderator)
            await self.user.send(view=build_view(dm_embed))
        except Exception as e:
            LogError(f"Failed to send DM to user {self.user.id}: {e}")

        try:
            if action_type == "ban":
                if self.user.guild_permissions.administrator:
                    safety_embed = create_mod_embed(
                        "❌ Safety Lock",
                        "Cannot ban server administrators",
                        'error'
                    )
                    await interaction.followup.send(view=build_view(safety_embed), ephemeral=True)
                    return
                await self.user.ban(reason=f"{self.moderator}: {reason}")
            elif action_type == "kick":
                await self.user.kick(reason=f"{self.moderator}: {reason}")
            elif action_type == "timeout":
                await self.user.timeout(duration, reason=reason)
            elif action_type == "warn":
                LogModeration(f"Warned {self.user.id} by {self.moderator.id}: {reason}")

            success_embed = create_mod_embed(
                f"✅ {action_type.title()} Successful",
                f"{self.user.mention} has been {action_text}",
                'success',
                self.moderator
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(view=build_view(success_embed), ephemeral=True)
            else:
                await interaction.followup.send(view=build_view(success_embed), ephemeral=True)

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
            error_embed = create_mod_embed(
                "⚠️ Error",
                f"Action failed: {str(e)}",
                'error',
                interaction.user
            )
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(view=build_view(error_embed), ephemeral=True)
                else:
                    await interaction.followup.send(view=build_view(error_embed), ephemeral=True)
            except discord.errors.NotFound:
                LogError("Webhook not found while sending error message.")

    async def show_history(self, interaction: discord.Interaction):
        history_embed = create_mod_embed(
            "📚 Moderation History",
            f"**User:** {self.user.mention}\nNo recent actions found",
            'info'
        )
        await interaction.response.send_message(view=build_view(history_embed), ephemeral=True)

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
            if self.user.guild_permissions.manage_messages:
                perms.append("Manage Messages")
            if self.user.guild_permissions.ban_members:
                perms.append("Ban Members")
            if self.user.guild_permissions.kick_members:
                perms.append("Kick Members")
            if self.user.guild_permissions.moderate_members:
                perms.append("Timeout Members")

        return build_container(
            title=f"User Information: {self.user}",
            description=f"{status} **Status:** {self.user.status}",
            color='info',
            thumbnail=self.user.display_avatar.url,
            fields=[
                ("User ID", str(self.user.id), False),
                ("Nickname", self.user.nick or "None", True),
                ("Bot Account", "Yes" if self.user.bot else "No", True),
                ("Pending Verification", "Yes" if self.user.pending else "No", True),
                ("Joined Server", f"<t:{int(self.user.joined_at.timestamp())}:R>", False),
                ("Account Created", f"<t:{int(self.user.created_at.timestamp())}:R>", False),
                (f"Roles ({len(roles)})", ", ".join(roles) if roles else "None", False),
                ("Key Permissions", ", ".join(perms) if perms else "No special permissions", False),
            ],
            timestamp=True,
            bot_user=self.bot.user,
        )


class ModerationPrimaryRow(ActionRow):
    def __init__(self, panel: ModerationView):
        super().__init__()
        self.panel = panel

    @button(label="Ban", style=discord.ButtonStyle.red, emoji="🔨")
    async def ban_button(self, button: Button, interaction: discord.Interaction):
        await self.panel.handle_action(interaction, "ban")

    @button(label="Kick", style=discord.ButtonStyle.primary, emoji="⚠️")
    async def kick_button(self, button: Button, interaction: discord.Interaction):
        await self.panel.handle_action(interaction, "kick")

    @button(label="Timeout", style=discord.ButtonStyle.grey, emoji="🔇")
    async def timeout_button(self, button: Button, interaction: discord.Interaction):
        await self.panel.handle_action(interaction, "timeout")


class ModerationSecondaryRow(ActionRow):
    def __init__(self, panel: ModerationView):
        super().__init__()
        self.panel = panel

    @button(label="Warn", style=discord.ButtonStyle.primary, emoji="⚠️")
    async def warn_button(self, button: Button, interaction: discord.Interaction):
        await self.panel.handle_action(interaction, "warn")

    @button(label="History", style=discord.ButtonStyle.secondary, emoji="📚")
    async def history_button(self, button: Button, interaction: discord.Interaction):
        await self.panel.show_history(interaction)

    @button(label="Refresh", style=discord.ButtonStyle.grey, emoji="🔄")
    async def refresh_button(self, button: Button, interaction: discord.Interaction):
        await self.panel.refresh_info(interaction)


class ModerationCloseRow(ActionRow):
    def __init__(self, panel: ModerationView):
        super().__init__()
        self.panel = panel

    @button(label="Close", style=discord.ButtonStyle.red, emoji="✖️")
    async def close_button(self, button: Button, interaction: discord.Interaction):
        self.panel.disable_rows()
        await interaction.response.edit_message(view=self.panel.designer_view)
        if self.panel.designer_view:
            self.panel.designer_view.stop()

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

            container = await view.generate_user_embed()
            row_one = ModerationPrimaryRow(view)
            row_two = ModerationSecondaryRow(view)
            row_three = ModerationCloseRow(view)
            designer_view = build_view(container, row_one, row_two, row_three, timeout=60)
            view.set_panel(designer_view, [row_one, row_two, row_three])

            await ctx.respond(view=designer_view)
            LogModeration(f"User info requested for {user.id} by {ctx.author.id}")
        except Exception as e:
            LogError(f"User info command error: {str(e)}")
            error_embed = create_mod_embed(
                "⚠️ Error",
                f"Failed to retrieve user information: {str(e)}",
                'error',
                ctx.author
            )
            await ctx.respond(view=build_view(error_embed), ephemeral=True)

def setup(bot: discord.Bot):
    bot.add_cog(UserModerationCog(bot))
