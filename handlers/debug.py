import time
import logging
import os

DEBUG = os.getenv('DEBUG_MODE')
logging_dir = 'logs'
log_file = os.path.join(logging_dir, 'log.txt')

if not os.path.exists(logging_dir):
    os.makedirs(logging_dir)

logging.basicConfig(filename=log_file, level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def LogDebug(value):
    if DEBUG == 'TRUE':
        print(value)
        log(value)  
    else:
        log(value)  

def log(message):
    logging.info(message)
