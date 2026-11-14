# -*- coding: utf-8 -*-
"""
MaggiBot Honeypot Protection Cog
Creates a security trap channel. Any non-admin account sending a message is
automatically banned for 3 days. Includes automatic unban scheduler after 3 days.
"""

import discord
from discord.ext import commands, tasks
from discord.commands import slash_command
import datetime
from typing import Optional

import handlers.config as config
from handlers.debug import LogDebug, LogError, LogModeration
from handlers.locale import t
from utils.embed_helpers import create_embed, create_success_embed, create_error_embed, create_warning_embed, create_security_embed
from utils.colors import EmbedColors


class Honeypot(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.check_unbans.start()

    def cog_unload(self):
        self.check_unbans.cancel()

    @slash_command(
        name="honeypot",
        description="🍯 Manage honeypot trap channel (bans spammers for 3 days)",
        guild_only=True,
        default_member_permissions=discord.Permissions(administrator=True)
    )
    @commands.has_permissions(administrator=True)
    async def honeypot_cmd(
        self,
        ctx: discord.ApplicationContext,
        action: discord.Option(str, "Action to perform", choices=["setup", "remove"], default="setup"),
        channel: discord.Option(discord.TextChannel, "Channel to use (leave empty to auto-create)", required=False, default=None),
        delete_channel: discord.Option(bool, "Delete channel on remove?", required=False, default=False)
    ):
        await ctx.defer(ephemeral=True)
        if action == "setup":
            await self._setup_honeypot(ctx, channel)
        else:
            await self._remove_honeypot(ctx, delete_channel)

    @slash_command(
        name="honeypot-setup",
        description="🍯 Setup or create a honeypot trap channel (bans spammers for 3 days)",
        guild_only=True,
        default_member_permissions=discord.Permissions(administrator=True)
    )
    @commands.has_permissions(administrator=True)
    async def honeypot_setup_cmd(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.Option(discord.TextChannel, "Target channel (leave empty to auto-create)", required=False, default=None)
    ):
        await ctx.defer(ephemeral=True)
        await self._setup_honeypot(ctx, channel)

    @slash_command(
        name="honeypot-remove",
        description="🍯 Remove honeypot trap protection from this server",
        guild_only=True,
        default_member_permissions=discord.Permissions(administrator=True)
    )
    @commands.has_permissions(administrator=True)
    async def honeypot_remove_cmd(
        self,
        ctx: discord.ApplicationContext,
        delete_channel: discord.Option(bool, "Also delete the Discord channel?", required=False, default=False)
    ):
        await ctx.defer(ephemeral=True)
        await self._remove_honeypot(ctx, delete_channel)

    async def _setup_honeypot(self, ctx: discord.ApplicationContext, channel: Optional[discord.TextChannel] = None):
        guild = ctx.guild
        created = False

        if channel is None:
            try:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True, manage_channels=True)
                }
                channel = await guild.create_text_channel(
                    name="🍯・honeypot",
                    topic="⚠️ HONEYPOT CHANNEL - DO NOT SEND MESSAGES HERE OR YOU WILL BE BANNED FOR 3 DAYS!",
                    overwrites=overwrites,
                    reason=f"Honeypot channel setup by {ctx.author}"
                )
                created = True
            except discord.Forbidden:
                await ctx.respond(
                    embed=create_error_embed(
                        t("common.error", ctx=ctx),
                        "Missing permission to create text channels on this server."
                    ),
                    ephemeral=True
                )
                return
            except Exception as e:
                LogError(f"[HONEYPOT] Failed to create channel: {e}")
                await ctx.respond(embed=create_error_embed(t("common.error", ctx=ctx), str(e)), ephemeral=True)
                return

        # Post permanent warning embed
        embed = create_embed(
            title=t("honeypot.embed_title", ctx=ctx),
            description=t("honeypot.embed_desc", ctx=ctx),
            color=EmbedColors.SECURITY,
            bot_user=self.bot.user,
            footer_text=t("honeypot.embed_footer", ctx=ctx)
        )

        try:
            warning_msg = await channel.send(embed=embed)
            try:
                await warning_msg.pin(reason="Honeypot permanent warning banner")
            except Exception:
                pass
        except Exception as e:
            LogError(f"[HONEYPOT] Could not send warning message in #{channel.name}: {e}")

        # Save to configuration
        cfg = config.loadserverconfig()
        guild_cfg = cfg.setdefault(str(guild.id), {})
        guild_cfg["honeypot_channel"] = channel.id
        config.saveserverconfig(cfg)

        msg_key = "honeypot.setup_created" if created else "honeypot.setup_success"
        resp_embed = create_success_embed(
            t("common.success", ctx=ctx),
            t(msg_key, ctx=ctx, channel=channel.mention)
        )
        await ctx.respond(embed=resp_embed, ephemeral=True)
        LogModeration(f"[HONEYPOT] Setup channel {channel.id} in guild {guild.id} by {ctx.author.id}")

    async def _remove_honeypot(self, ctx: discord.ApplicationContext, delete_channel: bool = False):
        guild = ctx.guild
        cfg = config.loadserverconfig()
        guild_cfg = cfg.get(str(guild.id), {})
        hp_id = guild_cfg.pop("honeypot_channel", None)
        config.saveserverconfig(cfg)

        if not hp_id:
            await ctx.respond(
                embed=create_warning_embed(t("common.warning", ctx=ctx), t("honeypot.not_active", ctx=ctx)),
                ephemeral=True
            )
            return

        desc = t("honeypot.remove_success", ctx=ctx)
        if delete_channel:
            chan = guild.get_channel(int(hp_id))
            if chan:
                try:
                    await chan.delete(reason=f"Honeypot channel deleted by {ctx.author}")
                    desc += f"\n• {t('honeypot.channel_deleted', ctx=ctx)}"
                except Exception as e:
                    LogError(f"[HONEYPOT] Could not delete channel {hp_id}: {e}")

        await ctx.respond(embed=create_success_embed(t("common.success", ctx=ctx), desc), ephemeral=True)
        LogModeration(f"[HONEYPOT] Removed honeypot in guild {guild.id} by {ctx.author.id}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if message.author.id == self.bot.user.id:
            return

        cfg = config.loadserverconfig()
        guild_cfg = cfg.get(str(message.guild.id), {})
        hp_channel_id = guild_cfg.get("honeypot_channel")
        if not hp_channel_id or message.channel.id != int(hp_channel_id):
            return

        # Bypass for administrators or owner to prevent accidental bans
        if isinstance(message.author, discord.Member) and message.author.guild_permissions.administrator:
            return

        guild = message.guild
        user = message.author
        now = discord.utils.utcnow()
        unban_time = now + datetime.timedelta(days=3)
        unban_str = discord.utils.format_dt(unban_time, 'F')

        # 1. Delete triggering spam message immediately
        try:
            await message.delete()
        except Exception as e:
            LogError(f"[HONEYPOT] Failed to delete message {message.id}: {e}")

        # 2. Attempt DM notification before banning
        try:
            dm_embed = create_embed(
                title=t("honeypot.dm_banned_title", guild=guild),
                description=t("honeypot.dm_banned_desc", guild=guild, guild_name=guild.name, unban_time=unban_str),
                color=EmbedColors.SECURITY,
                bot_user=self.bot.user
            )
            await user.send(embed=dm_embed)
        except Exception as dm_e:
            LogDebug(f"[HONEYPOT] Could not send DM to user {user.id}: {dm_e}")

        # 3. Ban user for 3 days
        reason = f"Honeypot Triggered: Sent message in #{message.channel.name} (3-Day Tempban)"
        try:
            await guild.ban(user, reason=reason, delete_message_days=1)
            LogModeration(f"[HONEYPOT] Banned {user.id} in guild {guild.id} for 3 days")
        except Exception as ban_e:
            LogError(f"[HONEYPOT] Failed to ban {user.id} in guild {guild.id}: {ban_e}")
            # Fallback timeout if ban fails
            if isinstance(user, discord.Member):
                try:
                    await user.timeout_for(datetime.timedelta(days=3), reason=reason)
                except Exception:
                    pass
            return

        # 4. Save tempban record (Database-backed for multi-backend & Docker)
        config.add_tempban(guild.id, user.id, unban_time.isoformat(), reason)

        # 5. Log incident to configured guild log channel
        log_channel_id = guild_cfg.get("logchannel")
        if log_channel_id:
            log_chan = guild.get_channel(int(log_channel_id))
            if log_chan:
                preview = message.content[:300] if message.content else "[Attachments / Media Only]"
                log_embed = create_security_embed(
                    t("honeypot.log_title", guild=guild),
                    t(
                        "honeypot.log_desc",
                        guild=guild,
                        user=user.mention,
                        user_id=user.id,
                        channel=message.channel.mention,
                        content=preview,
                        unban_time=unban_str
                    ),
                    color=EmbedColors.ERROR,
                    bot_user=self.bot.user
                )
                try:
                    await log_chan.send(embed=log_embed)
                except Exception as log_e:
                    LogError(f"[HONEYPOT] Could not send log to channel {log_channel_id}: {log_e}")

    @tasks.loop(minutes=1)
    async def check_unbans(self):
        try:
            tempbans = config.load_tempbans()
            if not tempbans:
                return

            now = discord.utils.utcnow()

            for tb in tempbans:
                try:
                    unban_at = datetime.datetime.fromisoformat(tb["unban_at"])
                    if now >= unban_at:
                        guild = self.bot.get_guild(int(tb["guild_id"]))
                        if guild:
                            try:
                                user_obj = discord.Object(id=int(tb["user_id"]))
                                await guild.unban(user_obj, reason="Honeypot 3-day tempban expired")
                                LogModeration(f"[HONEYPOT] Automatically unbanned {tb['user_id']} in guild {tb['guild_id']}")
                            except discord.NotFound:
                                pass
                            except Exception as unban_e:
                                LogError(f"[HONEYPOT] Could not unban user {tb.get('user_id')} in guild {tb.get('guild_id')}: {unban_e}")
                        # Remove from database
                        config.remove_tempban(tb["guild_id"], tb["user_id"])
                except Exception as tb_e:
                    LogError(f"[HONEYPOT] Error processing unban for user {tb.get('user_id')}: {tb_e}")

        except Exception as loop_e:
            LogError(f"[HONEYPOT] Error in unban task: {loop_e}")

    @check_unbans.before_loop
    async def before_check_unbans(self):
        await self.bot.wait_until_ready()


def setup(bot: discord.Bot):
    bot.add_cog(Honeypot(bot))
