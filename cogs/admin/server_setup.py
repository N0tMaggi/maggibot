import discord
from discord.ext import commands
from discord.ext.commands import Cog
import datetime
import handlers.config as config
from handlers.debug import LogDebug, LogNetwork, LogSystem, LogError

async def safe_respond(ctx: discord.ApplicationContext, embed: discord.Embed):
    try:
        await ctx.respond(embed=embed, ephemeral=True)
    except Exception:
        await ctx.followup.send(embed=embed, ephemeral=True)

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

            embed = discord.Embed(
                title="📁 Log Channel Configuration",
                description=f"**Successfully configured logging system!**",
                color=0x3498DB,
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_author(
                name=f"{ctx.guild.name} Settings",
                icon_url=ctx.guild.icon.url if ctx.guild.icon else self.bot.user.avatar.url
            )
            embed.add_field(
                name="⚙️ Setting Updated",
                value=f"```diff\n+ Log Channel: #{channel.name}\n```",
                inline=False
            )
            embed.add_field(
                name="📝 Details",
                value=f"• Channel: {channel.mention}\n• ID: `{channel.id}`\n• Server: `{ctx.guild.id}`",
                inline=True
            )
            embed.set_footer(
                text=f"Configured by {ctx.author.display_name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else self.bot.user.avatar.url
            )
            await ctx.respond(embed=embed)

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
                embed_prompt = discord.Embed(
                    title="Voice Gate Setup",
                    description="Please enter the rules text within 30 seconds.",
                    color=0x3498DB
                )
                await safe_respond(ctx, embed_prompt)

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

            embed_success = discord.Embed(
                title="Success",
                description="Voice gate has been successfully set up.",
                color=0x2ECC71
            )
            await safe_respond(ctx, embed_success)

        except Exception as e:
            raise RuntimeError(f"Error in setup_voicegate command: {e}")

    @commands.has_permissions(administrator=True)
    async def setup_showvoicegatesettings(self, ctx: discord.ApplicationContext):
        try:
            if str(ctx.guild.id) not in self.voicegateconfig:
                raise ValueError("No voice gate configuration found for this server.")
            config_data = self.voicegateconfig[str(ctx.guild.id)]
            embed_settings = discord.Embed(
                title="Voice Gate Settings",
                color=0x3498DB
            )
            for key, value in config_data.items():
                embed_settings.add_field(name=key, value=str(value), inline=False)
            await safe_respond(ctx, embed_settings)
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
            embed_success = discord.Embed(
                title="Success",
                description="Voice gate configuration has been deleted.",
                color=0x2ECC71
            )
            await safe_respond(ctx, embed_success)
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

            embed = discord.Embed(
                title="Autorole Setup",
                description="Autorole has been successfully configured for this server.",
                color=0x00ff00,
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Role", value=role.mention, inline=True)
            embed.add_field(name="Guild", value=ctx.guild.name, inline=True)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            embed.set_footer(text="Autorole Setup")
            await ctx.respond(embed=embed)

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

                embed = discord.Embed(
                    title="Autorole Deleted",
                    description="Autorole configuration has been removed from this server.",
                    color=0x00ff00,
                    timestamp=datetime.datetime.utcnow()
                )
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
                embed.set_footer(text="Autorole Configuration")
                await ctx.respond(embed=embed)
            else:
                embed = discord.Embed(
                    title="No Autorole Found",
                    description="There is no autorole configuration set up for this server.",
                    color=0xff0000,
                    timestamp=datetime.datetime.utcnow()
                )
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
                embed.set_footer(text="Autorole Configuration")
                await ctx.respond(embed=embed, ephemeral=True)

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
            embed = discord.Embed(
                title="✅ Admin feedback set up!",
                description="The admin feedback system has been successfully configured.",
                color=discord.Color.green()
            )
            embed.add_field(name="👥 Team Role", value=team_role.mention, inline=False)
            embed.set_footer(text="Use /feedback to send feedback to an admin.")
            await ctx.respond(embed=embed)
        except Exception as e:
            LogError(f"❌ Error setting up admin feedback: {e}")
            raise RuntimeError("Error setting up admin feedback") from e

    @commands.has_permissions(administrator=True)
    async def setup_delete_admin_feedback(self, ctx):
        try:
            if str(ctx.guild.id) in self.admin_feedback["configs"]:
                del self.admin_feedback["configs"][str(ctx.guild.id)]
                config.save_admin_feedback(self.admin_feedback)
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
            LogError(f"❌ Error deleting admin feedback configuration: {e}")
            raise RuntimeError("Error deleting admin feedback configuration") from e


def setup(bot):
    bot.add_cog(Server(bot))