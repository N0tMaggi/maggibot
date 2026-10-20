# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from handlers.config import load_onlyimages, save_onlyimages
from handlers.debug import LogError
from handlers.locale import t
from utils.embed_helpers import create_embed, create_success_embed, create_warning_embed


class OnlyImages(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.slash_command(
        name="onlyimages-enable",
        description="Enable image-only mode in the current channel",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_channels=True)
    )
    @commands.has_permissions(manage_channels=True)
    async def enableonlyimages(self, ctx: discord.ApplicationContext):
        gid = ctx.guild.id
        channels = load_onlyimages()
        channel_id = str(ctx.channel.id)

        if channel_id in channels:
            embed = create_warning_embed(
                t("common.warning", guild_id=gid),
                t("onlyimages.already_enabled", guild_id=gid, channel=ctx.channel.mention)
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        channels[channel_id] = True
        save_onlyimages(channels)

        embed = create_success_embed(
            t("onlyimages.activated", guild_id=gid),
            t("onlyimages.activated_desc", guild_id=gid, channel=ctx.channel.mention, count=len(channels)),
            bot_user=self.bot.user
        )
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="onlyimages-disable",
        description="Disable image-only mode in the current channel",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_channels=True)
    )
    @commands.has_permissions(manage_channels=True)
    async def disableonlyimages(self, ctx: discord.ApplicationContext):
        gid = ctx.guild.id
        channels = load_onlyimages()
        channel_id = str(ctx.channel.id)

        if channel_id not in channels:
            embed = create_warning_embed(
                t("common.warning", guild_id=gid),
                t("onlyimages.not_active", guild_id=gid, channel=ctx.channel.mention)
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        del channels[channel_id]
        save_onlyimages(channels)

        embed = create_success_embed(
            t("onlyimages.deactivated", guild_id=gid),
            t("onlyimages.deactivated_desc", guild_id=gid, channel=ctx.channel.mention),
            bot_user=self.bot.user
        )
        await ctx.respond(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.type != discord.MessageType.default:
            return

        channels = load_onlyimages()
        if str(message.channel.id) not in channels:
            return

        if not message.attachments:
            try:
                await message.delete()
            except discord.Forbidden:
                LogError(f"Missing permissions to delete message in {message.channel.id}")
            except Exception as e:
                LogError(f"Failed to delete non-image message: {str(e)}")

            gid = message.guild.id if message.guild else None
            warning_embed = create_warning_embed(
                t("onlyimages.warn_title", guild_id=gid),
                t("onlyimages.warn_desc", guild_id=gid, user=message.author.mention),
                bot_user=self.bot.user
            )

            try:
                await message.channel.send(embed=warning_embed, delete_after=10)
            except Exception as e:
                LogError(f"Failed to send image-only warning: {e}")


def setup(bot: discord.Bot):
    bot.add_cog(OnlyImages(bot))
