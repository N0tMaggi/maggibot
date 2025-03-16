import discord
from discord.ext import commands
from discord.commands import slash_command
import datetime
import asyncio
import os
import handlers.config as cfg
from handlers.debug import LogDebug, LogError, LogNetwork, LogSystem, LogModeration

class Moderation(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.embed_colors = {
            'success': 0x2ECC71,
            'error': 0xE74C3C,
            'warning': 0xF1C40F,
            'info': 0x3498DB,
            'mod_action': 0x992D22
        }

    def create_embed(self, title, description, color_type='info', author=None):
        embed = discord.Embed(
            title=title,
            description=description,
            color=self.embed_colors.get(color_type, 0x3498DB),
            timestamp=datetime.datetime.utcnow()
        )
        if author:
            embed.set_author(name=str(author), icon_url=author.avatar.url)
        embed.set_footer(text="ModSystem | Maggi", icon_url=self.bot.user.avatar.url)
        return embed

    async def send_mod_log(self, guild_id, embed_data):
        try:
            log_channel = cfg.get_log_channel(guild_id)
            if log_channel:
                embed = self.create_embed(**embed_data)
                await log_channel.send(embed=embed)
                LogModeration(f"Log sent to channel {log_channel.id}")
            else:
                LogDebug(f"No log channel set for guild {guild_id}")
        except Exception as e:
            LogError(f"Failed to send mod log: {str(e)}")

    @commands.slash_command(name="checkperms", description="Check bot permissions")
    @commands.has_permissions(administrator=True)
    async def checkperms(self, ctx):
        try:
            initial_embed = self.create_embed(
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

            result_embed = self.create_embed(
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
                owner_embed = self.create_embed(
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
                warning_embed = self.create_embed(
                    "⚠️ Delivery Failed",
                    f"Couldn't send DM to {ctx.guild.owner.mention}",
                    'warning',
                    ctx.author
                )
                await ctx.followup.send(embed=warning_embed, ephemeral=True)
                LogError(f"Failed to DM owner {ctx.guild.owner.id}")

        except Exception as e:
            LogError(f"Checkperms error: {str(e)}")
            raise Exception(f"Permission check failed: {str(e)}")

    @commands.slash_command(name="mod-ban", description="Ban a user from the server")
    @commands.has_permissions(ban_members=True)
    async def mod_ban(self, ctx, user: discord.Member, *, reason: str = "No reason provided"):
        try:
            if user == ctx.author:
                embed = self.create_embed(
                    "❌ Self-Ban Attempt",
                    "You cannot ban yourself!",
                    'error',
                    ctx.author
                )
                await ctx.respond(embed=embed, ephemeral=True)
                LogModeration(f"Self-ban attempt by {ctx.author.id}")
                return

            # User notification
            try:
                user_embed = self.create_embed(
                    "🔨 Account Banned",
                    f"You were banned from **{ctx.guild.name}**\n**Reason:** {reason}",
                    'error'
                )
                await user.send(embed=user_embed)
                LogModeration(f"Ban notification sent to {user.id}")
            except discord.Forbidden:
                LogError(f"Failed to DM banned user {user.id}")

            # Execute ban
            try:
                await user.ban(reason=f"{ctx.author}: {reason}")
                LogModeration(f"Banned {user.id} in {ctx.guild.id}")
            except discord.Forbidden:
                embed = self.create_embed(
                    "❌ Permission Denied",
                    "I don't have permission to ban this user",
                    'error',
                    ctx.author
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # Response embed
            confirm_embed = self.create_embed(
                "✅ Ban Successful",
                f"{user.mention} has been banned",
                'success',
                ctx.author
            )
            confirm_embed.add_field(name="User ID", value=user.id)
            confirm_embed.add_field(name="Reason", value=reason)
            confirm_embed.set_thumbnail(url=user.avatar.url)
            await ctx.respond(embed=confirm_embed)

            # Log channel handling
            log_data = {
                "title": "🔨 Ban Executed",
                "description": f"**User:** {user.mention}\n**Moderator:** {ctx.author.mention}",
                "color_type": 'mod_action',
                "author": ctx.author
            }
            await self.send_mod_log(ctx.guild.id, log_data)

        except Exception as e:
            LogError(f"Ban error: {str(e)}")
            raise Exception(f"Ban operation failed: {str(e)}")

    @commands.slash_command(name="mod-kick", description="Kick a user from the server")
    @commands.has_permissions(kick_members=True)
    async def mod_kick(self, ctx, user: discord.Member, *, reason: str = "No reason provided"):
        try:
            if user == ctx.author:
                embed = self.create_embed(
                    "❌ Self-Kick Attempt",
                    "You cannot kick yourself!",
                    'error',
                    ctx.author
                )
                await ctx.respond(embed=embed, ephemeral=True)
                LogModeration(f"Self-kick attempt by {ctx.author.id}")
                return

            # User notification
            try:
                user_embed = self.create_embed(
                    "👢 Account Kicked",
                    f"You were kicked from **{ctx.guild.name}**\n**Reason:** {reason}",
                    'error'
                )
                await user.send(embed=user_embed)
                LogModeration(f"Kick notification sent to {user.id}")
            except discord.Forbidden:
                LogError(f"Failed to DM kicked user {user.id}")

            # Execute kick
            try:
                await user.kick(reason=f"{ctx.author}: {reason}")
                LogModeration(f"Kicked {user.id} in {ctx.guild.id}")
            except discord.Forbidden:
                embed = self.create_embed(
                    "❌ Permission Denied",
                    "I don't have permission to kick this user",
                    'error',
                    ctx.author
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # Response embed
            confirm_embed = self.create_embed(
                "✅ Kick Successful",
                f"{user.mention} has been kicked",
                'success',
                ctx.author
            )
            confirm_embed.add_field(name="User ID", value=user.id)
            confirm_embed.add_field(name="Reason", value=reason)
            confirm_embed.set_thumbnail(url=user.avatar.url)
            await ctx.respond(embed=confirm_embed)

            # Log channel handling
            log_data = {
                "title": "👢 Kick Executed",
                "description": f"**User:** {user.mention}\n**Moderator:** {ctx.author.mention}",
                "color_type": 'mod_action',
                "author": ctx.author
            }
            await self.send_mod_log(ctx.guild.id, log_data)

        except Exception as e:
            LogError(f"Kick error: {str(e)}")
            raise Exception(f"Kick operation failed: {str(e)}")
        
    
    @commands.slash_command(name= "purge-onlymessages", description="Purge all messages without attachments in this channel.")
    @commands.cooldown(1, 240, commands.BucketType.user)
    @commands.has_permissions(manage_messages=True)
    async def purge_onlymessages(self, ctx: discord.ApplicationContext, limit: int = 1000):
        await ctx.defer()  # Prevent timeout issues
        deleted_count = 0
        
        async for message in ctx.channel.history(limit=limit):  # Use user-defined limit
            if not message.attachments and not message.pinned:
                try:
                    await message.delete()
                    deleted_count += 1
                except discord.Forbidden:
                    continue  # Skip if the bot lacks permission
                except discord.NotFound:
                    continue  # Skip if the message is already deleted
        
        embed = discord.Embed(
            title="Purge Completed",
            description=f"🧹 Successfully deleted **{deleted_count}** messages without attachments.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Checked the last {limit} messages.")
        
        await ctx.respond(embed=embed, ephemeral=True)




def setup(bot: discord.Bot):
    bot.add_cog(Moderation(bot))