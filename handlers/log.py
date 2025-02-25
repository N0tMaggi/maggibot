import logging
import os
from debug import LogDebug


logging_dir = 'logs'

def log(message):
    # check if the directory exists
    if not os.path.exists(logging_dir):
        os.makedirs(logging_dir)
    if not os.path.exists(logging_dir + '/log.txt'):
        with open(logging_dir + '/log.txt', 'w') as f:
            f.write('')
    # log the message
    logging.basicConfig(filename=logging_dir + '/log.txt', level=logging.INFO)
    logging.info(message)
    LogDebug(message)

