import discord
from discord.ext import commands
import os
from discord.commands import slash_command
import datetime
import json
import requests
import dotenv
from dotenv import load_dotenv
import time
import handlers.debug as DebugHandler
import logging
from colorama import Fore, Style, init


init(autoreset=True)

# Load the .env file
load_dotenv()

DEBUG = os.getenv('DEBUG_MODE')

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

currenttime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
intents = discord.Intents.all()
TOKEN = os.getenv('TOKEN')

bot = discord.Bot(intents=intents)

def is_admin(ctx):
    return ctx.author.guild_permissions.administrator

def is_connected_to_internet():
    try:
        requests.get("https://google.com")
        return True, "Connected to the internet"
    except:
        return False, "Not connected to the internet"

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

def delete_traceback_files():
    for filename in os.listdir('./logs'):
        if filename.startswith('traceback_'):
            try:
                os.remove(os.path.join('./logs', filename))
                DebugHandler.LogDebug(f" Deleted traceback file {filename}")
                print(Fore.GREEN + Style.BRIGHT + f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
                print (Fore.GREEN + Style.BRIGHT + f"Deleted traceback file {filename}")
            except Exception as e:
                DebugHandler.LogDebug(f" Error deleting log file {filename}: {e}")
                raise Exception (f"Error deleting log file {filename}: {e}")
    print(Fore.GREEN + Style.BRIGHT + f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
    
def DEBUG_MODE_PRINT_ENV():
    if DEBUG == 'TRUE':
        DebugHandler.LogDebug(f"DEBUG: {DEBUG}")
        DebugHandler.LogDebug(f"OWNER_ID: {os.getenv('OWNER_ID')}")
        DebugHandler.LogDebug(f"Error Log Channel ID: {os.getenv('ERROR_LOG_CHANNEL_ID')}")
        DebugHandler.LogDebug(f"Command log Channel ID: {os.getenv('COMMAND_LOG_CHANNEL_ID')}")
        time.sleep(5)
        logging.basicConfig(level=logging.DEBUG)
        return True
    return False

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print("-------------------------------------------")
    print(f'Connected to {len(bot.guilds)} servers: ')
    for guild in bot.guilds:
        print(f'- {guild.name} (ID: {guild.id})')
    print("-------------------------------------------")
    print(f'Connected to the internet: {is_connected_to_internet()[0]}')
    print("-------------------------------------------")
    print(f'JSON files are valid: {check_json_files("data")}')
    print("-------------------------------------------")
    print(f'Current time: {currenttime}')
    print("-------------------------------------------")
    await bot.change_presence(activity=discord.Game(name="with your mom"))

def load_cogs(bot, directory='cogs'):
    cog_count = 0
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.py'):
                module_name = os.path.join(root, filename)[:-3].replace(os.sep, '.')
                try:
                    bot.load_extension(module_name)
                    print(f'Loaded COG: {module_name}')
                    cog_count += 1
                except Exception as e:
                    print(f'Failed to load {module_name}: {e}')
    print(f'------------------------------------')
    print(f'Loaded {cog_count} Cogs')
    print(f'------------------------------------')

try:
    if not is_connected_to_internet()[0]:
        print('Not connected to the Internet')
        os._exit(1)
    
    if DEBUG_MODE_PRINT_ENV():
        pass
    
    if not check_json_files('data'):
        print(Fore.RED + Style.BRIGHT + f"Not all JSON files are valid")
        os._exit(1)
    else:
        print(Fore.GREEN + Style.BRIGHT + f"All JSON files are valid!")
    

    clear_screen()
    delete_traceback_files()
    time.sleep(1)
    print('------------STARTING THE BOT------------')
    print("""
    ╔╦╗┌─┐┌─┐┌─┐┬╔═╗┬ ┬┌─┐┌┬┐┌─┐┌┬┐
    ║║║├─┤│ ┬│ ┬│╚═╗└┬┘└─┐ │ ├┤ │││
    ╩ ╩┴ ┴└─┘└─┘┴╚═╝ ┴ └─┘ ┴ └─┘┴ ┴
    """)
    print(f'------------------------------------')
    load_cogs(bot)
    bot.run(TOKEN)

except Exception as e:
    raise Exception(f"An error occurred while starting the bot: {e}")
except KeyboardInterrupt:
    print("\n Keyboard Interrupt detected..... Stopping the bot...")
    bot.close()
