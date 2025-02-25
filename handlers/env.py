import dotenv
import os
from debug import LogDebug

dotenv.load_dotenv()

def get_owner():
    return int(os.getenv('OWNER_ID'))


def get_token():
    return int(os.getenv('TOKEN'))

def get_version():
    return os.getenv('BOT_VERSION')


def get_error_log_channel_id():
    return int(os.getenv('ERROR_LOG_CHANNEL_ID'))

def get_command_log_channel_id():
    return int(os.getenv('COMMAND_LOG_CHANNEL_ID'))

def get_banner(status):
    if status:
        try:
            if status == "SUCCESS":
                return os.getenv('SUCCESS_BANNER')
            elif status == "ERROR":
                return os.getenv('ERROR_BANNER')
            elif status == "WARNING":
                return os.getenv('WARNING_BANNER')
            elif status == "INFO":
                return os.getenv('INFO_BANNER')
            else:
                raise Exception("Invalid status")
        except Exception as e:
            LogDebug(f"Error while getting banner: {e}")
            return None
    else:
        raise Exception("Status not provided")
    