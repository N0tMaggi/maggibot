import json
import os
from handlers.debug import LogError
from dotenv import load_dotenv

load_dotenv()

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Generic File Handlers
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def load_data(filename, default=None, transform_fn=None):
    """Generic function to load data from JSON files"""
    try:
        if not os.path.exists(filename):
            return default() if callable(default) else default
            
        with open(filename, "r") as f:
            data = json.load(f)
            return transform_fn(data) if transform_fn else data
            
    except (FileNotFoundError, json.JSONDecodeError) as e:
        LogError(f"Error loading {filename}: {str(e)}")
        return default() if callable(default) else default

def save_data(filename, data, mkdir=False):
    """Generic function to save data to JSON files"""
    try:
        if mkdir:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        return True
        
    except Exception as e:
        LogError(f"Error saving {filename}: {str(e)}")
        raise

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

# Data
MAC_FILE = "data/mac.json"
MAC_BYPASS_FILE = "data/mac_bypass.json"
STATS_FILE = "data/stats.json"
XP_MULTIPLIER_FILE = "data/xpmultiplier.json"
TICKET_DATA_FILE = "data/tickets.json"
COOKIES_FILE = "data/cookies.json"
TAGS_CONFIG_FILE = "data/tags.json"

# Categorised File List
JSON_FILES = [
    SERVER_CONFIG_FILE,
    ADMIN_FEEDBACK_FILE,
    LOCKDOWN_CONFIG_FILE,
    VOICEGATE_CONFIG_FILE,
    ONLY_IMAGES_FILE,
    RANDOM_MATH_FILE,
    MAC_FILE,
    MAC_BYPASS_FILE,
    STATS_FILE,
    XP_MULTIPLIER_FILE,
    TICKET_DATA_FILE,
    COOKIES_FILE,
    TAGS_CONFIG_FILE
]

CONFIG_FILES = [
    SERVER_CONFIG_FILE,
    ADMIN_FEEDBACK_FILE,
    LOCKDOWN_CONFIG_FILE,
    VOICEGATE_CONFIG_FILE,
    ONLY_IMAGES_FILE,
    RANDOM_MATH_FILE
]

DATA_FILES = [
    MAC_FILE,
    MAC_BYPASS_FILE,
    STATS_FILE,
    XP_MULTIPLIER_FILE,
    TICKET_DATA_FILE,
    COOKIES_FILE,
    TAGS_CONFIG_FILE
]

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# File Categorization Functions
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def get_json_files():
    """Return all JSON files used by the system"""
    return JSON_FILES

def get_config_files():
    """Return all configuration files"""
    return CONFIG_FILES

def get_data_files():
    """Return all data storage files"""
    return DATA_FILES

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
    return load_data(SERVER_CONFIG_FILE, default=dict)

def saveserverconfig(serverconfig):
    save_data(SERVER_CONFIG_FILE, serverconfig)

def get_log_channel(guild):
    serverconfig = loadserverconfig()
    return guild.get_channel(serverconfig.get(str(guild.id), {}).get("log_channel"))

def get_logging_forum(guild):
    serverconfig = loadserverconfig()
    forum_id = serverconfig.get(str(guild.id), {}).get("logging_forum")
    return guild.get_channel(forum_id)

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Statistics Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def load_stats():
    return load_data(STATS_FILE, default=dict)

def save_stats(stats):
    save_data(STATS_FILE, stats)

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# XP Multiplier Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def load_multiplier_config():
    default = {"channels": [], "multipliers": {}}
    loaded = load_data(XP_MULTIPLIER_FILE, default=default)
    for key in default:
        if key not in loaded:
            loaded[key] = default[key]
    return loaded

def save_multiplier_config(config):
    save_data(XP_MULTIPLIER_FILE, config)

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Admin feedback configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def load_admin_feedback():
    default = {"configs": {}, "feedbacks": {}}
    return load_data(ADMIN_FEEDBACK_FILE, default=default)

def save_admin_feedback(data):
    save_data(ADMIN_FEEDBACK_FILE, data)

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Ticket configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def load_ticket_data():
    return load_data(TICKET_DATA_FILE, default=dict)

def save_ticket_data(data):
    save_data(TICKET_DATA_FILE, data)

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Lockdown Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def load_lockdown_config():
    data = load_data(LOCKDOWN_CONFIG_FILE, default={"lockdown": False})
    if not isinstance(data, dict) or "lockdown" not in data:
        data = {"lockdown": False}
        save_data(LOCKDOWN_CONFIG_FILE, data)
    return data

def save_lockdown_config(lockdown_status):
    save_data(LOCKDOWN_CONFIG_FILE, {"lockdown": lockdown_status})

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Voicegate Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def loadvoicegateconfig():
    return load_data(VOICEGATE_CONFIG_FILE, default=dict)

def savevoicegateconfig(config):
    save_data(VOICEGATE_CONFIG_FILE, config)

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# OnlyImages Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def load_onlyimages():
    def transform(data):
        return {channel_id: True for channel_id in data} if isinstance(data, list) else data
    return load_data(ONLY_IMAGES_FILE, default=dict, transform_fn=transform)

def save_onlyimages(channels):
    save_data(ONLY_IMAGES_FILE, channels, mkdir=True)

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Random Math + Cookies Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def load_randommath():
    return load_data(RANDOM_MATH_FILE, default=dict)

def save_randommath(data):
    save_data(RANDOM_MATH_FILE, data)

def load_cookies():
    return load_data(COOKIES_FILE, default=dict)

def save_cookies(data):
    save_data(COOKIES_FILE, data)

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Tags Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def load_tags():
    return load_data(TAGS_CONFIG_FILE, default=dict)

def save_tags(tags):
    save_data(TAGS_CONFIG_FILE, tags)

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# MAC Ban System Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
from handlers.database import get_db_connection, DB_TYPE

def mac_load_bans():
    if DB_TYPE == "json":
        data = load_data(MAC_FILE, default=dict)
        if isinstance(data, list):
            bans = {str(ban["id"]): ban for ban in data}
        else:
            bans = {str(k): v for k, v in data.items()}

        for user_id, ban in bans.items():
            if "id" not in ban:
                try:
                    ban["id"] = int(user_id)
                except ValueError:
                    ban["id"] = user_id
        return bans
    else:
        conn = get_db_connection()
        if not conn:
            return {}
        cursor = conn.cursor(dictionary=True if DB_TYPE == 'mysql' else False)
        cursor.execute("SELECT * FROM mac_bans")
        rows = cursor.fetchall()
        conn.close()

        bans = {}
        if DB_TYPE == 'sqlite':
            # For sqlite, rows are tuples, convert them to dicts
            column_names = [description[0] for description in cursor.description]
            for row in rows:
                ban_data = dict(zip(column_names, row))
                bans[str(ban_data['id'])] = ban_data
        else: # mysql
            for row in rows:
                bans[str(row['id'])] = row
        return bans


def mac_save_bans(bans):
    if DB_TYPE == "json":
        save_data(MAC_FILE, bans, mkdir=True)
    else:
        conn = get_db_connection()
        if not conn:
            return
        cursor = conn.cursor()
        
        # Inefficient for databases, but matches the current logic.
        # A better implementation would be specific add/update/delete functions.
        cursor.execute("DELETE FROM mac_bans")

        for ban in bans.values():
            if DB_TYPE == 'mysql':
                sql = "INSERT INTO mac_bans (id, name, bandate, reason, serverid, servername, bannedby) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            elif DB_TYPE == 'sqlite':
                sql = "INSERT INTO mac_bans (id, name, bandate, reason, serverid, servername, bannedby) VALUES (?, ?, ?, ?, ?, ?, ?)"
            
            values = (ban.get('id'), ban.get('name'), ban.get('bandate'), ban.get('reason'), ban.get('serverid'), ban.get('servername'), ban.get('bannedby'))
            cursor.execute(sql, values)

        conn.commit()
        conn.close()


def mac_load_bypasses():
    if DB_TYPE == "json":
        data = load_data(MAC_BYPASS_FILE, default=dict)
        return {str(k): v for k, v in data.items()}
    else:
        conn = get_db_connection()
        if not conn:
            return {}
        cursor = conn.cursor(dictionary=True if DB_TYPE == 'mysql' else False)
        cursor.execute("SELECT user_id, server_id FROM mac_bypass")
        rows = cursor.fetchall()
        conn.close()

        bypasses = {}
        if DB_TYPE == 'sqlite':
            for row in rows:
                user_id, server_id = row
                bypasses.setdefault(str(user_id), []).append(server_id)
        else:  # mysql
            for row in rows:
                user_id = str(row['user_id'])
                bypasses.setdefault(user_id, []).append(row['server_id'])
        return bypasses


def mac_save_bypasses(bypasses):
    if DB_TYPE == "json":
        save_data(MAC_BYPASS_FILE, bypasses, mkdir=True)
    else:
        conn = get_db_connection()
        if not conn:
            return
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mac_bypass")

        for user_id, servers in bypasses.items():
            for server_id in servers:
                if DB_TYPE == 'mysql':
                    sql = "INSERT INTO mac_bypass (user_id, server_id) VALUES (%s, %s)"
                elif DB_TYPE == 'sqlite':
                    sql = "INSERT INTO mac_bypass (user_id, server_id) VALUES (?, ?)"
                cursor.execute(sql, (int(user_id), server_id))

        conn.commit()
        conn.close()


