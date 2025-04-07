import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.ui import View, Select, Button
from discord import ui
import datetime
from handlers.debug import LogDebug



class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



def setup(bot):
    bot.add_cog(Test(bot))