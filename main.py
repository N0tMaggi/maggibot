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



def is_connected_to_internet():
    try:
        requests.get("https://google.com")
        return (True, "Connected to the internet")
    except:
        return (False, "Not connected to the internet") 



@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print(f"-------------------------------------------")
    print(f'Connected to {len(bot.guilds)} servers:')
    for guild in bot.guilds:
        print(f'- {guild.name} (ID: {guild.id})')
    print(f"-------------------------------------------")
    print(f'Connected to the internet: {is_connected_to_internet()[0]}')
    print(f'Current time: {currenttime}')
    print(f"-------------------------------------------")
    await bot.change_presence(activity=discord.Game(name="with your mom"))
    


import json
import os

def check_json_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, 'r') as file:
                    json.load(file)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON in file {filename}: {e}")
                return False
    return True



#------------------ START OF BOT
if __name__ == "__main__":
    if is_connected_to_internet:
        pass
    else: 
        print('Not connected to the Internet')
        exit()
        os._exit(1)

    if not check_json_files('data'):
        print("Not all JSON files are valid")
        os._exit(1)
    else:
        print("All JSON files are valid!")

    clear_screen()
    print('------------STARTING THE BOT------------')
    asciiheader = """


╔╦╗┌─┐┌─┐┌─┐┬╔═╗┬ ┬┌─┐┌┬┐┌─┐┌┬┐
║║║├─┤│ ┬│ ┬│╚═╗└┬┘└─┐ │ ├┤ │││
╩ ╩┴ ┴└─┘└─┘┴╚═╝ ┴ └─┘ ┴ └─┘┴ ┴



"""
    print(asciiheader)
    print(f'------------------------------------')
    cog_count = 0
    for filename in os.listdir("cogs"):
        if filename.endswith('.py'):
            cog_count += 1
            print(f'Loaded COG: {filename}')
    print(f'Loaded {cog_count} Cogs')
    print(f'------------------------------------')
    for filename in os.listdir("cogs"):
        if filename.endswith('.py'):
            bot.load_extension(f"cogs.{filename[:-3]}")

bot.run(TOKEN)
