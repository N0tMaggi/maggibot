import discord
from discord.ext import commands
import json
import os
import datetime
import uuid 
from handlers.debug import LogDebug, LogError, LogSystem
from handlers.config import load_admin_feedback, save_admin_feedback
from utils.components import build_container, build_view
class AdminFeedback(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admin_feedback = load_admin_feedback()


    @commands.slash_command(name="feedback", description="📩 Send feedback to an admin")
    async def feedback(self, ctx, admin_user: discord.Member, *, feedback: str):
        try:
            if str(ctx.guild.id) in self.admin_feedback["configs"]:
                team_role = ctx.guild.get_role(self.admin_feedback["configs"][str(ctx.guild.id)]["team_role"])
                if admin_user in team_role.members:
                    if admin_user.id != ctx.author.id:
                        current_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                        container = build_container(
                            title="📩 New feedback received!",
                            description=feedback,
                            color="info",
                            fields=[
                                ("👤 From", ctx.author.mention, False),
                                ("🏠 Server", ctx.guild.name, False),
                                ("📌 Channel", ctx.channel.mention, False),
                                ("⏰ Time", current_time, False),
                            ],
                            footer_text="Feedback system by Maggi Bot"
                        )
                        await admin_user.send(view=build_view(container))

                        feedback_id = str(uuid.uuid4())
                        entry = {
                            "server": str(ctx.guild.id),
                            "channel": str(ctx.channel.id),
                            "time": current_time,
                            "from": str(ctx.author.id),
                            "to": str(admin_user.id),
                            "feedback": feedback
                        }
                        self.admin_feedback["feedbacks"][feedback_id] = entry
                        save_admin_feedback(self.admin_feedback)

                        container_response = build_container(
                            title="✅ Feedback sent!",
                            description=f"Your feedback has been sent to {admin_user.mention}.\nFeedback ID: `{feedback_id}`",
                            color="success",
                            footer_text="Thank you for your feedback!"
                        )
                        await ctx.respond(view=build_view(container_response))
                    else:
                        await ctx.respond(view=build_view(build_container(
                            title="❌ Error",
                            description="You cannot send feedback to yourself!",
                            color="error"
                        )))
                else:
                    await ctx.respond(view=build_view(build_container(
                        title="❌ Error",
                        description="The selected admin is not part of the team role.",
                        color="error"
                    )))
            else:
                await ctx.respond(view=build_view(build_container(
                    title="❌ Error",
                    description="Admin feedback has not been set up on this server yet!",
                    color="error"
                )))
        except Exception as e:
            LogError(f"❌ Error sending feedback: {e}")
            await ctx.respond(view=build_view(build_container(
                title="❌ Error",
                description="An error occurred while sending your feedback.",
                color="error"
            )))
            raise RuntimeError(f"❌ Error sending feedback: {e}")

    @commands.slash_command(name="view-feedbacks-from", description="🔍 View feedbacks from a specific user across all servers")
    async def view_feedbacks_from(self, ctx, user: discord.Member):
        try:
            feedback_entries = []
            for fid, entry in self.admin_feedback["feedbacks"].items():
                if entry["from"] == str(user.id):
                    feedback_entries.append((fid, entry))
            if not feedback_entries:
                await ctx.respond(view=build_view(build_container(
                    title="ℹ️ No Feedback Found",
                    description=f"No feedbacks found from {user.mention}.",
                    color="warning"
                )))
                return
            description = ""
            for fid, entry in feedback_entries:
                description += (f"**ID:** `{fid}`\n"
                                f"**Server:** <@{entry['server']}>\n"
                                f"**Channel:** <#{entry['channel']}>\n"
                                f"**Time:** {entry['time']}\n"
                                f"**To:** <@{entry['to']}>\n"
                                f"**Feedback:** {entry['feedback']}\n"
                                "——————————————\n")
            container = build_container(
                title=f"📋 Feedbacks from {user}",
                description=description,
                color="info"
            )
            await ctx.respond(view=build_view(container))
        except Exception as e:
            LogError(f"❌ Error viewing feedbacks: {e}")
            await ctx.respond(view=build_view(build_container(
                title="❌ Error",
                description="An error occurred while retrieving feedbacks.",
                color="error"
            )))

    @commands.slash_command(name="owner-deletefeedback", description="🚫 (Owner Only) Delete a feedback by its ID")
    @commands.is_owner()
    async def owner_deletefeedback(self, ctx, feedback_id: str):
        try:
            if feedback_id in self.admin_feedback["feedbacks"]:
                del self.admin_feedback["feedbacks"][feedback_id]
                save_admin_feedback(self.admin_feedback)
                container = build_container(
                    title="✅ Feedback Deleted",
                    description=f"Feedback with ID `{feedback_id}` has been deleted.",
                    color="success"
                )
                await ctx.respond(view=build_view(container))
            else:
                await ctx.respond(view=build_view(build_container(
                    title="❌ Error",
                    description=f"No feedback found with ID `{feedback_id}`.",
                    color="error"
                )))
        except Exception as e:
            LogError(f"❌ Error deleting feedback: {e}")
            await ctx.respond(view=build_view(build_container(
                title="❌ Error",
                description="An error occurred while deleting the feedback.",
                color="error"
            )))

    @commands.slash_command(name="view-feedbacks", description="🔍 View feedbacks from a specific user across all servers")
    async def view_feedbacks(self, ctx, user: discord.Member):
        try:
            feedback_entries = []
            for fid, entry in self.admin_feedback["feedbacks"].items():
                if entry["to"] == str(user.id):
                    feedback_entries.append((fid, entry))
            if not feedback_entries:
                await ctx.respond(view=build_view(build_container(
                    title="ℹ️ No Feedback Found",
                    description=f"No feedbacks found for {user.mention}.",
                    color="warning"
                )))
                return
            description = ""
            for fid, entry in feedback_entries:
                description += (f"**ID:** `{fid}`\n"
                                f"**Server:** <@{entry['server']}>\n"
                                f"**Channel:** <#{entry['channel']}>\n"
                                f"**Time:** {entry['time']}\n"
                                f"**To:** <@{entry['to']}>\n"
                                f"**From :** <@{entry['from']}>\n"
                                f"**Feedback:** {entry['feedback']}\n"
                                "——————————————\n")
            container = build_container(
                title=f"📋 Feedbacks from {user}",
                description=description,
                color="info"
            )
            await ctx.respond(view=build_view(container))
        except Exception as e:
            LogError(f"❌ Error viewing feedbacks: {e}")
            await ctx.respond(view=build_view(build_container(
                title="❌ Error",
                description="An error occurred while retrieving feedbacks.",
                color="error"
            )))

def setup(bot):
    bot.add_cog(AdminFeedback(bot))
