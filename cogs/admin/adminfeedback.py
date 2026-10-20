# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import uuid 
from handlers.debug import LogDebug, LogError
from handlers.config import load_admin_feedback, save_admin_feedback
from handlers.locale import t
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
                            title=t("feedback.dm_title", ctx=ctx),
                            description=feedback,
                            color="info",
                            author=ctx.author,
                            fields=[
                                (t("feedback.from_field", ctx=ctx), ctx.author.mention, True),
                                (t("feedback.server_field", ctx=ctx), ctx.guild.name, True),
                                (t("feedback.channel_field", ctx=ctx), ctx.channel.mention, True),
                                (t("feedback.sent_at_field", ctx=ctx), current_time, False)
                            ],
                            footer_text=t("feedback.footer", ctx=ctx)
                        )
                        try:
                            await admin_user.send(embed=dm_embed)
                        except discord.Forbidden:
                            await ctx.respond(
                                embed=create_error_embed(t("common.error", ctx=ctx), t("feedback.dm_disabled", ctx=ctx)),
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
                            t("feedback.sent_title", ctx=ctx),
                            t("feedback.sent_desc", ctx=ctx, admin=admin_user.mention, feedback_id=feedback_id)
                        )
                        await ctx.respond(embed=resp_embed, ephemeral=True)
                    else:
                        await ctx.respond(
                            embed=create_error_embed(t("common.error", ctx=ctx), t("feedback.self_error", ctx=ctx)),
                            ephemeral=True
                        )
                else:
                    await ctx.respond(
                        embed=create_error_embed(t("common.error", ctx=ctx), t("feedback.not_team_error", ctx=ctx)),
                        ephemeral=True
                    )
            else:
                await ctx.respond(
                    embed=create_warning_embed(t("common.warning", ctx=ctx), t("feedback.not_configured", ctx=ctx)),
                    ephemeral=True
                )
        except Exception as e:
            LogError(f"❌ Error sending feedback: {e}")
            await ctx.respond(
                embed=create_error_embed(t("common.error", ctx=ctx), t("errors.generic", ctx=ctx, command="feedback")),
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
                    embed=create_info_embed(t("feedback.none_found", ctx=ctx), t("feedback.none_found", ctx=ctx)),
                    ephemeral=True
                )
                return

            desc = []
            for fid, entry in feedback_entries[:15]:
                desc.append(
                    f"**ID:** `{fid}` | **Zeit:** `{entry.get('time', 'N/A')}`\n"
                    f"• **{t('feedback.to_field', ctx=ctx)}:** <@{entry.get('to')}>\n"
                    f"• **{t('common.details', ctx=ctx)}:** {entry.get('feedback')}\n"
                    f"───────────────────────────────"
                )

            embed = create_info_embed(
                t("feedback.view_from_title", ctx=ctx, user_name=user.display_name),
                "\n".join(desc),
                bot_user=self.bot.user
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            LogError(f"❌ Error viewing feedbacks: {e}")
            await ctx.respond(
                embed=create_error_embed(t("common.error", ctx=ctx), str(e)),
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
                    embed=create_success_embed(t("feedback.deleted_title", ctx=ctx), t("feedback.deleted", ctx=ctx, feedback_id=feedback_id)),
                    ephemeral=True
                )
            else:
                await ctx.respond(
                    embed=create_error_embed(t("common.error", ctx=ctx), f"ID `{feedback_id}` not found."),
                    ephemeral=True
                )
        except Exception as e:
            LogError(f"❌ Error deleting feedback: {e}")
            await ctx.respond(
                embed=create_error_embed(t("common.error", ctx=ctx), str(e)),
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
                    embed=create_info_embed(t("feedback.none_found", ctx=ctx), t("feedback.none_found", ctx=ctx)),
                    ephemeral=True
                )
                return

            desc = []
            for fid, entry in feedback_entries[:15]:
                desc.append(
                    f"**ID:** `{fid}` | **Zeit:** `{entry.get('time', 'N/A')}`\n"
                    f"• **{t('feedback.from_field', ctx=ctx)}:** <@{entry.get('from')}>\n"
                    f"• **{t('common.details', ctx=ctx)}:** {entry.get('feedback')}\n"
                    f"───────────────────────────────"
                )

            embed = create_info_embed(
                t("feedback.view_for_title", ctx=ctx, user_name=user.display_name),
                "\n".join(desc),
                bot_user=self.bot.user
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            LogError(f"❌ Error viewing feedbacks: {e}")
            await ctx.respond(
                embed=create_error_embed(t("common.error", ctx=ctx), str(e)),
                ephemeral=True
            )


def setup(bot: discord.Bot):
    bot.add_cog(AdminFeedback(bot))
