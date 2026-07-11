import discord
from discord.ext import commands
import handlers.config as config
from handlers.debug import LogDebug, LogError, LogNetwork, LogSystem
from utils.components import build_container, build_view

class TicketVerify(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def create_embed(self, title, description, color_type="info", thumbnail=""):
        # Dynamic emoji icons for titles
        title_icon = "✅" if color_type == "success" else "❌" if color_type == "error" else "ℹ️"
        
        normalized_color = "verify" if color_type == "success" else color_type
        return build_container(
            title=f"{title_icon} {title}",
            description=description,
            color=normalized_color,
            thumbnail=thumbnail if thumbnail else None,
            footer_text="Maggi Verification System",
            timestamp=True
        )

    def format_role(self, role):
        """Hilfsfunktion für konsistente Formatierung von Rollen"""
        return f"**{role.name}**" if role else "None"

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
            
            embed = self.create_embed(
                title="Configuration Complete",
                description=f"**Verification system configured!**\n\nSettings for {ctx.guild.name}:",
                color_type="success",
                thumbnail=ctx.guild.icon.url if ctx.guild.icon else ""
            )
            
            fields = [
                ("🔴 Role to Remove", role_to_remove.mention, True),
                ("🟢 Role to Grant", role_to_give.mention, True),
                ("🛡️ Moderator Role", modrole.mention, True),
                ("📢 Ghostping Channel", ghostping_channel.mention, True)
            ]
            
            for name, value, inline in fields:
                embed.add_item(discord.ui.TextDisplay(f"**{name}**\n{value}"))
            
            await ctx.respond(view=build_view(embed), ephemeral=True)
            LogDebug(f"Verification system configured for guild {guild_id}")
            
        except Exception as e:
            raise Exception(f"Setup error: {str(e)}")

    @commands.slash_command(
        name="verify",
        description="✅ Verify a user and update their roles"
    )
    async def verify(self, ctx: discord.ApplicationContext, user: discord.User):
        try:
            await ctx.defer()
            cfg = config.loadserverconfig()
            guild_id = str(ctx.guild.id)
            
            if guild_id not in cfg:
                embed = self.create_embed(
                    title="System Not Configured",
                    description="Use `/setup-verifysystem` first!",
                    color_type="error",
                    thumbnail=ctx.guild.icon.url if ctx.guild.icon else ""
                )
                await ctx.respond(view=build_view(embed), ephemeral=True)
                return
            
            guild_config = cfg[guild_id]
            modrole = ctx.guild.get_role(guild_config["modrole"])
            
            if not modrole or modrole not in ctx.author.roles:
                embed = self.create_embed(
                    title="Permission Denied",
                    description=f"You need {modrole.mention} role!",
                    color_type="error",
                    thumbnail=modrole.display_icon.url if modrole.display_icon else ""
                )
                await ctx.respond(view=build_view(embed), ephemeral=True)
                return
            
            member = ctx.guild.get_member(user.id)
            if not member:
                embed = self.create_embed(
                    title="User Not Found",
                    description="User not found in this server!",
                    color_type="error"
                )
                await ctx.respond(view=build_view(embed), ephemeral=True)
                return
            
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
                    title="Permission Error",
                    description="Bot can't manage roles!",
                    color_type="error"
                )
                await ctx.respond(view=build_view(embed), ephemeral=True)
                return
            
            if ghostping_channel:
                try:
                    await ghostping_channel.send(
                        view=build_view(
                            discord.ui.TextDisplay(
                                f"{member.mention}\n```diff\n- Verification ping - Do not respond\n```"
                            )
                        ),
                        delete_after=0.5
                    )
                except Exception as e:
                    LogError(f"Ghostping failed: {str(e)}")
            
            try:
                user_embed = self.create_embed(
                    title="Verification Complete",
                    description=f"You've been verified in {ctx.guild.name}!",
                    color_type="success",
                    thumbnail=ctx.guild.icon.url
                )
                user_embed.add_item(discord.ui.TextDisplay(f"**Verification Time**\n{discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"))
                user_embed.add_item(discord.ui.TextDisplay(f"**Verified By**\n{ctx.author.mention}"))
                await member.send(view=build_view(user_embed))
            except discord.Forbidden:
                pass  
            
            confirm_embed = self.create_embed(
                title="Verification Successful",
                description=f"{member.mention} verified! ✅",
                color_type="success",
                thumbnail=ctx.guild.icon.url
            )
            confirm_embed.add_item(
                discord.ui.TextDisplay(
                    f"**Role Changes**\n"
                    f"• Added: {role_to_give.mention if role_to_give else 'None'}\n"
                    f"• Removed: {role_to_remove.mention if role_to_remove else 'None'}"
                )
            )
            
            await ctx.respond(view=build_view(confirm_embed), ephemeral=True)
            
        except Exception as e:
            raise Exception(f"Verify error: {str(e)}")

    async def ghost_ping(self, member, channel):
        try:
            await channel.send(
                view=build_view(
                    discord.ui.TextDisplay(
                        f"{member.mention}\n```diff\n- Verification ping - Do not respond\n```"
                    )
                ),
                delete_after=0.5
            )
        except discord.HTTPException as e:
            LogError(f"Ghostping failed: {str(e)}")

def setup(bot: commands.Bot):
    bot.add_cog(TicketVerify(bot))
