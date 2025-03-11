import discord
from discord.ext import commands
import os
from discord.commands import slash_command  # Import slash_command correctly
import datetime
import json
import requests
import re
import dotenv
from dotenv import load_dotenv
import time
import handlers.debug as DebugHandler
import logging

# Load the .env file
load_dotenv()

DEBUG = os.getenv('DEBUG_MODE')


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

currenttime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
intents = discord.Intents.all()
TOKEN = os.getenv('TOKEN')

bot = discord.Bot(
    intents=intents,
    #debug_guilds=[int(os.getenv('DEBUG_GUILD_ID'))],

)

def is_admin(ctx):
    return ctx.author.guild_permissions.administrator

def is_connected_to_internet():
    try:
        requests.get("https://google.com")
        return (True, "Connected to the internet")
    except:
        return (False, "Not connected to the internet") 


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



def DEBUG_MODE_PRINT_ENV():
    if DEBUG == 'TRUE':
        DebugHandler.LogDebug(f"DEBUG: {DEBUG}")
        DebugHandler.LogDebug(f"OWNER_ID: {os.getenv('OWNER_ID')}")
        DebugHandler.LogDebug(f"Error Log Channel ID: {os.getenv('ERROR_LOG_CHANNEL_ID')}")
        DebugHandler.LogDebug(f"Command log Channel ID: {os.getenv('COMMAND_LOG_CHANNEL_ID')}")
        time.sleep(5)
        logging.basicConfig(level=logging.DEBUG)
        return True
    else:
        return False

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print(f"-------------------------------------------")
    print(f'Connected to {len(bot.guilds)} servers: ')
    for guild in bot.guilds:
        print(f'- {guild.name} (ID: {guild.id})')
    print(f"-------------------------------------------")
    print(f'Connected to the internet: {is_connected_to_internet()[0]}')
    print(f"-------------------------------------------")
    print(f'JSON files are valid: {check_json_files("data")}')
    print(f"-------------------------------------------")
    print(f'Current time: {currenttime}')
    print(f"-------------------------------------------")
    await bot.change_presence(activity=discord.Game(name="with your mom"))



#------------------ START OF BOT

try:
    if is_connected_to_internet()[0]:
        pass
    else:
        print('Not connected to the Internet')
        os._exit(1)
    
    if DEBUG_MODE_PRINT_ENV():
        pass
    else:
        pass

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

except Exception as e:
    raise Exception(f"An error occured while starting the bot: {e}")
except KeyboardInterrupt:
    print("\n Keyboard Interrupt detected..... Stopping the bot...")
    bot.close()
