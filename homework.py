import os
import sys
import requests
from http import HTTPStatus
import time
import telegram
import logging

# Без этого импорта не проходят тесты,
# поэтому в первой версии убрала вызов хэндлера из файла app_logger
from dotenv import load_dotenv
import app_logger
from exceptions import SendExceptionError, NotSendExceptionError


load_dotenv()


PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}

# Не проходят автотесты, если именно в этом файле нет вызова метода getLogger
# :(


def get_logger(name):
    """Настройка логирования."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(app_logger.get_stream_handler())
    logger.addHandler(app_logger.get_file_handler())
    return logger


logger = get_logger(__name__)


def check_tokens():
    """Проверка наличия всех необходимых токенов."""
    token_list = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return all(token_list)


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
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
        if homework_statuses.status_code == HTTPStatus.OK:
            return homework_statuses.json()
        elif homework_statuses.status_code == HTTPStatus.BAD_REQUEST:
            raise SendExceptionError(
                f'{homework_statuses.json()["error"]}'
            )
        elif homework_statuses.status_code == HTTPStatus.UNAUTHORIZED:
            raise SendExceptionError(
                f'{homework_statuses.json()["message"]}'
            )
        else:
            raise SendExceptionError(
                'неизвестный код ошибки'
            )
    except Exception as error:
        raise SendExceptionError(error)


# Автотесты проверяют, что функция обязательно выбрасывает TypeErro
# Из-за этого не получается все ошибки поделить на отправляемы в ТГ
# и не отправляемые
def check_response(response):
    """Проверка корректности ответа."""
    try:
        if isinstance(response, dict) is False:
            raise TypeError(
                'Некорректный тип данных homeworks'
            ) from None
        elif isinstance(response["homeworks"], list) is False:
            raise TypeError(
                'Некорректный тип данных homeworks'
            ) from None
        elif isinstance(response["homeworks"][0], dict) is False:
            raise TypeError(
                'Некорректный тип данных homeworks[0]'
            )
        elif response['homeworks'] == []:
            return "", ""
        else:
            return response['homeworks'][0], response['homeworks'][0]['status']
    except TypeError as error:
        raise TypeError(error) from None
    except Exception as error:
        raise SendExceptionError(error)


def parse_status(homework):
    """Получение параметров статуса и названия дз."""
    try:
        homework_name = homework['homework_name']
        status = homework['status']
        if status not in HOMEWORK_VERDICTS:
            raise SendExceptionError(f'{status} не найден')
        if status is None:
            raise SendExceptionError(f'{status} не найден')
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception as error:
        raise SendExceptionError(error) from None


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_status = ""
    error_message = ""
    while True:
        if check_tokens() is False:
            logger.critical('Не все токены заданы')
            sys.exit(1)
        try:
            response = get_api_answer(timestamp)
            check, status = check_response(response)
            if status != previous_status:
                message = parse_status(check)
                send_message(bot, message)
                previous_status = status
            else:
                logger.debug(
                    f'Статус c {status} не изменился'
                )
        except SendExceptionError as error:
            message = f'Сбой в работе программы 2: {error}'
            if error_message != message:
                # send_message(bot, message)
                error_message = message
            logger.error(message)
        except TypeError as error:
            message = f'Сбой в работе программы 1: {error}'
            if error_message != message:
                # send_message(bot, message)
                error_message = message
            logger.error(message)
        except NotSendExceptionError as debug:
            logger.debug(debug)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
