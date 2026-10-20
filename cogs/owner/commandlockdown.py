# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from handlers.env import get_owner
from handlers.debug import LogSystem, LogError, LogModeration
from handlers.config import load_lockdown_config, save_lockdown_config
from handlers.locale import t
from utils.embed_helpers import create_embed, create_security_embed, create_error_embed


class LockdownCheckFailure(commands.CheckFailure):
    pass


class CommandLockdown(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lockdown_data = load_lockdown_config()

    @commands.slash_command(name="lockdown", description="🔒 Emergency command lockdown toggle (Owner only)")
    async def lockdown(self, ctx: discord.ApplicationContext):
        """Toggle emergency command lockdown"""
        await ctx.defer(ephemeral=True)

        try:
            authorised_owner = get_owner()
            if ctx.user.id != authorised_owner:
                embed = create_error_embed(
                    t("lockdown.denied_title", ctx=ctx),
                    t("lockdown.denied_desc", ctx=ctx, user=ctx.user.mention, user_id=ctx.user.id),
                    author=ctx.user
                )
                await ctx.followup.send(embed=embed, ephemeral=True)
                LogModeration(f"Unauthorized lockdown attempt by {ctx.user.id}")
                return

            self.lockdown_data = load_lockdown_config()
            new_status = not self.lockdown_data.get("lockdown", False)
            save_lockdown_config(new_status)

            status_word = t("lockdown.activated", ctx=ctx) if new_status else t("lockdown.deactivated", ctx=ctx)
            embed = create_security_embed(
                t("lockdown.title", ctx=ctx, status=status_word),
                t("lockdown.desc", ctx=ctx, status_lower=status_word.lower(), sign='+' if new_status else '-', status=status_word),
                color="error" if new_status else "success",
                bot_user=self.bot.user,
                fields=[
                    (t("common.status", ctx=ctx), f"`{t('lockdown.status_locked' if new_status else 'lockdown.status_operational', ctx=ctx)}`", True),
                    (t("lockdown.executed_by", ctx=ctx), f"`{ctx.user.display_name}`", True),
                    (t("lockdown.timestamp", ctx=ctx), discord.utils.format_dt(discord.utils.utcnow(), 'F'), False)
                ]
            )

            await ctx.followup.send(embed=embed, ephemeral=True)
            LogSystem(f"Lockdown {'enabled' if new_status else 'disabled'} by {ctx.user.id}")

        except Exception as e:
            LogError(f"Lockdown command failed: {str(e)}")
            await ctx.followup.send(embed=create_error_embed(t("common.error", ctx=ctx), str(e)), ephemeral=True)


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
                t("lockdown.title", ctx=ctx, status=t("lockdown.activated", ctx=ctx)),
                t("lockdown.active_warning", ctx=ctx),
                color="error",
                fields=[
                    (t("lockdown.security_level", ctx=ctx), f"`{t('lockdown.max_alert', ctx=ctx)}`", True),
                    (t("common.time", ctx=ctx), f"`{discord.utils.format_dt(discord.utils.utcnow(), 'R')}`", True)
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
