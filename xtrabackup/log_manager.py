import logging


class LogManager:

    def __init__(self):
        logging.basicConfig(level=logging.INFO)

    def attach_file_handler(self, logger, log_file):
        try:
            handler = logging.FileHandler(log_file)
        except Exception as error:
            print(error)
            raise error
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
