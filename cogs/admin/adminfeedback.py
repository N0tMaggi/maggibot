import discord
from discord.ext import commands
import json
import os
import datetime
import uuid 
import handlers.debug as DH
ADMINFEEDBACKFILE = "data/adminfeedback.json"

def load_admin_feedback():
    try:
        if not os.path.exists(ADMINFEEDBACKFILE):
            data = {"configs": {}, "feedbacks": {}}
            with open(ADMINFEEDBACKFILE, "w") as f:
                json.dump(data, f, indent=4)
            return data
        else:
            with open(ADMINFEEDBACKFILE, "r") as f:
                data = json.load(f)
                if "configs" not in data:
                    data["configs"] = {}
                if "feedbacks" not in data:
                    data["feedbacks"] = {}
                return data
    except Exception as e:
        DH.LogError(f"❌ Error loading admin feedback: {e}")
        return {"configs": {}, "feedbacks": {}}

def save_admin_feedback(data):
    try:
        with open(ADMINFEEDBACKFILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        DH.LogError(f"❌ Error saving admin feedback: {e}")

class AdminFeedback(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admin_feedback = load_admin_feedback()

    @commands.slash_command(name="setup-adminfeedback", description="🔧 Set up admin feedback")
    @commands.has_permissions(administrator=True)
    async def setup_admin_feedback(self, ctx, team_role: discord.Role):
        try:
            self.admin_feedback["configs"][str(ctx.guild.id)] = {"team_role": team_role.id}
            save_admin_feedback(self.admin_feedback)
            embed = discord.Embed(
                title="✅ Admin feedback set up!",
                description="The admin feedback system has been successfully configured.",
                color=discord.Color.green()
            )
            embed.add_field(name="👥 Team Role", value=team_role.mention, inline=False)
            embed.set_footer(text="Use /feedback to send feedback to an admin.")
            await ctx.respond(embed=embed)
        except Exception as e:
            DH.LogError(f"❌ Error setting up admin feedback: {e}")
            await ctx.respond(embed=discord.Embed(
                title="❌ Error",
                description="An error occurred while setting up.",
                color=discord.Color.red()
            ))

    @commands.slash_command(name="setup-deleteadminfeedback", description="🗑 Remove the admin feedback system")
    @commands.has_permissions(administrator=True)
    async def setup_delete_admin_feedback(self, ctx):
        try:
            if str(ctx.guild.id) in self.admin_feedback["configs"]:
                del self.admin_feedback["configs"][str(ctx.guild.id)]
                save_admin_feedback(self.admin_feedback)
                embed = discord.Embed(
                    title="🗑 Admin feedback deleted!",
                    description="The admin feedback configuration has been removed.",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="⚠️ No configuration found!",
                    description="There is no stored admin feedback configuration for this server.",
                    color=discord.Color.orange()
                )
            await ctx.respond(embed=embed)
        except Exception as e:
            DH.LogError(f"❌ Error deleting admin feedback configuration: {e}")
            await ctx.respond(embed=discord.Embed(
                title="❌ Error",
                description="An error occurred while deleting.",
                color=discord.Color.red()
            ))

    @commands.slash_command(name="feedback", description="📩 Send feedback to an admin")
    async def feedback(self, ctx, admin_user: discord.Member, *, feedback: str):
        try:
            if str(ctx.guild.id) in self.admin_feedback["configs"]:
                team_role = ctx.guild.get_role(self.admin_feedback["configs"][str(ctx.guild.id)]["team_role"])
                if admin_user in team_role.members:
                    if admin_user.id != ctx.author.id:
                        embed = discord.Embed(
                            title="📩 New feedback received!",
                            description=feedback,
                            color=discord.Color.blue()
                        )
                        embed.add_field(name="👤 From", value=ctx.author.mention, inline=False)
                        embed.add_field(name="🏠 Server", value=ctx.guild.name, inline=False)
                        embed.add_field(name="📌 Channel", value=ctx.channel.mention, inline=False)
                        current_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                        embed.add_field(name="⏰ Time", value=current_time, inline=False)
                        embed.set_footer(text="Feedback system by Maggi Bot")
                        await admin_user.send(embed=embed)

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

                        embed_response = discord.Embed(
                            title="✅ Feedback sent!",
                            description=f"Your feedback has been sent to {admin_user.mention}.\nFeedback ID: `{feedback_id}`",
                            color=discord.Color.green()
                        )
                        embed_response.set_footer(text="Thank you for your feedback!")
                        await ctx.respond(embed=embed_response)
                    else:
                        await ctx.respond(embed=discord.Embed(
                            title="❌ Error",
                            description="You cannot send feedback to yourself!",
                            color=discord.Color.red()
                        ))
                else:
                    await ctx.respond(embed=discord.Embed(
                        title="❌ Error",
                        description="The selected admin is not part of the team role.",
                        color=discord.Color.red()
                    ))
            else:
                await ctx.respond(embed=discord.Embed(
                    title="❌ Error",
                    description="Admin feedback has not been set up on this server yet!",
                    color=discord.Color.red()
                ))
        except Exception as e:
            DH.LogError(f"❌ Error sending feedback: {e}")
            await ctx.respond(embed=discord.Embed(
                title="❌ Error",
                description="An error occurred while sending your feedback.",
                color=discord.Color.red()
            ))
            raise Exception(f"❌ Error sending feedback: {e}")

    @commands.slash_command(name="view-feedbacks-from", description="🔍 View feedbacks from a specific user across all servers")
    async def view_feedbacks_from(self, ctx, user: discord.Member):
        try:
            feedback_entries = []
            for fid, entry in self.admin_feedback["feedbacks"].items():
                if entry["from"] == str(user.id):
                    feedback_entries.append((fid, entry))
            if not feedback_entries:
                await ctx.respond(embed=discord.Embed(
                    title="ℹ️ No Feedback Found",
                    description=f"No feedbacks found from {user.mention}.",
                    color=discord.Color.orange()
                ))
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
            embed = discord.Embed(
                title=f"📋 Feedbacks from {user}",
                description=description,
                color=discord.Color.blue()
            )
            await ctx.respond(embed=embed)
        except Exception as e:
            DH.LogError(f"❌ Error viewing feedbacks: {e}")
            await ctx.respond(embed=discord.Embed(
                title="❌ Error",
                description="An error occurred while retrieving feedbacks.",
                color=discord.Color.red()
            ))

    @commands.slash_command(name="owner-deletefeedback", description="🚫 (Owner Only) Delete a feedback by its ID")
    @commands.is_owner()
    async def owner_deletefeedback(self, ctx, feedback_id: str):
        try:
            if feedback_id in self.admin_feedback["feedbacks"]:
                del self.admin_feedback["feedbacks"][feedback_id]
                save_admin_feedback(self.admin_feedback)
                embed = discord.Embed(
                    title="✅ Feedback Deleted",
                    description=f"Feedback with ID `{feedback_id}` has been deleted.",
                    color=discord.Color.green()
                )
                await ctx.respond(embed=embed)
            else:
                await ctx.respond(embed=discord.Embed(
                    title="❌ Error",
                    description=f"No feedback found with ID `{feedback_id}`.",
                    color=discord.Color.red()
                ))
        except Exception as e:
            DH.LogError(f"❌ Error deleting feedback: {e}")
            await ctx.respond(embed=discord.Embed(
                title="❌ Error",
                description="An error occurred while deleting the feedback.",
                color=discord.Color.red()
            ))

    @commands.slash_command(name="view-feedbacks", description="🔍 View feedbacks from a specific user across all servers")
    async def view_feedbacks(self, ctx, user: discord.Member):
        try:
            feedback_entries = []
            for fid, entry in self.admin_feedback["feedbacks"].items():
                if entry["to"] == str(user.id):
                    feedback_entries.append((fid, entry))
            if not feedback_entries:
                await ctx.respond(embed=discord.Embed(
                    title="ℹ️ No Feedback Found",
                    description=f"No feedbacks found for {user.mention}.",
                    color=discord.Color.orange()
                ))
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
            embed = discord.Embed(
                title=f"📋 Feedbacks from {user}",
                description=description,
                color=discord.Color.blue()
            )
            await ctx.respond(embed=embed)
        except Exception as e:
            DH.LogError(f"❌ Error viewing feedbacks: {e}")
            await ctx.respond(embed=discord.Embed(
                title="❌ Error",
                description="An error occurred while retrieving feedbacks.",
                color=discord.Color.red()
            ))

def setup(bot):
    bot.add_cog(AdminFeedback(bot))
