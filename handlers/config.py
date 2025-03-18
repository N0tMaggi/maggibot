import json
import os
import handlers.debug as DebugHandler
from dotenv import load_dotenv

SERVERCONFIGFILE = "config/serverconfig.json"
load_dotenv()
MESSAGE_XP_COUNT = float(os.getenv("MESSAGE_XP_COUNT", 0.1))
ATTACHMENT_XP_COUNT = float(os.getenv("ATTACHMENT_XP_COUNT", 0.3))
VOICE_XP_COUNT = float(os.getenv('VOICE_XP_COUNT', 0.2))

STATS_FILE = "data/stats.json"
XP_MULTIPLIER_FILE = "data/xpmultiplier.json"

def loadserverconfig():
    try:
        with open(SERVERCONFIGFILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        DebugHandler.LogError(f"Error loading server config: {e}")
        return {}

def saveserverconfig(serverconfig):
    try:
        with open(SERVERCONFIGFILE, "w") as f:
            json.dump(serverconfig, f, indent=4)
    except IOError as e:
        DebugHandler.LogError(f"Error saving the configuration: {e}")
        raise Exception(f"Error saving the configuration: {e}")

def get_log_channel(guild):
    try:
        serverconfig = loadserverconfig()
        return guild.get_channel(serverconfig.get(str(guild.id), {}).get("log_channel"))
    except Exception as e:
        DebugHandler.LogError(f"Error getting log channel: {e}")
        return None

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

def load_multiplier_config():
    if not os.path.exists(XP_MULTIPLIER_FILE):
        return {"channels": [], "multipliers": {}}
    try:
        with open(XP_MULTIPLIER_FILE, "r") as f:
            data = json.load(f)
            return {
                "channels": data.get("channels", []),
                "multipliers": data.get("multipliers", {})
            }
    except (json.JSONDecodeError, FileNotFoundError):
        return {"channels": [], "multipliers": {}}

def save_multiplier_config(config):
    with open(XP_MULTIPLIER_FILE, "w") as f:
        json.dump(config, f, indent=4)