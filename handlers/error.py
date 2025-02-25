# universal erro handler for all errors

import logging
import sys
import traceback
import functools
import json


def handle_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(traceback.format_exc())
            return json.dumps({'error': str(e)}), 500

def handle_critical_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(traceback.format_exc())
            return json.dumps({'error': str(e)}), 500
    return wrapper

def handle_unhandled_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(traceback.format_exc())
            sys.exit(1)