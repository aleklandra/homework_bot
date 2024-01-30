import logging

_log_format = ('%(asctime)s - [%(levelname)s] - %(name)s - '
               '(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s')


def get_file_handler():
    """Настройка хэндлера для файлов."""
    file_handler = logging.FileHandler("my_logger.log")
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter(_log_format))
    return file_handler


def get_stream_handler():
    """Настройка хэндлера."""
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter(_log_format))
    return stream_handler


# def get_logger(name):
    """Настройка логирования."""
    # logger = logging.getLogger(name)
    # logger.setLevel(logging.DEBUG)
    # logger.addHandler(get_stream_handler())
    # logger.addHandler(get_file_handler())
    # return logger
