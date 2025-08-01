import discord
from discord.ext import commands
import datetime

import handlers.config as config
from handlers.debug import LogDebug, LogError
from extensions.loggingextension import create_log_embed


class Logging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.serverconfig = config.loadserverconfig()

    # ------------------------------------------------------------
    # Setup command
    # ------------------------------------------------------------
    @commands.slash_command(name="setup-logging", description="Set the logging forum channel")
    @commands.has_permissions(administrator=True)
    async def setup_logging(self, ctx: discord.ApplicationContext, forum: discord.ForumChannel):
        try:
            guild_id = str(ctx.guild.id)
            if guild_id not in self.serverconfig:
                self.serverconfig[guild_id] = {}
            self.serverconfig[guild_id]["logging_forum"] = forum.id
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
            await forum.create_thread(name=thread_name, embed=embed)
        except Exception as e:
            LogError(f"Failed to post log in guild {guild.id}: {e}")

    # ------------------------------------------------------------
    # Event listeners
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
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
        description = f"{user.mention} was banned."
        fields = [("User ID", str(user.id), True)]
        embed = create_log_embed("Member Banned", description, "ban", user, fields, guild=guild)
        await self.post_log(guild, embed, "ban", user.id)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        content = message.content or "*No text content*"
        description = f"Message deleted in {message.channel.mention}."
        attachments = ", ".join(a.url for a in message.attachments) or "None"
        fields = [
            ("Author", message.author.mention, True),
            ("Channel", message.channel.mention, True),
            ("Content", content, False),
            ("Attachments", attachments, False),
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
        description = f"Message edited in {after.channel.mention}."
        attachments = ", ".join(a.url for a in after.attachments) or "None"
        fields = [
            ("Author", after.author.mention, True),
            ("Channel", after.channel.mention, True),
            ("Before", before.content or "*No text*", False),
            ("After", after.content or "*No text*", False),
            ("Attachments", attachments, False),
            ("Message ID", str(after.id), True),
            ("User ID", str(after.author.id), True),
        ]
        embed = create_log_embed(
            "Message Edited",
            description,
            "message_delete",
            after.author,
            fields,
            guild=after.guild,
        )
        await self.post_log(after.guild, embed, "message-edit", after.author.id)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        description = f"{user.mention} was unbanned."
        fields = [("User ID", str(user.id), True)]
        embed = create_log_embed("Member Unbanned", description, "ban", user, fields, guild=guild)
        await self.post_log(guild, embed, "unban", user.id)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
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
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel != after.channel:
            if before.channel is None:
                action = "joined"
                channel = after.channel
            elif after.channel is None:
                action = "left"
                channel = before.channel
            else:
                action = "moved"
                channel = after.channel

            description = f"{member.mention} {action} voice channel {channel.mention if channel else 'N/A'}."
            fields = [
                ("User ID", str(member.id), True),
            ]
            embed = create_log_embed(
                "Voice Channel Update",
                description,
                "default",
                member,
                fields,
                guild=member.guild,
            )
            await self.post_log(member.guild, embed, "voice-update", member.id)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        fields = [
            ("Channel ID", str(channel.id), True),
            ("Type", str(channel.type), True),
        ]
        creator = None
        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                if entry.target.id == channel.id:
                    creator = entry.user
                    break
        except Exception:
            pass

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
        fields = [
            ("Channel ID", str(channel.id), True),
            ("Type", str(channel.type), True),
        ]
        deleter = None
        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id:
                    deleter = entry.user
                    break
        except Exception:
            pass

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
        if before.name == after.name and getattr(before, "topic", None) == getattr(after, "topic", None):
            return
        fields = [
            ("Before", before.name, True),
            ("After", after.name, True),
            ("Channel ID", str(after.id), True),
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
        fields = [
            ("Role Name", role.name, True),
            ("Role ID", str(role.id), True),
        ]
        creator = None
        try:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
                if entry.target.id == role.id:
                    creator = entry.user
                    break
        except Exception:
            pass

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
        fields = [
            ("Role Name", role.name, True),
            ("Role ID", str(role.id), True),
        ]
        deleter = None
        try:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                if entry.target.id == role.id:
                    deleter = entry.user
                    break
        except Exception:
            pass

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
        if before.name == after.name and before.permissions == after.permissions and before.color == after.color:
            return
        fields = [
            ("Before Name", before.name, True),
            ("After Name", after.name, True),
            ("Role ID", str(after.id), True),
        ]
        editor = None
        try:
            async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                if entry.target.id == after.id:
                    editor = entry.user
                    break
        except Exception:
            pass

        description = f"Role {before.name} updated."
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
