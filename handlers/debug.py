import time
import logging
import os
from log import log

DEBUG = os.getenv('DEBUG_MODE')


def LogDebug(value):
    try:
        if DEBUG == 'TRUE':
            print(value)
            log.log(value)
        else:
            log.log(value)
    except Exception as e:
        raise "Error in LogDebug: " + str(e)
    

