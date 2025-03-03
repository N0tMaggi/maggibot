import json
import os
import handlers.debug as DebugHandler

SERVERCONFIGFILE = "config/serverconfig.json"

def loadserverconfig():
    try:
        with open(SERVERCONFIGFILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        DebugHandler.LogDebug(f"Error loading server config: {e}")
        return {}

def saveserverconfig(serverconfig):
    try:
        with open(SERVERCONFIGFILE, "w") as f:
            json.dump(serverconfig, f, indent=4)
    except IOError as e:
        DebugHandler.LogDebug(f"Error saving the configuration: {e}")
        raise Exception(f"Error saving the configuration: {e}")

def get_log_channel(guild):
    try:
        serverconfig = loadserverconfig()
        return guild.get_channel(serverconfig.get(str(guild.id), {}).get("log_channel"))
    except Exception as e:
        DebugHandler.LogDebug(f"Error getting log channel: {e}")
        return None
