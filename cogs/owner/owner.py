import discord
from discord.ext import commands
import datetime
import os
import asyncio
from typing import Optional
from handlers.debug import LogDebug, LogSystem, LogError
class OwnerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.shutdown_in_progress = False
        self.reboot_in_progress = False

    async def check_running_tasks(self) -> bool:
        # Work in progress
        return True
    

    async def shutdown_sequence(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(
            title="🛑 Bot Shutdown",
            description="Shutdown sequence initiated...",
            color=discord.Color.red()
        )
        msg = await ctx.respond(embed=embed)
        
        for i in range(1, 6):
            progress = "▰" * i + "▱" * (5 - i)
            embed.description = f"Shutting down... [{progress}] ({i*20}%)"
            await msg.edit(embed=embed)
            await asyncio.sleep(0.5)

    async def reboot_sequence(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(
            title="🔄 Bot Reboot",
            description="Reboot sequence initiated...",
            color=discord.Color.blue()
        )
        msg = await ctx.respond(embed=embed)
        
        for i in range(1, 6):
            progress = "▰" * i + "▱" * (5 - i)
            embed.description = f"Rebooting... [{progress}] ({i*20}%)"
            await msg.edit(embed=embed)
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
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="Only the bot owner can perform this action",
                color=discord.Color.brand_red()
            )
            LogSystem(f" Access denied for {ctx.author} to stop the bot")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        if not await self.check_running_tasks():
            embed = discord.Embed(
                title="⚠️ Safety Check Failed",
                description="There are still active tasks running. Please try again later.",
                color=discord.Color.yellow()
            )
            LogError(f" Safety check failed, stopping...")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        LogSystem(f" Stopping the bot...")
        await self.shutdown_sequence(ctx)
        
        try:
            await self.bot.close()
        except Exception as e:
            LogError(f"Shutdown failed: {str(e)}")
            await ctx.edit(embed=discord.Embed(
                title="❌ Shutdown Failed",
                description="An error occurred during shutdown",
                color=discord.Color.dark_red()
            ))

    @commands.slash_command(name="reboot", description="[Owner only] Reboot the bot 🔄")
    @commands.is_owner()
    async def reboot(self, ctx: discord.ApplicationContext):
        if self.reboot_in_progress:
            LogSystem(f" Reboot already in progress for {ctx.author}")
            return await ctx.respond("Reboot already in progress!", ephemeral=True)
        
        self.reboot_in_progress = True
        authorised = int(os.getenv('OWNER_ID'))
        
        if ctx.author.id != authorised:
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="Only the bot owner can perform this action",
                color=discord.Color.brand_red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        if not await self.check_running_tasks():
            embed = discord.Embed(
                title="⚠️ Safety Check Failed",
                description="There are still active tasks running. Please try again later.",
                color=discord.Color.yellow()
            )
            LogError(f" Safety check failed, skipping...")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        await self.reboot_sequence(ctx)
        
        try:
            await self.bot.close()
            
        except Exception as e:
            LogError(f"Reboot failed: {str(e)}")
            await ctx.edit(embed=discord.Embed(
                title="❌ Reboot Failed",
                description="An error occurred during reboot",
                color=discord.Color.dark_red()
            ))


    @commands.slash_command(name="error-normal", description="⚡ Trigger a controlled test error")
    async def error_normal(self, ctx: discord.ApplicationContext):
        """Generate a test error (Owner only)"""
        await ctx.defer(ephemeral=True)
        
        if ctx.author.id != int(self.owner_id):
            embed = self.create_embed(
                "⛔ Unauthorized Access",
                "```diff\n- Critical Security Alert: Unauthorized error trigger attempt!```",
                "error"
            )
            await ctx.followup.send(embed=embed)
            LogError(f"Unauthorized error trigger by {ctx.author.id}")
            return

        try:
            LogError("⚠️ Test error triggered (normal)")
            raise Exception("🚨 Controlled test error triggered successfully!")
            
        except Exception as e:
            embed = self.create_embed(
                "⚠️ Test Error Generated",
                f"```diff\n- {str(e)}\n+ Error handling working correctly!```",
                "error"
            )
            await ctx.followup.send(embed=embed)
            raise

    @commands.slash_command(name="error-fatal", description="💥 Trigger a critical test error")
    async def error_fatal(self, ctx: discord.ApplicationContext):
        """Generate a fatal test error (Owner only)"""
        await ctx.defer(ephemeral=True)

        if ctx.author.id != int(self.owner_id):
            embed = self.create_embed(
                "⛔ Security Violation",
                "```diff\n- ALERT: Unauthorized critical error trigger attempt!```",
                "error"
            )
            await ctx.followup.send(embed=embed)
            LogError(f"Unauthorized fatal error attempt by {ctx.author.id}")
            return

        try:
            LogError("💥 Fatal test error triggered")
            raise Exception("🔥 CRITICAL TEST ERROR - SYSTEM SIMULATION")
            
        except Exception as e:
            embed = self.create_embed(
                "💥 Fatal Error Simulation",
                f"```diff\n- {str(e)}\n+ Error containment successful!```",
                "error"
            )
            await ctx.followup.send(embed=embed)
            raise


def setup(bot):
    bot.add_cog(OwnerCommands(bot))