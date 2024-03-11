import asyncio
import json
import logging
import string
import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import random

from jsonref import requests
from telegram import Bot

log_file = 'logfile_PingAndCashChecker.log'
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

token = '6354808644:AAEA9pvVZj6YqvXKCyyyF9ay0q4mdXqXfxE'
chatId = -1001995965101  # мой тестовый чат


# chatId = -1002096660763 # наш основной чат


async def send_telegram_message(message_text):
    try:
        bot = Bot(token=token)
        await bot.send_message(chat_id=chatId, text=message_text)
    except Exception as e:
        print('Сообщение не отправлено', e)



def initial_parser(url):
    articles_json = []
    try:
        s_time = time.time()
        response = requests.get(url)

        if response.status_code == 200:
            start = response.text.find('"articles":') + len('"articles":')
            end = response.text.find(']', start) + 1

            articles_json = response.text[start:end]

        f_time = time.time()
        logging.info(f"initial_parser is done. {(f_time - s_time)} sec: ")
        return articles_json
    except Exception as e:
        print(f'initial_parser Error {e}')
        logging.info(f'initial_parser Error {e}')
        return articles_json


def add_random_params(url, num_params=3, param_length=3):
    s_time = time.time()
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    for _ in range(num_params):
        param_name = ''.join(random.choices(string.ascii_lowercase, k=param_length))
        param_value = ''.join(random.choices(string.digits, k=3))
        query_params[param_name] = param_value

    new_query = urlencode(query_params, doseq=True)
    new_url = urlunparse(
        (parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, new_query, parsed_url.fragment))
    f_time = time.time()
    logging.info(f"add_random_params is done. {(f_time - s_time)} sec: ")
    return new_url


def master_parser(url, previous_articles_json):
    s_time = time.time()
    try:
        s_time = time.time()
        response = requests.get(add_random_params(url), verify=False, headers={'Cache-Control': 'no-cache'},
                                cookies=None)
        # asyncio.run(send_telegram_message(f'Время между отправкой и получением {time.time() - s_time}'))
        print(f'Время между отправкой и получением {time.time() - s_time}')

        logging.info(response)
        print(response)

        if response.status_code == 200:
            # Ищем начало и конец строки, содержащей ключ "articles"
            start = response.text.find('"articles":') + len('"articles":')
            end = response.text.find(']', start) + 1

            # Извлекаем JSON-строку, содержащую "articles"
            articles_json = response.text[start:end]
            # print(articles_json)
            # print(previous_articles_json)
            # print(articles_json!=previous_articles_json)

            if articles_json == previous_articles_json:
                print('    Нет новых записей')
                logging.info('    No updates')
                f_time = time.time()
                logging.info(f"master_parser is done. {(f_time - s_time)} sec: ")
                return previous_articles_json


            if articles_json != previous_articles_json:
                # print('!')
                articles = json.loads(str(articles_json))
                prev_articles = json.loads(previous_articles_json)
                new_articles = [article for article in articles if article not in prev_articles]

                # print('!!')
                # print('LATEST NEWS', new_articles)

                ### Если есть новые записи, парсим их дальше с целью достать оттуда нужные данные ###

                print('Найдено', len(new_articles), 'новых записей!')

                for j in range(len(new_articles)):
                    print('---------------------------------')
                    print('Обработка ', j + 1, '-й новой записи!')
                    print(
                        f"{new_articles[j]['title']} \n время отправки запроса {s_time} \n время выхода новости {new_articles[j]['releaseDate'] / 1000} \n разница {s_time - new_articles[j]['releaseDate'] / 1000} sec")

                    logging.info('---------------------------------')
                    logging.info(f'Обработка {j + 1}-й новой записи!')
                    logging.info(f"{new_articles[j]['title']} \n время отправки запроса {s_time} \n время выхода новости {new_articles[j]['releaseDate'] / 1000} \n разница {s_time - new_articles[j]['releaseDate'] / 1000} sec")
                    logging.info('---------------------------------')

                    asyncio.run(send_telegram_message(f"{new_articles[j]['title']} \n время отправки запроса {s_time} \n время выхода новости {new_articles[j]['releaseDate'] / 1000} \n разница {s_time - new_articles[j]['releaseDate'] / 1000} sec"))

                previous_articles_json = articles_json

                f_time = time.time()
                logging.info(f"master_parser is done. {(f_time - s_time)} sec: ")
                return previous_articles_json


        else:
            print("Не удалось получить доступ к странице. Пауза 10 сек. Код состояния:", response.status_code)
            time.sleep(10)
            return previous_articles_json
    except Exception as e:
        print('ERROR, ', e)
        asyncio.run(send_telegram_message(f'Error master_parser all news {e}'))
        logging.info(f"master_parser ERROR: {e}")
        return previous_articles_json



def main():
    try:
        logging.info("-----Парсер всех новостей бинанса запущен-----")
        asyncio.run(send_telegram_message("-----Парсер всех новостей бинанса запущен-----"))

        #
        url1 = 'https://www.binance.com/en/support/announcement/c-49?navId=49'
        pa_1 = initial_parser(url1)
        asyncio.run(send_telegram_message(f"from url1: {pa_1}"))


        #
        url2 = 'https://www.binance.com/en/support/announcement/latest-activities?c=93&navId=93'
        pa_2 = initial_parser(url2)
        asyncio.run(send_telegram_message(f"from url2: {pa_2}"))

        i = 0
        while True:
            i += 1
            print(f'--{i}--')
            # if i == 1:
            #     print('Первый запуск')
            #     pa_1 = master_parser(url1, '[]')
            #     pa_2 = master_parser(url2, '[]')
            #     time.sleep(5)

            s_time = time.time()
            pa_1 = master_parser(url1, pa_1)
            f_time = time.time()
            if i < 5:
                asyncio.run(send_telegram_message(f"Время выполнения: {f_time - s_time}"))

            pa_2 = master_parser(url2, pa_2)


            time.sleep(5)
    except KeyboardInterrupt:
        asyncio.run(send_telegram_message("Парсер всех новостей остановлен вручную"))

import warnings
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

if __name__ == "__main__":
    main()
