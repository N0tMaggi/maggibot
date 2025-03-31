import discord
from discord.ext import commands
from datetime import datetime

import os
import asyncio
from typing import Optional
from handlers.debug import LogDebug, LogSystem, LogError
from handlers.env import get_owner

class Error(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = get_owner()
        self.embed_colors = {
            "info": 0x3498db,
            "status": 0x2ecc71,
            "error": 0xe74c3c
        }


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

        LogError("💥 Fatal test error triggered")

        embed = self.create_embed(
            "⚠️ Sucesfully Triggered",
            "```diff\n- ALERT: Bot Might Becomes Unresponsive for a few seconds!```",
            "error"
        )
        await ctx.followup.send(embed=embed)
        raise Exception("🔥 CRITICAL TEST ERROR - SYSTEM SIMULATION")



def setup(bot):
    bot.add_cog(Error(bot))