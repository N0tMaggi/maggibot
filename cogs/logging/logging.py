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
        )
        await self.post_log(member.guild, embed, "member-leave", member.id)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        description = f"{user.mention} was banned."
        fields = [("User ID", str(user.id), True)]
        embed = create_log_embed("Member Banned", description, "ban", user, fields)
        await self.post_log(guild, embed, "ban", user.id)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        content = message.content or "*No text content*"
        description = f"Message deleted in {message.channel.mention}."
        fields = [
            ("Author", message.author.mention, True),
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
        )
        await self.post_log(message.guild, embed, "message-delete", message.author.id)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not after.guild or after.author.bot:
            return
        if before.content == after.content:
            return
        description = f"Message edited in {after.channel.mention}."
        fields = [
            ("Author", after.author.mention, True),
            ("Before", before.content or "*No text*", False),
            ("After", after.content or "*No text*", False),
            ("Message ID", str(after.id), True),
            ("User ID", str(after.author.id), True),
        ]
        embed = create_log_embed(
            "Message Edited",
            description,
            "message_delete",
            after.author,
            fields,
        )
        await self.post_log(after.guild, embed, "message-edit", after.author.id)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        description = f"{user.mention} was unbanned."
        fields = [("User ID", str(user.id), True)]
        embed = create_log_embed("Member Unbanned", description, "ban", user, fields)
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
            )
            await self.post_log(after.guild, embed, "nickname-update", after.id)

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
            )
            await self.post_log(member.guild, embed, "voice-update", member.id)


def setup(bot: commands.Bot):
    bot.add_cog(Logging(bot))
