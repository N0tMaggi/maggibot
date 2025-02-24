import discord
from discord.ext import commands
import json
import os
import asyncio


class Activity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    async def change_activity(self):
        activities = ["with ur mom", "with ur dad", "with nobody :("]  # list of possible activities
        while True:
            for activity in activities:
                await self.bot.change_presence(activity=discord.Game(name=activity))
                await asyncio.sleep(300)  # 5 minutes in seconds

def setup(bot):
    bot.add_cog(Activity(bot))

