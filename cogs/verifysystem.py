import discord
from discord.ext import commands
import handlers.config as config

class TicketVerify(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="setup-verifysystem",
        description="Set up the verify system for this server."
    )
    @commands.has_permissions(administrator=True)
    async def setupverifysystem(
        self,
        ctx: discord.ApplicationContext,
        role_to_remove: discord.Role,
        role_to_give: discord.Role,
        modrole: discord.Role,
        ghostping_channel: discord.TextChannel
    ):
        cfg = config.loadserverconfig()
        guild_id = str(ctx.guild.id)

        if guild_id not in cfg:
            cfg[guild_id] = {}

        cfg[guild_id].update({
            "role_to_remove": role_to_remove.id,
            "role_to_give": role_to_give.id,
            "modrole": modrole.id,
            "ghostping_channel": ghostping_channel.id
        })

        config.saveserverconfig(cfg)

        embed = discord.Embed(
            title="✅ Verify System Configured Successfully!",
            description="The verification system has been successfully set up for this server.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url="https://ag7-dev.de/favicon/favicon.ico")
        embed.add_field(name="🔴 Role to Remove", value=role_to_remove.mention, inline=True)
        embed.add_field(name="🟢 Role to Give", value=role_to_give.mention, inline=True)
        embed.add_field(name="🛡️ Moderator Role", value=modrole.mention, inline=True)
        embed.add_field(name="📢 Ghost Ping Channel", value=ghostping_channel.mention, inline=True)
        embed.set_footer(text="AG7 Dev Team | Verification System", icon_url="https://ag7-dev.de/favicon/favicon.ico")
        embed.timestamp = discord.utils.utcnow()

        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(
        name="verify",
        description="Verify a user by updating their roles."
    )
    async def verify(self, ctx: discord.ApplicationContext, user: discord.User):
        cfg = config.loadserverconfig()
        guild_id = str(ctx.guild.id)

        if guild_id not in cfg:
            await ctx.respond(embed=self.error_embed("Configuration Missing", "The verification system is not configured for this server. Please run `/setup-verifysystem` first."), ephemeral=True)
            return

        guild_config = cfg[guild_id]
        modrole = ctx.guild.get_role(guild_config.get("modrole"))

        if not modrole or modrole not in ctx.author.roles:
            await ctx.respond(embed=self.error_embed("Insufficient Permissions", f"You need the {modrole.mention} role to use this command."), ephemeral=True)
            return

        role_to_remove = ctx.guild.get_role(guild_config.get("role_to_remove"))
        role_to_give = ctx.guild.get_role(guild_config.get("role_to_give"))
        ghostping_channel = ctx.guild.get_channel(guild_config.get("ghostping_channel"))

        member = ctx.guild.get_member(user.id)
        if not member:
            await ctx.respond(embed=self.error_embed("User Not Found", "The specified user is not in this server."), ephemeral=True)
            return

        try:
            if role_to_remove and role_to_remove in member.roles:
                await member.remove_roles(role_to_remove, reason="Verified via ticket verify system.")
            if role_to_give:
                await member.add_roles(role_to_give, reason="Verified via ticket verify system.")
        except Exception as e:
            await ctx.respond(embed=self.error_embed("Role Update Failed", f"An error occurred while updating roles: {e}"), ephemeral=True)
            return

        if ghostping_channel:
            await self.ghost_ping(member, ghostping_channel)

        embed = discord.Embed(
            title="✅ Verification Successful",
            description=f"**{member.mention}** has been successfully verified and updated with the new role.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url="https://ag7-dev.de/favicon/favicon.ico")
        embed.set_footer(text="AG7 Dev Team | Verification System", icon_url="https://ag7-dev.de/favicon/favicon.ico")
        embed.timestamp = discord.utils.utcnow()

        await ctx.respond(embed=embed, ephemeral=True)

    async def ghost_ping(self, member, channel):
        try:
            verify_embed = discord.Embed(
                title="✅ User Verified",
                description=f"**{member.mention}** has been successfully verified and updated with the new role.",
                color=discord.Color.green()
            )
            ghost_msg = await channel.send(embed=verify_embed)
            ghost_ping = await channel.send(f"{member.mention}")
            await ghost_msg.delete(delay=1)
            await ghost_ping.delete(delay=1)
        except Exception as ex:
            print(f"Ghost ping failed: {ex}")

    def error_embed(self, title, description):
        embed = discord.Embed(title=f"❌ {title}", description=description, color=discord.Color.red())
        embed.set_footer(text="AG7 Dev Team", icon_url="https://ag7-dev.de/favicon/favicon.ico")
        embed.timestamp = discord.utils.utcnow()
        return embed


def setup(bot: commands.Bot):
    bot.add_cog(TicketVerify(bot))
