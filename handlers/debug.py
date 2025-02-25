import time
import logging
import os

DEBUG = os.getenv('DEBUG_MODE')


def LogDebug(value):
    if DEBUG == 'TRUE':
        print(value)
    else:
        pass