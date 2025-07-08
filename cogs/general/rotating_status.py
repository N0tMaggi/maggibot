import discord
from discord.ext import commands, tasks
from handlers.config import mac_load_bans

class RotatingStatus(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.update_status.start()

    def cog_unload(self):
        self.update_status.cancel()

    @tasks.loop(seconds=30)
    async def update_status(self):
        bans = mac_load_bans()
        banned_count = len(bans) if bans else 0
        statuses = [
            f"\U0001F6AB {banned_count} globally banned",
            f"\U0001F465 Managing {len(self.bot.users)} users",
            f"\U0001F6E1\uFE0F On {len(self.bot.guilds)} servers",
        ]
        message = statuses[self.update_status.current_loop % len(statuses)]
        try:
            await self.bot.change_presence(activity=discord.Game(name=message))
        except Exception:
            pass

    @update_status.before_loop
    async def before_update_status(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(RotatingStatus(bot))
