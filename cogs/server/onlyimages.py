# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from handlers.config import load_onlyimages, save_onlyimages
from handlers.debug import LogError
from utils.embed_helpers import create_embed, create_success_embed, create_warning_embed, create_error_embed


class OnlyImages(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.slash_command(
        name="onlyimages-enable",
        description="Nur-Bilder Modus im aktuellen Kanal aktivieren",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_channels=True)
    )
    @commands.has_permissions(manage_channels=True)
    async def enableonlyimages(self, ctx: discord.ApplicationContext):
        channels = load_onlyimages()
        channel_id = str(ctx.channel.id)

        if channel_id in channels:
            embed = create_warning_embed(
                "Bereits aktiv",
                f"Der Nur-Bilder Modus ist in {ctx.channel.mention} bereits aktiv!"
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        channels[channel_id] = True
        save_onlyimages(channels)

        embed = create_success_embed(
            "Nur-Bilder Modus aktiviert",
            f"**{ctx.channel.mention}** erlaubt ab sofort nur noch Nachrichten mit Anhängen oder Bildern.\n\n"
            f"• Reine Textnachrichten werden automatisch gelöscht\n"
            f"• Aktive Only-Images Kanäle: `{len(channels)}`",
            bot_user=self.bot.user
        )
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="onlyimages-disable",
        description="Nur-Bilder Modus im aktuellen Kanal deaktivieren",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_channels=True)
    )
    @commands.has_permissions(manage_channels=True)
    async def disableonlyimages(self, ctx: discord.ApplicationContext):
        channels = load_onlyimages()
        channel_id = str(ctx.channel.id)

        if channel_id not in channels:
            embed = create_warning_embed(
                "Nicht aktiv",
                f"Der Nur-Bilder Modus ist in {ctx.channel.mention} nicht aktiv."
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        del channels[channel_id]
        save_onlyimages(channels)

        embed = create_success_embed(
            "Nur-Bilder Modus deaktiviert",
            f"**{ctx.channel.mention}** wurde in den Normalzustand zurückversetzt.",
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

            warning_embed = create_warning_embed(
                "Anhang erforderlich",
                f"{message.author.mention}, in diesem Kanal sind nur Nachrichten mit Bildern, Dateien oder Videos erlaubt!",
                bot_user=self.bot.user
            )

            try:
                await message.channel.send(embed=warning_embed, delete_after=10)
            except Exception as e:
                LogError(f"Failed to send image-only warning: {e}")


def setup(bot: commands.Bot):
    bot.add_cog(OnlyImages(bot))
