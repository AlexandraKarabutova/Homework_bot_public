import json
import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from endpoint import ENDPOINT
from exceptions import APIUnexpectedError, APIUnexpectedHTTPStatusError

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(
    stream=sys.stdout
)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

TELEGRAM_RETRY_TIME: int = 600

HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения в тг чат."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logger.info(f'Удачная отправка сообщения в Телеграмм: {message}')
        logger.debug('func send_message: OK')
    except Exception as error:
        logger.error(f'Сбой при отправке сообщения в Телеграмм: {error}')


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        logger.info('Обращение к эндпоинту API-сервиса.')
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except APIUnexpectedError as error:
        logger.error(f'Ошибка при запросе к API: {error}')
        raise APIUnexpectedError(f'Ошибка при запросе к API: {error}')
    if response.status_code != HTTPStatus.OK:
        logger.error(
            f'Ошибка несоответствия статуса ответа: {response.status_code}'
        )
        raise APIUnexpectedHTTPStatusError(
            f'Ошибка несоответствия статуса ответа: {response.status_code}'
        )
    logger.debug('func get_api_answer: OK')
    try:
        return response.json()
    except json.decoder.JSONDecodeError:
        logger.error(f'response не в формате json:{type(response)}')


def check_response(response):
    """Проверка ответа API на корректность."""
    logger.info('Начало проверки ответа сервера')
    logger.debug(f'response: {response}')
    if type(response) != dict:
        logger.error(f'Ответ API не словарь: {type(response)}')
        raise TypeError(f'Ответ API не словарь: {type(response)}')
    try:
        homeworks = response['homeworks']
        logger.debug(f'homeworks:{homeworks}')
    except KeyError:
        logger.error('Нет ключа "homeworks"')
        raise KeyError('Нет ключа "homeworks"')
    if type(homeworks) != list:
        logger.error(f'"homeworks" не список: {type(homeworks)}')
        raise TypeError(f'"homeworks" не список: {type(homeworks)}')
    try:
        homework = homeworks[0]
        logger.debug(f'homework:{homework}')
    except IndexError:
        logger.error('Список домашних работ пуст')
        raise IndexError('Список домашних работ пуст')
    if type(homework) != dict:
        logger.error(f'"homework" не словарь: {type(homework)}')
        raise TypeError(f'"homework" не словарь: {type(homework)}')
    logger.debug('func check_response: OK')
    return homework


def get_current_date(response):
    """Получаем текущую дату."""
    try:
        current_date = response['current_date']
    except KeyError:
        logger.error('Нет ключа "current_date"')
        raise KeyError('Нет ключа "current_date"')
    logger.debug(f'current_date: {current_date}')
    logger.debug('func get_current_date: OK')
    return current_date


def parse_status(homework):
    """Извлечение из информации о домашней работе ее статуса."""
    if 'homework_name' not in homework:
        logger.error(
            'Ошибка при получении ключа "homework_name"'
        )
        raise KeyError('Ошибка при получении ключа "homework_name"')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    try:
        if homework_status in HOMEWORK_VERDICTS.keys():
            verdict = HOMEWORK_VERDICTS[homework_status]
            logger.debug('В ответе отсутствуют неизвестные статусы проверки')
    except Exception as error:
        logger.error(f'Недокументированный статус домашней работы: {error}')
    logger.debug('func parse_status: OK')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Доступность переменных окружения."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        logger.debug('func check_tokens: OK')
        return True
    else:
        logger.critical('Отсутствует переменная окружения.')
        return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    response_homeworks = []
    check_tokens()

    while True:
        try:
            response = get_api_answer(current_timestamp)
            if response['homeworks'] != response_homeworks and response['homeworks'][0] not in response_homeworks:
                homework = check_response(response)
                message = parse_status(homework)
                send_message(bot, message)
                response_homeworks = response['homeworks']
                logger.debug(f'MAIN. response_homeworks:{response_homeworks}')
            else:
                logger.debug('В ответе отсутствуют новые записи')
                logger.debug(f'MAIN. response_homeworks:{response_homeworks}')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message
            )
            logger.info(f'Отправка сообщения в Телеграмм: {message}')

        time.sleep(TELEGRAM_RETRY_TIME)


if __name__ == '__main__':
    main()
