import json
import os
import handlers.debug as DebugHandler
from dotenv import load_dotenv

load_dotenv()

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# File Path Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Configs
SERVER_CONFIG_FILE = "config/serverconfig.json"
ADMIN_FEEDBACK_FILE = "config/adminfeedback.json"
LOCKDOWN_CONFIG_FILE = "config/lockdown.json"
VOICEGATE_CONFIG_FILE = "config/voicegateconfig.json"
ONLY_IMAGES_FILE = "config/onlyimages.json"
RANDOM_MATH_FILE = "config/randommathchannel.json"



#Data
MAC_FILE = "data/mac.json"
STATS_FILE = "data/stats.json"
XP_MULTIPLIER_FILE = "data/xpmultiplier.json"
TICKET_DATA_FILE = "data/tickets.json"
COOKIES_FILE = "data/cookies.json"
TAGS_CONFIG_FILE = "data/tags.json"
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
        with open(SERVER_CONFIG_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        DebugHandler.LogError(f"Error in loadserverconfig: {str(e)}")
        return {}

def saveserverconfig(serverconfig):
    try:
        with open(SERVER_CONFIG_FILE, "w") as f:
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
# Admin feedback configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def load_admin_feedback():
    try:
        if not os.path.exists(ADMIN_FEEDBACK_FILE):
            return {}
        with open(ADMIN_FEEDBACK_FILE, "r") as f:
            data = json.load(f)
            if "configs" not in data:
                data["configs"] = {}
            if "feedbacks" not in data:
                data["feedbacks"] = {}
            return data
    except Exception as e:
        DebugHandler.LogError(f"Error in load_admin_feedback: {str(e)}")
        return {}

def save_admin_feedback(data):
    try:
        with open(ADMIN_FEEDBACK_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        DebugHandler.LogError(f"Error in save_admin_feedback: {str(e)}")
        raise


#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# ticket configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def load_ticket_data():
    try:
        if not os.path.exists(TICKET_DATA_FILE):
            return {}
        with open(TICKET_DATA_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        DebugHandler.LogError(f"Error in load_ticket_data: {str(e)}")
        return {}

def save_ticket_data(data):
    try:
        with open(TICKET_DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        DebugHandler.LogError(f"Error in save_ticket_data: {str(e)}")
        raise


#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Lockdown Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def load_lockdown_config():
    try:
        with open(LOCKDOWN_CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        DebugHandler.LogDebug("Lockdown config created")
        with open(LOCKDOWN_CONFIG_FILE, "w") as f:
            json.dump({"lockdown": False}, f)
        return {"lockdown": False}
    except json.JSONDecodeError as e:
        DebugHandler.LogError(f"Corrupted lockdown config: {str(e)}")
        os.remove(LOCKDOWN_CONFIG_FILE)
        with open(LOCKDOWN_CONFIG_FILE, "w") as f:
            json.dump({"lockdown": False}, f)
        return {"lockdown": False}

def save_lockdown_config(lockdown_status):
    try:
        with open(LOCKDOWN_CONFIG_FILE, "w") as f:
            json.dump({"lockdown": lockdown_status}, f)
        DebugHandler.LogSystem(f"Lockdown status updated to {lockdown_status}")
    except Exception as e:
        DebugHandler.LogError(f"Failed to save lockdown config: {str(e)}")
        raise

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Lockdown Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def loadvoicegateconfig():
    try:
        if not os.path.exists(VOICEGATE_CONFIG_FILE):
            return {}
        with open(VOICEGATE_CONFIG_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        DebugHandler.LogError(f"Error in loadvoicegateconfig: {str(e)}")
        return {}

def savevoicegateconfig(config):
    try:
        with open(VOICEGATE_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        DebugHandler.LogError(f"Error in savevoicegateconfig: {str(e)}")
        raise

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# OnlyImages Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def load_onlyimages():
    if not os.path.exists(ONLY_IMAGES_FILE):
        return {}
    try:
        with open(ONLY_IMAGES_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return {channel_id: True for channel_id in data}
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_onlyimages(channels):
    os.makedirs(os.path.dirname(ONLY_IMAGES_FILE), exist_ok=True)
    with open(ONLY_IMAGES_FILE, "w") as f:
        json.dump(channels, f, indent=4)


#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Random Math + Cookies Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def load_randommath_file(filename, default):
    if not os.path.exists(filename):
        return default
    with open(filename, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default

def save_randommath_file(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def load_cookies_file(filename, default):
    if not os.path.exists(filename):
        return default
    with open(filename, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default

def save_cookies_file(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Tags Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def load_tags():
    try:
        with open(TAGS_CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_tags(tags):
    with open(TAGS_CONFIG_FILE, "w") as f:
        json.dump(tags, f, indent=4)

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# MAC Ban System Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def mac_load_bans():
    try:
        if not os.path.exists(MAC_FILE):
            return {}
        with open(MAC_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return {str(ban["id"]): ban for ban in data}
            return {str(k): v for k, v in data.items()}
    except Exception as e:
        DebugHandler.LogError(f"Error in mac_load_bans: {str(e)}")
        return {}

def mac_save_bans(bans):
    try:
        os.makedirs(os.path.dirname(MAC_FILE), exist_ok=True)
        with open(MAC_FILE, "w") as f:
            json.dump(bans, f, indent=4)
    except Exception as e:
        DebugHandler.LogError(f"Error in mac_save_bans: {str(e)}")
        raise