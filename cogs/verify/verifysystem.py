# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import handlers.config as config
from handlers.debug import LogDebug, LogError
from utils.embed_helpers import create_embed, create_success_embed, create_error_embed, create_warning_embed


class VerifySystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="setup-verifysystem",
        description="🎚️ Verifizierungs-System für diesen Server einrichten",
        guild_only=True,
        default_member_permissions=discord.Permissions(administrator=True)
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

            embed = create_success_embed(
                "Verifizierungssystem eingerichtet",
                f"Die Einstellungen für **{ctx.guild.name}** wurden erfolgreich gespeichert.",
                thumbnail=ctx.guild.icon.url if ctx.guild.icon else None,
                fields=[
                    ("🔴 Zu entfernende Rolle", role_to_remove.mention, True),
                    ("🟢 Zu vergebende Rolle", role_to_give.mention, True),
                    ("🛡️ Moderator-Rolle", modrole.mention, True),
                    ("📢 Ghostping Kanal", ghostping_channel.mention, False)
                ]
            )
            await ctx.respond(embed=embed, ephemeral=True)
            LogDebug(f"Verification system configured for guild {guild_id}")
        except Exception as e:
            LogError(f"Setup verify error: {e}")
            await ctx.respond(embed=create_error_embed("Fehler", str(e)), ephemeral=True)

    @commands.slash_command(
        name="verify",
        description="✅ Einen Nutzer verifizieren und Rollen aktualisieren",
        guild_only=True
    )
    async def verify(self, ctx: discord.ApplicationContext, user: discord.User):
        try:
            await ctx.defer(ephemeral=True)
            cfg = config.loadserverconfig()
            guild_id = str(ctx.guild.id)

            if guild_id not in cfg or "modrole" not in cfg[guild_id]:
                embed = create_warning_embed(
                    "Nicht eingerichtet",
                    "Das Verifizierungssystem ist noch nicht eingerichtet. Bitte verwende `/setup` oder `/setup-verifysystem`."
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            guild_config = cfg[guild_id]
            modrole = ctx.guild.get_role(guild_config.get("modrole"))

            if not modrole or (modrole not in ctx.author.roles and not ctx.author.guild_permissions.administrator):
                embed = create_error_embed(
                    "Keine Berechtigung",
                    f"Du benötigst die Rolle {modrole.mention if modrole else 'Moderator'} oder Administrator-Rechte."
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            member = ctx.guild.get_member(user.id)
            if not member:
                embed = create_error_embed("Nutzer nicht gefunden", "Der angegebene Nutzer befindet sich nicht auf diesem Server.")
                await ctx.respond(embed=embed, ephemeral=True)
                return

            role_to_remove = ctx.guild.get_role(guild_config.get("role_to_remove"))
            role_to_give = ctx.guild.get_role(guild_config.get("role_to_give"))
            ghostping_channel = ctx.guild.get_channel(guild_config.get("ghostping_channel"))

            try:
                if role_to_remove and role_to_remove in member.roles:
                    await member.remove_roles(role_to_remove, reason=f"Verifiziert von {ctx.author}")
                if role_to_give and role_to_give not in member.roles:
                    await member.add_roles(role_to_give, reason=f"Verifiziert von {ctx.author}")
            except discord.Forbidden:
                embed = create_error_embed("Fehlende Bot-Rechte", "Der Bot hat nicht die erforderlichen Rechte, um diese Rollen zu verwalten.")
                await ctx.respond(embed=embed, ephemeral=True)
                return

            if ghostping_channel:
                try:
                    await ghostping_channel.send(
                        content=f"{member.mention}\n```diff\n- Verification ping - Do not respond\n```",
                        delete_after=0.5
                    )
                except Exception as gp_e:
                    LogError(f"Ghostping failed: {gp_e}")

            try:
                dm_embed = create_success_embed(
                    "Verifizierung abgeschlossen",
                    f"Du wurdest auf **{ctx.guild.name}** erfolgreich verifiziert!",
                    thumbnail=ctx.guild.icon.url if ctx.guild.icon else None,
                    fields=[
                        ("Verifiziert von", ctx.author.mention, True),
                        ("Zeitpunkt", discord.utils.format_dt(discord.utils.utcnow(), 'F'), True)
                    ]
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass

            confirm_embed = create_success_embed(
                "Erfolgreich verifiziert",
                f"{member.mention} wurde erfolgreich verifiziert! ✅",
                thumbnail=member.display_avatar.url,
                fields=[
                    ("Hinzugefügt", role_to_give.mention if role_to_give else "Keine", True),
                    ("Entfernt", role_to_remove.mention if role_to_remove else "Keine", True)
                ]
            )
            await ctx.respond(embed=confirm_embed, ephemeral=True)

        except Exception as e:
            LogError(f"Verify error: {e}")
            await ctx.respond(embed=create_error_embed("Fehler", str(e)), ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(VerifySystem(bot))
