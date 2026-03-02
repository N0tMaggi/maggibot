import discord
from discord.ext import commands
import datetime

import handlers.config as config
from handlers.debug import LogError
from extensions.loggingextension import create_log_embed
from utils.audit import find_audit_actor


def _format_perm_changes(before: discord.Permissions, after: discord.Permissions) -> str:
    before_set = {name for name, value in before if value}
    after_set = {name for name, value in after if value}
    added = sorted(after_set - before_set)
    removed = sorted(before_set - after_set)

    parts = []
    if added:
        parts.append("+ " + ", ".join(added[:25]))
    if removed:
        parts.append("- " + ", ".join(removed[:25]))

    return "\n".join(parts) if parts else "None"


class Logging(commands.Cog):
    DEFAULT_EVENT_FLAGS = {
        "member_join": True,
        "member_remove": True,
        "member_ban": True,
        "member_unban": True,
        "member_update": True,
        "message_delete": True,
        "message_edit": True,
        "voice_state": True,
        "channel_create": True,
        "channel_delete": True,
        "channel_update": True,
        "role_create": True,
        "role_delete": True,
        "role_update": True,
    }

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.serverconfig = config.loadserverconfig()

    def _refresh_config(self):
        self.serverconfig = config.loadserverconfig()

    def _get_event_flags(self, guild_id: str) -> dict:
        guild_cfg = self.serverconfig.get(guild_id, {})
        flags = guild_cfg.get("logging_events", {})
        merged = self.DEFAULT_EVENT_FLAGS.copy()
        if isinstance(flags, dict):
            merged.update({k: bool(v) for k, v in flags.items() if k in merged})
        return merged

    def _is_enabled(self, guild: discord.Guild, event_name: str) -> bool:
        self._refresh_config()
        return self._get_event_flags(str(guild.id)).get(event_name, True)

    def _trim(self, value: str, max_len: int = 950) -> str:
        if not value:
            return "N/A"
        return value if len(value) <= max_len else f"{value[:max_len]}…"

    async def configure_logging_forum(
        self,
        ctx: discord.ApplicationContext,
        forum: discord.ForumChannel,
    ):
        try:
            self._refresh_config()
            guild_id = str(ctx.guild.id)
            if guild_id not in self.serverconfig:
                self.serverconfig[guild_id] = {}
            self.serverconfig[guild_id]["logging_forum"] = forum.id

            self.serverconfig[guild_id].setdefault("logging_events", self.DEFAULT_EVENT_FLAGS.copy())
            config.saveserverconfig(self.serverconfig)

            embed = discord.Embed(
                title="Logging Configured",
                description=f"Logs will be posted in {forum.mention}",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow(),
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            LogError(f"Failed to configure logging forum: {e}")
            await ctx.respond("Error configuring logging forum.", ephemeral=True)

    async def configure_event(
        self,
        ctx: discord.ApplicationContext,
        event_name: str,
        enabled: bool,
    ):
        if event_name not in self.DEFAULT_EVENT_FLAGS:
            await ctx.respond("Unknown logging event.", ephemeral=True)
            return

        self._refresh_config()
        guild_id = str(ctx.guild.id)
        self.serverconfig.setdefault(guild_id, {})
        event_flags = self._get_event_flags(guild_id)
        event_flags[event_name] = enabled
        self.serverconfig[guild_id]["logging_events"] = event_flags
        config.saveserverconfig(self.serverconfig)

        state = "enabled" if enabled else "disabled"
        await ctx.respond(
            f"Logging event `{event_name}` is now **{state}**.",
            ephemeral=True,
        )

    # ------------------------------------------------------------
    # Helper to send logs
    # ------------------------------------------------------------
    async def post_log(
        self,
        guild: discord.Guild,
        embed: discord.Embed,
        title: str,
        user_id: int | None = None,
    ):
        forum = config.get_logging_forum(guild)
        if not forum or not isinstance(forum, discord.ForumChannel):
            return
        try:
            thread_name = f"{title}-{user_id}" if user_id else title
            thread_name = self._trim(thread_name, max_len=95)
            await forum.create_thread(name=thread_name, embed=embed)
        except Exception as e:
            LogError(f"Failed to post log in guild {guild.id}: {e}")

    # ------------------------------------------------------------
    # Event listeners
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not self._is_enabled(member.guild, "member_join"):
            return
        description = f"{member.mention} joined the server."
        fields = [
            ("Account Created", f"<t:{int(member.created_at.timestamp())}:R>", True),
            ("User ID", str(member.id), True),
        ]
        embed = create_log_embed(
            "Member Joined",
            description,
            "join",
            member,
            fields,
            guild=member.guild,
        )
        await self.post_log(member.guild, embed, "member-join", member.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if not self._is_enabled(member.guild, "member_remove"):
            return
        description = f"{member.mention} left the server."
        join_time = (
            f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Unknown"
        )
        fields = [
            ("Joined", join_time, True),
            ("User ID", str(member.id), True),
        ]
        embed = create_log_embed(
            "Member Left",
            description,
            "leave",
            member,
            fields,
            guild=member.guild,
        )
        await self.post_log(member.guild, embed, "member-leave", member.id)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        if not self._is_enabled(guild, "member_ban"):
            return

        audit = await find_audit_actor(
            guild=guild,
            action=discord.AuditLogAction.ban,
            target_id=user.id,
        )

        description = f"{user.mention} was banned."
        fields = [
            ("User ID", str(user.id), True),
            ("Actor", audit.user.mention if audit.user else "Unknown", True),
            ("Reason", self._trim(audit.reason) if audit.reason else "None", False),
        ]
        embed = create_log_embed("Member Banned", description, "ban", user, fields, guild=guild)
        await self.post_log(guild, embed, "ban", user.id)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        if not self._is_enabled(message.guild, "message_delete"):
            return

        content = self._trim(message.content or "*No text content*")
        description = f"Message deleted in {message.channel.mention}."
        attachments = self._trim(", ".join(a.url for a in message.attachments) or "None")
        attachment_count = len(message.attachments)

        created_ts = int(message.author.created_at.timestamp()) if getattr(message.author, "created_at", None) else None
        joined_ts = int(message.author.joined_at.timestamp()) if getattr(message.author, "joined_at", None) else None
        created_rel = f"<t:{created_ts}:R>" if created_ts else "Unknown"
        joined_rel = f"<t:{joined_ts}:R>" if joined_ts else "Unknown"

        fields = [
            ("Author", message.author.mention, True),
            ("Channel", message.channel.mention, True),
            ("Account created", created_rel, True),
            ("Joined server", joined_rel, True),
            ("Attachments", f"{attachment_count}\n{attachments}", False),
            ("Content", content, False),
            ("Message ID", str(message.id), True),
            ("User ID", str(message.author.id), True),
        ]
        embed = create_log_embed(
            "Message Deleted",
            description,
            "message_delete",
            message.author,
            fields,
            guild=message.guild,
        )
        await self.post_log(message.guild, embed, "message-delete", message.author.id)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not after.guild or after.author.bot:
            return
        if before.content == after.content:
            return
        if not self._is_enabled(after.guild, "message_edit"):
            return
        jump_url = f"https://discord.com/channels/{after.guild.id}/{after.channel.id}/{after.id}"
        description = f"Message edited in {after.channel.mention}."
        attachments = self._trim(", ".join(a.url for a in after.attachments) or "None")
        fields = [
            ("Author", after.author.mention, True),
            ("Channel", after.channel.mention, True),
            ("Jump", f"[Open message]({jump_url})", False),
            ("Before", self._trim(before.content or "*No text*"), False),
            ("After", self._trim(after.content or "*No text*"), False),
            ("Attachments", attachments, False),
            ("Message ID", str(after.id), True),
            ("User ID", str(after.author.id), True),
        ]
        embed = create_log_embed(
            "Message Edited",
            description,
            "default",
            after.author,
            fields,
            guild=after.guild,
        )
        await self.post_log(after.guild, embed, "message-edit", after.author.id)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        if not self._is_enabled(guild, "member_unban"):
            return

        audit = await find_audit_actor(
            guild=guild,
            action=discord.AuditLogAction.unban,
            target_id=user.id,
        )

        description = f"{user.mention} was unbanned."
        fields = [
            ("User ID", str(user.id), True),
            ("Actor", audit.user.mention if audit.user else "Unknown", True),
            ("Reason", self._trim(audit.reason) if audit.reason else "None", False),
        ]
        embed = create_log_embed("Member Unbanned", description, "ban", user, fields, guild=guild)
        await self.post_log(guild, embed, "unban", user.id)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if not self._is_enabled(after.guild, "member_update"):
            return
        if before.nick != after.nick:
            description = f"Nickname changed for {after.mention}"
            fields = [
                ("Before", before.nick or before.name, True),
                ("After", after.nick or after.name, True),
                ("User ID", str(after.id), True),
            ]
            embed = create_log_embed(
                "Nickname Updated",
                description,
                "default",
                after,
                fields,
                guild=after.guild,
            )
            await self.post_log(after.guild, embed, "nickname-update", after.id)

        if before.roles != after.roles:
            before_roles = ", ".join(r.mention for r in before.roles if r.name != "@everyone") or "None"
            after_roles = ", ".join(r.mention for r in after.roles if r.name != "@everyone") or "None"
            description = f"Roles updated for {after.mention}"
            fields = [
                ("Before", before_roles, False),
                ("After", after_roles, False),
                ("User ID", str(after.id), True),
            ]
            embed = create_log_embed(
                "Roles Updated",
                description,
                "default",
                after,
                fields,
                guild=after.guild,
            )
            await self.post_log(after.guild, embed, "roles-update", after.id)

        if before.display_avatar != after.display_avatar:
            description = f"Avatar updated for {after.mention}"
            fields = [("User ID", str(after.id), True)]
            embed = create_log_embed(
                "Avatar Updated",
                description,
                "default",
                after,
                fields,
                guild=after.guild,
            )
            await self.post_log(after.guild, embed, "avatar-update", after.id)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if not self._is_enabled(member.guild, "voice_state"):
            return

        changed = []
        if before.channel != after.channel:
            changed.append("channel")
        if before.self_mute != after.self_mute:
            changed.append("self_mute")
        if before.self_deaf != after.self_deaf:
            changed.append("self_deaf")
        if before.mute != after.mute:
            changed.append("server_mute")
        if before.deaf != after.deaf:
            changed.append("server_deaf")
        if before.self_stream != after.self_stream:
            changed.append("stream")
        if before.self_video != after.self_video:
            changed.append("video")

        if not changed:
            return

        before_channel = before.channel.mention if before.channel else "None"
        after_channel = after.channel.mention if after.channel else "None"

        description = f"Voice state updated for {member.mention}."
        fields = [
            ("Changed", ", ".join(changed), False),
            ("Channel (before)", before_channel, True),
            ("Channel (after)", after_channel, True),
            ("Self mute", str(bool(after.self_mute)), True),
            ("Self deaf", str(bool(after.self_deaf)), True),
            ("Server mute", str(bool(after.mute)), True),
            ("Server deaf", str(bool(after.deaf)), True),
            ("Streaming", str(bool(after.self_stream)), True),
            ("Video", str(bool(after.self_video)), True),
            ("User ID", str(member.id), True),
        ]

        embed = create_log_embed(
            "Voice State Update",
            description,
            "default",
            member,
            fields,
            guild=member.guild,
        )
        await self.post_log(member.guild, embed, "voice-update", member.id)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        if not self._is_enabled(channel.guild, "channel_create"):
            return
        audit = await find_audit_actor(
            guild=channel.guild,
            action=discord.AuditLogAction.channel_create,
            target_id=channel.id,
        )
        creator = audit.user

        fields = [
            ("Channel ID", str(channel.id), True),
            ("Type", str(channel.type), True),
            ("Actor", creator.mention if creator else "Unknown", True),
            ("Reason", self._trim(audit.reason) if audit.reason else "None", False),
        ]

        description = f"{channel.mention} was created."
        embed = create_log_embed(
            "Channel Created",
            description,
            "default",
            creator,
            fields,
            guild=channel.guild,
        )
        await self.post_log(channel.guild, embed, "channel-create")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        if not self._is_enabled(channel.guild, "channel_delete"):
            return
        audit = await find_audit_actor(
            guild=channel.guild,
            action=discord.AuditLogAction.channel_delete,
            target_id=channel.id,
        )
        deleter = audit.user

        fields = [
            ("Channel ID", str(channel.id), True),
            ("Type", str(channel.type), True),
            ("Actor", deleter.mention if deleter else "Unknown", True),
            ("Reason", self._trim(audit.reason) if audit.reason else "None", False),
        ]

        description = f"{channel.name} was deleted."
        embed = create_log_embed(
            "Channel Deleted",
            description,
            "default",
            deleter,
            fields,
            guild=channel.guild,
        )
        await self.post_log(channel.guild, embed, "channel-delete")

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self,
        before: discord.abc.GuildChannel,
        after: discord.abc.GuildChannel,
    ):
        if not self._is_enabled(after.guild, "channel_update"):
            return
        before_topic = getattr(before, "topic", None)
        after_topic = getattr(after, "topic", None)

        changed = []
        if before.name != after.name:
            changed.append("name")
        if before_topic != after_topic:
            changed.append("topic")

        if not changed:
            return

        fields = [
            ("Changed", ", ".join(changed), False),
            ("Name (before)", before.name, True),
            ("Name (after)", after.name, True),
            ("Topic (before)", self._trim(before_topic or ""), False),
            ("Topic (after)", self._trim(after_topic or ""), False),
            ("Channel ID", str(after.id), True),
            ("Type", str(after.type), True),
        ]
        description = f"{before.mention} was updated."
        embed = create_log_embed(
            "Channel Updated",
            description,
            "default",
            None,
            fields,
            guild=after.guild,
        )
        await self.post_log(after.guild, embed, "channel-update")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        if not self._is_enabled(role.guild, "role_create"):
            return
        fields = [
            ("Role Name", role.name, True),
            ("Role ID", str(role.id), True),
        ]
        audit = await find_audit_actor(
            guild=role.guild,
            action=discord.AuditLogAction.role_create,
            target_id=role.id,
        )
        creator = audit.user

        description = f"{role.mention} was created."
        embed = create_log_embed(
            "Role Created",
            description,
            "default",
            creator,
            fields,
            guild=role.guild,
        )
        await self.post_log(role.guild, embed, "role-create")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        if not self._is_enabled(role.guild, "role_delete"):
            return
        fields = [
            ("Role Name", role.name, True),
            ("Role ID", str(role.id), True),
        ]
        audit = await find_audit_actor(
            guild=role.guild,
            action=discord.AuditLogAction.role_delete,
            target_id=role.id,
        )
        deleter = audit.user

        description = f"Role {role.name} was deleted."
        embed = create_log_embed(
            "Role Deleted",
            description,
            "default",
            deleter,
            fields,
            guild=role.guild,
        )
        await self.post_log(role.guild, embed, "role-delete")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        if not self._is_enabled(after.guild, "role_update"):
            return

        changed = []
        if before.name != after.name:
            changed.append("name")
        if before.permissions != after.permissions:
            changed.append("permissions")
        if before.color != after.color:
            changed.append("color")
        if before.hoist != after.hoist:
            changed.append("hoist")
        if before.mentionable != after.mentionable:
            changed.append("mentionable")

        if not changed:
            return

        audit = await find_audit_actor(
            guild=after.guild,
            action=discord.AuditLogAction.role_update,
            target_id=after.id,
        )
        editor = audit.user

        fields = [
            ("Changed", ", ".join(changed), False),
            ("Role", after.mention, True),
            ("Role ID", str(after.id), True),
            ("Actor", editor.mention if editor else "Unknown", True),
            ("Reason", self._trim(audit.reason) if audit.reason else "None", False),
            ("Name (before)", before.name, True),
            ("Name (after)", after.name, True),
            ("Color (before)", str(before.color), True),
            ("Color (after)", str(after.color), True),
            ("Hoist", f"{before.hoist} -> {after.hoist}", True),
            ("Mentionable", f"{before.mentionable} -> {after.mentionable}", True),
        ]

        if before.permissions != after.permissions:
            fields.append(("Permission changes", _format_perm_changes(before.permissions, after.permissions), False))

        description = f"Role {after.mention} updated."
        embed = create_log_embed(
            "Role Updated",
            description,
            "default",
            editor,
            fields,
            guild=after.guild,
        )
        await self.post_log(after.guild, embed, "role-update")


def setup(bot: commands.Bot):
    bot.add_cog(Logging(bot))
