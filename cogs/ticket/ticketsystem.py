import discord
from discord.ext import commands, tasks
from discord.ext.commands import Cog
import datetime
import json
import os
import io
import html
import handlers.config as config
from handlers.debug import LogDebug, LogError


def NoPrivateMessage(ctx):
    if isinstance(ctx.channel, discord.DMChannel):
        raise commands.NoPrivateMessage(
            "This command can only be used in a server. Please use it on the corresponding server."
        )
    return True


class TicketSystem(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.serverconfig = config.loadserverconfig()
        self.tickets = config.load_ticket_data()
        self.ticket_check_loop.start()
        self.save_ticket_data = config.save_ticket_data
        self.bot.loop.create_task(self._register_persistent_view())

    async def _register_persistent_view(self):
        await self.bot.wait_until_ready()
        self.bot.add_view(self.TicketOpenView(self))

    class TicketOpenView(discord.ui.View):
        def __init__(self, cog):
            super().__init__(timeout=None)
            self.cog = cog

        @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.success, emoji="🎫", custom_id="ticket_open_button")
        async def open_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            await self.cog.button_create_ticket(interaction)

    async def ensure_forum_tags(self, forum: discord.ForumChannel):
        required = ["claimed", "new-ticket", "closed"]
        existing = [t.name.lower() for t in forum.available_tags]
        new_tags = [discord.ForumTag(name=name, emoji="🏷️") for name in required if name not in existing]
        if new_tags:
            try:
                await forum.edit(available_tags=forum.available_tags + new_tags)
            except Exception as e:
                LogError(f"Failed to create forum tags: {e}")

    async def configure_ticket_system(self, guild: discord.Guild, role: discord.Role, logchannel: discord.TextChannel, forum: discord.ForumChannel):
        guild_id = str(guild.id)
        if guild_id not in self.serverconfig:
            self.serverconfig[guild_id] = {}
        self.serverconfig[guild_id]["ticketrole"] = role.id
        self.serverconfig[guild_id]["ticketlogchannel"] = logchannel.id
        self.serverconfig[guild_id]["ticketforum"] = forum.id
        config.saveserverconfig(self.serverconfig)
        await self.ensure_forum_tags(forum)

    class TicketControlView(discord.ui.View):
        def __init__(self, cog, guild_id: str, user_id: str):
            super().__init__(timeout=None)
            self.cog = cog
            self.guild_id = guild_id
            self.user_id = user_id

        @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary, emoji="📌")
        async def claim(
            self, button: discord.ui.Button, interaction: discord.Interaction
        ):
            await interaction.response.defer(ephemeral=True)
            await self.cog.button_claim_ticket(interaction, self.guild_id, self.user_id)

        @discord.ui.button(
            label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒"
        )
        async def close_ticket(
            self, button: discord.ui.Button, interaction: discord.Interaction
        ):
            await interaction.response.defer(ephemeral=True)
            await self.cog.button_close_ticket(interaction, self.guild_id, self.user_id)

    def cog_unload(self):
        self.ticket_check_loop.cancel()

    async def check_if_able_dm(self, user: discord.User):
        if user.dm_channel is None:
            try:
                await user.create_dm()
            except discord.Forbidden:
                raise commands.Forbidden("I don't have permission to DM you!")
        return True

    def generate_ticket_id(self, author_id):
        return f"{author_id}-{int(datetime.datetime.utcnow().timestamp())}"

    async def generate_transcript_html(self, thread: discord.Thread) -> str:
        """Generate an HTML transcript for a ticket thread."""
        lines = [
            "<!DOCTYPE html>",
            "<html><head><meta charset='UTF-8'>",
            "<style>",
            "body{font-family:Arial, sans-serif;background:#2b2d31;color:#ddd;padding:10px;}",
            ".message{margin-bottom:15px;padding:10px;background:#36393f;border-radius:4px;}",
            ".timestamp{color:#999;margin-right:5px;font-size:0.9em;}",
            ".author{font-weight:bold;margin-right:5px;}",
            ".attachments a{display:block;color:#58a6ff;}",
            ".embed{border-left:4px solid #666;margin-top:5px;padding-left:6px;}",
            "</style></head><body>",
            f"<h2>Transcript for {html.escape(thread.name)}</h2>",
        ]

        async for message in thread.history(limit=None, oldest_first=True):
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            author = f"{message.author.name}#{message.author.discriminator}"
            lines.append("<div class='message'>")
            lines.append(
                f"<span class='timestamp'>[{timestamp}]</span> <span class='author'>{html.escape(author)}</span>"
            )
            if message.content:
                lines.append(
                    f"<div class='content'>{html.escape(message.content)}</div>"
                )
            if message.attachments:
                lines.append("<div class='attachments'>")
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith(
                        "image"
                    ):
                        lines.append(
                            f"<img src='{attachment.url}' alt='{html.escape(attachment.filename)}' style='max-width:300px;'>"
                        )
                    else:
                        lines.append(
                            f"<a href='{attachment.url}'>{html.escape(attachment.filename)}</a>"
                        )
                lines.append("</div>")
            if message.embeds:
                for embed in message.embeds:
                    e_html = ["<div class='embed'>"]
                    if embed.title:
                        e_html.append(
                            f"<div class='embed-title'>{html.escape(embed.title)}</div>"
                        )
                    if embed.description:
                        e_html.append(
                            f"<div class='embed-description'>{html.escape(embed.description)}</div>"
                        )
                    for field in embed.fields:
                        e_html.append(
                            f"<div class='embed-field'><strong>{html.escape(field.name)}:</strong> {html.escape(field.value)}</div>"
                        )
                    e_html.append("</div>")
                    lines.extend(e_html)
            lines.append("</div>")

        lines.append("</body></html>")
        return "\n".join(lines)

    @commands.slash_command(
        name="setup-ticketsystem", description="Setup the Ticket System for the server"
    )
    @commands.has_permissions(administrator=True)
    async def setup_ticketsystem(
        self,
        ctx: discord.ApplicationContext,
        role: discord.Role,
        logchannel: discord.TextChannel,
        forum: discord.ForumChannel,
    ):
        try:
            await self.configure_ticket_system(ctx.guild, role, logchannel, forum)
            guild_id = str(ctx.guild.id)
            LogDebug(f"Updated server config for guild {guild_id}: {self.serverconfig[guild_id]}")

            embed = discord.Embed(
                title="Ticket System Setup",
                description="The Ticket System has been successfully set up.",
                color=0x00FF00,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_author(
                name=ctx.guild.name,
                icon_url=ctx.guild.icon.url if ctx.guild.icon else None,
            )
            embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
            )
            embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed.add_field(name="Ticket Role", value=role.mention, inline=True)
            embed.add_field(
                name="Ticket Log Channel", value=logchannel.mention, inline=True
            )
            embed.add_field(name="Ticket Forum", value=forum.name, inline=True)
            embed.add_field(name="Guild ID", value=ctx.guild.id, inline=False)

            await ctx.respond(embed=embed)

        except Exception as e:
            LogError(f"An error occurred while setting up the Ticket System: {e}")
            raise Exception(
                f"An error occurred while setting up the Ticket System: {e}"
            )

    @commands.slash_command(
        name="setup-sendticket",
        description="Send the ticket creation embed to a channel",
    )
    @commands.has_permissions(administrator=True)
    async def setup_sendticket(
        self, ctx: discord.ApplicationContext, channel: discord.TextChannel
    ):
        try:
            view = self.TicketOpenView(self)
            embed = discord.Embed(
                title="Create a Ticket",
                description="Press the button below to open a support ticket.",
                color=0x3498DB,
            )
            await channel.send(embed=embed, view=view)
            await ctx.respond("Ticket panel sent.", ephemeral=True)
        except Exception as e:
            LogError(f"Failed to send ticket panel: {e}")
            await ctx.respond("Failed to send panel.", ephemeral=True)

    @commands.slash_command(
        name="setup-deleteticketconfig",
        description="Deletes the Ticket System configuration entries for the server",
    )
    @commands.has_permissions(administrator=True)
    async def setup_deleteticketconfig(self, ctx: discord.ApplicationContext):
        try:
            guild_id = str(ctx.guild.id)
            LogDebug(f"Current server config for guild {guild_id}: {self.serverconfig}")

            if (
                guild_id not in self.serverconfig
                or "ticketrole" not in self.serverconfig[guild_id]
            ):
                embed = discord.Embed(
                    title="Ticket System Setup Deletion",
                    description="No Ticket System configuration found for this server.",
                    color=0xFF0000,
                    timestamp=datetime.datetime.utcnow(),
                )
                embed.set_author(
                    name=ctx.guild.name,
                    icon_url=ctx.guild.icon.url if ctx.guild.icon else None,
                )
                embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
                )
                await ctx.respond(embed=embed)
                return

            self.serverconfig[guild_id].pop("ticketrole", None)
            self.serverconfig[guild_id].pop("ticketlogchannel", None)
            self.serverconfig[guild_id].pop("ticketforum", None)
            LogDebug(
                f"Removed Ticket System entries for guild {guild_id}: {self.serverconfig[guild_id]}"
            )

            config.saveserverconfig(self.serverconfig)

            embed = discord.Embed(
                title="Ticket System Setup Deletion",
                description="The Ticket System configuration entries have been successfully deleted.",
                color=0xFF0000,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_author(
                name=ctx.guild.name,
                icon_url=ctx.guild.icon.url if ctx.guild.icon else None,
            )
            embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
            )

            await ctx.respond(embed=embed)

        except Exception as e:
            LogError(
                f"An error occurred while deleting the Ticket System configuration entries: {e}"
            )
            raise Exception(
                f"An error occurred while deleting the Ticket System configuration entries: {e}"
            )

    @commands.slash_command(
        name="ticket-create", description="Create a ticket for support"
    )
    async def ticket_create(self, ctx: discord.ApplicationContext):
        if not NoPrivateMessage(ctx):
            return

        guild_id = str(ctx.guild.id)
        if (
            guild_id not in self.serverconfig
            or "ticketrole" not in self.serverconfig[guild_id]
            or "ticketlogchannel" not in self.serverconfig[guild_id]
            or "ticketforum" not in self.serverconfig[guild_id]
        ):
            await ctx.respond(
                "Ticket system is not set up on this server.", ephemeral=True
            )
            return

        try:
            await self.check_if_able_dm(ctx.author)
        except commands.Forbidden:
            await ctx.respond(
                "I cannot DM you, please check your DM settings.", ephemeral=True
            )
            return

        if guild_id in self.tickets and str(ctx.author.id) in self.tickets[guild_id]:
            await ctx.respond("You already have an open ticket.", ephemeral=True)
            return

        forum_id = self.serverconfig[guild_id]["ticketforum"]
        forum_channel = ctx.guild.get_channel(forum_id)
        if forum_channel is None or not isinstance(forum_channel, discord.ForumChannel):
            await ctx.respond("Ticket forum is invalid or not found.", ephemeral=True)
            return

        ticket_role_id = self.serverconfig[guild_id]["ticketrole"]
        ticket_role = ctx.guild.get_role(ticket_role_id)
        if ticket_role is None:
            await ctx.respond("Ticket role is invalid or not found.", ephemeral=True)
            return

        channel_name = f"ticket-{ctx.author.name}-{ctx.author.discriminator}"
        try:
            ticket_thread = await forum_channel.create_thread(
                name=channel_name, content=ticket_role.mention
            )
        except Exception as e:
            LogError(f"Failed to create ticket thread: {e}")
            await ctx.respond("Failed to create ticket thread.", ephemeral=True)
            return

        ticket_id = self.generate_ticket_id(ctx.author.id)
        now_iso = datetime.datetime.utcnow().isoformat()
        ticket_data = {
            "channel_id": ticket_thread.id,
            "ticket_id": ticket_id,
            "status": "Open",
            "created_at": now_iso,
            "last_activity": now_iso,
            "assigned_to": None,
            "feedback": None,
        }
        if guild_id not in self.tickets:
            self.tickets[guild_id] = {}
        self.tickets[guild_id][str(ctx.author.id)] = ticket_data
        self.save_ticket_data(self.tickets)

        embed_channel = discord.Embed(
            title="🎟️ Support Ticket Created",
            description=(
                f"{ctx.author.mention}, your ticket has been opened. "
                "A member of our team will be with you shortly."
            ),
            color=0x00FF00,
            timestamp=datetime.datetime.utcnow(),
        )
        embed_channel.set_author(
            name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None
        )
        embed_channel.add_field(name="Ticket ID", value=ticket_id, inline=True)
        embed_channel.add_field(name="Status", value="Open", inline=True)
        embed_channel.add_field(name="Created At", value=now_iso, inline=False)
        embed_channel.set_footer(text="Use the buttons below to manage this ticket.")
        view = self.TicketControlView(self, guild_id, str(ctx.author.id))
        await ticket_thread.send(embed=embed_channel, view=view)

        # Log embed for ticket creation
        log_channel_id = self.serverconfig[guild_id]["ticketlogchannel"]
        log_channel = ctx.guild.get_channel(log_channel_id)
        if log_channel:
            embed_log = discord.Embed(
                title="Ticket Created",
                description=f"Ticket created by {ctx.author.mention} in {ticket_thread.mention}.",
                color=0x00FF00,
                timestamp=datetime.datetime.utcnow(),
            )
            embed_log.set_author(
                name=ctx.guild.name,
                icon_url=ctx.guild.icon.url if ctx.guild.icon else None,
            )
            embed_log.add_field(name="Ticket ID", value=ticket_id, inline=True)
            embed_log.add_field(
                name="User", value=f"{ctx.author} ({ctx.author.id})", inline=True
            )
            embed_log.add_field(
                name="Channel", value=ticket_thread.mention, inline=True
            )
            await log_channel.send(embed=embed_log)

        # DM embed for ticket creation
        embed_dm = discord.Embed(
            title="Ticket Opened",
            description=(
                f"Your ticket in **{ctx.guild.name}** has been successfully opened.\n"
                "You can reply here or in the server channel."
            ),
            color=0x00FF00,
            timestamp=datetime.datetime.utcnow(),
        )
        embed_dm.set_author(
            name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None
        )
        embed_dm.add_field(name="Ticket ID", value=ticket_id, inline=True)
        embed_dm.add_field(
            name="Ticket Thread", value=ticket_thread.mention, inline=True
        )
        try:
            await ctx.author.send(embed=embed_dm)
        except Exception as e:
            LogError(f"Failed to send DM to {ctx.author.id}: {e}")

        await ctx.respond("Ticket created successfully!", ephemeral=True)

    @commands.slash_command(
        name="ticket-delete", description="Close and delete your ticket"
    )
    async def ticket_delete(self, ctx: discord.ApplicationContext):
        if not NoPrivateMessage(ctx):
            return

        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)
        if guild_id not in self.tickets or user_id not in self.tickets[guild_id]:
            await ctx.respond(
                "You don't have an open ticket to delete.", ephemeral=True
            )
            return

        ticket_data = self.tickets[guild_id][user_id]
        ticket_channel_id = ticket_data["channel_id"]
        if (
            ctx.channel.id != ticket_channel_id
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.respond(
                "You can only delete your ticket in the ticket thread.", ephemeral=True
            )
            return

        ticket_thread = ctx.guild.get_thread(ticket_channel_id)
        if ticket_thread is None:
            await ctx.respond("Ticket thread not found.", ephemeral=True)
            return

        transcript_html = await self.generate_transcript_html(ticket_thread)
        transcript_file = discord.File(
            fp=io.StringIO(transcript_html),
            filename=f"transcript-{ticket_thread.id}.html",
        )

        # Log embed for ticket deletion
        log_channel_id = self.serverconfig[guild_id]["ticketlogchannel"]
        log_channel = ctx.guild.get_channel(log_channel_id)
        if log_channel:
            embed_log = discord.Embed(
                title="Ticket Closed",
                description=f"Ticket for {ctx.author.mention} has been closed. Transcript attached.",
                color=0xFF0000,
                timestamp=datetime.datetime.utcnow(),
            )
            embed_log.set_author(
                name=ctx.guild.name,
                icon_url=ctx.guild.icon.url if ctx.guild.icon else None,
            )
            embed_log.add_field(
                name="Ticket ID", value=ticket_data["ticket_id"], inline=True
            )
            embed_log.add_field(
                name="User", value=f"{ctx.author} ({ctx.author.id})", inline=True
            )
            await log_channel.send(embed=embed_log, file=transcript_file)

        try:
            dm_embed = discord.Embed(
                title="Ticket Closed",
                description=f"Your ticket in **{ctx.guild.name}** has been closed.\nPlease provide feedback using `/ticket-feedback`.",
                color=0xFF0000,
                timestamp=datetime.datetime.utcnow(),
            )
            dm_embed.set_author(
                name=ctx.guild.name,
                icon_url=ctx.guild.icon.url if ctx.guild.icon else None,
            )
            dm_embed.add_field(
                name="Ticket ID", value=ticket_data["ticket_id"], inline=True
            )
            await ctx.author.send(embed=dm_embed)
        except Exception as e:
            LogError(f"Failed to send DM to {ctx.author.id}: {e}")

        # Update ticket status to Closed before deletion
        ticket_data["status"] = "Closed"
        self.save_ticket_data(self.tickets)

        del self.tickets[guild_id][user_id]
        if not self.tickets[guild_id]:
            del self.tickets[guild_id]
        self.save_ticket_data(self.tickets)
        await ctx.respond("Ticket will be deleted shortly.", ephemeral=True)
        await ticket_thread.delete()

    @commands.slash_command(
        name="ticket-assign",
        description="Assign or transfer a ticket to a support agent",
    )
    async def ticket_assign(
        self, ctx: discord.ApplicationContext, agent: discord.Member
    ):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)
        if guild_id not in self.tickets or user_id not in self.tickets[guild_id]:
            await ctx.respond(
                "You don't have an open ticket to assign.", ephemeral=True
            )
            return

        ticket_data = self.tickets[guild_id][user_id]
        ticket_thread = ctx.guild.get_thread(ticket_data["channel_id"])
        if ticket_thread is None:
            await ctx.respond("Ticket thread not found.", ephemeral=True)
            return

        ticket_data["assigned_to"] = agent.id
        ticket_data["status"] = "In Progress"
        ticket_data["last_activity"] = datetime.datetime.utcnow().isoformat()
        self.save_ticket_data(self.tickets)

        embed_assign = discord.Embed(
            title="Ticket Assigned",
            description=f"Ticket {ticket_data['ticket_id']} has been assigned to {agent.mention}.",
            color=0x0000FF,
            timestamp=datetime.datetime.utcnow(),
        )
        embed_assign.add_field(
            name="Ticket ID", value=ticket_data["ticket_id"], inline=True
        )
        embed_assign.add_field(name="Assigned To", value=agent.mention, inline=True)
        embed_assign.set_footer(text="Ticket status updated to In Progress.")
        await ticket_thread.send(embed=embed_assign)
        await ctx.respond("Ticket assignment updated.", ephemeral=True)

    @commands.slash_command(
        name="ticket-feedback", description="Provide feedback for a closed ticket"
    )
    async def ticket_feedback(
        self,
        ctx: discord.ApplicationContext,
        ticket_id: str,
        rating: int,
        comment: str = None,
    ):
        if rating < 1 or rating > 5:
            await ctx.respond("Rating must be between 1 and 5.", ephemeral=True)
            return

        feedback_embed = discord.Embed(
            title="Ticket Feedback Received",
            description=f"Feedback for Ticket ID: {ticket_id}",
            color=0x00FF00,
            timestamp=datetime.datetime.utcnow(),
        )
        feedback_embed.add_field(name="Rating", value=str(rating), inline=True)
        feedback_embed.add_field(
            name="Comment",
            value=comment if comment else "No comment provided",
            inline=False,
        )
        feedback_embed.set_footer(text=f"Feedback submitted by {ctx.author}")

        sent = False
        for guild_id, conf in self.serverconfig.items():
            log_channel_id = conf.get("ticketlogchannel")
            if log_channel_id:
                guild = self.bot.get_guild(int(guild_id))
                if guild:
                    log_channel = guild.get_channel(log_channel_id)
                    if log_channel:
                        await log_channel.send(embed=feedback_embed)
                        sent = True

        if sent:
            await ctx.respond("Thank you for your feedback!", ephemeral=True)
        else:
            await ctx.respond(
                "Feedback could not be sent. Please contact support.", ephemeral=True
            )

    async def button_create_ticket(self, interaction: discord.Interaction):
        ctx = interaction
        guild_id = str(ctx.guild.id)
        if (
            guild_id not in self.serverconfig
            or "ticketrole" not in self.serverconfig[guild_id]
            or "ticketlogchannel" not in self.serverconfig[guild_id]
            or "ticketforum" not in self.serverconfig[guild_id]
        ):
            await ctx.followup.send("Ticket system is not set up on this server.", ephemeral=True)
            return

        user = ctx.user
        try:
            await self.check_if_able_dm(user)
        except commands.Forbidden:
            await ctx.followup.send("I cannot DM you, please check your DM settings.", ephemeral=True)
            return

        if guild_id in self.tickets and str(user.id) in self.tickets[guild_id]:
            await ctx.followup.send("You already have an open ticket.", ephemeral=True)
            return

        forum_id = self.serverconfig[guild_id]["ticketforum"]
        forum_channel = ctx.guild.get_channel(forum_id)
        if forum_channel is None or not isinstance(forum_channel, discord.ForumChannel):
            await ctx.followup.send("Ticket forum is invalid or not found.", ephemeral=True)
            return

        ticket_role_id = self.serverconfig[guild_id]["ticketrole"]
        ticket_role = ctx.guild.get_role(ticket_role_id)
        if ticket_role is None:
            await ctx.followup.send("Ticket role is invalid or not found.", ephemeral=True)
            return

        channel_name = f"ticket-{user.name}-{user.discriminator}"
        try:
            ticket_thread = await forum_channel.create_thread(name=channel_name, content=ticket_role.mention, applied_tags=[forum_channel.get_tag(tag.id) for tag in forum_channel.available_tags if tag.name.lower()=="new-ticket"] if forum_channel.requires_tag else None)
        except Exception as e:
            LogError(f"Failed to create ticket thread: {e}")
            await ctx.followup.send("Failed to create ticket thread.", ephemeral=True)
            return

        ticket_id = self.generate_ticket_id(user.id)
        now_iso = datetime.datetime.utcnow().isoformat()
        data = {
            "channel_id": ticket_thread.id,
            "ticket_id": ticket_id,
            "status": "Open",
            "created_at": now_iso,
            "last_activity": now_iso,
            "assigned_to": None,
            "feedback": None,
        }
        if guild_id not in self.tickets:
            self.tickets[guild_id] = {}
        self.tickets[guild_id][str(user.id)] = data
        self.save_ticket_data(self.tickets)

        embed_channel = discord.Embed(
            title="🎟️ Support Ticket Created",
            description=(f"{user.mention}, your ticket has been opened. A member of our team will be with you shortly."),
            color=0x00FF00,
            timestamp=datetime.datetime.utcnow(),
        )
        embed_channel.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed_channel.add_field(name="Ticket ID", value=ticket_id, inline=True)
        embed_channel.add_field(name="Status", value="Open", inline=True)
        embed_channel.add_field(name="Created At", value=now_iso, inline=False)
        embed_channel.set_footer(text="Use the buttons below to manage this ticket.")
        view = self.TicketControlView(self, guild_id, str(user.id))
        await ticket_thread.send(embed=embed_channel, view=view)

        log_channel_id = self.serverconfig[guild_id]["ticketlogchannel"]
        log_channel = ctx.guild.get_channel(log_channel_id)
        if log_channel:
            embed_log = discord.Embed(
                title="Ticket Created",
                description=f"Ticket created by {user.mention} in {ticket_thread.mention}.",
                color=0x00FF00,
                timestamp=datetime.datetime.utcnow(),
            )
            embed_log.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed_log.add_field(name="Ticket ID", value=ticket_id, inline=True)
            embed_log.add_field(name="User", value=f"{user} ({user.id})", inline=True)
            embed_log.add_field(name="Channel", value=ticket_thread.mention, inline=True)
            await log_channel.send(embed=embed_log)

        try:
            embed_dm = discord.Embed(
                title="Ticket Opened",
                description=(f"Your ticket in **{ctx.guild.name}** has been successfully opened.\nYou can reply here or in the server channel."),
                color=0x00FF00,
                timestamp=datetime.datetime.utcnow(),
            )
            embed_dm.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed_dm.add_field(name="Ticket ID", value=ticket_id, inline=True)
            embed_dm.add_field(name="Ticket Thread", value=ticket_thread.mention, inline=True)
            await user.send(embed=embed_dm)
        except Exception as e:
            LogError(f"Failed to send DM to {user.id}: {e}")

        await ctx.followup.send("Ticket created successfully!", ephemeral=True)

    async def button_claim_ticket(
        self, interaction: discord.Interaction, guild_id: str, user_id: str
    ):
        if guild_id not in self.tickets or user_id not in self.tickets[guild_id]:
            await interaction.followup.send("Ticket no longer exists.", ephemeral=True)
            return

        ticket_data = self.tickets[guild_id][user_id]
        ticket_thread = interaction.guild.get_thread(ticket_data["channel_id"])
        if ticket_thread is None:
            await interaction.followup.send("Ticket thread not found.", ephemeral=True)
            return

        ticket_data["assigned_to"] = interaction.user.id
        ticket_data["status"] = "In Progress"
        ticket_data["last_activity"] = datetime.datetime.utcnow().isoformat()
        self.save_ticket_data(self.tickets)

        embed = discord.Embed(
            title="Ticket Claimed",
            description=f"{interaction.user.mention} has claimed this ticket.",
            color=0x3498DB,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.add_field(name="Ticket ID", value=ticket_data["ticket_id"], inline=True)
        await ticket_thread.send(embed=embed)
        await interaction.followup.send("Ticket claimed.", ephemeral=True)

    async def button_close_ticket(
        self, interaction: discord.Interaction, guild_id: str, user_id: str
    ):
        if guild_id not in self.tickets or user_id not in self.tickets[guild_id]:
            await interaction.followup.send("Ticket not found.", ephemeral=True)
            return

        ticket_data = self.tickets[guild_id][user_id]
        if (
            str(interaction.user.id) != user_id
            and not interaction.user.guild_permissions.administrator
        ):
            await interaction.followup.send(
                "You cannot close this ticket.", ephemeral=True
            )
            return

        ticket_thread = interaction.guild.get_thread(ticket_data["channel_id"])
        if ticket_thread is None:
            await interaction.followup.send("Ticket thread not found.", ephemeral=True)
            return

        transcript_html = await self.generate_transcript_html(ticket_thread)
        transcript_file = discord.File(
            fp=io.StringIO(transcript_html),
            filename=f"transcript-{ticket_thread.id}.html",
        )

        log_channel_id = self.serverconfig[guild_id]["ticketlogchannel"]
        log_channel = interaction.guild.get_channel(log_channel_id)
        if log_channel:
            embed_log = discord.Embed(
                title="Ticket Closed",
                description=f"Ticket for <@{user_id}> has been closed. Transcript attached.",
                color=0xFF0000,
                timestamp=datetime.datetime.utcnow(),
            )
            embed_log.add_field(
                name="Ticket ID", value=ticket_data["ticket_id"], inline=True
            )
            embed_log.add_field(
                name="Closed By", value=interaction.user.mention, inline=True
            )
            await log_channel.send(embed=embed_log, file=transcript_file)

        try:
            dm_embed = discord.Embed(
                title="Ticket Closed",
                description=f"Your ticket in **{interaction.guild.name}** has been closed.\nPlease provide feedback using `/ticket-feedback`.",
                color=0xFF0000,
                timestamp=datetime.datetime.utcnow(),
            )
            dm_embed.add_field(
                name="Ticket ID", value=ticket_data["ticket_id"], inline=True
            )
            user = interaction.guild.get_member(int(user_id))
            if user:
                await user.send(embed=dm_embed)
        except Exception as e:
            LogError(f"Failed to send DM to {user_id}: {e}")

        ticket_data["status"] = "Closed"
        self.save_ticket_data(self.tickets)

        del self.tickets[guild_id][user_id]
        if not self.tickets[guild_id]:
            del self.tickets[guild_id]
        self.save_ticket_data(self.tickets)

        await interaction.followup.send("Ticket closed and deleted.", ephemeral=True)
        await ticket_thread.delete()

    @tasks.loop(minutes=10)
    async def ticket_check_loop(self):
        now = datetime.datetime.utcnow()
        reminder_threshold = datetime.timedelta(hours=1)
        escalation_threshold = datetime.timedelta(hours=2)
        for guild_id, tickets in list(self.tickets.items()):
            guild = self.bot.get_guild(int(guild_id))
            if guild is None:
                continue
            for user_id, ticket_data in list(tickets.items()):
                ticket_thread = guild.get_thread(ticket_data["channel_id"])
                if ticket_thread is None:
                    continue
                last_activity = datetime.datetime.fromisoformat(
                    ticket_data["last_activity"]
                )
                inactivity = now - last_activity
                if (
                    ticket_data["status"] == "Open"
                    and reminder_threshold < inactivity < escalation_threshold
                ):
                    embed_reminder = discord.Embed(
                        title="Ticket Reminder",
                        description="There has been no activity in this ticket for over 1 hour. Please update your ticket or a support agent will follow up shortly.",
                        color=0xFFA500,
                        timestamp=datetime.datetime.utcnow(),
                    )
                    embed_reminder.add_field(
                        name="Ticket ID", value=ticket_data["ticket_id"], inline=True
                    )
                    embed_reminder.add_field(
                        name="Status", value=ticket_data["status"], inline=True
                    )
                    await ticket_thread.send(embed=embed_reminder)
                elif (
                    ticket_data["status"] == "Open"
                    and inactivity >= escalation_threshold
                ):
                    log_channel_id = self.serverconfig[guild_id]["ticketlogchannel"]
                    log_channel = guild.get_channel(log_channel_id)
                    if log_channel:
                        embed_escalation = discord.Embed(
                            title="Ticket Escalation",
                            description=f"Ticket {ticket_data['ticket_id']} has been inactive for over 2 hours and is being escalated.",
                            color=0xFF0000,
                            timestamp=datetime.datetime.utcnow(),
                        )
                        embed_escalation.add_field(
                            name="Ticket ID",
                            value=ticket_data["ticket_id"],
                            inline=True,
                        )
                        embed_escalation.add_field(
                            name="Last Activity",
                            value=ticket_data["last_activity"],
                            inline=True,
                        )
                        await log_channel.send(embed=embed_escalation)
                        ticket_data["status"] = "Escalated"
                        self.save_ticket_data(self.tickets)

    @Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        guild_id = str(guild.id)
        user_id = str(member.id)
        if guild_id in self.tickets and user_id in self.tickets[guild_id]:
            ticket_data = self.tickets[guild_id][user_id]
            ticket_thread = guild.get_thread(ticket_data["channel_id"])
            if ticket_thread:
                log_channel_id = self.serverconfig[guild_id]["ticketlogchannel"]
                log_channel = guild.get_channel(log_channel_id)
                if log_channel:
                    embed_log = discord.Embed(
                        title="Ticket Closed",
                        description=f"Ticket for {member.mention} has been closed because the user left the server.",
                        color=0xFFA500,
                        timestamp=datetime.datetime.utcnow(),
                    )
                    embed_log.set_author(
                        name=guild.name, icon_url=guild.icon.url if guild.icon else None
                    )
                    embed_log.add_field(
                        name="Ticket ID", value=ticket_data["ticket_id"], inline=True
                    )
                    embed_log.add_field(
                        name="User", value=f"{member} ({member.id})", inline=True
                    )
                    await log_channel.send(embed=embed_log)
                try:
                    dm_embed = discord.Embed(
                        title="Ticket Closed",
                        description=f"Your ticket in **{guild.name}** has been closed as you left the server.",
                        color=0xFFA500,
                        timestamp=datetime.datetime.utcnow(),
                    )
                    dm_embed.set_author(
                        name=guild.name, icon_url=guild.icon.url if guild.icon else None
                    )
                    dm_embed.add_field(
                        name="Ticket ID", value=ticket_data["ticket_id"], inline=True
                    )
                    await member.send(embed=dm_embed)
                except Exception as e:
                    LogError(f"Failed to send DM to {member.id}: {e}")
                try:
                    await ticket_thread.delete()
                except Exception as e:
                    LogError(f"Failed to delete ticket thread for {member.id}: {e}")
                del self.tickets[guild_id][user_id]
                if not self.tickets[guild_id]:
                    del self.tickets[guild_id]
                self.save_ticket_data(self.tickets)

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if isinstance(message.channel, discord.DMChannel):
            user = message.author
            # Forward DM only if a ticket exists – otherwise ignore
            for guild_id, tickets in self.tickets.items():
                if str(user.id) in tickets:
                    ticket_data = tickets[str(user.id)]
                    thread = self.bot.get_channel(ticket_data["channel_id"])
                    if thread:
                        try:
                            content = (
                                f"**{user.name}#{user.discriminator}:** {message.content}"
                                if message.content
                                else f"**{user.name}#{user.discriminator}**"
                            )
                            await thread.send(content)
                            for attachment in message.attachments:
                                await thread.send(attachment.url)
                            try:
                                await message.add_reaction("✅")
                            except Exception as e:
                                LogError(f"Failed to add reaction to DM message: {e}")
                            ticket_data["last_activity"] = (
                                datetime.datetime.utcnow().isoformat()
                            )
                            self.save_ticket_data(self.tickets)
                        except Exception as e:
                            LogError(f"Error forwarding DM message: {e}")
                    break

        elif message.guild is not None:
            guild_id = str(message.guild.id)
            if guild_id in self.tickets:
                for user_id, ticket_data in self.tickets[guild_id].items():
                    if message.channel.id == ticket_data["channel_id"]:
                        if message.content.startswith("."):
                            return
                        user = self.bot.get_user(int(user_id))
                        if user:
                            try:
                                content = (
                                    f"**Support ({message.author.name}#{message.author.discriminator}):** {message.content}"
                                    if message.content
                                    else f"**Support ({message.author.name}#{message.author.discriminator})**"
                                )
                                await user.send(content)
                                for attachment in message.attachments:
                                    await user.send(attachment.url)
                                try:
                                    await message.add_reaction("✅")
                                except Exception as e:
                                    LogError(
                                        f"Failed to add reaction to ticket thread message: {e}"
                                    )
                            except Exception as e:
                                LogError(f"Error forwarding message to user DM: {e}")
                                try:
                                    await message.add_reaction("❌")
                                except Exception as e2:
                                    LogError(f"Failed to add failure reaction: {e2}")
                        break


def setup(bot):
    cog = TicketSystem(bot)
    bot.add_cog(cog)
