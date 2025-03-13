import discord
from discord.ext import commands
from discord.ext.commands import Cog
import datetime
import handlers.config as config
import handlers.debug as DebugHandler

class AutoRole(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.serverconfig = config.loadserverconfig()

    @commands.slash_command(name="setup-autorole", description="Setup autorole for the server")
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
            DebugHandler.LogDebug(f"Autorole setup for guild: {guild_id} Role: {role_id}")

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
            DebugHandler.LogError(f"Error setting up autorole: {str(e)}")
            raise Exception ("Error setting up autorole") from e

    @commands.slash_command(name="delete-autorole", description="Delete autorole configuration for the server")
    @commands.has_permissions(administrator=True)
    async def delete_autorole(self, ctx: discord.ApplicationContext):
        """Delete autorole for server"""
        try:
            guild_id = str(ctx.guild.id)

            if guild_id in self.serverconfig and "autoroleid" in self.serverconfig[guild_id]:
                del self.serverconfig[guild_id]["autoroleid"]
                config.saveserverconfig(self.serverconfig)
                DebugHandler.LogDebug(f"Autorole deleted for guild: {guild_id}")

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
            DebugHandler.LogError(f"Error deleting autorole: {str(e)}")
            await ctx.respond(f"An error occurred while deleting autorole: {str(e)}", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Auto give role."""
        try:
            guild_id = str(member.guild.id)
            if guild_id not in self.serverconfig or "autoroleid" not in self.serverconfig[guild_id]:
                return

            role_id = self.serverconfig[guild_id]["autoroleid"]
            role = member.guild.get_role(role_id)
            if role:
                await member.add_roles(role)
                DebugHandler.LogDebug(f"Added autorole to {member.name} ({member.id}) in guild {guild_id}")
            else:
                DebugHandler.LogError(f"Role {role_id} not found in guild {guild_id}")
        except Exception as e:
            DebugHandler.LogError(f"Error in on_member_join autorole listener: {str(e)}")
            raise e 



def setup(bot):
    bot.add_cog(AutoRole(bot))
