import logging


class LogManager:

    def __init__(self):
        logging.basicConfig(level=logging.INFO)

    def attach_file_handler(self, logger, log_file):
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
