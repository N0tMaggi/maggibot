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
    async def post_log(self, guild: discord.Guild, embed: discord.Embed, title: str):
        forum = config.get_logging_forum(guild)
        if not forum or not isinstance(forum, discord.ForumChannel):
            return
        try:
            await forum.create_thread(name=title, embed=embed)
        except Exception as e:
            LogError(f"Failed to post log in guild {guild.id}: {e}")

    # ------------------------------------------------------------
    # Event listeners
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        description = (
            f"{member.mention} joined the server.\n"
            f"Account created: <t:{int(member.created_at.timestamp())}:R>"
        )
        embed = create_log_embed("Member Joined", description, "join", member)
        await self.post_log(member.guild, embed, "member-join")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        description = (
            f"{member.mention} left the server.\n"
            f"Joined: <t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else ""
        )
        embed = create_log_embed("Member Left", description, "leave", member)
        await self.post_log(member.guild, embed, "member-leave")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        description = f"{user.mention} was banned."
        embed = create_log_embed("Member Banned", description, "ban", user)
        await self.post_log(guild, embed, "ban")

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        content = message.content or "*No text content*"
        description = (
            f"Author: {message.author.mention}\n"
            f"Channel: {message.channel.mention}\n"
            f"Content: {content}"
        )
        embed = create_log_embed("Message Deleted", description, "message_delete", message.author)
        await self.post_log(message.guild, embed, "message-delete")


def setup(bot: commands.Bot):
    bot.add_cog(Logging(bot))
