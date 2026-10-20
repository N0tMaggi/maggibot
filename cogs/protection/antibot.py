import discord
from discord.ext import commands
import json
import datetime
from handlers.debug import LogDebug, LogError
import handlers.config as config
from utils.embed_helpers import (
    create_embed,
    create_mod_embed,
    create_security_embed,
    create_success_embed,
    create_error_embed,
    create_warning_embed,
)

def _create_antibot_embed(member: discord.Member, inviter: discord.User | None, is_verified: bool = True, action_taken: bool = True) -> discord.Embed:
    status = "Verified" if is_verified else "Unverified"
    action = "Allowed" if is_verified else ("Kicked" if action_taken else "Not Kicked")
    emoji = "✅" if is_verified else ("🛑" if action_taken else "⚠️")
    color = 'success' if is_verified else ('error' if action_taken else 'warning')

    if is_verified:
        description = "A **verified bot** was added to the server and has been allowed."
    elif action_taken:
        description = "An **unverified bot** was detected and immediately kicked."
    else:
        description = "⚠️ Failed to kick unverified bot! Please check permissions."

    fields = [
        ("Bot Account", f"{member.mention}\n{member.name}#{member.discriminator}", False),
        ("Bot ID", f"`{member.id}`", True),
        ("Account Created", f"<t:{int(member.created_at.timestamp())}:R>", True),
    ]
    if inviter:
        fields.append(("Invited By", f"{inviter.mention}\n({inviter.name}#{inviter.discriminator})", False))

    embed = create_security_embed(
        title=f"{emoji} {status} Bot Detection",
        description=description,
        color=color,
        thumbnail=member.display_avatar.url,
        footer_text=f"Protection System • Action: {action}",
        footer_icon=member.guild.me.display_avatar.url if member.guild and member.guild.me else None,
        fields=fields
    )
    if member.guild:
        embed.set_author(name=member.guild.name, icon_url=member.guild.icon.url if member.guild.icon else None)
    return embed

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
            embed = _create_antibot_embed(member, inviter, is_verified=True)
            await log_channel.send(embed=embed)
            return

        if serverconfig[str(member.guild.id)].get("protection"):
            try:
                await member.kick(reason="Unverified bot protection")
                LogDebug(f"Successfully kicked unverified bot: {member}")
                embed = _create_antibot_embed(member, inviter, is_verified=False, action_taken=True)
            except discord.Forbidden:
                LogError(f"Missing permissions to kick {member} in {member.guild.name}")
                embed = _create_antibot_embed(member, inviter, is_verified=False, action_taken=False)
                embed.title = "⚠️ Protection Action Failed"
            except Exception as e:
                LogError(f"Error kicking bot: {str(e)}")
                embed = create_error_embed(
                    title="Critical Protection Error",
                    description=f"Unexpected error handling bot: {str(e)}"
                )
        else:
            LogDebug(f"Protection disabled - allowing unverified bot: {member}")
            embed = _create_antibot_embed(member, inviter, is_verified=False, action_taken=False)
            embed.title = "⚠️ Unverified Bot Allowed"

        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            LogError(f"Failed to send log message: {str(e)}")

def setup(bot):
    bot.add_cog(Antibot(bot))
