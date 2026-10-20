# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import asyncio
from handlers.debug import LogDebug, LogError
from utils.embed_helpers import create_embed, create_info_embed, create_success_embed, create_error_embed, create_warning_embed


class Miscellaneous(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.slash_command(
        name="serverinfo",
        description="Detaillierte Informationen über diesen Server",
        guild_only=True
    )
    async def serverinfo(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        server = ctx.guild
        owner = server.owner

        features = [f.replace('_', ' ').title() for f in server.features]
        features_str = ", ".join(features) if features else "Standard"
        if len(features_str) > 500:
            features_str = features_str[:497] + "..."

        embed = create_embed(
            title=f"📊 Server-Informationen • {server.name}",
            description=server.description or "Keine Serverbeschreibung angegeben.",
            color="primary",
            thumbnail=server.icon.url if server.icon else None,
            image=server.banner.url if server.banner else None,
            author=ctx.author,
            fields=[
                ("👑 Eigentümer", owner.mention if owner else "Unbekannt", True),
                ("🆔 Server ID", f"`{server.id}`", True),
                ("📆 Erstellt am", f"{discord.utils.format_dt(server.created_at, 'D')} ({discord.utils.format_dt(server.created_at, 'R')})", False),
                ("👥 Mitglieder", f"**Gesamt:** `{server.member_count}`", True),
                ("🚀 Nitro Boosts", f"Stufe `{server.premium_tier}` ({server.premium_subscription_count} Boosts)", True),
                ("🛡️ Verifizierung", f"`{str(server.verification_level).title()}`", True),
                ("📚 Kanäle", f"💬 Text: `{len(server.text_channels)}` | 🔊 Voice: `{len(server.voice_channels)}` | 📁 Kategorien: `{len(server.categories)}`", False),
                ("🎭 Rollen", f"`{len(server.roles)}` Rollen", True),
                ("😄 Emojis", f"`{len(server.emojis)}` Emojis", True),
                ("✨ Features", f"```{features_str}```", False),
            ]
        )
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="userinfo",
        description="Informationen über einen Nutzer abrufen",
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install},
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm, discord.InteractionContextType.private_channel}
    )
    async def userinfo(self, ctx: discord.ApplicationContext, target: discord.User = None):
        await ctx.defer()
        target = target or ctx.author
        member = ctx.guild.get_member(target.id) if ctx.guild else None

        fields = [
            ("👤 Name", f"{target.name} ({target.mention})", True),
            ("🆔 User ID", f"`{target.id}`", True),
            ("🤖 Bot-Account", "Ja" if target.bot else "Nein", True),
            ("📆 Account erstellt", f"{discord.utils.format_dt(target.created_at, 'F')} ({discord.utils.format_dt(target.created_at, 'R')})", False),
        ]

        if member:
            if member.joined_at:
                fields.append(("📥 Server beigetreten", f"{discord.utils.format_dt(member.joined_at, 'F')} ({discord.utils.format_dt(member.joined_at, 'R')})", False))
            roles = [r.mention for r in member.roles[1:]]
            roles_str = " ".join(roles[:15]) if roles else "Keine speziellen Rollen"
            if len(roles) > 15:
                roles_str += f" *(+{len(roles)-15} weitere)*"
            fields.append((f"🎭 Rollen ({len(roles)})", roles_str, False))
            if member.top_role:
                fields.append(("🔝 Höchste Rolle", member.top_role.mention, True))

        embed = create_embed(
            title=f"👤 Nutzerprofil • {target.display_name}",
            color="primary",
            thumbnail=target.display_avatar.url,
            author=ctx.author,
            fields=fields
        )
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="ping",
        description="Prüft die Antwortzeit des Bots",
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install},
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm, discord.InteractionContextType.private_channel}
    )
    async def ping(self, ctx: discord.ApplicationContext):
        latency_ms = round(self.bot.latency * 1000)
        embed = create_embed(
            title="🏓 Pong!",
            description=f"Websocket-Latenz: **{latency_ms} ms**",
            color="success" if latency_ms < 150 else ("warning" if latency_ms < 300 else "error"),
            bot_user=self.bot.user
        )
        await ctx.respond(embed=embed)


def setup(bot: discord.Bot):
    bot.add_cog(Miscellaneous(bot))
