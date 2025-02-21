import discord
from discord.ext import commands
import json
import os

CONFIG_FILE = "data/serververify.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

class TicketVerify(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="setupverifysystem",
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
        config = load_config()
        guild_id = str(ctx.guild.id)
        config[guild_id] = {
            "role_to_remove": role_to_remove.id,
            "role_to_give": role_to_give.id,
            "modrole": modrole.id,
            "ghostping_channel": ghostping_channel.id
        }
        save_config(config)
        embed = discord.Embed(
            title="Verify System Configured",
            description="The verify system has been set up for this server.",
            color=discord.Color.green()
        )
        embed.add_field(name="Role to Remove", value=role_to_remove.mention, inline=True)
        embed.add_field(name="Role to Give", value=role_to_give.mention, inline=True)
        embed.add_field(name="Moderator Role", value=modrole.mention, inline=True)
        embed.add_field(name="Ghost Ping Channel", value=ghostping_channel.mention, inline=True)
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(
        name="verify",
        description="Verify a user by updating their roles."
    )
    async def verify(self, ctx: discord.ApplicationContext, user: discord.User):
        config = load_config()
        guild_id = str(ctx.guild.id)
        if guild_id not in config:
            embed = discord.Embed(
                title="Configuration Missing",
                description="The verify system is not configured for this server. Please run /setupverifysystem first.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        guild_config = config[guild_id]
        modrole_id = guild_config.get("modrole")
        modrole = ctx.guild.get_role(modrole_id)
        if modrole not in ctx.author.roles:
            embed = discord.Embed(
                title="Insufficient Permissions",
                description=f"You do not have permission to use this command. Required role: {modrole.mention}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        role_to_remove = ctx.guild.get_role(guild_config.get("role_to_remove"))
        role_to_give = ctx.guild.get_role(guild_config.get("role_to_give"))
        ghostping_channel = ctx.guild.get_channel(guild_config.get("ghostping_channel"))

        member = ctx.guild.get_member(user.id)
        if member is None:
            embed = discord.Embed(
                title="User Not Found",
                description="The specified user is not in this server.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        try:
            if role_to_remove in member.roles:
                await member.remove_roles(role_to_remove, reason="Verified via ticket verify system.")
            await member.add_roles(role_to_give, reason="Verified via ticket verify system.")
        except Exception as e:
            embed = discord.Embed(
                title="Role Update Failed",
                description=f"An error occurred while updating roles for {member.mention}: {e}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        # Ghost ping the user in the designated channel
        if ghostping_channel:
            verify_embed = discord.Embed(
                title="User Verified",
                description=f"✅ {member.mention} has been verified and updated with the new role.",
                color=discord.Color.green()
            )
            try:
                ghost_msg = await ghostping_channel.send(embed=verify_embed)
                ghost_ping = await ghostping_channel.send(f"{member.mention}")
                await ghost_msg.delete(delay=1)
                await ghost_ping.delete(delay=1)
            except Exception:
                pass

        embed = discord.Embed(
            title="Verification Successful",
            description=f"{member.mention} has been verified successfully.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(TicketVerify(bot))
