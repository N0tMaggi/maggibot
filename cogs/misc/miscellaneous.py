# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import asyncio
from handlers.debug import LogDebug, LogError
from handlers.locale import t
from utils.embed_helpers import create_embed, create_info_embed, create_success_embed, create_error_embed, create_warning_embed


class Miscellaneous(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.slash_command(
        name="serverinfo",
        description="Detailed information about this server",
        guild_only=True
    )
    async def serverinfo(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        server = ctx.guild
        owner = server.owner

        features = [f.replace('_', ' ').title() for f in server.features]
        features_str = ", ".join(features) if features else t("common.none", ctx=ctx)
        if len(features_str) > 500:
            features_str = features_str[:497] + "..."

        embed = create_embed(
            title=t("general.serverinfo_title", ctx=ctx, server_name=server.name),
            description=server.description or t("general.no_description", ctx=ctx),
            color="primary",
            thumbnail=server.icon.url if server.icon else None,
            image=server.banner.url if server.banner else None,
            author=ctx.author,
            fields=[
                (t("general.owner", ctx=ctx), owner.mention if owner else t("common.unknown", ctx=ctx), True),
                (t("general.server_id", ctx=ctx), f"`{server.id}`", True),
                (t("general.created_on", ctx=ctx), f"{discord.utils.format_dt(server.created_at, 'D')} ({discord.utils.format_dt(server.created_at, 'R')})", False),
                (t("general.members", ctx=ctx), f"**{t('common.total', ctx=ctx)}:** `{server.member_count}`", True),
                (t("general.boosts", ctx=ctx), f"{t('common.status', ctx=ctx)} `{server.premium_tier}` ({server.premium_subscription_count} Boosts)", True),
                (t("general.verification", ctx=ctx), f"`{str(server.verification_level).title()}`", True),
                (t("general.channels", ctx=ctx), f"💬 Text: `{len(server.text_channels)}` | 🔊 Voice: `{len(server.voice_channels)}` | 📁 Categories: `{len(server.categories)}`", False),
                (t("general.roles", ctx=ctx), f"`{len(server.roles)}` {t('general.roles', ctx=ctx)}", True),
                (t("general.emojis", ctx=ctx), f"`{len(server.emojis)}` {t('general.emojis', ctx=ctx)}", True),
                (t("general.features", ctx=ctx), f"```{features_str}```", False),
            ]
        )
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="userinfo",
        description="Lookup profile and details for a user",
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install},
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm, discord.InteractionContextType.private_channel}
    )
    async def userinfo(self, ctx: discord.ApplicationContext, target: discord.User = None):
        await ctx.defer()
        target = target or ctx.author
        member = ctx.guild.get_member(target.id) if ctx.guild else None

        fields = [
            (t("common.user", ctx=ctx), f"{target.name} ({target.mention})", True),
            ("ID", f"`{target.id}`", True),
            (t("general.bot_account", ctx=ctx), t("common.yes", ctx=ctx) if target.bot else t("common.no", ctx=ctx), True),
            (t("general.account_created", ctx=ctx), f"{discord.utils.format_dt(target.created_at, 'F')} ({discord.utils.format_dt(target.created_at, 'R')})", False),
        ]

        if member:
            if member.joined_at:
                fields.append((t("general.joined_server", ctx=ctx), f"{discord.utils.format_dt(member.joined_at, 'F')} ({discord.utils.format_dt(member.joined_at, 'R')})", False))
            roles = [r.mention for r in member.roles[1:]]
            roles_str = " ".join(roles[:15]) if roles else t("general.no_special_roles", ctx=ctx)
            if len(roles) > 15:
                roles_str += f" *({t('general.more_roles', ctx=ctx, count=len(roles)-15)})*"
            fields.append((f"{t('general.roles', ctx=ctx)} ({len(roles)})", roles_str, False))
            if member.top_role:
                fields.append((t("general.highest_role", ctx=ctx), member.top_role.mention, True))

        embed = create_embed(
            title=t("general.userinfo_title", ctx=ctx, user_name=target.display_name),
            color="primary",
            thumbnail=target.display_avatar.url,
            author=ctx.author,
            fields=fields
        )
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="ping",
        description="Check bot latency and websocket responsiveness",
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install},
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm, discord.InteractionContextType.private_channel}
    )
    async def ping(self, ctx: discord.ApplicationContext):
        latency_ms = round(self.bot.latency * 1000)
        embed = create_embed(
            title=t("general.ping_title", ctx=ctx),
            description=t("general.ping_latency", ctx=ctx, latency=latency_ms),
            color="success" if latency_ms < 150 else ("warning" if latency_ms < 300 else "error"),
            bot_user=self.bot.user
        )
        await ctx.respond(embed=embed)


def setup(bot: discord.Bot):
    bot.add_cog(Miscellaneous(bot))
