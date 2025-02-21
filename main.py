import discord
from discord.ext import commands
import os
from discord.commands import slash_command  # Import slash_command correctly
import datetime
import json
import requests
import re
from discord.ext import commands
import dotenv
from dotenv import load_dotenv

load_dotenv()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

currenttime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
intents = discord.Intents.all()
TOKEN = os.getenv('TOKEN')

# Correct class to instantiate the bot
bot = discord.Bot(
    intents=intents,
    #debug_guilds=[1227993713813356654]
)

def is_admin(ctx):
    return ctx.author.guild_permissions.administrator




@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    


#------------------ START OF BOT
if __name__ == "__main__":
    clear_screen()
    print('------------STARTING THE BOT------------')
    asciiheader = """


╔╦╗┌─┐┌─┐┌─┐┬╔═╗┬ ┬┌─┐┌┬┐┌─┐┌┬┐
║║║├─┤│ ┬│ ┬│╚═╗└┬┘└─┐ │ ├┤ │││
╩ ╩┴ ┴└─┘└─┘┴╚═╝ ┴ └─┘ ┴ └─┘┴ ┴



"""
    print(asciiheader)
    print(f'------------------------------------')
    for filename in os.listdir("cogs"):
        if filename.endswith('.py'):
            print(f'Loaded COG: {filename}')
            print(f'------------------------------------')
            bot.load_extension(f"cogs.{filename[:-3]}")

bot.run(TOKEN)
