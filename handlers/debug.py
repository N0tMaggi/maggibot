import os
import logging

DEBUG = os.getenv('DEBUG_MODE')
logging_dir = 'logs'

if not os.path.exists(logging_dir):
    os.makedirs(logging_dir)

log_files = {
    'system': os.path.join(logging_dir, 'system.log'),
    'network': os.path.join(logging_dir, 'network.log'),
    'discord': os.path.join(logging_dir, 'discord.log'),
    'debug': os.path.join(logging_dir, 'debug.log')
}

for file in log_files.values():
    if not os.path.exists(file):
        with open(file, 'w') as f:
            pass

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

loggers = {}
for category, file in log_files.items():
    logger = logging.getLogger(category)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(file)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    loggers[category] = logger

def log(message):
    loggers['system'].info(message)

def LogDebug(value):
    if DEBUG == 'TRUE':
        print(value)
    loggers['debug'].info(value)

def log_network(message):
    loggers['network'].info(message)

def log_discord(message):
    loggers['discord'].info(message)
