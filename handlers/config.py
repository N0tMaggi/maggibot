import json 
import os

SERVERCONFIGFILE = "config/serverconfig.json"

def loadserverconfig():
    try:
        with open(SERVERCONFIGFILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(SERVERCONFIGFILE, "w") as f:
            json.dump({}, f)
            return {}
    except json.JSONDecodeError:
        return {}

# save serverconfig with error handling
def saveserverconfig(serverconfig):
    with open(SERVERCONFIGFILE, "w") as f:
        json.dump(serverconfig, f, indent=4)