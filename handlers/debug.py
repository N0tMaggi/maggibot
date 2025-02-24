import time
import logging
import os

DEBUG = os.getenv('DEBUG_MODE')


def debuglog(debuglog):
    if DEBUG == 'TRUE':
        logging.debug(debuglog)
    else:
        pass