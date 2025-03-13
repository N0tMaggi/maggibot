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
    'debug': os.path.join(logging_dir, 'debug.log'),
    'error': os.path.join(logging_dir, 'error.log')
}

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

loggers = {}
for category, file in log_files.items():
    logger = logging.getLogger(category)
    logger.setLevel(logging.INFO)
    
    handler = logging.FileHandler(file, encoding='utf-8')
    
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    loggers[category] = logger

def LogSystem(message):
    loggers['system'].info(message)

def LogDebug(value):
    if DEBUG == 'TRUE':
        print(value)
    loggers['debug'].info(value)

def LogNetwork(message):
    loggers['network'].info(message)

def LogDiscord(message):
    loggers['discord'].info(message)

def LogError(message):
    loggers['error'].error(message)  