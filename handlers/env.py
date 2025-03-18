import dotenv
import os

from handlers.debug import LogDebug

dotenv.load_dotenv()

def get_owner():
    owner_id = os.getenv('OWNER_ID')
    if not owner_id:
        raise Exception("OWNER_ID not set in environment")
    return int(owner_id)


def get_token():
    token = os.getenv('TOKEN')
    if not token:
        raise Exception("TOKEN not set in environment")
    return int(token)


def get_version():
    version = os.getenv('BOT_VERSION')
    if not version:
        raise Exception("BOT_VERSION not set in environment")
    return version


def get_error_log_channel_id():
    error_log_channel_id = os.getenv('ERROR_LOG_CHANNEL_ID')
    if not error_log_channel_id:
        raise Exception("ERROR_LOG_CHANNEL_ID not set in environment")
    return int(error_log_channel_id)


def get_command_log_channel_id():
    command_log_channel_id = os.getenv('COMMAND_LOG_CHANNEL_ID')
    if not command_log_channel_id:
        raise Exception("COMMAND_LOG_CHANNEL_ID not set in environment")
    return int(command_log_channel_id)


def get_banner(status):
    if not status:
        raise Exception("Status not provided")

    try:
        if status == "SUCCESS":
            banner = os.getenv('SUCCESS_BANNER')
        elif status == "ERROR":
            banner = os.getenv('ERROR_BANNER')
        elif status == "WARNING":
            banner = os.getenv('WARNING_BANNER')
        elif status == "INFO":
            banner = os.getenv('INFO_BANNER')
        else:
            raise Exception(f"Invalid status: {status}")
        
        if not banner:
            raise Exception(f"Banner for status '{status}' not set in environment")
        
        return banner
    except Exception as e:
        raise Exception(f"Error while getting banner: {e}")
    

def get_mac_banner():
    try:
        banner = os.getenv('MAC_NORMAL_BANNER')
        return banner
    except Exception as e:
        raise Exception(f"Error while getting MAC banner: {e}")


def get_tiktok_api_key():
    try: 
        APIKEY = os.getenv('AG7_DEV_API_KEY')
        return APIKEY
    except Exception as e:
        raise Exception(f"Error while getting AG7-DEV API KEY: {e}")

def get_mac_channel():
    try:
        mac_channel = os.getenv('MAC_NOTIFY_CHANNEL_ID')
        return mac_channel
    except Exception as e:
        raise Exception(f"Error while getting MAC channel: {e}")