import dotenv
import os
from handlers.debug import LogDebug

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Initialization
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
dotenv.load_dotenv()

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Core Bot Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def get_owner():
    try:
        owner_id = os.getenv('OWNER_ID')
        if not owner_id:
            raise ValueError("OWNER_ID not set in environment")
        return int(owner_id)
    except Exception as e:
        LogDebug(f"get_owner error: {str(e)}")
        raise

def get_token():
    try:
        token = os.getenv('TOKEN')
        if not token:
            raise ValueError("TOKEN not set in environment")
        return int(token)
    except Exception as e:
        LogDebug(f"get_token error: {str(e)}")
        raise

def get_version():
    try:
        version = os.getenv('BOT_VERSION')
        if not version:
            raise ValueError("BOT_VERSION not set in environment")
        return version
    except Exception as e:
        LogDebug(f"get_version error: {str(e)}")
        raise

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Logging Channels
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def get_error_log_channel_id():
    try:
        channel_id = os.getenv('ERROR_LOG_CHANNEL_ID')
        if not channel_id:
            raise ValueError("ERROR_LOG_CHANNEL_ID not set in environment")
        return int(channel_id)
    except Exception as e:
        LogDebug(f"get_error_log_channel_id error: {str(e)}")
        raise

def get_command_log_channel_id():
    try:
        channel_id = os.getenv('COMMAND_LOG_CHANNEL_ID')
        if not channel_id:
            raise ValueError("COMMAND_LOG_CHANNEL_ID not set in environment")
        return int(channel_id)
    except Exception as e:
        LogDebug(f"get_command_log_channel_id error: {str(e)}")
        raise

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Banner Configuration
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def get_banner(status):
    try:
        if not status:
            raise ValueError("Status not provided")
        
        banner_map = {
            "SUCCESS": os.getenv('SUCCESS_BANNER'),
            "ERROR": os.getenv('ERROR_BANNER'),
            "WARNING": os.getenv('WARNING_BANNER'),
            "INFO": os.getenv('INFO_BANNER')
        }
        
        if status not in banner_map:
            raise ValueError(f"Invalid status: {status}")
            
        banner = banner_map[status]
        if not banner:
            raise ValueError(f"Banner for status '{status}' not set")
            
        return banner
    except Exception as e:
        LogDebug(f"get_banner error: {str(e)}")
        raise

def get_mac_banner():
    try:
        return os.getenv('MAC_NORMAL_BANNER')
    except Exception as e:
        LogDebug(f"get_mac_banner error: {str(e)}")
        raise

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# API & External Services
#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
def get_tiktok_api_key():
    try:
        return os.getenv('AG7_DEV_API_KEY')
    except Exception as e:
        LogDebug(f"get_tiktok_api_key error: {str(e)}")
        raise

def get_mac_channel():
    try:
        return os.getenv('MAC_NOTIFY_CHANNEL_ID')
    except Exception as e:
        LogDebug(f"get_mac_channel error: {str(e)}")
        raise

def get_pangea_api():
    try:
        return os.getenv('PANGEA_API_KEY')
    except Exception as e:
        LogDebug(f"get_pangea_api error: {str(e)}")
        raise

def get_pangea_domain():
    try:
        return os.getenv('PANGEA_DOMAIN')
    except Exception as e:
        LogDebug(f"get_pangea_api error: {str(e)}")
        raise