import discord
from discord.ext import commands
from discord.commands import slash_command
import datetime
import asyncio
import os
import handlers.config as cfg
from extensions.modextensions import create_mod_embed, send_mod_log
from handlers.debug import LogDebug, LogError, LogNetwork, LogSystem, LogModeration

class Moderation(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.slash_command(name="checkperms", description="Check bot permissions")
    @commands.has_permissions(administrator=True)
    async def checkperms(self, ctx):
        try:
            initial_embed = create_mod_embed(
                "🔍 Permission Scan Initialized",
                "Scanning bot permissions...",
                'info',
                ctx.author
            )
            await ctx.respond(embed=initial_embed)

            await asyncio.sleep(1.5)

            bot_perms = ctx.guild.me.guild_permissions
            required_perms = ["administrator"]
            missing_perms = [perm for perm in required_perms if not getattr(bot_perms, perm)]

            result_embed = create_mod_embed(
                "📋 Permission Check Results",
                f"**Server:** {ctx.guild.name}\n"
                f"**Scan requested by:** {ctx.author.mention}",
                'success' if not missing_perms else 'error',
                ctx.author
            )

            if missing_perms:
                result_embed.add_field(
                    name="🚨 Missing Permissions",
                    value="\n".join([f"• {perm.capitalize()}" for perm in missing_perms]),
                    inline=False
                )
                result_embed.description += "\n\n⚠️ **Warning:** Bot functionality may be limited!"
            else:
                result_embed.add_field(
                    name="✅ All Permissions Granted",
                    value="Bot has full administrative access",
                    inline=False
                )

            await ctx.interaction.edit_original_response(embed=result_embed)
            LogDebug(f"Permission check completed for {ctx.guild.id}")

            # Owner report
            try:
                owner_embed = create_mod_embed(
                    "📊 Full Permission Report",
                    f"**Server:** {ctx.guild.name}\n"
                    f"**Administrator:** {'✅ Yes' if bot_perms.administrator else '❌ No'}",
                    'info'
                )
                enabled_perms = [perm.replace('_', ' ').title() for perm, value in bot_perms if value]
                disabled_perms = [perm.replace('_', ' ').title() for perm, value in bot_perms if not value]

                owner_embed.add_field(
                    name="🟢 Enabled Permissions",
                    value=", ".join(enabled_perms) or "None",
                    inline=False
                )
                owner_embed.add_field(
                    name="🔴 Disabled Permissions",
                    value=", ".join(disabled_perms) or "None",
                    inline=False
                )

                await ctx.guild.owner.send(embed=owner_embed)
                LogModeration(f"Sent owner report to {ctx.guild.owner.id}")
            except discord.Forbidden:
                warning_embed = create_mod_embed(
                    "⚠️ Delivery Failed",
                    f"Couldn't send DM to {ctx.guild.owner.mention}",
                    'warning',
                    ctx.author
                )
                await ctx.followup.send(embed=warning_embed, ephemeral=True)
                LogError(f"Failed to DM owner {ctx.guild.owner.id}")

        except Exception as e:
            LogError(f"Checkperms error: {str(e)}")
            await ctx.followup.send(embed=create_mod_embed(
                "⚠️ Error",
                f"An error occurred while checking permissions: {str(e)}",
                'error', ctx.author), ephemeral=True)
    
    @commands.slash_command(name="purge-onlymessages", description="🧹 Purge only messages in a channel without deleting images")
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.has_permissions(manage_messages=True)
    async def purge_onlymessages(self, ctx: discord.ApplicationContext, limit: int = 1000):
        try:
            await ctx.defer(ephemeral=True)

            before = discord.utils.utcnow()

            def check(message):
                return not message.attachments and not message.pinned

            deleted = await ctx.channel.purge(
                limit=limit,
                check=check,
                bulk=True,
                before=before
            )

            deleted_count = len(deleted)
            color = discord.Color.green() if deleted_count > 0 else discord.Color.orange()
            description = (
                f"🗑️ **{deleted_count}** purged!" 
                if deleted_count > 0 
                else "❌ No deletable messages found!"
            )

            embed = discord.Embed(
                title="Channel Purged" + (" ✅" if deleted_count > 0 else " ⚠️"),
                description=description,
                color=color
            )
            embed.add_field(name="Checking Messages", value=f"`{limit}`", inline=True)
            embed.add_field(name="Pinned Ignored", value="✅", inline=True)
            embed.set_footer(text="Maggi Bot • Deletion takes about 1 Minute", icon_url=ctx.guild.icon.url)

        except discord.HTTPException as e:
            embed = discord.Embed(
                title="⚠️ Error Purge",
                description=f"API-Error: `{e}`",
                color=discord.Color.red()
            )
        except Exception as e:
            embed = discord.Embed(
                title="❌ Critical Error",
                description=f"Unexpected error: `{str(e)}`",
                color=discord.Color.dark_red()
            )

        await ctx.followup.send(embed=embed, ephemeral=True)

def setup(bot: discord.Bot):
    bot.add_cog(Moderation(bot))
