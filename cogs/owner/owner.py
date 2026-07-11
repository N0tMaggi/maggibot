import discord
from discord.ext import commands
from datetime import datetime

import os
import asyncio
from typing import Optional
from handlers.debug import LogDebug, LogSystem, LogError
from handlers.env import get_owner
from utils.components import build_container, build_view

class OwnerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.shutdown_in_progress = False
        self.reboot_in_progress = False
        self.owner_id = get_owner()

    async def check_running_tasks(self) -> bool:
        # Work in progress
        return True

    def create_embed(self, title, description, color_name="info"):
        return build_container(
            title=title,
            description=description,
            color=color_name,
            thumbnail=self.bot.user.display_avatar.url if self.bot.user else None,
            footer_text="Maggi Dev System",
            footer_icon="https://maggi.dev/favicon/favicon.ico",
            timestamp=True,
            bot_user=self.bot.user,
        )
    

    async def shutdown_sequence(self, ctx: discord.ApplicationContext):
        embed = build_container(
            title="🛑 Bot Shutdown",
            description="Shutdown sequence initiated...",
            color='error',
            bot_user=self.bot.user,
        )
        await ctx.respond(view=build_view(embed))
        msg = await ctx.interaction.original_response()
        
        for i in range(1, 6):
            progress = "▰" * i + "▱" * (5 - i)
            embed = build_container(
                title="🛑 Bot Shutdown",
                description=f"Shutting down... [{progress}] ({i*20}%)",
                color='error',
                bot_user=self.bot.user,
            )
            await msg.edit(view=build_view(embed))
            await asyncio.sleep(0.5)

    async def reboot_sequence(self, ctx: discord.ApplicationContext):
        embed = build_container(
            title="🔄 Bot Reboot",
            description="Reboot sequence initiated...",
            color='info',
            bot_user=self.bot.user,
        )
        await ctx.respond(view=build_view(embed))
        msg = await ctx.interaction.original_response()
        
        for i in range(1, 6):
            progress = "▰" * i + "▱" * (5 - i)
            embed = build_container(
                title="🔄 Bot Reboot",
                description=f"Rebooting... [{progress}] ({i*20}%)",
                color='info',
                bot_user=self.bot.user,
            )
            await msg.edit(view=build_view(embed))
            await asyncio.sleep(0.5)

    @commands.slash_command(name="stop", description="[Owner only] Stop the bot 🛑")
    @commands.is_owner()
    async def stop(self, ctx: discord.ApplicationContext):
        if self.shutdown_in_progress:
            LogSystem(f" Shutdown already in progress, skipping...")
            return await ctx.respond("Shutdown already in progress!", ephemeral=True)
        
        self.shutdown_in_progress = True
        authorised = int(os.getenv('OWNER_ID'))
        
        if ctx.author.id != authorised:
            embed = build_container(
                title="🚫 Access Denied",
                description="Only the bot owner can perform this action",
                color='error',
                bot_user=self.bot.user,
            )
            LogSystem(f" Access denied for {ctx.author} to stop the bot")
            return await ctx.respond(view=build_view(embed), ephemeral=True)
        
        if not await self.check_running_tasks():
            embed = build_container(
                title="⚠️ Safety Check Failed",
                description="There are still active tasks running. Please try again later.",
                color='warning',
                bot_user=self.bot.user,
            )
            LogError(f" Safety check failed, stopping...")
            return await ctx.respond(view=build_view(embed), ephemeral=True)
        
        LogSystem(f" Stopping the bot...")
        await self.shutdown_sequence(ctx)
        
        try:
            await self.bot.close()
        except Exception as e:
            LogError(f"Shutdown failed: {str(e)}")
            await ctx.edit(view=build_view(build_container(
                title="❌ Shutdown Failed",
                description="An error occurred during shutdown",
                color=discord.Color.dark_red().value,
                bot_user=self.bot.user,
            )))

    @commands.slash_command(name="reboot", description="[Owner only] Reboot the bot 🔄")
    @commands.is_owner()
    async def reboot(self, ctx: discord.ApplicationContext):
        if self.reboot_in_progress:
            LogSystem(f" Reboot already in progress for {ctx.author}")
            return await ctx.respond("Reboot already in progress!", ephemeral=True)
        
        self.reboot_in_progress = True
        authorised = int(os.getenv('OWNER_ID'))
        
        if ctx.author.id != authorised:
            embed = build_container(
                title="🚫 Access Denied",
                description="Only the bot owner can perform this action",
                color='error',
                bot_user=self.bot.user,
            )
            return await ctx.respond(view=build_view(embed), ephemeral=True)
        
        if not await self.check_running_tasks():
            embed = build_container(
                title="⚠️ Safety Check Failed",
                description="There are still active tasks running. Please try again later.",
                color='warning',
                bot_user=self.bot.user,
            )
            LogError(f" Safety check failed, skipping...")
            return await ctx.respond(view=build_view(embed), ephemeral=True)
        
        await self.reboot_sequence(ctx)
        
        try:
            await self.bot.close()
            
        except Exception as e:
            LogError(f"Reboot failed: {str(e)}")
            await ctx.edit(view=build_view(build_container(
                title="❌ Reboot Failed",
                description="An error occurred during reboot",
                color=discord.Color.dark_red().value,
                bot_user=self.bot.user,
            )))

def setup(bot):
    bot.add_cog(OwnerCommands(bot))
