# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
import traceback
import sys
import uuid
from colorama import Fore, Style, init

from cogs.owner.commandlockdown import LockdownCheckFailure
from handlers.debug import LogError
from handlers.env import get_owner
from handlers.locale import t
from utils.embed_helpers import create_embed, create_error_embed, create_warning_embed

init(autoreset=True)
error_log_channel_id = os.getenv("ERROR_LOG_CHANNEL_ID")


class ErrorHandling(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        try:
            self.owner_id = get_owner()
        except Exception:
            self.owner_id = None

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        error_message = str(error).lower()
        if "fatal" in error_message or "critical" in error_message:
            cmd_name = ctx.command.name if ctx.command else "Unknown"
            await self.fatal_error(f"FATAL ERROR in: {cmd_name}", error)
            return

        if isinstance(error, LockdownCheckFailure):
            return

        try:
            await self.handle_error(ctx, error, t("common.error", ctx=ctx))
        except Exception as e:
            await self.fatal_error("Error in on_command_error handler", e)
            traceback.print_exc()

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error):
        error_message = str(error).lower()
        if "fatal" in error_message or "critical" in error_message:
            await self.fatal_error("FATAL ERROR in application command error", error)
            return

        original_error = getattr(error, "original", error)
        if isinstance(original_error, LockdownCheckFailure):
            return

        if isinstance(original_error, commands.NoPrivateMessage):
            await self.handle_error_without_log(ctx, original_error, t("errors.guild_only", ctx=ctx))
        elif isinstance(error, commands.CommandOnCooldown):
            await self.handle_error_without_log(ctx, error, t("errors.cooldown", ctx=ctx))
        elif isinstance(error, commands.MissingPermissions):
            await self.handle_missing_permissions_error(ctx, error, t("common.warning", ctx=ctx))
        else:
            await self.handle_error(ctx, error, t("common.error", ctx=ctx))

    async def handle_error(self, ctx, error, error_type: str):
        cmd_name = ctx.command.name if ctx.command else "Unknown"
        LogError(f"Handling error for command: {cmd_name}")

        error_uid = str(uuid.uuid4())[:8]
        error_info = f"{error.__class__.__name__}: {error}"
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        traceback_text = "".join(tb_lines)

        user = ctx.author
        guild_info = f"{ctx.guild.name} ({ctx.guild.id})" if ctx.guild else "Direct Message"
        channel_info = f"{ctx.channel.mention} ({ctx.channel.id})" if hasattr(ctx.channel, 'mention') else "DM"

        fields = [
            (t("common.details", ctx=ctx), f"```\n{error_info[:1000]}\n```", False),
            ("ID", f"`{error_uid}`", True),
            (t("common.user", ctx=ctx), f"{user.mention} (`{user.id}`)", True),
            (t("common.server", ctx=ctx), f"{channel_info}\n{guild_info}", False)
        ]

        embed = create_error_embed(
            error_type,
            t("errors.generic", ctx=ctx, command=cmd_name),
            author=user,
            fields=fields
        )

        try:
            if isinstance(ctx, discord.ApplicationContext):
                if ctx.response.is_done():
                    await ctx.followup.send(embed=embed, ephemeral=True)
                else:
                    await ctx.response.send_message(embed=embed, ephemeral=True)
            else:
                await ctx.send(embed=embed)
        except Exception as e:
            LogError(f"Failed to respond to user with error: {e}")

        # Send to developer error channel
        if len(traceback_text) > 1024:
            tb_file = await self.create_traceback_file(traceback_text)
            log_embed = embed.copy()
            log_embed.add_field(name="Traceback", value="See attached file", inline=False)
            await self.log_error(ctx, error, log_embed, tb_file, error_uid)
        else:
            log_embed = embed.copy()
            log_embed.add_field(name="Traceback", value=f"```py\n{traceback_text[:1000]}\n```", inline=False)
            await self.log_error(ctx, error, log_embed, error_uid=error_uid)

    async def handle_error_without_log(self, ctx, error, error_type: str):
        embed = create_warning_embed(
            error_type,
            f"{error}",
            author=ctx.author
        )
        try:
            if isinstance(ctx, discord.ApplicationContext):
                if ctx.response.is_done():
                    await ctx.followup.send(embed=embed, ephemeral=True)
                else:
                    await ctx.response.send_message(embed=embed, ephemeral=True)
            else:
                await ctx.send(embed=embed)
        except Exception:
            pass

    async def handle_missing_permissions_error(self, ctx, error, error_type: str):
        missing_perms = ", ".join(getattr(error, "missing_permissions", ["Administrator"]))
        embed = create_error_embed(
            error_type,
            t("errors.missing_permissions", ctx=ctx, permissions=missing_perms),
            author=ctx.author
        )
        try:
            if isinstance(ctx, discord.ApplicationContext):
                if ctx.response.is_done():
                    await ctx.followup.send(embed=embed, ephemeral=True)
                else:
                    await ctx.response.send_message(embed=embed, ephemeral=True)
            else:
                await ctx.send(embed=embed)
        except Exception:
            pass

    async def log_error(self, ctx, error, embed, traceback_file=None, error_uid=None):
        if not error_log_channel_id or not str(error_log_channel_id).strip().isdigit():
            return
        try:
            chan_id = int(error_log_channel_id)
            log_channel = self.bot.get_channel(chan_id) or await self.bot.fetch_channel(chan_id)
            if log_channel:
                if traceback_file:
                    await log_channel.send(embed=embed, file=traceback_file)
                else:
                    await log_channel.send(embed=embed)
        except Exception as e:
            LogError(f"Could not log error to Discord channel: {e}")

    async def create_traceback_file(self, traceback_text: str):
        now_str = discord.utils.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
        file_name = f"traceback_{now_str}.txt"
        file_path = os.path.join("logs/traceback", file_name)
        os.makedirs("logs/traceback", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(traceback_text)
        return discord.File(file_path, filename=file_name)

    async def fatal_error(self, error_message: str, error: Exception):
        LogError(f"FATAL ERROR: {error_message} | Details: {error}")
        fatal_embed = create_error_embed(
            t("errors.fatal_title"),
            t("errors.fatal_desc", error_message=error_message, error=error),
            footer_text="System Failure Protocol"
        )
        try:
            if error_log_channel_id and str(error_log_channel_id).strip().isdigit():
                log_channel = self.bot.get_channel(int(error_log_channel_id))
                if log_channel:
                    await log_channel.send(embed=fatal_embed)
        except Exception:
            pass


def setup(bot: commands.Bot):
    bot.add_cog(ErrorHandling(bot))
