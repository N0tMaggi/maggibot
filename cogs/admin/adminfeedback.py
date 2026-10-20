# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import uuid 
from handlers.debug import LogDebug, LogError
from handlers.config import load_admin_feedback, save_admin_feedback
from utils.embed_helpers import create_embed, create_success_embed, create_error_embed, create_info_embed, create_warning_embed


class AdminFeedback(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.admin_feedback = load_admin_feedback()

    @commands.slash_command(
        name="feedback",
        description="📩 Send feedback to an administrator",
        guild_only=True
    )
    async def feedback(self, ctx: discord.ApplicationContext, admin_user: discord.Member, *, feedback: str):
        try:
            guild_id_str = str(ctx.guild.id)
            if guild_id_str in self.admin_feedback["configs"]:
                team_role_id = self.admin_feedback["configs"][guild_id_str]["team_role"]
                team_role = ctx.guild.get_role(team_role_id)
                if team_role and admin_user in team_role.members:
                    if admin_user.id != ctx.author.id:
                        current_time = discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                        dm_embed = create_embed(
                            title="📩 Neues Feedback erhalten!",
                            description=feedback,
                            color="info",
                            author=ctx.author,
                            fields=[
                                ("👤 Von", ctx.author.mention, True),
                                ("🏠 Server", ctx.guild.name, True),
                                ("📌 Channel", ctx.channel.mention, True),
                                ("⏰ Gesendet am", current_time, False)
                            ],
                            footer_text="MaggiBot Feedback-System"
                        )
                        try:
                            await admin_user.send(embed=dm_embed)
                        except discord.Forbidden:
                            await ctx.respond(
                                embed=create_error_embed("Fehler", "Der Administrator hat Direktnachrichten (DMs) deaktiviert."),
                                ephemeral=True
                            )
                            return

                        feedback_id = str(uuid.uuid4())[:8]
                        entry = {
                            "server": guild_id_str,
                            "channel": str(ctx.channel.id),
                            "time": current_time,
                            "from": str(ctx.author.id),
                            "to": str(admin_user.id),
                            "feedback": feedback
                        }
                        self.admin_feedback["feedbacks"][feedback_id] = entry
                        save_admin_feedback(self.admin_feedback)

                        resp_embed = create_success_embed(
                            "Feedback gesendet!",
                            f"Dein Feedback wurde an {admin_user.mention} übermittelt.\n**Feedback ID:** `{feedback_id}`"
                        )
                        await ctx.respond(embed=resp_embed, ephemeral=True)
                    else:
                        await ctx.respond(
                            embed=create_error_embed("Ungültig", "Du kannst dir selbst kein Feedback senden!"),
                            ephemeral=True
                        )
                else:
                    await ctx.respond(
                        embed=create_error_embed("Ungültiges Team-Mitglied", "Der ausgewählte Nutzer besitzt nicht die Team-Rolle."),
                        ephemeral=True
                    )
            else:
                await ctx.respond(
                    embed=create_warning_embed("Nicht eingerichtet", "Admin-Feedback wurde auf diesem Server noch nicht über `/setup` konfiguriert."),
                    ephemeral=True
                )
        except Exception as e:
            LogError(f"❌ Error sending feedback: {e}")
            await ctx.respond(
                embed=create_error_embed("Fehler", "Beim Senden des Feedbacks ist ein Fehler aufgetreten."),
                ephemeral=True
            )

    @commands.slash_command(
        name="view-feedbacks-from",
        description="🔍 Feedbacks eines bestimmten Nutzers anzeigen",
        guild_only=True,
        default_member_permissions=discord.Permissions(administrator=True)
    )
    @commands.has_permissions(administrator=True)
    async def view_feedbacks_from(self, ctx: discord.ApplicationContext, user: discord.Member):
        try:
            feedback_entries = [
                (fid, entry) for fid, entry in self.admin_feedback.get("feedbacks", {}).items()
                if entry.get("from") == str(user.id)
            ]
            if not feedback_entries:
                await ctx.respond(
                    embed=create_info_embed("Kein Feedback gefunden", f"Keine Feedbacks von {user.mention} vorhanden."),
                    ephemeral=True
                )
                return

            desc = []
            for fid, entry in feedback_entries[:15]:
                desc.append(
                    f"**ID:** `{fid}` | **Zeit:** `{entry.get('time', 'N/A')}`\n"
                    f"• **An:** <@{entry.get('to')}>\n"
                    f"• **Inhalt:** {entry.get('feedback')}\n"
                    f"───────────────────────────────"
                )

            embed = create_info_embed(
                f"📋 Feedbacks von {user.display_name}",
                "\n".join(desc),
                bot_user=self.bot.user
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            LogError(f"❌ Error viewing feedbacks: {e}")
            await ctx.respond(
                embed=create_error_embed("Fehler", "Fehler beim Abrufen der Feedbacks."),
                ephemeral=True
            )

    @commands.slash_command(
        name="owner-deletefeedback",
        description="🚫 (Owner Only) Feedback anhand der ID löschen"
    )
    @commands.is_owner()
    async def owner_deletefeedback(self, ctx: discord.ApplicationContext, feedback_id: str):
        try:
            if feedback_id in self.admin_feedback.get("feedbacks", {}):
                del self.admin_feedback["feedbacks"][feedback_id]
                save_admin_feedback(self.admin_feedback)
                await ctx.respond(
                    embed=create_success_embed("Gelöscht", f"Feedback `{feedback_id}` wurde erfolgreich entfernt."),
                    ephemeral=True
                )
            else:
                await ctx.respond(
                    embed=create_error_embed("Nicht gefunden", f"Kein Feedback mit der ID `{feedback_id}` gefunden."),
                    ephemeral=True
                )
        except Exception as e:
            LogError(f"❌ Error deleting feedback: {e}")
            await ctx.respond(
                embed=create_error_embed("Fehler", "Beim Löschen des Feedbacks ist ein Fehler aufgetreten."),
                ephemeral=True
            )

    @commands.slash_command(
        name="view-feedbacks",
        description="🔍 Feedbacks an einen Administrator anzeigen",
        guild_only=True,
        default_member_permissions=discord.Permissions(administrator=True)
    )
    @commands.has_permissions(administrator=True)
    async def view_feedbacks(self, ctx: discord.ApplicationContext, user: discord.Member):
        try:
            feedback_entries = [
                (fid, entry) for fid, entry in self.admin_feedback.get("feedbacks", {}).items()
                if entry.get("to") == str(user.id)
            ]
            if not feedback_entries:
                await ctx.respond(
                    embed=create_info_embed("Kein Feedback gefunden", f"Keine Feedbacks für {user.mention} vorhanden."),
                    ephemeral=True
                )
                return

            desc = []
            for fid, entry in feedback_entries[:15]:
                desc.append(
                    f"**ID:** `{fid}` | **Zeit:** `{entry.get('time', 'N/A')}`\n"
                    f"• **Von:** <@{entry.get('from')}>\n"
                    f"• **Inhalt:** {entry.get('feedback')}\n"
                    f"───────────────────────────────"
                )

            embed = create_info_embed(
                f"📋 Feedbacks für {user.display_name}",
                "\n".join(desc),
                bot_user=self.bot.user
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            LogError(f"❌ Error viewing feedbacks: {e}")
            await ctx.respond(
                embed=create_error_embed("Fehler", "Fehler beim Abrufen der Feedbacks."),
                ephemeral=True
            )


def setup(bot: discord.Bot):
    bot.add_cog(AdminFeedback(bot))
