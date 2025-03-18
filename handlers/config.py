import json
import os
import handlers.debug as DebugHandler
from dotenv import load_dotenv

load_dotenv()

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# File Path Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
SERVERCONFIGFILE = "config/serverconfig.json"
MACFILE = "data/mac.json"
STATS_FILE = "data/stats.json"
XP_MULTIPLIER_FILE = "data/xpmultiplier.json"

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# XP System Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
MESSAGE_XP_COUNT = float(os.getenv("MESSAGE_XP_COUNT", 0.1))
ATTACHMENT_XP_COUNT = float(os.getenv("ATTACHMENT_XP_COUNT", 0.3))
VOICE_XP_COUNT = float(os.getenv('VOICE_XP_COUNT', 0.2))

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Server Configuration Handlers
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def loadserverconfig():
    try:
        with open(SERVERCONFIGFILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        DebugHandler.LogError(f"Error in loadserverconfig: {str(e)}")
        return {}

def saveserverconfig(serverconfig):
    try:
        with open(SERVERCONFIGFILE, "w") as f:
            json.dump(serverconfig, f, indent=4)
    except Exception as e:
        DebugHandler.LogError(f"Error in saveserverconfig: {str(e)}")
        raise

def get_log_channel(guild):
    try:
        serverconfig = loadserverconfig()
        return guild.get_channel(serverconfig.get(str(guild.id), {}).get("log_channel"))
    except Exception as e:
        DebugHandler.LogError(f"Error in get_log_channel: {str(e)}")
        return None

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Statistics Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def load_stats():
    try:
        if not os.path.exists(STATS_FILE):
            return {}
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        DebugHandler.LogError(f"Error in load_stats: {str(e)}")
        return {}

def save_stats(stats):
    try:
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f, indent=4)
    except Exception as e:
        DebugHandler.LogError(f"Error in save_stats: {str(e)}")
        raise

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# XP Multiplier Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def load_multiplier_config():
    try:
        if not os.path.exists(XP_MULTIPLIER_FILE):
            return {"channels": [], "multipliers": {}}
        with open(XP_MULTIPLIER_FILE, "r") as f:
            data = json.load(f)
            return {
                "channels": data.get("channels", []),
                "multipliers": data.get("multipliers", {})
            }
    except Exception as e:
        DebugHandler.LogError(f"Error in load_multiplier_config: {str(e)}")
        return {"channels": [], "multipliers": {}}

def save_multiplier_config(config):
    try:
        with open(XP_MULTIPLIER_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        DebugHandler.LogError(f"Error in save_multiplier_config: {str(e)}")
        raise

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# MAC Ban System Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def mac_load_bans():
    try:
        if not os.path.exists(MACFILE):
            return {}
        with open(MACFILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return {str(ban["id"]): ban for ban in data}
            return {str(k): v for k, v in data.items()}
    except Exception as e:
        DebugHandler.LogError(f"Error in mac_load_bans: {str(e)}")
        return {}

def mac_save_bans(bans):
    try:
        os.makedirs(os.path.dirname(MACFILE), exist_ok=True)
        with open(MACFILE, "w") as f:
            json.dump(bans, f, indent=4)
    except Exception as e:
        DebugHandler.LogError(f"Error in mac_save_bans: {str(e)}")
        raise