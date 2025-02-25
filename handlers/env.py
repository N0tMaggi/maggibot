import dotenv
import os

dotenv.load_dotenv()

def get_owner():
    return int(os.getenv('OWNER_ID'))