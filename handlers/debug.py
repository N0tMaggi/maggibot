import time
import logging
import os

DEBUG = os.getenv('DEBUG_MODE')


def LogDebug(value):
    if DEBUG == 'TRUE':
        logging.debug(value)
    else:
        pass