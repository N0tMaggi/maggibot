# -*- coding: utf-8 -*-
import discord
from utils.embed_helpers import create_embed, create_security_embed


async def create_antibot_protection_embed(member, inviter, is_verified=True, action_taken=True):
    color = "success" if is_verified else "error"
    status = "Verified" if is_verified else "Unverified"
    action = "Allowed" if is_verified else ("Kicked" if action_taken else "Not Kicked")
    emoji = "✅" if is_verified else ("🛑" if action_taken else "⚠️")

    desc = "A **verified bot** was added to the server and has been allowed." if is_verified else (
        "An **unverified bot** was detected and immediately kicked." if action_taken else
        "⚠️ Failed to kick unverified bot! Please check bot permissions."
    )

    fields = [
        ("Bot Account", f"{member.mention}\n{member.name}", False),
        ("Bot ID", f"`{member.id}`", True),
        ("Account Created", f"<t:{int(member.created_at.timestamp())}:R>", True)
    ]
    if inviter:
        fields.append(("Invited By", f"{inviter.mention}\n({inviter.name})", False))

    embed = create_embed(
        title=f"{emoji} {status} Bot Detection",
        description=desc,
        color=color,
        thumbnail=member.display_avatar.url,
        footer_text=f"Protection System • Action: {action}",
        fields=fields
    )
    if member.guild:
        guild_icon = member.guild.icon.url if member.guild.icon else None
        embed.set_author(name=member.guild.name, icon_url=guild_icon)

    return embed


async def create_alert_embed(message, mention_count):
    guild_icon = message.guild.icon.url if (message.guild and message.guild.icon) else None
    content = message.content[:1000] + "..." if len(message.content) > 1000 else message.content

    embed = create_embed(
        title=f"🚨 Mass Mention Detected ({mention_count} mentions)",
        description=f"Automated anti-spam alert triggered in {message.channel.mention}.",
        color="error",
        author=message.author,
        footer_text=f"{message.guild.name} • Anti-Spam Protection",
        footer_icon=guild_icon,
        fields=[
            ("👤 User", f"{message.author.mention}\n`{message.author.id}`", True),
            ("📅 Account Created", f"<t:{int(message.author.created_at.timestamp())}:R>", True),
            ("🔗 Channel", f"{message.channel.mention}\n`{message.channel.id}`", True),
            ("📝 Message Content", f"```{content}```" if content else "*No text content*", False),
            ("📌 Message ID", f"`{message.id}`", True)
        ]
    )
    return embed


def _format_user_label(user: discord.abc.User | None) -> str:
    if user is None:
        return "Unknown"
    return f"{user.mention}\n{user.name}"


async def create_protection_config_embed(ctx, title, description, color, fields=None):
    guild = getattr(ctx, "guild", None)
    guild_icon = guild.icon.url if (guild and guild.icon) else None
    user = getattr(ctx, "author", None) or getattr(ctx, "user", None)

    embed_fields = [
        ("Action Performed By", _format_user_label(user), True)
    ]
    if fields:
        embed_fields.extend(fields)

    embed = create_embed(
        title=title,
        description=description,
        color=color,
        footer_text=f"Server ID: {guild.id} | Protection System" if guild else "Protection System",
        fields=embed_fields
    )
    if guild:
        embed.set_author(name=guild.name, icon_url=guild_icon)
    return embed


async def create_protection_status_embed(ctx, enabled: bool, log_channel_id: int | None):
    """Return a standardized embed showing current protection settings."""
    title = "🛡️ Protection Configuration"
    description = "Current server protection settings."
    color = "success" if enabled else "error"
    status = "Enabled ✅" if enabled else "Disabled ❌"
    log_channel_value = f"<#{log_channel_id}>" if log_channel_id else "Not set"
    fields = [
        ("Protection Status", status, False),
        ("Log Channel", log_channel_value, False),
    ]
    return await create_protection_config_embed(ctx, title, description, color, fields)
