import discord
from discord.ext import commands
import handlers.config as config
from handlers.debug import LogDebug, LogError, LogNetwork, LogSystem

class TicketVerify(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_footer = {
            "text": "AG7 Verification System",
            "icon_url": "https://ag7-dev.de/favicon/favicon.ico"
        }
        self.embed_colors = {
            "success": 0x2ECC71,
            "error": 0xE74C3C,
            "info": 0x3498DB
        }

    def create_embed(self, title, description, color_type="info"):
        embed = discord.Embed(
            title=title,
            description=description,
            color=self.embed_colors.get(color_type, 0x3498DB)
        )
        embed.set_footer(**self.embed_footer)
        embed.timestamp = discord.utils.utcnow()
        return embed

    @commands.slash_command(
        name="setup-verifysystem",
        description="🎚️ Set up the verify system for this server"
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
        """Initialize server verification system configuration"""
        try:
            cfg = config.loadserverconfig()
            guild_id = str(ctx.guild.id)

            cfg.setdefault(guild_id, {}).update({
                "role_to_remove": role_to_remove.id,
                "role_to_give": role_to_give.id,
                "modrole": modrole.id,
                "ghostping_channel": ghostping_channel.id
            })

            config.saveserverconfig(cfg)
            LogDebug(f"Verification system configured for guild {guild_id} by {ctx.author}")

            embed = self.create_embed(
                title="⚙️ System Configuration Complete",
                description="**Verification system has been successfully configured!**\n\n"
                           "Below are the current settings:",
                color_type="success"
            )
            embed.set_thumbnail(url="")
            fields = [
                ("🔴 Role to Remove", role_to_remove.mention, True),
                ("🟢 Role to Grant", role_to_give.mention, True),
                ("🛡️ Moderator Role", modrole.mention, True),
                ("📢 Ghostping Channel", ghostping_channel.mention, True)
            ]
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            raise Exception(f"Unexpected error in setup-verifysystem: {str(e)}")

    @commands.slash_command(
        name="verify",
        description="✅ Verify a user and update their roles"
    )
    async def verify(self, ctx: discord.ApplicationContext, user: discord.User):
        """Verify a user by adjusting their roles and sending notifications"""
        try:
            await ctx.defer()
            cfg = config.loadserverconfig()
            guild_id = str(ctx.guild.id)
            
            if guild_id not in cfg:
                embed = self.create_embed(
                    title="⚠️ System Not Configured",
                    description="This server has not configured the verification system yet!\n"
                               "Please use `/setup-verifysystem` first.",
                    color_type="error"
                )
                await ctx.respond(embed=embed, ephemeral=True)
                LogDebug(f"Missing configuration in guild {guild_id}")
                return

            guild_config = cfg[guild_id]
            modrole = ctx.guild.get_role(guild_config["modrole"])
            
            if not modrole or modrole not in ctx.author.roles:
                embed = self.create_embed(
                    title="⛔ Permission Denied",
                    description=f"You require the {modrole.mention if modrole else 'Moderator'} role to use this command!",
                    color_type="error"
                )
                await ctx.respond(embed=embed, ephemeral=True)
                LogDebug(f"Unauthorized verify attempt by {ctx.author} in {guild_id}")
                return

            member = ctx.guild.get_member(user.id)
            if not member:
                embed = self.create_embed(
                    title="❓ User Not Found",
                    description="The specified user could not be found in this server!",
                    color_type="error"
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # Role management
            role_to_remove = ctx.guild.get_role(guild_config["role_to_remove"])
            role_to_give = ctx.guild.get_role(guild_config["role_to_give"])
            ghostping_channel = ctx.guild.get_channel(guild_config["ghostping_channel"])

            try:
                if role_to_remove and role_to_remove in member.roles:
                    await member.remove_roles(role_to_remove, reason=f"Verified by {ctx.author}")
                if role_to_give and role_to_give not in member.roles:
                    await member.add_roles(role_to_give, reason=f"Verified by {ctx.author}")
            except discord.Forbidden:
                embed = self.create_embed(
                    title="🔒 Permission Error",
                    description="Bot lacks permissions to manage roles!",
                    color_type="error"
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # Ghostping functionality
            if ghostping_channel:
                try:
                    await self.ghost_ping(member, ghostping_channel)
                    LogDebug(f"Ghostping sent for {member} in {ghostping_channel}")
                except Exception as e:
                    LogError(f"Ghostping failed: {str(e)}")

            # User notification
            user_dm_error = False
            try:
                user_embed = discord.Embed(
                    title="🎉 Verification Complete!",
                    description=f"You've been successfully verified in **{ctx.guild.name}**!",
                    color=self.embed_colors["success"]
                )
                user_embed.add_field(
                    name="🕒 Verification Time",
                    value=discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    inline=False
                )
                user_embed.add_field(
                    name="🔑 Verified By",
                    value=ctx.author.mention,
                    inline=False
                )
                user_embed.add_field(
                    name="📌 Server",
                    value=ctx.guild.name,
                    inline=False
                )
                user_embed.set_thumbnail(url="")
                await member.send(embed=user_embed)
                LogDebug(f"Successfully sent DM to {member}")
            except discord.Forbidden:
                user_dm_error = True
                LogDebug(f"Could not send DM to {member}")

            # Confirmation response
            confirm_embed = self.create_embed(
                title="✅ Verification Successful",
                description=f"{member.mention} has been successfully verified!",
                color_type="success"
            )
            confirm_embed.add_field(
                name="Role Changes",
                value=f"• Added: {role_to_give.mention if role_to_give else 'None'}\n"
                      f"• Removed: {role_to_remove.mention if role_to_remove else 'None'}",
                inline=False
            )
            confirm_embed.set_thumbnail(url="")
            
            if user_dm_error:
                confirm_embed.add_field(
                    name="⚠️ DM Error",
                    value="User did not receive a DM. This could be due to DM settings or other issues.",
                    inline=False
                )
            
            await ctx.respond(embed=confirm_embed, ephemeral=True)
            LogDebug(f"User {member} verified by {ctx.author}")

        except Exception as e:
            raise Exception(f"Unexpected error in verify command: {str(e)}")

    async def ghost_ping(self, member, channel):
        """Send and immediately delete a ping message"""
        try:
            ghost_msg = await channel.send(f"{member.mention} ||Verification ping||", delete_after=0.5)
            LogDebug(f"Ghostping sent in {channel.id} for {member.id}")
        except discord.HTTPException as e:
            LogError(f"Ghostping failed in {channel.id}: {str(e)}")
            raise

def setup(bot: commands.Bot):
    bot.add_cog(TicketVerify(bot))
