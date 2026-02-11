import datetime

import discord
from discord.commands import SlashCommandGroup
from discord.ext import commands


class CentralSetup(commands.Cog):
    """Centralized setup command tree.

    Goal: keep all server setup actions under a single `/setup` command group.
    """

    def __init__(self, bot):
        self.bot = bot

    setup = SlashCommandGroup("setup", "Centralized setup commands")

    async def _get_cog_or_respond(
        self,
        ctx: discord.ApplicationContext,
        cog_name: str,
        error_message: str,
    ):
        cog = self.bot.get_cog(cog_name)
        if not cog:
            await ctx.respond(error_message, ephemeral=True)
            return None
        return cog

    # ------------------------------
    # Logging setup
    # ------------------------------
    @setup.command(name="logging-forum", description="Set the logging forum channel")
    @commands.has_permissions(administrator=True)
    async def setup_logging_forum(
        self,
        ctx: discord.ApplicationContext,
        forum: discord.ForumChannel,
    ):
        cog = await self._get_cog_or_respond(ctx, "Logging", "Logging setup not available.")
        if cog:
            await cog.configure_logging_forum(ctx, forum)

    @setup.command(name="logging-event", description="Enable/disable a specific logging event")
    @commands.has_permissions(administrator=True)
    async def setup_logging_event(
        self,
        ctx: discord.ApplicationContext,
        event: str,
        enabled: bool,
    ):
        cog = await self._get_cog_or_respond(ctx, "Logging", "Logging setup not available.")
        if cog:
            await cog.configure_event(ctx, event, enabled)

    @setup.command(name="logging-status", description="Show current logging event settings")
    @commands.has_permissions(administrator=True)
    async def setup_logging_status(self, ctx: discord.ApplicationContext):
        cog = await self._get_cog_or_respond(ctx, "Logging", "Logging setup not available.")
        if not cog:
            return

        guild_id = str(ctx.guild.id)
        flags = cog._get_event_flags(guild_id)
        forum = ctx.guild.get_channel(cog.serverconfig.get(guild_id, {}).get("logging_forum"))

        embed = discord.Embed(
            title="Logging Configuration",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow(),
        )
        embed.add_field(
            name="Forum",
            value=forum.mention if forum else "Not configured",
            inline=False,
        )
        formatted = "\n".join(
            f"• `{name}`: {'✅ Enabled' if state else '❌ Disabled'}"
            for name, state in flags.items()
        )
        embed.add_field(name="Event Flags", value=formatted, inline=False)
        await ctx.respond(embed=embed, ephemeral=True)

    # ------------------------------
    # Existing setup wrappers
    # ------------------------------
    @setup.command(name="logchannel", description="Set the log channel for the server")
    @commands.has_permissions(administrator=True)
    async def setup_logchannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        cog = await self._get_cog_or_respond(ctx, "Server", "Logchannel setup not available.")
        if cog:
            await cog.settings_logchannel(ctx, channel)

    @setup.command(name="voicegate", description="Set up a voice gate channel for this server")
    @commands.has_permissions(administrator=True)
    async def setup_voicegate(
        self,
        ctx: discord.ApplicationContext,
        gate_channel: discord.VoiceChannel,
        final_channel: discord.VoiceChannel,
        need_accept_rules: bool,
    ):
        cog = await self._get_cog_or_respond(ctx, "Server", "Voicegate setup not available.")
        if cog:
            await cog.setup_voicegate(ctx, gate_channel, final_channel, need_accept_rules)

    @setup.command(name="showvoicegate", description="Show the current voice gate settings for this server")
    @commands.has_permissions(administrator=True)
    async def setup_showvoicegate(self, ctx: discord.ApplicationContext):
        cog = await self._get_cog_or_respond(ctx, "Server", "Voicegate settings not available.")
        if cog:
            await cog.setup_showvoicegatesettings(ctx)

    @setup.command(name="deletevoicegate", description="Delete voice gate config for the given gate voice channel")
    @commands.has_permissions(administrator=True)
    async def setup_deletevoicegate(self, ctx: discord.ApplicationContext, gate_channel: discord.VoiceChannel):
        cog = await self._get_cog_or_respond(ctx, "Server", "Delete voicegate not available.")
        if cog:
            await cog.setup_deletevoicegate(ctx, gate_channel)

    @setup.command(name="autorole", description="Setup autorole for the server")
    @commands.has_permissions(administrator=True)
    async def setup_autorole(self, ctx: discord.ApplicationContext, role: discord.Role):
        cog = await self._get_cog_or_respond(ctx, "Server", "Autorole setup not available.")
        if cog:
            await cog.setup_autorole(ctx, role)

    @setup.command(name="deleteautorole", description="Delete autorole configuration for the server")
    @commands.has_permissions(administrator=True)
    async def setup_deleteautorole(self, ctx: discord.ApplicationContext):
        cog = await self._get_cog_or_respond(ctx, "Server", "Delete autorole not available.")
        if cog:
            await cog.setup_deleteautorole(ctx)

    @setup.command(name="adminfeedback", description="Set up admin feedback")
    @commands.has_permissions(administrator=True)
    async def setup_adminfeedback(self, ctx: discord.ApplicationContext, team_role: discord.Role):
        cog = await self._get_cog_or_respond(ctx, "Server", "Admin feedback setup not available.")
        if cog:
            await cog.setup_admin_feedback(ctx, team_role)

    @setup.command(name="deleteadminfeedback", description="Remove the admin feedback system")
    @commands.has_permissions(administrator=True)
    async def setup_deleteadminfeedback(self, ctx: discord.ApplicationContext):
        cog = await self._get_cog_or_respond(ctx, "Server", "Delete admin feedback not available.")
        if cog:
            await cog.setup_delete_admin_feedback(ctx)

    @setup.command(name="ticketsystem-setup", description="Setup the Ticket System for the server")
    @commands.has_permissions(administrator=True)
    async def setup_ticketsystem(
        self,
        ctx: discord.ApplicationContext,
        role: discord.Role,
        logchannel: discord.TextChannel,
        forum: discord.ForumChannel,
    ):
        cog = await self._get_cog_or_respond(ctx, "TicketSystem", "Ticket system setup not available.")
        if cog:
            await cog.setup_ticketsystem(ctx, role, logchannel, forum)

    @setup.command(name="ticketsystem", description="Manage the ticket system")
    @commands.has_permissions(administrator=True)
    async def setup_ticketsystem_central(self, ctx: discord.ApplicationContext):
        cog = await self._get_cog_or_respond(ctx, "TicketSystem", "Ticket system not available.")
        if not cog:
            return

        serverconfig = cog.serverconfig.get(str(ctx.guild.id), {})
        forum_id = serverconfig.get("ticketforum")
        forum_channel = ctx.guild.get_channel(forum_id) if forum_id else None

        embed = discord.Embed(
            title="Ticket System Configuration",
            color=0x9B59B6,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.add_field(name="Ticket Role", value=f"<@&{serverconfig.get('ticketrole', 'N/A')}>", inline=False)
        embed.add_field(name="Log Channel", value=f"<#{serverconfig.get('ticketlogchannel', 'N/A')}>", inline=False)
        embed.add_field(name="Forum", value=forum_channel.name if forum_channel else "N/A", inline=False)
        embed.set_footer(text="Use /setup ticketsystem-setup to change settings or /setup-sendticket to post a panel.")
        await ctx.respond(embed=embed, ephemeral=True)

    @setup.command(name="deleteticketconfig", description="Delete ticket system configuration entries for the server")
    @commands.has_permissions(administrator=True)
    async def setup_deleteticketconfig(self, ctx: discord.ApplicationContext):
        cog = await self._get_cog_or_respond(ctx, "TicketSystem", "Delete ticket config not available.")
        if cog:
            await cog.setup_deleteticketconfig(ctx)

    @setup.command(name="verifysystem", description="Set up the verify system for this server")
    @commands.has_permissions(administrator=True)
    async def setup_verifysystem(
        self,
        ctx: discord.ApplicationContext,
        role_to_remove: discord.Role,
        role_to_give: discord.Role,
        modrole: discord.Role,
        ghostping_channel: discord.TextChannel,
    ):
        cog = await self._get_cog_or_respond(ctx, "TicketVerify", "Verify system setup not available.")
        if cog:
            await cog.setupverifysystem(ctx, role_to_remove, role_to_give, modrole, ghostping_channel)

    @setup.command(name="showconfig", description="Show the current server configuration")
    @commands.has_permissions(administrator=True)
    async def setup_showconfig(self, ctx: discord.ApplicationContext):
        cog = await self._get_cog_or_respond(ctx, "ConfigSettings", "Show config not available.")
        if cog:
            await cog.settings_showconfig(ctx)


def setup(bot):
    bot.add_cog(CentralSetup(bot))
