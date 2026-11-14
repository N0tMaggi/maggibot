# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
import asyncio
from handlers.debug import LogDebug, LogSystem, LogError
from handlers.env import get_owner
from utils.embed_helpers import create_embed, create_error_embed, create_warning_embed, create_info_embed, create_success_embed


class OwnerCommands(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.shutdown_in_progress = False
        self.reboot_in_progress = False

    async def check_running_tasks(self) -> bool:
        return True

    async def shutdown_sequence(self, ctx: discord.ApplicationContext):
        embed = create_embed(
            title="🛑 Bot-Herunterfahren",
            description="Herunterfahren wird vorbereitet...",
            color="error",
            bot_user=self.bot.user
        )
        msg = await ctx.respond(embed=embed)

        for i in range(1, 6):
            progress = "▰" * i + "▱" * (5 - i)
            embed.description = f"Herunterfahren... [{progress}] ({i*20}%)"
            await msg.edit(embed=embed)
            await asyncio.sleep(0.4)

    async def reboot_sequence(self, ctx: discord.ApplicationContext):
        embed = create_embed(
            title="🔄 Bot-Neustart",
            description="Neustart-Sequenz wird eingeleitet...",
            color="info",
            bot_user=self.bot.user
        )
        msg = await ctx.respond(embed=embed)

        for i in range(1, 6):
            progress = "▰" * i + "▱" * (5 - i)
            embed.description = f"Neustart... [{progress}] ({i*20}%)"
            await msg.edit(embed=embed)
            await asyncio.sleep(0.4)

    @commands.slash_command(name="stop", description="[Owner only] Stoppt den Bot sicher 🛑")
    @commands.is_owner()
    async def stop(self, ctx: discord.ApplicationContext):
        if self.shutdown_in_progress:
            return await ctx.respond("Shutdown läuft bereits!", ephemeral=True)

        try:
            authorised = get_owner()
        except Exception:
            authorised = None

        if ctx.author.id != authorised:
            embed = create_error_embed("Zugriff verweigert", "Nur der Bot-Owner kann diesen Befehl ausführen.")
            LogSystem(f"Access denied for {ctx.author} to stop the bot")
            return await ctx.respond(embed=embed, ephemeral=True)

        if not await self.check_running_tasks():
            embed = create_warning_embed("Sicherheitsprüfung fehlgeschlagen", "Aktive Tasks laufen noch. Bitte später erneut versuchen.")
            return await ctx.respond(embed=embed, ephemeral=True)

        self.shutdown_in_progress = True
        LogSystem(f"Stopping the bot by {ctx.author.id}...")
        await self.shutdown_sequence(ctx)

        try:
            await self.bot.close()
        except Exception as e:
            LogError(f"Shutdown failed: {str(e)}")
            await ctx.respond(embed=create_error_embed("Fehler", f"Fehler beim Beenden: {e}"), ephemeral=True)

    @commands.slash_command(name="reboot", description="[Owner only] Startet den Bot neu 🔄")
    @commands.is_owner()
    async def reboot(self, ctx: discord.ApplicationContext):
        if self.reboot_in_progress:
            return await ctx.respond("Neustart läuft bereits!", ephemeral=True)

        try:
            authorised = get_owner()
        except Exception:
            authorised = None

        if ctx.author.id != authorised:
            embed = create_error_embed("Zugriff verweigert", "Nur der Bot-Owner kann diesen Befehl ausführen.")
            return await ctx.respond(embed=embed, ephemeral=True)

        if not await self.check_running_tasks():
            embed = create_warning_embed("Sicherheitsprüfung fehlgeschlagen", "Aktive Tasks laufen noch. Bitte später erneut versuchen.")
            return await ctx.respond(embed=embed, ephemeral=True)

        self.reboot_in_progress = True
        await self.reboot_sequence(ctx)

        try:
            await self.bot.close()
        except Exception as e:
            LogError(f"Reboot failed: {str(e)}")
            await ctx.respond(embed=create_error_embed("Fehler", f"Fehler beim Neustart: {e}"), ephemeral=True)


def setup(bot: discord.Bot):
    bot.add_cog(OwnerCommands(bot))
