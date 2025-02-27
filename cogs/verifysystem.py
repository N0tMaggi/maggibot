import discord
from discord.ext import commands
import json
import os
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
        config = config.loadserverconfig()
        guild_id = str(ctx.guild.id)

        # Check if the guild already has a config. If not, create an empty one.
        if guild_id not in config:
            config[guild_id] = {}

        # Add or update the config values for this guild
        config[guild_id]["role_to_remove"] = role_to_remove.id
        config[guild_id]["role_to_give"] = role_to_give.id
        config[guild_id]["modrole"] = modrole.id
        config[guild_id]["ghostping_channel"] = ghostping_channel.id

        config.saveserverconfig(config)

        # Enhanced embed with emojis, footer, and image
        embed = discord.Embed(
            title="✅ Verify System Configured Successfully!",
            description="The verification system has been successfully set up for this server.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url="https://ag7-dev.de/favicon/favicon.ico")  # Replace with your own image URL
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
        config = config.loadserverconfig()
        guild_id = str(ctx.guild.id)
        if guild_id not in config:
            embed = discord.Embed(
                title="❌ Configuration Missing",
                description="The verification system is not configured for this server. Please run `/setup-verifysystem` first.",
                color=discord.Color.red()
            )
            embed.set_footer(text="AG7 Dev Team", icon_url="https://ag7-dev.de/favicon/favicon.ico")
            embed.timestamp = discord.utils.utcnow()
            await ctx.respond(embed=embed, ephemeral=True)
            return

        guild_config = config[guild_id]
        modrole_id = guild_config.get("modrole")
        modrole = ctx.guild.get_role(modrole_id)
        if modrole not in ctx.author.roles:
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description=f"You need the {modrole.mention} role to use this command.",
                color=discord.Color.red()
            )
            embed.set_footer(text="AG7 Dev Team", icon_url="https://ag7-dev.de/favicon/favicon.ico")
            embed.timestamp = discord.utils.utcnow()
            await ctx.respond(embed=embed, ephemeral=True)
            return

        role_to_remove = ctx.guild.get_role(guild_config.get("role_to_remove"))
        role_to_give = ctx.guild.get_role(guild_config.get("role_to_give"))
        ghostping_channel = ctx.guild.get_channel(guild_config.get("ghostping_channel"))

        member = ctx.guild.get_member(user.id)
        if member is None:
            embed = discord.Embed(
                title="❌ User Not Found",
                description="The specified user is not in this server.",
                color=discord.Color.red()
            )
            embed.set_footer(text="AG7 Dev Team", icon_url="https://ag7-dev.de/favicon/favicon.ico")
            embed.timestamp = discord.utils.utcnow()
            await ctx.respond(embed=embed, ephemeral=True)
            return

        try:
            if role_to_remove in member.roles:
                await member.remove_roles(role_to_remove, reason="Verified via ticket verify system.")
            await member.add_roles(role_to_give, reason="Verified via ticket verify system.")
        except Exception as e:
            embed = discord.Embed(
                title="❌ Role Update Failed",
                description=f"An error occurred while updating roles for {member.mention}: {e}",
                color=discord.Color.red()
            )
            embed.set_footer(text="AG7 Dev Team", icon_url="https://ag7-dev.de/favicon/favicon.ico")
            embed.timestamp = discord.utils.utcnow()
            await ctx.respond(embed=embed, ephemeral=True)
            return

        # Ghost ping the user in the designated channel
        if ghostping_channel:
            verify_embed = discord.Embed(
                title="✅ User Verified",
                description=f"**{member.mention}** has been successfully verified and updated with the new role.",
                color=discord.Color.green()
            )
            try:
                ghost_msg = await ghostping_channel.send(embed=verify_embed)
                ghost_ping = await ghostping_channel.send(f"{member.mention}")
                await ghost_msg.delete(delay=1)
                await ghost_ping.delete(delay=1)
            except Exception as ex:
                error_embed = discord.Embed(
                    title="❌ Ghost Ping Failed",
                    description=f"An error occurred while ghost pinging the user: {ex}",
                    color=discord.Color.red()
                )
                error_embed.set_footer(text="AG7 Dev Team", icon_url="https://ag7-dev.de/favicon/favicon.ico")
                error_embed.timestamp = discord.utils.utcnow()
                await ctx.respond(embed=error_embed, ephemeral=True)

        embed = discord.Embed(
            title="✅ Verification Successful",
            description=f"**{member.mention}** has been successfully verified and updated with the new role.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url="https://ag7-dev.de/favicon/favicon.ico")
        embed.set_footer(text="AG7 Dev Team | Verification System", icon_url="https://ag7-dev.de/favicon/favicon.ico")
        embed.timestamp = discord.utils.utcnow()

        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(TicketVerify(bot))
