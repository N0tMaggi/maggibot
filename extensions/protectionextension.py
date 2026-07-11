import discord
import handlers.config as cfg
from handlers.debug import LogDebug, LogError, LogModeration
from utils.components import build_container


async def create_antibot_protection_embed(member, inviter, is_verified=True, action_taken=True):
    color = 0x2ECC71 if is_verified else 0xE74C3C
    status = "Verified" if is_verified else "Unverified"
    action = "Allowed" if is_verified else "Kicked" if action_taken else "Not Kicked"
    emoji = "✅" if is_verified else "🛑" if action_taken else "⚠️"

    description = "A **verified bot** was added to the server and has been allowed."
    if not is_verified:
        if action_taken:
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

    return build_container(
        title=f"{emoji} {status} Bot Detection",
        description=description,
        color=color,
        author=member.guild,
        thumbnail=member.display_avatar.url,
        fields=fields,
        footer_text=f"Protection System • Action: {action}",
        footer_icon=member.guild.me.display_avatar.url,
        timestamp=True,
    )

async def create_alert_embed(message, mention_count):
    content = message.content[:1000] + "..." if len(message.content) > 1000 else message.content
    fields = [
        ("👤 User", f"{message.author.mention}\n{message.author.id}", True),
        ("📅 Account Created", f"<t:{int(message.author.created_at.timestamp())}:R>", True),
        ("📝 Message Content", f"```{content}```" if content else "*No text content*", False),
        ("📌 Message ID", f"`{message.id}`", True),
        ("🔗 Channel", f"{message.channel.mention}\n({message.channel.id})", True),
    ]

    return build_container(
        title=f"🚨 Mass Mention Detected ({mention_count} mentions)",
        color="error",
        author=message.author,
        fields=fields,
        footer_text=f"{message.guild.name} • Anti-Spam Protection",
        footer_icon=message.guild.icon.url if message.guild.icon else None,
        timestamp=True,
    )



def _format_user_label(user: discord.abc.User | None) -> str:
    if user is None:
        return "Unknown"
    name = user.name
    discriminator = getattr(user, "discriminator", None)
    if discriminator and discriminator != "0":
        tag = f"{name}#{discriminator}"
    else:
        tag = name
    return f"{user.mention}\n{tag}"


async def create_protection_config_embed(ctx, title, description, color, fields=None):
    guild = getattr(ctx, "guild", None)
    user = getattr(ctx, "author", None) or getattr(ctx, "user", None)

    container_fields = [
        ("Action Performed By", _format_user_label(user), True),
    ]

    if fields:
        for name, value, inline in fields:
            container_fields.append((name, value, inline))

    footer_text = f"Server ID: {guild.id} | Protection System" if guild else "Protection System"

    return build_container(
        title=title,
        description=description,
        color=color,
        author=guild,
        fields=container_fields,
        footer_text=footer_text,
        timestamp=True,
    )


async def create_protection_status_embed(ctx, enabled: bool, log_channel_id: int | None):
    """Return a standardized container showing current protection settings."""
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
