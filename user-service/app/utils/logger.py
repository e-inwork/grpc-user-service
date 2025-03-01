# 2024 amicroservice author.

import logging
import sys


class Logger:
    """
    Custom Logger
    """

    def __init__(self, name: str):
        # Setting up the basic configuration for logging
        logging.basicConfig(
            level=logging.WARNING,  # Set the minimum level to capture (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
            datefmt="%Y-%m-%d %H:%M:%S",  # Date format
            handlers=[
                logging.FileHandler(f"{name}.log"),  # Log to a file
                logging.StreamHandler(sys.stdout),  # Log to the console
            ],
        )

        self.logger = logging.getLogger(f"{name}")

    def debug(self, msg: str):
        self.logger.debug(msg=msg)

    def info(self, msg: str):
        """
        Swicth between INFO and WARNING
        """
        self.logger.setLevel(logging.INFO)
        self.logger.info(msg=msg)
        self.logger.setLevel(logging.WARNING)

    def warning(self, msg: str):
        self.logger.warning(msg=msg)

    def error(self, msg: str):
        self.logger.error(msg=msg)

    def critical(self, msg: str):
        self.logger.critical(msg=msg)
