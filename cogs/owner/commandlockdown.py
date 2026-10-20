# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from handlers.env import get_owner
from handlers.debug import LogSystem, LogError, LogModeration
from handlers.config import load_lockdown_config, save_lockdown_config
from utils.embed_helpers import create_embed, create_security_embed, create_error_embed


class LockdownCheckFailure(commands.CheckFailure):
    pass


class CommandLockdown(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lockdown_data = load_lockdown_config()

    @commands.slash_command(name="lockdown", description="🔒 Notfall-Sperre für alle Befehle (Owner only)")
    async def lockdown(self, ctx: discord.ApplicationContext):
        """Toggle emergency command lockdown"""
        await ctx.defer(ephemeral=True)

        try:
            authorised_owner = get_owner()
            if ctx.user.id != authorised_owner:
                embed = create_error_embed(
                    "ZUGRIFF VERWEIGERT",
                    f"**Unberechtigter Versuch zur Aktivierung der Notfallsperre!**\n\nNutzer: {ctx.user.mention} (`{ctx.user.id}`)\nDieser Vorfall wurde protokolliert.",
                    author=ctx.user
                )
                await ctx.followup.send(embed=embed, ephemeral=True)
                LogModeration(f"Unauthorized lockdown attempt by {ctx.user.id}")
                return

            self.lockdown_data = load_lockdown_config()
            new_status = not self.lockdown_data.get("lockdown", False)
            save_lockdown_config(new_status)

            status_word = "AKTIVIERT" if new_status else "DEAKTIVIERT"
            embed = create_security_embed(
                f"NOTFALL-SPERRE {status_word}",
                f"**Globaler Befehls-Lockdown wurde {status_word.lower()}!**\n\n"
                f"```diff\n{'+' if new_status else '-'} NOTFALL-SPERRPROTOKOLL {status_word}\n```",
                color="error" if new_status else "success",
                bot_user=self.bot.user,
                fields=[
                    ("🔐 Status", f"`{'🛑 GESPERRT' if new_status else '✅ BETRIEBSBEREIT'}`", True),
                    ("🛡️ Ausgeführt von", f"`{ctx.user.display_name}`", True),
                    ("🕒 Zeitstempel", discord.utils.format_dt(discord.utils.utcnow(), 'F'), False)
                ]
            )

            await ctx.followup.send(embed=embed, ephemeral=True)
            LogSystem(f"Lockdown {'enabled' if new_status else 'disabled'} by {ctx.user.id}")

        except Exception as e:
            LogError(f"Lockdown command failed: {str(e)}")
            await ctx.followup.send(embed=create_error_embed("Fehler", str(e)), ephemeral=True)


async def global_lockdown_check(ctx: commands.Context):
    try:
        lockdown_data = load_lockdown_config()
        locked = lockdown_data.get("lockdown", False)

        try:
            owner_id = get_owner()
        except Exception:
            owner_id = None

        if locked and ctx.user.id != owner_id:
            embed = create_security_embed(
                "NOTFALL-SPERRE AKTIV",
                "**Befehle sind derzeit serverseitig gesperrt.**\n\n"
                "Der Bot befindet sich momentan im Notfall-Wartungsmodus. "
                "Bitte versuche es später erneut oder kontaktiere die Bot-Administration.",
                color="error",
                fields=[
                    ("🔒 Sicherheitsstufe", "`MAXIMALER ALARM`", True),
                    ("🕒 Status", f"`{discord.utils.format_dt(discord.utils.utcnow(), 'R')}`", True)
                ]
            )

            if hasattr(ctx, "response") and not ctx.response.is_done():
                await ctx.response.send_message(embed=embed, ephemeral=True)
            elif hasattr(ctx, "followup"):
                await ctx.followup.send(embed=embed, ephemeral=True)
            else:
                await ctx.send(embed=embed)

            LogModeration(f"Command blocked during lockdown: {ctx.command} by {ctx.user.id}")
            raise LockdownCheckFailure("Lockdown active")

        return True
    except LockdownCheckFailure:
        raise
    except Exception as e:
        LogError(f"Lockdown check failed: {str(e)}")
        return True


def setup(bot: commands.Bot):
    bot.add_cog(CommandLockdown(bot))
    bot.add_check(global_lockdown_check)
