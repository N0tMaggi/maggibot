import discord
from discord.ext import commands, tasks
from discord.ext.commands import Cog
import datetime
import json
import os
import io
import handlers.config as config
from handlers.debug import LogDebug, LogError




def NoPrivateMessage(ctx):
    if isinstance(ctx.channel, discord.DMChannel):
        raise commands.NoPrivateMessage("This command can only be used in a server. Please use it on the corresponding server.")
    return True

class TicketSystem(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.serverconfig = config.loadserverconfig()
        self.tickets = config.load_ticket_data()
        self.ticket_check_loop.start()
        self.save_ticket_data = config.save_ticket_data

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
    

    @commands.slash_command(name="setup-ticketsystem", description="Setup the Ticket System for the server")
    @commands.has_permissions(administrator=True)
    async def setup_ticketsystem(
        self,
        ctx: discord.ApplicationContext,
        role: discord.Role,
        logchannel: discord.TextChannel,
        categorie: discord.CategoryChannel
    ):
        try:
            guild_id = str(ctx.guild.id)
            LogDebug(f"Current server config for guild {guild_id}: {self.serverconfig}")

            if guild_id not in self.serverconfig:
                self.serverconfig[guild_id] = {}

            self.serverconfig[guild_id]["ticketrole"] = role.id
            self.serverconfig[guild_id]["ticketlogchannel"] = logchannel.id
            self.serverconfig[guild_id]["ticketcategorie"] = categorie.id
            LogDebug(f"Updated server config for guild {guild_id}: {self.serverconfig[guild_id]}")

            config.saveserverconfig(self.serverconfig)

            embed = discord.Embed(
                title="Ticket System Setup",
                description="The Ticket System has been successfully set up.",
                color=0x00ff00,
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed.add_field(name="Ticket Role", value=role.mention, inline=True)
            embed.add_field(name="Ticket Log Channel", value=logchannel.mention, inline=True)
            embed.add_field(name="Ticket Category", value=categorie.name, inline=True)
            embed.add_field(name="Guild ID", value=ctx.guild.id, inline=False)

            await ctx.respond(embed=embed)

        except Exception as e:
            LogError(f"An error occurred while setting up the Ticket System: {e}")
            raise Exception(f"An error occurred while setting up the Ticket System: {e}")
        

    @commands.slash_command(name="setup-deleteticketconfig", description="Deletes the Ticket System configuration entries for the server")
    @commands.has_permissions(administrator=True)
    async def setup_deleteticketconfig(
        self,
        ctx: discord.ApplicationContext
    ):
        try:
            guild_id = str(ctx.guild.id)
            LogDebug(f"Current server config for guild {guild_id}: {self.serverconfig}")

            if guild_id not in self.serverconfig or "ticketrole" not in self.serverconfig[guild_id]:
                embed = discord.Embed(
                    title="Ticket System Setup Deletion",
                    description="No Ticket System configuration found for this server.",
                    color=0xff0000,
                    timestamp=datetime.datetime.utcnow()
                )
                embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
                embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                                 icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
                await ctx.respond(embed=embed)
                return

            self.serverconfig[guild_id].pop("ticketrole", None)
            self.serverconfig[guild_id].pop("ticketlogchannel", None)
            self.serverconfig[guild_id].pop("ticketcategorie", None)
            LogDebug(f"Removed Ticket System entries for guild {guild_id}: {self.serverconfig[guild_id]}")

            config.saveserverconfig(self.serverconfig)

            embed = discord.Embed(
                title="Ticket System Setup Deletion",
                description="The Ticket System configuration entries have been successfully deleted.",
                color=0xff0000,
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                             icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

            await ctx.respond(embed=embed)

        except Exception as e:
            LogError(f"An error occurred while deleting the Ticket System configuration entries: {e}")
            raise Exception(f"An error occurred while deleting the Ticket System configuration entries: {e}")



    @commands.slash_command(name="ticket-create", description="Create a ticket for support")
    async def ticket_create(self, ctx: discord.ApplicationContext):
        if not NoPrivateMessage(ctx):
            return
        
        guild_id = str(ctx.guild.id)
        if guild_id not in self.serverconfig or \
           "ticketrole" not in self.serverconfig[guild_id] or \
           "ticketlogchannel" not in self.serverconfig[guild_id] or \
           "ticketcategorie" not in self.serverconfig[guild_id]:
            await ctx.respond("Ticket system is not set up on this server.", ephemeral=True)
            return

        try:
            await self.check_if_able_dm(ctx.author)
        except commands.Forbidden:
            await ctx.respond("I cannot DM you, please check your DM settings.", ephemeral=True)
            return

        if guild_id in self.tickets and str(ctx.author.id) in self.tickets[guild_id]:
            await ctx.respond("You already have an open ticket.", ephemeral=True)
            return

        category_id = self.serverconfig[guild_id]["ticketcategorie"]
        category = ctx.guild.get_channel(category_id)
        if category is None or not isinstance(category, discord.CategoryChannel):
            await ctx.respond("Ticket category is invalid or not found.", ephemeral=True)
            return

        ticket_role_id = self.serverconfig[guild_id]["ticketrole"]
        ticket_role = ctx.guild.get_role(ticket_role_id)
        if ticket_role is None:
            await ctx.respond("Ticket role is invalid or not found.", ephemeral=True)
            return

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ticket_role: discord.PermissionOverwrite(read_messages=True),
            self.bot.user: discord.PermissionOverwrite(read_messages=True)
        }
        channel_name = f"ticket-{ctx.author.name}-{ctx.author.discriminator}"
        try:
            ticket_channel = await ctx.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites
            )
        except Exception as e:
            LogError(f"Failed to create ticket channel: {e}")
            await ctx.respond("Failed to create ticket channel.", ephemeral=True)
            return

        ticket_id = self.generate_ticket_id(ctx.author.id)
        now_iso = datetime.datetime.utcnow().isoformat()
        ticket_data = {
            "channel_id": ticket_channel.id,
            "ticket_id": ticket_id,
            "status": "Open",
            "created_at": now_iso,
            "last_activity": now_iso,
            "assigned_to": None,
            "feedback": None
        }
        if guild_id not in self.tickets:
            self.tickets[guild_id] = {}
        self.tickets[guild_id][str(ctx.author.id)] = ticket_data
        self.save_ticket_data(self.tickets)

        embed_channel = discord.Embed(
            title="Ticket Created",
            description=f"{ctx.author.mention}, your ticket has been opened. Support will contact you soon.",
            color=0x00ff00,
            timestamp=datetime.datetime.utcnow()
        )
        embed_channel.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed_channel.add_field(name="Ticket ID", value=ticket_id, inline=True)
        embed_channel.add_field(name="Status", value="Open", inline=True)
        embed_channel.add_field(name="Created At", value=now_iso, inline=False)
        embed_channel.set_footer(text="Use /ticket-delete to close the ticket. Use /ticket-assign to assign a support agent.")
        await ticket_channel.send(embed=embed_channel)

        # Log embed for ticket creation
        log_channel_id = self.serverconfig[guild_id]["ticketlogchannel"]
        log_channel = ctx.guild.get_channel(log_channel_id)
        if log_channel:
            embed_log = discord.Embed(
                title="Ticket Created",
                description=f"Ticket created by {ctx.author.mention} in {ticket_channel.mention}.",
                color=0x00ff00,
                timestamp=datetime.datetime.utcnow()
            )
            embed_log.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed_log.add_field(name="Ticket ID", value=ticket_id, inline=True)
            embed_log.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})", inline=True)
            embed_log.add_field(name="Channel", value=ticket_channel.mention, inline=True)
            await log_channel.send(embed=embed_log)

        # DM embed for ticket creation
        embed_dm = discord.Embed(
            title="Ticket Opened",
            description=f"Your ticket in **{ctx.guild.name}** has been successfully opened.",
            color=0x00ff00,
            timestamp=datetime.datetime.utcnow()
        )
        embed_dm.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed_dm.add_field(name="Ticket ID", value=ticket_id, inline=True)
        embed_dm.add_field(name="Ticket Channel", value=ticket_channel.mention, inline=True)
        try:
            await ctx.author.send(embed=embed_dm)
        except Exception as e:
            LogError(f"Failed to send DM to {ctx.author.id}: {e}")

        await ctx.respond("Ticket created successfully!", ephemeral=True)

    @commands.slash_command(name="ticket-delete", description="Close and delete your ticket")
    async def ticket_delete(self, ctx: discord.ApplicationContext):
        if not NoPrivateMessage(ctx):
            return
        
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)
        if guild_id not in self.tickets or user_id not in self.tickets[guild_id]:
            await ctx.respond("You don't have an open ticket to delete.", ephemeral=True)
            return
        
        ticket_data = self.tickets[guild_id][user_id]
        ticket_channel_id = ticket_data["channel_id"]
        if ctx.channel.id != ticket_channel_id and not ctx.author.guild_permissions.administrator:
            await ctx.respond("You can only delete your ticket in the ticket channel.", ephemeral=True)
            return

        ticket_channel = ctx.guild.get_channel(ticket_channel_id)
        if ticket_channel is None:
            await ctx.respond("Ticket channel not found.", ephemeral=True)
            return

        transcript_lines = []
        async for message in ticket_channel.history(limit=None, oldest_first=True):
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            author = f"{message.author.name}#{message.author.discriminator}"
            content = message.content
            transcript_lines.append(f"[{timestamp}] {author}: {content}")
            if message.attachments:
                for attachment in message.attachments:
                    transcript_lines.append(f"[{timestamp}] {author} attached: {attachment.url}")
        transcript_text = "\n".join(transcript_lines)
        transcript_file = discord.File(fp=io.StringIO(transcript_text), filename=f"transcript-{ticket_channel.id}.txt")

        # Log embed for ticket deletion
        log_channel_id = self.serverconfig[guild_id]["ticketlogchannel"]
        log_channel = ctx.guild.get_channel(log_channel_id)
        if log_channel:
            embed_log = discord.Embed(
                title="Ticket Closed",
                description=f"Ticket for {ctx.author.mention} has been closed. Transcript attached.",
                color=0xff0000,
                timestamp=datetime.datetime.utcnow()
            )
            embed_log.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed_log.add_field(name="Ticket ID", value=ticket_data["ticket_id"], inline=True)
            embed_log.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})", inline=True)
            await log_channel.send(embed=embed_log, file=transcript_file)

        try:
            dm_embed = discord.Embed(
                title="Ticket Closed",
                description=f"Your ticket in **{ctx.guild.name}** has been closed.\nPlease provide feedback using `/ticket-feedback`.",
                color=0xff0000,
                timestamp=datetime.datetime.utcnow()
            )
            dm_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            dm_embed.add_field(name="Ticket ID", value=ticket_data["ticket_id"], inline=True)
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
        await ticket_channel.delete()

    @commands.slash_command(name="ticket-assign", description="Assign or transfer a ticket to a support agent")
    async def ticket_assign(self, ctx: discord.ApplicationContext, agent: discord.Member):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)
        if guild_id not in self.tickets or user_id not in self.tickets[guild_id]:
            await ctx.respond("You don't have an open ticket to assign.", ephemeral=True)
            return
        
        ticket_data = self.tickets[guild_id][user_id]
        ticket_channel = ctx.guild.get_channel(ticket_data["channel_id"])
        if ticket_channel is None:
            await ctx.respond("Ticket channel not found.", ephemeral=True)
            return

        ticket_data["assigned_to"] = agent.id
        ticket_data["status"] = "In Progress"
        ticket_data["last_activity"] = datetime.datetime.utcnow().isoformat()
        self.save_ticket_data(self.tickets)

        embed_assign = discord.Embed(
            title="Ticket Assigned",
            description=f"Ticket {ticket_data['ticket_id']} has been assigned to {agent.mention}.",
            color=0x0000ff,
            timestamp=datetime.datetime.utcnow()
        )
        embed_assign.add_field(name="Ticket ID", value=ticket_data["ticket_id"], inline=True)
        embed_assign.add_field(name="Assigned To", value=agent.mention, inline=True)
        embed_assign.set_footer(text="Ticket status updated to In Progress.")
        await ticket_channel.send(embed=embed_assign)
        await ctx.respond("Ticket assignment updated.", ephemeral=True)

    @commands.slash_command(name="ticket-feedback", description="Provide feedback for a closed ticket")
    async def ticket_feedback(self, ctx: discord.ApplicationContext, ticket_id: str, rating: int, comment: str = None):
        if rating < 1 or rating > 5:
            await ctx.respond("Rating must be between 1 and 5.", ephemeral=True)
            return

        feedback_embed = discord.Embed(
            title="Ticket Feedback Received",
            description=f"Feedback for Ticket ID: {ticket_id}",
            color=0x00ff00,
            timestamp=datetime.datetime.utcnow()
        )
        feedback_embed.add_field(name="Rating", value=str(rating), inline=True)
        feedback_embed.add_field(name="Comment", value=comment if comment else "No comment provided", inline=False)
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
            await ctx.respond("Feedback could not be sent. Please contact support.", ephemeral=True)

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
                ticket_channel = guild.get_channel(ticket_data["channel_id"])
                if ticket_channel is None:
                    continue
                last_activity = datetime.datetime.fromisoformat(ticket_data["last_activity"])
                inactivity = now - last_activity
                if ticket_data["status"] == "Open" and reminder_threshold < inactivity < escalation_threshold:
                    embed_reminder = discord.Embed(
                        title="Ticket Reminder",
                        description="There has been no activity in this ticket for over 1 hour. Please update your ticket or a support agent will follow up shortly.",
                        color=0xffa500,
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed_reminder.add_field(name="Ticket ID", value=ticket_data["ticket_id"], inline=True)
                    embed_reminder.add_field(name="Status", value=ticket_data["status"], inline=True)
                    await ticket_channel.send(embed=embed_reminder)
                elif ticket_data["status"] == "Open" and inactivity >= escalation_threshold:
                    log_channel_id = self.serverconfig[guild_id]["ticketlogchannel"]
                    log_channel = guild.get_channel(log_channel_id)
                    if log_channel:
                        embed_escalation = discord.Embed(
                            title="Ticket Escalation",
                            description=f"Ticket {ticket_data['ticket_id']} has been inactive for over 2 hours and is being escalated.",
                            color=0xff0000,
                            timestamp=datetime.datetime.utcnow()
                        )
                        embed_escalation.add_field(name="Ticket ID", value=ticket_data["ticket_id"], inline=True)
                        embed_escalation.add_field(name="Last Activity", value=ticket_data["last_activity"], inline=True)
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
            ticket_channel = guild.get_channel(ticket_data["channel_id"])
            if ticket_channel:
                log_channel_id = self.serverconfig[guild_id]["ticketlogchannel"]
                log_channel = guild.get_channel(log_channel_id)
                if log_channel:
                    embed_log = discord.Embed(
                        title="Ticket Closed",
                        description=f"Ticket for {member.mention} has been closed because the user left the server.",
                        color=0xffa500,
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed_log.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)
                    embed_log.add_field(name="Ticket ID", value=ticket_data["ticket_id"], inline=True)
                    embed_log.add_field(name="User", value=f"{member} ({member.id})", inline=True)
                    await log_channel.send(embed=embed_log)
                try:
                    dm_embed = discord.Embed(
                        title="Ticket Closed",
                        description=f"Your ticket in **{guild.name}** has been closed as you left the server.",
                        color=0xffa500,
                        timestamp=datetime.datetime.utcnow()
                    )
                    dm_embed.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)
                    dm_embed.add_field(name="Ticket ID", value=ticket_data["ticket_id"], inline=True)
                    await member.send(embed=dm_embed)
                except Exception as e:
                    LogError(f"Failed to send DM to {member.id}: {e}")
                try:
                    await ticket_channel.delete()
                except Exception as e:
                    LogError(f"Failed to delete ticket channel for {member.id}: {e}")
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
                    channel = self.bot.get_channel(ticket_data["channel_id"])
                    if channel:
                        try:
                            content = f"**{user.name}#{user.discriminator}:** {message.content}" if message.content else f"**{user.name}#{user.discriminator}**"
                            await channel.send(content)
                            for attachment in message.attachments:
                                await channel.send(attachment.url)
                            try:
                                await message.add_reaction("✅")
                            except Exception as e:
                                LogError(f"Failed to add reaction to DM message: {e}")
                            ticket_data["last_activity"] = datetime.datetime.utcnow().isoformat()
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
                                content = f"**Support ({message.author.name}#{message.author.discriminator}):** {message.content}" if message.content else f"**Support ({message.author.name}#{message.author.discriminator})**"
                                await user.send(content)
                                for attachment in message.attachments:
                                    await user.send(attachment.url)
                                try:
                                    await message.add_reaction("✅")
                                except Exception as e:
                                    LogError(f"Failed to add reaction to ticket channel message: {e}")
                            except Exception as e:
                                LogError(f"Error forwarding message to user DM: {e}")
                                try:
                                    await message.add_reaction("❌")
                                except Exception as e2:
                                    LogError(f"Failed to add failure reaction: {e2}")
                        break

def setup(bot):
    bot.add_cog(TicketSystem(bot))
