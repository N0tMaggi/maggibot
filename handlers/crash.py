import logging
import os
import sys
import traceback

def shutdown(exception=None):
    # Set up logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Log file and stream handler
    log_file = os.path.join(os.path.dirname(__file__), 'crash.log')
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    
    # Set log format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    # Log shutdown
    if exception:
        logger.error('Shutting down due to an error: %s', exception)
        logger.error('Traceback: %s', traceback.format_exc())
    else:
        logger.info('Shutting down...')
    
    # Exit
    sys.exit(1)
