import discord
from discord.ext import commands
import datetime
import handlers.debug as DebugHandler
import handlers.config as config
from extensions.protectionextension import create_protection_config_embed

class Protection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



    @commands.slash_command(name="setup-protectionlog", description="Set the protection log channel")
    @commands.has_permissions(administrator=True)
    async def setprotectionlogchannel(self, ctx, channel: discord.TextChannel):
        try:
            serverconfig = config.loadserverconfig()
            server_id = str(ctx.guild.id)

            serverconfig.setdefault(server_id, {})
            serverconfig[server_id]["protectionlogchannel"] = channel.id
            config.saveserverconfig(serverconfig)

            DebugHandler.LogDebug(f"Protection log set to {channel.id} in {ctx.guild.name}")

            fields = [
                ("📁 Log Channel", f"{channel.mention}\nID: `{channel.id}`", True),
                ("🔧 Configuration Type", "Protection System", True),
                ("🌐 Server Region", str(ctx.guild.region).title(), True)
            ]

            embed = await create_protection_config_embed(
                ctx=ctx,
                title="🔧 Protection Log Configured ✅",
                description=f"Successfully set up security logging in {channel.mention}",
                color=discord.Color.green(),
                fields=fields
            )
            
            await ctx.respond(embed=embed)

        except commands.BotMissingPermissions as e:
            embed = discord.Embed(
                title="⚠️ Missing Permissions",
                description=f"Could not set log channel:\n{e}",
                color=discord.Color.orange()
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            DebugHandler.LogError(f"Error setting protection log: {str(e)}")
            embed = discord.Embed(
                title="❌ Configuration Error",
                description="Failed to update protection settings",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="setup-protection", description="Enable or disable the protection system")
    @commands.has_permissions(administrator=True)
    async def antiraid(self, ctx, enabled: bool):
        try:
            serverconfig = config.loadserverconfig()
            server_id = str(ctx.guild.id)
            previous_state = serverconfig.get(server_id, {}).get("protection", False)
            
            serverconfig.setdefault(server_id, {})
            serverconfig[server_id]["protection"] = enabled
            config.saveserverconfig(serverconfig)

            DebugHandler.LogDebug(f"Protection {'enabled' if enabled else 'disabled'} in {ctx.guild.name}")

            status_icon = "✅" if enabled else "❌"
            fields = [
                ("🛡️ Previous State", "Active" if previous_state else "Inactive", True),
                ("⚡ New State", "Active" if enabled else "Inactive", True),
                ("📅 Effective Since", f"<t:{int(datetime.datetime.now().timestamp())}:R>", True)
            ]

            embed = await create_protection_config_embed(
                ctx=ctx,
                title=f"{status_icon} Protection System {'Enabled' if enabled else 'Disabled'}",
                description="Security system configuration updated",
                color=discord.Color.blue() if enabled else discord.Color.dark_gray(),
                fields=fields
            )
            
            modules_status = [
                f"{'✅' if enabled else '❌'} Anti-Raid Protection",
                f"{'✅' if enabled else '❌'} Mass Mention Detection",
                f"{'✅' if enabled else '❌'} Bot Verification System"
            ]
            embed.add_field(name="🔐 Active Modules", value="\n".join(modules_status), inline=False)
            
            await ctx.respond(embed=embed)

        except Exception as e:
            DebugHandler.LogError(f"Error toggling protection: {str(e)}")
            embed = discord.Embed(
                title="❌ Operation Failed",
                description="Could not update protection settings",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Protection(bot))