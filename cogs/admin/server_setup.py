import discord
from discord.ext import commands
from discord.ext.commands import Cog
import datetime
import handlers.config as config
from handlers.debug import LogDebug, LogNetwork, LogSystem, LogError
from utils.components import build_container, build_view

async def safe_respond(ctx: discord.ApplicationContext, container: discord.ui.Container):
    try:
        await ctx.respond(view=build_view(container), ephemeral=True)
    except Exception:
        await ctx.followup.send(view=build_view(container), ephemeral=True)

class Server(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.serverconfig = config.loadserverconfig()
        self.voicegateconfig = config.loadvoicegateconfig()
        self.pending_verifications = set() 
        self.admin_feedback = config.load_admin_feedback()



#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# LogChannel
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

    @commands.has_permissions(administrator=True)
    async def settings_logchannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        try:
            guild_id = str(ctx.guild.id)
            LogDebug(f"Current server config for guild {guild_id}: {self.serverconfig}")

            if guild_id not in self.serverconfig:
                self.serverconfig[guild_id] = {}

            self.serverconfig[guild_id]["logchannel"] = channel.id
            LogDebug(f"Updated server config for guild {guild_id}: {self.serverconfig[guild_id]}")

            config.saveserverconfig(self.serverconfig)

            container = build_container(
                title="📁 Log Channel Configuration",
                description=f"**Successfully configured logging system!**",
                color="info",
                author=ctx.guild,
                fields=[
                    ("⚙️ Setting Updated", f"```diff\n+ Log Channel: #{channel.name}\n```", False),
                    ("📝 Details", f"• Channel: {channel.mention}\n• ID: `{channel.id}`\n• Server: `{ctx.guild.id}`", True),
                ],
                footer_text=f"Configured by {ctx.author.display_name}",
                timestamp=True,
            )
            await ctx.respond(view=build_view(container))

        except Exception as e:
            LogError(f"An error occurred while setting the log channel: {e}")
            raise RuntimeError(f"An error occurred while setting the log channel: {e}")


#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# VoiceGate
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-


    @commands.has_permissions(administrator=True)
    async def setup_voicegate(
        self, 
        ctx: discord.ApplicationContext, 
        gate_channel: discord.VoiceChannel, 
        final_channel: discord.VoiceChannel, 
        need_accept_rules: bool
    ):
        try:
            rules_text = ""
            if need_accept_rules:
                prompt_container = build_container(
                    title="Voice Gate Setup",
                    description="Please enter the rules text within 30 seconds.",
                    color="info"
                )
                await safe_respond(ctx, prompt_container)

                def check(message: discord.Message):
                    return message.author == ctx.author and message.channel == ctx.channel

                try:
                    msg = await self.bot.wait_for('message', timeout=30, check=check)
                    rules_text = msg.content
                except Exception:
                    raise TimeoutError(" You did not provide the required text in time.")

            self.voicegateconfig[str(ctx.guild.id)] = {
                "gate_channel_id": gate_channel.id,
                "final_channel_id": final_channel.id,
                "need_accept_rules": need_accept_rules,
                "rules_text": rules_text
            }
            config.savevoicegateconfig(self.voicegateconfig)

            success_container = build_container(
                title="Success",
                description="Voice gate has been successfully set up.",
                color="success"
            )
            await safe_respond(ctx, success_container)

        except Exception as e:
            raise RuntimeError(f"Error in setup_voicegate command: {e}")

    @commands.has_permissions(administrator=True)
    async def setup_showvoicegatesettings(self, ctx: discord.ApplicationContext):
        try:
            if str(ctx.guild.id) not in self.voicegateconfig:
                raise ValueError("No voice gate configuration found for this server.")
            config_data = self.voicegateconfig[str(ctx.guild.id)]
            fields = []
            for key, value in config_data.items():
                fields.append((key, str(value), False))

            settings_container = build_container(
                title="Voice Gate Settings",
                color="info",
                fields=fields
            )
            await safe_respond(ctx, settings_container)
        except Exception as e:
            raise RuntimeError(f"Error in setup-showvoicegatesettings command: {e}")

    @commands.has_permissions(administrator=True)
    async def setup_deletevoicegate(self, ctx: discord.ApplicationContext, gate_channel: discord.VoiceChannel):
        try:
            if str(ctx.guild.id) not in self.voicegateconfig:
                raise ValueError("No voice gate configuration found for this server.")
            config_data = self.voicegateconfig[str(ctx.guild.id)]
            if config_data.get("gate_channel_id") != gate_channel.id:
                raise ValueError("The provided voice channel does not match the stored configuration.")
            del self.voicegateconfig[str(ctx.guild.id)]
            config.savevoicegateconfig(self.voicegateconfig)
            success_container = build_container(
                title="Success",
                description="Voice gate configuration has been deleted.",
                color="success"
            )
            await safe_respond(ctx, success_container)
        except Exception as e:
            raise RuntimeError(f"[VOICEGATE] Error in setup-deletevoicegate command: {e}")



#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# AutoRole
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-



    @commands.has_permissions(administrator=True)
    async def setup_autorole(self, ctx: discord.ApplicationContext, role: discord.Role):
        """Setup autorole for server"""
        try:
            guild_id = str(ctx.guild.id)
            role_id = role.id

            if guild_id not in self.serverconfig:
                self.serverconfig[guild_id] = {}

            self.serverconfig[guild_id]["autoroleid"] = role_id
            config.saveserverconfig(self.serverconfig)
            LogDebug(f"Autorole setup for guild: {guild_id} Role: {role_id}")

            container = build_container(
                title="Autorole Setup",
                description="Autorole has been successfully configured for this server.",
                color="success",
                author=ctx.author,
                fields=[
                    ("Role", role.mention, True),
                    ("Guild", ctx.guild.name, True),
                ],
                footer_text="Autorole Setup",
            )
            await ctx.respond(view=build_view(container))

        except Exception as e:
            LogError(f"Error setting up autorole: {str(e)}")
            raise RuntimeError("Error setting up autorole") from e

    @commands.has_permissions(administrator=True)
    async def setup_deleteautorole(self, ctx: discord.ApplicationContext):
        """Delete autorole for server"""
        try:
            guild_id = str(ctx.guild.id)

            if guild_id in self.serverconfig and "autoroleid" in self.serverconfig[guild_id]:
                del self.serverconfig[guild_id]["autoroleid"]
                config.saveserverconfig(self.serverconfig)
                LogDebug(f"Autorole deleted for guild: {guild_id}")

                container = build_container(
                    title="Autorole Deleted",
                    description="Autorole configuration has been removed from this server.",
                    color="success",
                    author=ctx.author,
                    footer_text="Autorole Configuration",
                )
                await ctx.respond(view=build_view(container))
            else:
                container = build_container(
                    title="No Autorole Found",
                    description="There is no autorole configuration set up for this server.",
                    color="error",
                    author=ctx.author,
                    footer_text="Autorole Configuration",
                )
                await ctx.respond(view=build_view(container), ephemeral=True)

        except Exception as e:
            LogError(f"Error deleting autorole: {str(e)}")
            raise RuntimeError("Error deleting autorole") from e

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#AdminFeedback
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

    @commands.has_permissions(administrator=True)
    async def setup_admin_feedback(self, ctx, team_role: discord.Role):
        try:
            self.admin_feedback["configs"][str(ctx.guild.id)] = {"team_role": team_role.id}
            config.save_admin_feedback(self.admin_feedback)
            container = build_container(
                title="✅ Admin feedback set up!",
                description="The admin feedback system has been successfully configured.",
                color="success",
                fields=[("👥 Team Role", team_role.mention, False)],
                footer_text="Use /feedback to send feedback to an admin."
            )
            await ctx.respond(view=build_view(container))
        except Exception as e:
            LogError(f"❌ Error setting up admin feedback: {e}")
            raise RuntimeError("Error setting up admin feedback") from e

    @commands.has_permissions(administrator=True)
    async def setup_delete_admin_feedback(self, ctx):
        try:
            if str(ctx.guild.id) in self.admin_feedback["configs"]:
                del self.admin_feedback["configs"][str(ctx.guild.id)]
                config.save_admin_feedback(self.admin_feedback)
                container = build_container(
                    title="🗑 Admin feedback deleted!",
                    description="The admin feedback configuration has been removed.",
                    color="success"
                )
            else:
                container = build_container(
                    title="⚠️ No configuration found!",
                    description="There is no stored admin feedback configuration for this server.",
                    color="warning"
                )
            await ctx.respond(view=build_view(container))
        except Exception as e:
            LogError(f"❌ Error deleting admin feedback configuration: {e}")
            raise RuntimeError("Error deleting admin feedback configuration") from e


def setup(bot):
    bot.add_cog(Server(bot))
