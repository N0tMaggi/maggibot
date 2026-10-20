# -*- coding: utf-8 -*-
"""
Maggibot - Modular & Modern Discord Bot
Main execution entry point.
"""

import sys
import os
import json
import datetime
import requests
import discord
from colorama import Fore, Style, init
from dotenv import load_dotenv

# Local imports
from handlers.debug import LogError, LogSystem, LogDebug
from handlers.config import get_config_files, get_data_files
from handlers.database import db

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Initialization
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
init(autoreset=True)
load_dotenv()

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Constants & Configuration
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
DEBUG = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
TOKEN = os.getenv('TOKEN')
BOT_VERSION = os.getenv('BOT_VERSION', '2.0.0')

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Core Functions
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def clear_screen():
    """Clear console screen"""
    if os.name == 'nt':
        os.system('cls')
    else:
        print('\033c', end='')


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
    print(Fore.GREEN + Style.BRIGHT + "-" * 65)
    print(Fore.YELLOW + Style.BRIGHT + "Initial Setup Wizard")
    print(Fore.GREEN + Style.BRIGHT + "-" * 65)

    all_files = get_config_files() + get_data_files()

    for file_path in all_files:
        print(Fore.CYAN + f"Checking: {file_path}", end=" ")
        try:
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({}, f)
                print(Fore.GREEN + "[CREATED]")
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    json.load(f)
                print(Fore.BLUE + "[OK]")
        except (json.JSONDecodeError, ValueError):
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({}, f)
            print(Fore.YELLOW + "[RESET CORRUPT FILE]")
        except Exception as e:
            print(Fore.RED + f"[ERROR] {str(e)}")

    print(Fore.GREEN + Style.BRIGHT + "-" * 65)
    print(Fore.YELLOW + Style.BRIGHT + "Setup completed successfully!")
    print(Fore.GREEN + Style.BRIGHT + "-" * 65)


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# System Checks
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def is_connected_to_internet():
    """Check internet connectivity"""
    try:
        requests.get("https://discord.com", timeout=5)
        return True, "-> Internet connection:" + Fore.GREEN + " Active" + Fore.RESET
    except Exception:
        return False, "-> Internet connection:" + Fore.YELLOW + " Degraded/Unavailable" + Fore.RESET


def validate_json_files(directory):
    """Validate all JSON files in directory"""
    if not os.path.exists(directory):
        return True
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                print(Fore.RED + f"Invalid JSON in {filename}: {str(e)}")
                return False
    return True


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Bot Events
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
@bot.event
async def on_ready():
    """Bot startup handler"""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_checks = [
        is_connected_to_internet()[1],
        f"-> Data Storage: {Fore.CYAN + db.backend.upper() + Fore.RESET}",
        f"-> JSON validation: {Fore.GREEN + 'Passed' if validate_json_files('data') and validate_json_files('config') else Fore.RED + 'Failed'}",
        Fore.RESET + "->" + Fore.MAGENTA + f" System time: {now_str}"
    ]
    print(Fore.WHITE + "\n".join(status_checks))
    print(Fore.GREEN + f"Logged in as {bot.user} (ID: {bot.user.id}) | Version: {BOT_VERSION}")
    print(Fore.CYAN + "-" * 45)


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Extension Loader
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def load_extensions(bot_instance, directory='cogs'):
    """Load all bot extensions from directory"""
    loaded_count = 0

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                ext_path = os.path.join(root, file)[:-3].replace(os.sep, '.')
                try:
                    bot_instance.load_extension(ext_path)
                    print(Fore.GREEN + f"✓ " + Fore.WHITE + f" {ext_path}")
                    loaded_count += 1
                except Exception as e:
                    print(Fore.RED + f"✗ {ext_path}: {str(e)}")

    print(Fore.GREEN + f"\nSuccessfully loaded {loaded_count} extensions\n")
    print(Fore.CYAN + "-" * 45)


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Delete Traceback Files
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def delete_traceback_files():
    traceback_directory = './logs/traceback'
    os.makedirs(traceback_directory, exist_ok=True)

    for filename in os.listdir(traceback_directory):
        if filename.startswith('traceback_'):
            try:
                os.remove(os.path.join(traceback_directory, filename))
                LogSystem(f"Deleted traceback file {filename}")
            except Exception as e:
                LogError(f"Error deleting log file {filename}: {e}")


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Main Execution
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def main():
    """Main application entry point"""
    handle_installation()

    if not validate_json_files('data') or not validate_json_files('config'):
        print(Fore.RED + "Critical error: Corrupted JSON configuration files!")
        sys.exit(1)

    clear_screen()
    delete_traceback_files()

    # Startup display
    print(Fore.GREEN + Style.BRIGHT + "\n" + "=" * 45)
    print(Fore.RESET + r"""
    ╔╦╗┌─┐┌─┐┌─┐┬╔═╗┬ ┬┌─┐┌┬┐┌─┐┌┬┐
    ║║║├─┤│ ┬│ ┬│╚═╗└┬┘└─┐ │ ├┤ │││
    ╩ ╩┴ ┴└─┘└─┘┴╚═╝ ┴ └─┘ ┴ └─┘┴ ┴
    """)
    print(Fore.GREEN + "=" * 45 + "\n")

    load_extensions(bot)

    if not TOKEN:
        print(Fore.RED + "Error: TOKEN is missing in .env! Please configure your bot token.")
        sys.exit(1)

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
