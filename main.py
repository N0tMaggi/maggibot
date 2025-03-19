# -*- coding: utf-8 -*-
# Main Bot Execution File

import sys
import os
import time
import json
import logging
import datetime
import requests
import discord
from discord.ext import commands
from discord.commands import slash_command
from colorama import Fore, Style, init
from dotenv import load_dotenv

# Local imports
import handlers.debug as DebugHandler
from handlers.config import get_config_files, get_data_files

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Initialization
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
init(autoreset=True)
load_dotenv()

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Constants & Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
DEBUG = os.getenv('DEBUG_MODE')
TOKEN = os.getenv('TOKEN')
currenttime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Core Functions
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def clear_screen():
    """Clear console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def handle_installation():
    """Handle command line installation arguments"""
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "install":
            install_for_first_use()
            sys.exit(0)
        else:
            print(Fore.RED + "Invalid command. Available commands:")
            print(Fore.YELLOW + "python main.py install" + Fore.WHITE + " - Setup required files")
            sys.exit(1)

def install_for_first_use():
    """Initial setup wizard for first-time users"""
    print(Fore.GREEN + Style.BRIGHT + "-"*65)
    print(Fore.YELLOW + Style.BRIGHT + "Initial Setup Wizard")
    print(Fore.GREEN + Style.BRIGHT + "-"*65)
    
    all_files = get_config_files() + get_data_files()
    
    for file_path in all_files:
        print(Fore.CYAN + f"Checking: {file_path}", end=" ")
        
        try:
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as f:
                    json.dump({}, f)
                print(Fore.GREEN + "[CREATED]")
            else:
                with open(file_path, "r") as f:
                    content = json.load(f)
                    if content != {}:
                        raise ValueError("Non-empty JSON")
        except (json.JSONDecodeError, ValueError):
            os.remove(file_path)
            with open(file_path, "w") as f:
                json.dump({}, f)
            print(Fore.YELLOW + "[RESET]")
        except Exception as e:
            print(Fore.RED + f"[ERROR] {str(e)}")
        else:
            print(Fore.BLUE + "[OK]")
    
    print(Fore.GREEN + Style.BRIGHT + "-"*65)
    print(Fore.YELLOW + Style.BRIGHT + "Setup completed successfully!")
    print(Fore.GREEN + Style.BRIGHT + "-"*65)

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# System Checks
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def is_connected_to_internet():
    """Check internet connectivity"""
    try:
        requests.get("https://google.com", timeout=5)
        return True, "-> Internet connection:" + Fore.GREEN + " Active" + Fore.RESET
    except requests.ConnectionError:
        return False, "-> Internet connection:"+ Fore.RED + " Unavailable" + Fore.RESET

def validate_json_files(directory):
    """Validate all JSON files in directory"""
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                print(Fore.RED + f"Invalid JSON in {filename}: {str(e)}")
                return False
    return True

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Bot Events
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
@bot.event
async def on_ready():
    """Bot startup handler"""
    status_checks = [
        is_connected_to_internet()[1],
        f"\n-> JSON validation: {Fore.GREEN + 'Passed' if validate_json_files('data') else Fore.RED + 'Failed'} \n",
        Fore.RESET + "->" + Fore.MAGENTA + f" System time: {currenttime}\n"
    ]
    print(Fore.WHITE + "\n".join(status_checks))
    print(Fore.WHITE + f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(Fore.CYAN + "-"*45)

    await bot.change_presence(activity=discord.Game(name="with your mom"))

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Extension Loader
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def load_extensions(bot, directory='cogs'):
    """Load all bot extensions from directory"""
    loaded_count = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                ext_path = os.path.join(root, file)[:-3].replace(os.sep, '.')
                try:
                    bot.load_extension(ext_path)
                    print(Fore.GREEN + f"✓ "+ Fore.WHITE + f" {ext_path}")
                    loaded_count += 1
                except Exception as e:
                    print(Fore.RED + f"✗ {ext_path}: {str(e)}")
    
    print("\n")
    print(Fore.GREEN + f"Successfully loaded {loaded_count} extensions\n")
    print(Fore.CYAN + "-"*45)

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Main Execution
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def main():
    """Main application entry point"""
    handle_installation()
    
    # Pre-flight checks
    if not is_connected_to_internet()[0]:
        print(Fore.RED + "Critical error: No internet connection!")
        sys.exit(1)
    
    if not validate_json_files('data'):
        print(Fore.RED + "Critical error: Invalid configuration files!")
        sys.exit(1)
    
    clear_screen()
    
    # Startup display
    print(Fore.GREEN + Style.BRIGHT + "\n" + "="*45)
    print(Fore.RESET + r"""
    ╔╦╗┌─┐┌─┐┌─┐┬╔═╗┬ ┬┌─┐┌┬┐┌─┐┌┬┐
    ║║║├─┤│ ┬│ ┬│╚═╗└┬┘└─┐ │ ├┤ │││
    ╩ ╩┴ ┴└─┘└─┘┴╚═╝ ┴ └─┘ ┴ └─┘┴ ┴
    """)
    print(Fore.GREEN + "="*45 + "\n")
    
    load_extensions(bot)
    bot.run(TOKEN)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nSafe shutdown initiated...")
        bot.close()
    except Exception as e:
        print(Fore.RED + f"\nCritical failure: {str(e)}")
        sys.exit(1)