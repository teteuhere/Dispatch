import logging
from logging.handlers import RotatingFileHandler
import sys
import os

def setup_logger(name="Operações"):
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = RotatingFileHandler('logs/mission_log.log', maxBytes=5*1024*1024, backupCount=2)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
