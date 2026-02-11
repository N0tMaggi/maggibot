import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup
import datetime

class CentralSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    setup = SlashCommandGroup(
        'setup',
        'Centralized setup commands'
    )

    # Log Channel
    @setup.command(name='logchannel', description='Set the log channel for the server')
    @commands.has_permissions(administrator=True)
    async def setup_logchannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        cog = self.bot.get_cog('Server')
        if cog:
            await cog.settings_logchannel(ctx, channel)
        else:
            await ctx.respond('Logchannel setup not available.', ephemeral=True)

    # Voice Gate
    @setup.command(name='voicegate', description='Set up a voice gate channel for this server')
    @commands.has_permissions(administrator=True)
    async def setup_voicegate(self, ctx: discord.ApplicationContext, gate_channel: discord.VoiceChannel, final_channel: discord.VoiceChannel, need_accept_rules: bool):
        cog = self.bot.get_cog('Server')
        if cog:
            await cog.setup_voicegate(ctx, gate_channel, final_channel, need_accept_rules)
        else:
            await ctx.respond('Voicegate setup not available.', ephemeral=True)

    @setup.command(name='showvoicegate', description='Show the current voice gate settings for this server')
    @commands.has_permissions(administrator=True)
    async def setup_showvoicegate(self, ctx: discord.ApplicationContext):
        cog = self.bot.get_cog('Server')
        if cog:
            await cog.setup_showvoicegatesettings(ctx)
        else:
            await ctx.respond('Voicegate settings not available.', ephemeral=True)

    @setup.command(name='deletevoicegate', description='Delete the voice gate configuration for the given voice channel')
    @commands.has_permissions(administrator=True)
    async def setup_deletevoicegate(self, ctx: discord.ApplicationContext, gate_channel: discord.VoiceChannel):
        cog = self.bot.get_cog('Server')
        if cog:
            await cog.setup_deletevoicegate(ctx, gate_channel)
        else:
            await ctx.respond('Delete voicegate not available.', ephemeral=True)

    # Autorole
    @setup.command(name='autorole', description='Setup autorole for the server')
    @commands.has_permissions(administrator=True)
    async def setup_autorole(self, ctx: discord.ApplicationContext, role: discord.Role):
        cog = self.bot.get_cog('Server')
        if cog:
            await cog.setup_autorole(ctx, role)
        else:
            await ctx.respond('Autorole setup not available.', ephemeral=True)

    @setup.command(name='deleteautorole', description='Delete autorole configuration for the server')
    @commands.has_permissions(administrator=True)
    async def setup_deleteautorole(self, ctx: discord.ApplicationContext):
        cog = self.bot.get_cog('Server')
        if cog:
            await cog.setup_deleteautorole(ctx)
        else:
            await ctx.respond('Delete autorole not available.', ephemeral=True)

    # Admin Feedback
    @setup.command(name='adminfeedback', description='Set up admin feedback')
    @commands.has_permissions(administrator=True)
    async def setup_adminfeedback(self, ctx: discord.ApplicationContext, team_role: discord.Role):
        cog = self.bot.get_cog('Server')
        if cog:
            await cog.setup_admin_feedback(ctx, team_role)
        else:
            await ctx.respond('Admin feedback setup not available.', ephemeral=True)

    @setup.command(name='deleteadminfeedback', description='Remove the admin feedback system')
    @commands.has_permissions(administrator=True)
    async def setup_deleteadminfeedback(self, ctx: discord.ApplicationContext):
        cog = self.bot.get_cog('Server')
        if cog:
            await cog.setup_delete_admin_feedback(ctx)
        else:
            await ctx.respond('Delete admin feedback not available.', ephemeral=True)

    # Ticket System
    @setup.command(name='ticketsystem-setup', description='Setup the Ticket System for the server')
    @commands.has_permissions(administrator=True)
    async def setup_ticketsystem(self, ctx: discord.ApplicationContext, role: discord.Role, logchannel: discord.TextChannel, forum: discord.ForumChannel):
        cog = self.bot.get_cog('TicketSystem')
        if cog:
            await cog.setup_ticketsystem(ctx, role, logchannel, forum)
        else:
            await ctx.respond('Ticket system setup not available.', ephemeral=True)

    @setup.command(name='ticketsystem', description='Manage the ticket system')
    @commands.has_permissions(administrator=True)
    async def setup_ticketsystem_central(self, ctx: discord.ApplicationContext):
        cog = self.bot.get_cog('TicketSystem')
        if not cog:
            await ctx.respond('Ticket system not available.', ephemeral=True)
            return

        serverconfig = cog.serverconfig.get(str(ctx.guild.id), {})
        embed = discord.Embed(
            title='Ticket System Configuration',
            color=0x9B59B6,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name='Ticket Role', value=f"<@&{serverconfig.get('ticketrole','N/A')}>", inline=False)
        embed.add_field(name='Log Channel', value=f"<#{serverconfig.get('ticketlogchannel','N/A')}>", inline=False)
        forum = serverconfig.get('ticketforum')
        embed.add_field(name='Forum', value=f"{ctx.guild.get_channel(forum).name if forum else 'N/A'}", inline=False)
        embed.set_footer(text='Use /setup ticketsystem-setup to change settings or /setup-sendticket to post a panel.')
        await ctx.respond(embed=embed, ephemeral=True)

    @setup.command(name='deleteticketconfig', description='Delete the Ticket System configuration entries for the server')
    @commands.has_permissions(administrator=True)
    async def setup_deleteticketconfig(self, ctx: discord.ApplicationContext):
        cog = self.bot.get_cog('TicketSystem')
        if cog:
            await cog.setup_deleteticketconfig(ctx)
        else:
            await ctx.respond('Delete ticket config not available.', ephemeral=True)

    # Verify System
    @setup.command(name='verifysystem', description='Set up the verify system for this server')
    @commands.has_permissions(administrator=True)
    async def setup_verifysystem(self, ctx: discord.ApplicationContext, role_to_remove: discord.Role, role_to_give: discord.Role, modrole: discord.Role, ghostping_channel: discord.TextChannel):
        cog = self.bot.get_cog('TicketVerify')
        if cog:
            await cog.setupverifysystem(ctx, role_to_remove, role_to_give, modrole, ghostping_channel)
        else:
            await ctx.respond('Verify system setup not available.', ephemeral=True)

    # Show Server Config
    @setup.command(name='showconfig', description='Show the current server configuration')
    @commands.has_permissions(administrator=True)
    async def setup_showconfig(self, ctx: discord.ApplicationContext):
        cog = self.bot.get_cog('ConfigSettings')
        if cog:
            await cog.settings_showconfig(ctx)
        else:
            await ctx.respond('Show config not available.', ephemeral=True)


def setup(bot):
    bot.add_cog(CentralSetup(bot))
