# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from handlers.debug import LogSystem, LogError, LogDebug
from handlers.config import load_stats, load_multiplier_config, save_multiplier_config
from utils.embed_helpers import create_embed, create_success_embed, create_error_embed, create_info_embed, create_warning_embed

load_dotenv()


class XPSetup(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.slash_command(
        name="xp-setmultiplier",
        description="⚖️ Setzt einen XP-Multiplikator für eine Rolle",
        guild_only=True,
        default_member_permissions=discord.Permissions(administrator=True)
    )
    @commands.has_permissions(administrator=True)
    async def xp_setmultiplier(self, ctx: discord.ApplicationContext, role: discord.Role, multiplier: float):
        await ctx.defer(ephemeral=True)
        try:
            cfg = load_multiplier_config()
            cfg["multipliers"][str(role.id)] = multiplier
            save_multiplier_config(cfg)

            embed = create_success_embed(
                "Multiplikator aktualisiert",
                f"Mitglieder mit der Rolle {role.mention} erhalten nun einen **{multiplier}x** XP-Multiplikator.",
                bot_user=self.bot.user
            )
            await ctx.followup.send(embed=embed)
        except Exception as e:
            LogError(f"Set multiplier error: {e}")
            await ctx.followup.send(embed=create_error_embed("Fehler", str(e)), ephemeral=True)

    @commands.slash_command(
        name="xp-showmultiplier",
        description="📜 Zeigt alle aktiven Rollen-Multiplikatoren",
        guild_only=True
    )
    async def xp_showmultiplier(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        try:
            cfg = load_multiplier_config()
            embed = create_embed(
                title="📜 Aktive XP-Multiplikatoren",
                color="stats",
                bot_user=self.bot.user
            )

            if cfg.get("multipliers"):
                for role_id, mult in cfg["multipliers"].items():
                    role = ctx.guild.get_role(int(role_id))
                    embed.add_field(
                        name=f"⚖️ {role.name if role else f'Rolle ID {role_id}'}",
                        value=f"`{mult}x` XP Multiplikator",
                        inline=True
                    )
            else:
                embed.description = "Keine rollenbasierten Multiplikatoren eingerichtet."

            await ctx.followup.send(embed=embed)
        except Exception as e:
            LogError(f"Show multipliers error: {e}")
            await ctx.followup.send(embed=create_error_embed("Fehler", str(e)), ephemeral=True)

    @commands.slash_command(
        name="xp-removemultiplier",
        description="🗑️ Entfernt den XP-Multiplikator einer Rolle",
        guild_only=True,
        default_member_permissions=discord.Permissions(administrator=True)
    )
    @commands.has_permissions(administrator=True)
    async def xp_removemultiplier(self, ctx: discord.ApplicationContext, role: discord.Role):
        await ctx.defer(ephemeral=True)
        try:
            cfg = load_multiplier_config()
            role_id = str(role.id)

            if role_id in cfg.get("multipliers", {}):
                del cfg["multipliers"][role_id]
                save_multiplier_config(cfg)
                embed = create_success_embed(
                    "Multiplikator entfernt",
                    f"Der Multiplikator für {role.mention} wurde gelöscht."
                )
            else:
                embed = create_warning_embed(
                    "Nicht vorhanden",
                    f"Für {role.mention} war kein Multiplikator hinterlegt."
                )
            await ctx.followup.send(embed=embed)
        except Exception as e:
            LogError(f"Remove multiplier error: {e}")
            await ctx.followup.send(embed=create_error_embed("Fehler", str(e)), ephemeral=True)

    @commands.slash_command(
        name="xp-count",
        description="📦 Zeigt globale Datenbankstatistiken zum Levelsystem",
        guild_only=True
    )
    async def xp_count(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        try:
            stats = load_stats()
            total = len(stats)
            active = sum(1 for u in stats.values() if isinstance(u, dict) and u.get("xp", 0) > 0)

            embed = create_embed(
                title="📦 XP & Level-Statistiken",
                color="stats",
                bot_user=self.bot.user,
                fields=[
                    ("Erfasste Profile", f"```yaml\n{total}```", True),
                    ("Aktive Nutzer (>0 XP)", f"```yaml\n{active}```", True)
                ]
            )
            await ctx.followup.send(embed=embed)
        except Exception as e:
            LogError(f"XP count error: {e}")
            await ctx.followup.send(embed=create_error_embed("Fehler", str(e)), ephemeral=True)


def setup(bot: discord.Bot):
    bot.add_cog(XPSetup(bot))
