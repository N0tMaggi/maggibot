import discord
from discord.ext import commands
import json
import datetime
from handlers.debug import LogDebug, LogError
import handlers.config as config
from extensions.protectionextension import create_antibot_protection_embed

class Antibot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_member_join(self, member):
        serverconfig = config.loadserverconfig()
        serverconfig[str(member.guild.id)] = serverconfig.get(str(member.guild.id), {})

        if not serverconfig[str(member.guild.id)].get("protection"):
            LogDebug(f"Protection disabled in {member.guild.name} (ID: {member.guild.id})")
            return

        if not member.bot:
            LogDebug(f"Non-bot member joined: {member} (ID: {member.id})")
            return

        LogDebug(f"Bot detected: {member} (ID: {member.id})")
        inviter = None

        try:
            async for entry in member.guild.audit_logs(limit=10, action=discord.AuditLogAction.bot_add):
                if entry.target.id == member.id:
                    inviter = entry.user
                    LogDebug(f"Found inviter: {inviter} for bot {member}")
                    break
        except Exception as e:
            LogError(f"Audit log error in {member.guild.name}: {str(e)}")
            inviter = None

        log_channel_id = serverconfig[str(member.guild.id)].get("protectionlogchannel")
        if not log_channel_id:
            LogDebug(f"No log channel set for {member.guild.name}")
            return

        try:
            log_channel = await member.guild.fetch_channel(log_channel_id)
        except Exception as e:
            LogError(f"Failed to fetch log channel in {member.guild.name}: {str(e)}")
            return

        if member.public_flags.verified_bot:
            LogDebug(f"Verified bot allowed: {member}")
            embed = await create_antibot_protection_embed(member, inviter, is_verified=True)
            await log_channel.send(embed=embed)
            return

        if serverconfig[str(member.guild.id)].get("protection"):
            try:
                await member.kick(reason="Unverified bot protection")
                LogDebug(f"Successfully kicked unverified bot: {member}")
                embed = await create_antibot_protection_embed(member, inviter, is_verified=False, action_taken=True)
            except discord.Forbidden:
                LogError(f"Missing permissions to kick {member} in {member.guild.name}")
                embed = await create_antibot_protection_embed(member, inviter, is_verified=False, action_taken=False)
                embed.color = discord.Color.orange()
                embed.title = "⚠️ Protection Action Failed"
            except Exception as e:
                LogError(f"Error kicking bot: {str(e)}")
                embed = discord.Embed(
                    title="⚠️ Critical Protection Error",
                    description=f"Unexpected error handling bot: {str(e)}",
                    color=discord.Color.dark_red()
                )
        else:
            LogDebug(f"Protection disabled - allowing unverified bot: {member}")
            embed = await create_antibot_protection_embed(member, inviter, is_verified=False, action_taken=False)
            embed.color = discord.Color.orange()
            embed.title = "⚠️ Unverified Bot Allowed"

        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            LogError(f"Failed to send log message: {str(e)}")

def setup(bot):
    bot.add_cog(Antibot(bot))