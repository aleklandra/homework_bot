import os
import requests
import time
import telegram
import io
import sys
import logging

from exceptions import ExceptionError, DebugException
from dotenv import load_dotenv

_log_format = ('%(asctime)s - [%(levelname)s] - %(name)s - '
               '(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s')

load_dotenv()
s = io.StringIO()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def get_stream_handler():
    """Настройка хэндлера."""
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter(_log_format))
    return stream_handler


def get_logger(name):
    """Настройка логирования."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_stream_handler())
    return logger


logger = get_logger(__name__)


def check_tokens():
    """Проверка наличия всех необходимых токенов."""
    for key in [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]:
        if key is None:
            logger.critical(f'Переменная {key} не задана')
            sys.exit()


def send_message(bot, message):
    """Отправка сообщения в чат-бот."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Сообщение отправлено в чат: {message}')
    except telegram.error.TelegramError:
        logger.error('Ошибка отправка сообщения в телеграмм')


def get_api_answer(timestamp):
    """Запрос данных дз."""
    try:
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS,
                                         params={'from_date': timestamp})
        if homework_statuses.status_code == 200:
            return homework_statuses.json()
        elif homework_statuses.status_code == 400:
            raise ExceptionError(f'{get_api_answer.__name__}: '
                                 f'{homework_statuses.json()["error"]}')
        elif homework_statuses.status_code == 401:
            raise ExceptionError(f'{get_api_answer.__name__}: '
                                 f'{homework_statuses.json()["message"]}')
        else:
            raise ExceptionError(f'{get_api_answer.__name__}: неизвестный '
                                 'код ошибки')
    except Exception as error:
        raise ExceptionError(f'{get_api_answer.__name__}: {error}') from None


def check_response(response):
    """Проверка корректности ответа."""
    try:
        if isinstance(response, dict) is False:
            raise TypeError(f'{check_response.__name__}'
                            f':Некорректный тип данных homeworks') from None
        elif isinstance(response['homeworks'], list) is False:
            raise TypeError(f'{check_response.__name__}'
                            f':Некорректный тип данных homeworks') from None
        elif isinstance(response['homeworks'][0], dict) is False:
            raise TypeError(f'{check_response.__name__}'
                            f':Некорректный тип данных homeworks[0]')
        elif response['homeworks'] == []:
            return '', ''
        else:
            return response['homeworks'][0], response['homeworks'][0]['status']
    except TypeError as error:
        raise TypeError(error)
    except Exception as error:
        raise ExceptionError(f'{check_response.__name__}: {error}') from None


def parse_status(homework):
    """Получение параметров статуса и названия дз."""
    try:
        homework_name = homework['homework_name']
        print()
        status = homework['status']
        if status not in HOMEWORK_VERDICTS:
            raise ExceptionError(f'{parse_status.__name__}: {status} '
                                 'не найден')
        if status is None:
            raise ExceptionError(f'{parse_status.__name__}: {status} '
                                 'не найден')
        verdict = HOMEWORK_VERDICTS[status]
        return ('Изменился статус проверки работы '
                f'"{homework_name}". {verdict}')
    except Exception as error:
        raise ExceptionError(f'{parse_status.__name__}: {error}') from None


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_status = ''
    error_message = ''

    while True:
        try:
            check_tokens()
            response = get_api_answer(timestamp)
            check, status = check_response(response)
            if check == '':
                raise DebugException('Данные по домашке отсутствуют')
            if status != previous_status:
                message = parse_status(check)
                send_message(bot, message)
                previous_status = status
            else:
                logger.debug(f'Статус c {status} не изменился,'
                             'сообщение не отправлено')
        except ExceptionError as error:
            message = f'Сбой в работе программы 2: {error}'
            if error_message != message:
                send_message(bot, message)
                error_message = message
            logger.error(message)
        except TypeError as error:
            message = f'Сбой в работе программы 1: {error}'
            if error_message != message:
                send_message(bot, message)
                error_message = message
            logger.error(message)
        except DebugException as debug:
            logger.debug(debug)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
