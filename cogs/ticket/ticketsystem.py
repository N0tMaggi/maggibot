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
        self.save_ticket_data = config.save_ticket_data

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

    def get_tag_by_name(self, forum: discord.ForumChannel, name: str):
        for tag in forum.available_tags:
            if tag.name.lower() == name.lower():
                return tag
        return None

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
        """Generate an HTML transcript for a ticket thread with Discord-like styling."""
        lines = [
            "<!DOCTYPE html>",
            "<html><head><meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "<style>",
            "* { box-sizing: border-box; }",
            "body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #313338; color: #dbdee1; margin: 0; padding: 20px; line-height: 1.375; }",
            ".container { max-width: 1200px; margin: 0 auto; background: #2b2d31; border-radius: 8px; overflow: hidden; }",
            ".header { background: #1e1f22; padding: 16px 20px; border-bottom: 1px solid #3f4147; }",
            ".header h2 { margin: 0; color: #f2f3f5; font-size: 20px; font-weight: 600; }",
            ".header .info { color: #b5bac1; font-size: 14px; margin-top: 4px; }",
            ".messages { padding: 0; }",
            ".message { padding: 8px 16px; position: relative; }",
            ".message:hover { background: #2e3035; }",
            ".message-group { margin-bottom: 17px; }",
            ".message-header { display: flex; align-items: baseline; margin-bottom: 2px; }",
            ".avatar { width: 40px; height: 40px; border-radius: 50%; margin-right: 16px; background: #5865f2; display: flex; align-items: center; justify-content: center; font-weight: 600; color: white; font-size: 16px; flex-shrink: 0; }",
            ".message-content { margin-left: 56px; }",
            ".author { font-weight: 500; color: #f2f3f5; margin-right: 8px; font-size: 16px; }",
            ".timestamp { color: #949ba4; font-size: 12px; font-weight: 500; }",
            ".content { color: #dbdee1; margin-top: 2px; word-wrap: break-word; }",
            ".content p { margin: 0; }",
            ".attachments { margin-top: 8px; }",
            ".attachment { background: #2b2d31; border: 1px solid #3f4147; border-radius: 8px; padding: 8px; margin-bottom: 8px; display: inline-block; }",
            ".attachment img { max-width: 400px; max-height: 300px; border-radius: 4px; display: block; }",
            ".attachment a { color: #00a8fc; text-decoration: none; display: flex; align-items: center; }",
            ".attachment a:hover { text-decoration: underline; }",
            ".embed { background: #2f3136; border-left: 4px solid #5865f2; border-radius: 4px; padding: 16px; margin-top: 8px; max-width: 520px; }",
            ".embed-author { display: flex; align-items: center; margin-bottom: 8px; }",
            ".embed-author-icon { width: 20px; height: 20px; border-radius: 50%; margin-right: 8px; }",
            ".embed-author-name { color: #f2f3f5; font-size: 14px; font-weight: 600; }",
            ".embed-title { color: #00a8fc; font-size: 16px; font-weight: 600; margin-bottom: 8px; }",
            ".embed-title a { color: #00a8fc; text-decoration: none; }",
            ".embed-title a:hover { text-decoration: underline; }",
            ".embed-description { color: #dbdee1; margin-bottom: 8px; }",
            ".embed-fields { display: grid; gap: 8px; }",
            ".embed-field { }",
            ".embed-field.inline { display: inline-block; margin-right: 16px; min-width: 150px; }",
            ".embed-field-name { color: #f2f3f5; font-size: 14px; font-weight: 600; margin-bottom: 2px; }",
            ".embed-field-value { color: #dbdee1; font-size: 14px; }",
            ".embed-footer { display: flex; align-items: center; margin-top: 8px; color: #949ba4; font-size: 12px; }",
            ".embed-footer-icon { width: 16px; height: 16px; border-radius: 50%; margin-right: 8px; }",
            ".embed-thumbnail { float: right; margin-left: 16px; margin-bottom: 8px; }",
            ".embed-thumbnail img { max-width: 80px; max-height: 80px; border-radius: 4px; }",
            ".embed-image { margin-top: 16px; }",
            ".embed-image img { max-width: 400px; max-height: 300px; border-radius: 4px; }",
            ".system-message { background: #2f3136; border-left: 4px solid #faa61a; padding: 16px; margin: 8px 16px; border-radius: 4px; }",
            ".system-message .content { color: #949ba4; font-size: 14px; }",
            ".bot-tag { background: #5865f2; color: white; font-size: 10px; font-weight: 600; padding: 1px 4px; border-radius: 3px; margin-left: 4px; vertical-align: middle; }",
            ".mention { background: rgba(88, 101, 242, 0.3); color: #dee0fc; padding: 0 2px; border-radius: 3px; }",
            ".code-inline { background: #1e1f22; color: #dbdee1; padding: 2px 4px; border-radius: 3px; font-family: 'Consolas', 'Monaco', monospace; font-size: 14px; }",
            ".code-block { background: #1e1f22; color: #dbdee1; padding: 8px; border-radius: 4px; font-family: 'Consolas', 'Monaco', monospace; font-size: 14px; margin: 8px 0; overflow-x: auto; }",
            "</style></head><body>",
            "<div class='container'>",
            f"<div class='header'>",
            f"<h2>#{html.escape(thread.name)}</h2>",
            f"<div class='info'>Transcript generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>",
            f"</div>",
            "<div class='messages'>",
        ]
        
        last_author = None
        last_timestamp = None
        
        async for message in thread.history(limit=None, oldest_first=True):
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            author_name = message.author.display_name
            author_discriminator = f"#{message.author.discriminator}" if message.author.discriminator != "0" else ""
            is_bot = message.author.bot
            
            # Check if we need a new message group
            time_diff = None
            if last_timestamp:
                time_diff = (message.created_at - last_timestamp).total_seconds()
            
            new_group = (last_author != message.author.id or 
                        time_diff is None or time_diff > 420)  # 7 minutes
            
            if new_group:
                if last_author is not None:
                    lines.append("</div>")  # Close previous message group
                
                lines.append("<div class='message-group'>")
                lines.append("<div class='message'>")
                
                # Avatar (first letter of username)
                avatar_letter = author_name[0].upper() if author_name else "?"
                lines.append(f"<div class='avatar'>{avatar_letter}</div>")
                
                lines.append("<div class='message-content'>")
                lines.append("<div class='message-header'>")
                lines.append(f"<span class='author'>{html.escape(author_name)}{html.escape(author_discriminator)}</span>")
                if is_bot:
                    lines.append("<span class='bot-tag'>BOT</span>")
                lines.append(f"<span class='timestamp'>{timestamp}</span>")
                lines.append("</div>")
            else:
                lines.append("<div class='message'>")
                lines.append("<div class='message-content' style='margin-left: 0;'>")
            
            # Message content
            if message.content:
                content = html.escape(message.content)
                # Simple formatting for mentions, code blocks, etc.
                content = content.replace("```", "<div class='code-block'>").replace("```", "</div>")
                content = content.replace("`", "<span class='code-inline'>").replace("`", "</span>")
                lines.append(f"<div class='content'>{content}</div>")
            
            # Attachments
            if message.attachments:
                lines.append("<div class='attachments'>")
                for attachment in message.attachments:
                    lines.append("<div class='attachment'>")
                    if attachment.content_type and attachment.content_type.startswith("image"):
                        lines.append(f"<img src='{attachment.url}' alt='{html.escape(attachment.filename)}'>")
                    else:
                        lines.append(f"<a href='{attachment.url}' target='_blank'>📎 {html.escape(attachment.filename)}</a>")
                    lines.append("</div>")
                lines.append("</div>")
            
            # Embeds
            if message.embeds:
                for embed in message.embeds:
                    embed_color = f"#{embed.color:06x}" if embed.color else "#5865f2"
                    lines.append(f"<div class='embed' style='border-left-color: {embed_color};'>")
                    
                    # Embed author
                    if embed.author:
                        lines.append("<div class='embed-author'>")
                        if embed.author.icon_url:
                            lines.append(f"<img class='embed-author-icon' src='{embed.author.icon_url}' alt=''>")
                        lines.append(f"<span class='embed-author-name'>{html.escape(embed.author.name)}</span>")
                        lines.append("</div>")
                    
                    # Embed thumbnail
                    if embed.thumbnail:
                        lines.append("<div class='embed-thumbnail'>")
                        lines.append(f"<img src='{embed.thumbnail.url}' alt='Thumbnail'>")
                        lines.append("</div>")
                    
                    # Embed title
                    if embed.title:
                        title_html = html.escape(embed.title)
                        if embed.url:
                            title_html = f"<a href='{embed.url}' target='_blank'>{title_html}</a>"
                        lines.append(f"<div class='embed-title'>{title_html}</div>")
                    
                    # Embed description
                    if embed.description:
                        lines.append(f"<div class='embed-description'>{html.escape(embed.description)}</div>")
                    
                    # Embed fields
                    if embed.fields:
                        lines.append("<div class='embed-fields'>")
                        for field in embed.fields:
                            field_class = "embed-field"
                            if field.inline:
                                field_class += " inline"
                            lines.append(f"<div class='{field_class}'>")
                            lines.append(f"<div class='embed-field-name'>{html.escape(field.name)}</div>")
                            lines.append(f"<div class='embed-field-value'>{html.escape(field.value)}</div>")
                            lines.append("</div>")
                        lines.append("</div>")
                    
                    # Embed image
                    if embed.image:
                        lines.append("<div class='embed-image'>")
                        lines.append(f"<img src='{embed.image.url}' alt='Embed image'>")
                        lines.append("</div>")
                    
                    # Embed footer
                    if embed.footer:
                        lines.append("<div class='embed-footer'>")
                        if embed.footer.icon_url:
                            lines.append(f"<img class='embed-footer-icon' src='{embed.footer.icon_url}' alt=''>")
                        footer_text = html.escape(embed.footer.text)
                        if embed.timestamp:
                            footer_text += f" • {embed.timestamp.strftime('%m/%d/%Y')}"
                        lines.append(f"<span>{footer_text}</span>")
                        lines.append("</div>")
                    
                    lines.append("</div>")
            
            lines.append("</div>")  # Close message-content
            lines.append("</div>")  # Close message
            
            last_author = message.author.id
            last_timestamp = message.created_at
        
        if last_author is not None:
            lines.append("</div>")  # Close last message group
        
        lines.extend([
            "</div>",  # Close messages
            "</div>",  # Close container
            "</body></html>"
        ])
        
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
            new_tag = self.get_tag_by_name(forum_channel, "new-ticket")
            ticket_thread = await forum_channel.create_thread(
                name=channel_name,
                content=ticket_role.mention,
                applied_tags=[new_tag] if new_tag else None,
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
                "Our support team will reply soon. Keep the Ticket ID below for reference."
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
        embed_dm.set_footer(text="Thank you for contacting support!")
        try:
            await ctx.author.send(embed=embed_dm)
        except Exception as e:
            LogError(f"Failed to send DM to {ctx.author.id}: {e}")

        await ctx.respond("Ticket created successfully!", ephemeral=True)

    @commands.slash_command(
        name="ticket-delete", description="Close your ticket"
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

        # Update ticket status to Closed before locking
        ticket_data["status"] = "Closed"
        self.save_ticket_data(self.tickets)

        del self.tickets[guild_id][user_id]
        if not self.tickets[guild_id]:
            del self.tickets[guild_id]
        self.save_ticket_data(self.tickets)

        closed_tag = self.get_tag_by_name(ticket_thread.parent, "closed")
        edit_kwargs = {"locked": True}
        if closed_tag:
            edit_kwargs["applied_tags"] = [closed_tag]
        await ticket_thread.edit(**edit_kwargs)

        await ctx.respond("Ticket closed.", ephemeral=True)

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
            new_tag = self.get_tag_by_name(forum_channel, "new-ticket")
            ticket_thread = await forum_channel.create_thread(
                name=channel_name,
                content=ticket_role.mention,
                applied_tags=[new_tag] if new_tag else None,
            )
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
                description=(
                    f"Your ticket in **{ctx.guild.name}** has been successfully opened.\n"
                    "Our support team will reply soon. Keep the Ticket ID below for reference."
                ),
                color=0x00FF00,
                timestamp=datetime.datetime.utcnow(),
            )
            embed_dm.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed_dm.add_field(name="Ticket ID", value=ticket_id, inline=True)
            embed_dm.add_field(name="Ticket Thread", value=ticket_thread.mention, inline=True)
            embed_dm.set_footer(text="Thank you for contacting support!")
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

        closed_tag = self.get_tag_by_name(ticket_thread.parent, "closed")
        edit_kwargs = {"locked": True}
        if closed_tag:
            edit_kwargs["applied_tags"] = [closed_tag]
        await ticket_thread.edit(**edit_kwargs)

        await interaction.followup.send("Ticket closed.", ephemeral=True)

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

    @ticket_check_loop.before_loop
    async def before_ticket_check(self):
        await self.bot.wait_until_ready()

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
    async def startup():
        await bot.wait_until_ready()
        bot.add_view(cog.TicketOpenView(cog))
        cog.ticket_check_loop.start()

    bot.loop.create_task(startup())
