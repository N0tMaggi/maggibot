import logging
import os

def shutdown():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(os.path.join(os.path.dirname(__file__), 'crash.log'))
    fh.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    if not fh.handlers:
        logger.addHandler(fh)
        if not ch.handlers:
            logger.addHandler(ch)
    logger.info('Shutting down...')
    os._exit(1)