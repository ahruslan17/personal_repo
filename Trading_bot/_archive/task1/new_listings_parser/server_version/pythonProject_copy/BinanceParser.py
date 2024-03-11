import requests
import json
import time
from datetime import datetime
import re
from gate_api import SpotApi, ApiClient, FuturesApi, FuturesOrder, FuturesTrade, Order
from bs4 import BeautifulSoup
import logging
import numpy as np
from IsTickerOnExchange import check_token
from Notifications import send_telegram_message, send_telegram_message_debug
import asyncio
from TradingTask_Bybit import SpotEnterOrder, FuturesEnterOrder, PositionInfo
from TradingTask_OKX import SpotEnterOrder_okx, FuturesEnterOrder_okx
from pybit.unified_trading import HTTP
from TradingTask_Gateio import placeSpotOrder_gateio, placeFuturesOrder_gateio
import gate_api
import random
import string
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import sys
import atexit

log_file = 'logfile.log'
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

prev = '[{"id":181463,"code":"5d8c7476197344d087b5af436bfc74ae","title":"Binance Futures Will Launch USDⓈ-M SLP Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698731158402},{"id":181434,"code":"4492f05f8b0e40f2a6dc9321aba0ba27","title":"Binance Will List Celestia (TIA) with Seed Tag Applied","type":1,"releaseDate":1698671932206},{"id":181387,"code":"8e7a24082b4f4ab39229b05cadbfce0a","title":"Binance Adds ACA, GHST, VIDT and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1698638428354},{"id":181301,"code":"90ccca2c5d6946ef9439dae41a517578","title":"Introducing Memecoin (MEME) on Binance Launchpool! Farm MEME by Staking BNB, TUSD and FDUSD","type":1,"releaseDate":1698415749172},{"id":181213,"code":"c40a1707de63466f9aa14fd046c75e81","title":"Binance Futures Will Launch USDⓈ-M POWR Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698321002985},{"id":180971,"code":"6cdb1faca0e44c188ab680494c3bfa11","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-26","type":1,"releaseDate":1698204603826},{"id":180905,"code":"d8b596b131b64130940798961d73a8b5","title":"Binance Futures Will Launch USDⓈ-M POLYX and GAS Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1698151948683},{"id":180616,"code":"cdeaa008a1484ba0974f4359a31d29c3","title":"Binance Futures Will Launch USDⓈ-M RIF Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697862003215},{"id":180345,"code":"21802d4be7ce4e4a880e2990a6775422","title":"Binance Futures Will Launch USDⓈ-M BSV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697771703998},{"id":180281,"code":"afd04e47bab84bdab855f7698bf40fb5","title":"Binance Adds ARK, OMG \u0026 More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1697688013854},{"id":180188,"code":"b68013d4a1b14c82bb019eabcc13391a","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-19","type":1,"releaseDate":1697612405894},{"id":180152,"code":"5d2d3a74fe6c4c89ac8eaac2959383d6","title":"Binance Futures Will Launch USDⓈ-M STPT and WAXP Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1697606833266},{"id":180014,"code":"93710257326b4f33aed7d8b7b73746d1","title":"Binance Futures Will Launch USDⓈ-M ORBS Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697506436276},{"id":179943,"code":"175604613129423199f61fda5ffe3615","title":"Binance Futures Will Launch USDⓈ-M BOND Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697345978273},{"id":179775,"code":"b4eb91b68a1a4dc1b2a2f45d7b8f1a1e","title":"Binance Adds NTRN on Margin","type":1,"releaseDate":1697173875790},{"id":179699,"code":"d956c31e085444c2ba4d97c554318476","title":"Binance Futures Will Launch USDⓈ-M BIGTIME Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697109442199},{"id":179392,"code":"59cba52c3bab4059897ae88d9bbb31cf","title":"Binance Futures Will Launch USDⓈ-M LOOM Perpetual Contract With Up to 10x Leverage","type":1,"releaseDate":1696997177546},{"id":179364,"code":"9ef0c43e0c06499a8cca5081883825c8","title":"Binance Adds ADA/FDUSD, FIL/FDUSD, FRONT/TUSD, LEVER/TRY, LTC/FDUSD, RUNE/TUSD \u0026 TRB/TRY Trading Pairs","type":1,"releaseDate":1696993228097},{"id":179344,"code":"01c84ac73fb442bdbeb2463ade2347f6","title":"Binance Adds New SEI \u0026 WBETH Pairs on Cross Margin","type":1,"releaseDate":1696990532517},{"id":179161,"code":"b64ac7bcfca54d2b8042c7aa0cfc5afe","title":"Binance Futures Will Launch USDⓈ-M STRAX Perpetual Contract With Up to 10x Leverage","type":1,"releaseDate":1696936465219}]'
leverage = 2
position_margin = 5


def convert_title_into_link(text, code):
    s_time = time.time()
    lower_case_text = text.lower()
    hyphenated_text = lower_case_text.replace(' ', '-')
    f_time = time.time()
    logging.info(f"convert_title_into_link is done. {(f_time - s_time)} sec: ")
    return 'https://www.binance.com/en/support/announcement/' + hyphenated_text + '-' + code


def parse_announcement_table(url):
    try:
        s_time = time.time()
        response = requests.get(url, verify=False)
        data_dict = {}  # Создаем пустой словарь для хранения данных
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Находим таблицу по атрибуту style
            table = soup.find('table', style='table-layout:auto')

            if table:
                # Находим tbody с классом 'bn-table-tbody' внутри таблицы
                tbody = table.find('tbody', class_='bn-table-tbody')

                if tbody:
                    # Перебираем строки (tr) в tbody
                    rows = tbody.find_all('tr')
                    for row in rows:
                        # Извлекаем текст из ячеек (td) в текущей строке
                        cells = row.find_all('td')
                        if len(cells) == 2:
                            key = cells[0].text.strip()
                            value = cells[1].text.strip()
                            data_dict[key] = value
                else:
                    print("Element with class 'bn-table-tbody' not found in the table.")
            else:
                print("Table with style 'table-layout:auto' not found on the page.")
        else:
            print(f"Request failed with status code {response.status_code}")
        f_time = time.time()
        logging.info(f"parse_announcement_table is done. {(f_time - s_time)} sec: ")
        return data_dict
    except Exception as e:
        print('parse_announcement_table Error', e)
        logging.info(f'parse_announcement_table Error: {e}')
        return -11


def parse_announcement_table_futures(url):
    try:
        s_time = time.time()
        response = requests.get(url, verify=False)
        data_dict = {}  # Создаем пустой словарь для хранения данных
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Находим таблицу по атрибуту style
            table = soup.find('table', style='table-layout:auto')

            if table:
                # Находим tbody внутри таблицы
                tbody = table.find('tbody')

                if tbody:
                    # Перебираем строки (tr) в tbody
                    rows = tbody.find_all('tr')
                    key = None
                    values = []

                    for row in rows:
                        # Извлекаем текст из ячеек (td) в текущей строке
                        cells = row.find_all('td')

                        # Извлекаем текст из всех ячеек и убираем лишние пробелы
                        cell_texts = [cell.text.strip() for cell in cells]

                        # Используем первую ячейку в качестве ключа, а остальные как значения
                        key = cell_texts[0]
                        values = cell_texts[1:]

                        # Сохраняем данные в словаре
                        data_dict[key] = values

                else:
                    print("Table body not found in the table.")
            else:
                print("Table with style 'table-layout:auto' not found on the page.")
        else:
            print(f"Request failed with status code {response.status_code}")
        f_time = time.time()
        logging.info(f"parse_announcement_table is done. {(f_time - s_time)} sec: ")

        return data_dict
    except Exception as e:
        print('parse_announcement_table_futures Error', e)
        logging.info(f"parse_announcement_table_futures Error, {e}")

        return -11


def parse_announcement_table_spot(url):
    try:
        s_time = time.time()
        data = {}
        is_stable_coin = False
        is_new_spot_pair = False
        is_pairs_with_usdt = False
        is_error = False
        # is_pairs_with_busd = False

        response = requests.get(url, verify=False)
        data_dict = {}  # Создаем пустой словарь для хранения данных
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Извлечь заголовок
            h1_element = soup.find('h1', class_='css-1cf3zsg')
            title = h1_element.text if h1_element else "Заголовок не найден"
            # Вывести результат
            print("Заголовок:", title)
            print('')

            # Извлечь первую часть текста
            part1_element = soup.find_all('p', class_='richtext-paragraph css-127w7vq')[1].find_all('span',
                                                                                                    class_='richtext-text css-5p8b6x')
            part1_text = ''.join([span.text for span in part1_element])
            print("Часть 1:")
            print(part1_text)

            # Извлечь вторую часть текста
            part2_element = soup.find('ul', class_='css-ja9e7d').find_all('li')
            part2_text = ''
            part2_array = []
            for li in part2_element:
                spans = li.find_all('span', class_='richtext-text css-5p8b6x')
                part2_text += ''.join([span.text for span in spans]) + '\n'
                part2_array.append(''.join([span.text for span in spans]).replace('\xa0', ' '))

            print("\nЧасть 2:")
            print(part2_text)
            print(part2_array)

            if 'New Spot Trading Pairs' in part2_array[0]:
                print('    Токен будет листиться на споте')
                is_new_spot_pair = True

            if 'stable' in part1_text:
                print('    Это стейблкоин.')
                is_stable_coin = True

            if 'USDT' in part2_array[0]:
                print('    Есть пара с USDT.')
                is_pairs_with_usdt = True

            # if 'BUSD' in part2_array[0]:
            #     print('    Есть пара с BUSD.')
            #     is_pairs_with_busd = True

            if is_new_spot_pair:
                data['is_pair_with_usdt'] = is_pairs_with_usdt
                data['USDⓈ-M Perpetual Contract'] = re.findall(r'(\w+)/USDT', part2_array[0])
                if data['USDⓈ-M Perpetual Contract'] == []:
                    print('Совпадений не найдено. Ошибка в парсинге. parse_announcement_table_spot')
                    is_error = True
                print('Список токенов в паре с USDT: ', data['USDⓈ-M Perpetual Contract'])

                data['Launch Time'] = re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2} \(UTC\)', part1_text)
                print(data['Launch Time'])
                if data['Launch Time'] == []:
                    print('Совпадений не найдено. Ошибка в парсинге. parse_announcement_table_spot')
                    is_error = True
                print('Дата и время начала торгов: ', data['Launch Time'])
            elif is_stable_coin:
                print('Это стейблкоин. Сделки не открываем.')


        else:
            print(f"Request failed with status code {response.status_code}")

        # cleaned_data_dict = {}
        # for key, value in data.items():
        #     cleaned_key = key.replace('\xa0', ' ')
        #     cleaned_value = value[0].replace('\xa0', ' ')
        #     cleaned_data_dict[cleaned_key] = [cleaned_value]
        f_time = time.time()
        logging.info(f"parse_announcement_table_spot is done. {(f_time - s_time)} sec: ")
        return is_error, data
    except Exception as e:
        print('parse_announcement_table_spot Error', e)
        logging.info(f"parse_announcement_table_spot Error, {e}")

        return -11


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


def master_parser(url, previous_articles_json):
    try:
        s_time = time.time()
        is_with_usdt = False
        # response = requests.get(url, verify=False, headers={'Cache-Control': 'no-cache'}, cookies=None)
        response = requests.get(add_random_params(url), verify=False, headers={'Cache-Control': 'no-store'},
                                cookies=None)
        # response = requests.get(url)
        code = 0

        # Проверяем статус код ответа
        if response.status_code == 200:
            # Ищем начало и конец строки, содержащей ключ "articles"
            start = response.text.find('"articles":') + len('"articles":')
            end = response.text.find(']', start) + 1

            # Извлекаем JSON-строку, содержащую "articles"
            articles_json = response.text[start:end]
            # Если JSON-строка изменилась, то это означает, что появились новые новости
            if articles_json == previous_articles_json:
                # print('    Нет новых записей')
                pass
            if articles_json != previous_articles_json:
                # Парсим JSON-данные
                try:

                    articles = json.loads(articles_json)
                    prev_articles = json.loads(previous_articles_json)
                    # Создаем список только с уникальными элементами

                    new_articles = [article for article in articles if article not in prev_articles]
                    # print('LATEST NEWS', new_articles)

                    ### Если есть новые записи, парсим их дальше с целью достать оттуда нужные данные ###

                    print('Найдено', len(new_articles), 'новых записей!')

                    for j in range(len(new_articles)):
                        print('---------------------------------')
                        print('Обработка ', j + 1, '-й новой записи!')

                        if 'Binance Futures Will Launch USDⓈ-M' in new_articles[j]['title']:
                            print('    Новость о листинге фьючерсов')

                            link = convert_title_into_link(new_articles[j]['title'], new_articles[j]['code'])

                            data = parse_announcement_table_futures(link)  ### именно для фьючей
                            print(data)
                            print(range(len(data['USDⓈ-M Perpetual Contract'])))
                            is_pair_with_usdt = ['USDT' in data['Settlement Asset'][i] for i in
                                                 range(len(data['USDⓈ-M Perpetual Contract']))]
                            print(is_pair_with_usdt)
                            news_type = ['Futures Listing' for i in range(len(data['USDⓈ-M Perpetual Contract']))]
                            print(news_type)
                            prior_exchange = [check_token(data['USDⓈ-M Perpetual Contract'][i]) for i in
                                              range(len(data['USDⓈ-M Perpetual Contract']))]
                            print(prior_exchange)

                            data['News Time'] = [str(new_articles[j]['releaseDate']) for _ in
                                                 range(len(data['USDⓈ-M Perpetual Contract']))]
                            data['News Type'] = news_type
                            data['Exchange, market'] = prior_exchange
                            data['is_pair_with_usdt'] = is_pair_with_usdt

                            # for key, value in data.items():
                            #     print(f"{key}: {value}")
                            # print(data)

                            print('    Дата выхода новости: ',
                                  datetime.utcfromtimestamp(new_articles[j]['releaseDate'] / 1000))
                            print('    Тип новости: ', data['News Type'])
                            print('    Тикер токена: ', data['USDⓈ-M Perpetual Contract'])
                            print('    Дата и время старта торгов: ', data['Launch Time'])
                            print('    Ссылка на страницу новости: ', link)
                            print(f'    Приоритетная биржа: ', data['Exchange, market'])
                            print(f'    Листинг пары с USDT? ', data['is_pair_with_usdt'])

                        elif 'Binance Will List ' in new_articles[j]['title']:
                            print('    Новость о листинге на споте')

                            link = convert_title_into_link(new_articles[j]['title'], new_articles[j]['code'])

                            _, data = parse_announcement_table_spot(link)  ### именно для спота

                            # print(data)
                            print(data['USDⓈ-M Perpetual Contract'])
                            data['USDⓈ-M Perpetual Contract'] = [data['USDⓈ-M Perpetual Contract'][i] + 'USDT' for i in
                                                                 range(len(data['USDⓈ-M Perpetual Contract']))]

                            print(range(len(data['USDⓈ-M Perpetual Contract'])))

                            prior_exchange = [check_token(data['USDⓈ-M Perpetual Contract'][i]) for i in
                                              range(len(data['USDⓈ-M Perpetual Contract']))]
                            print(prior_exchange)

                            data['News Time'] = [str(new_articles[j]['releaseDate']) for _ in
                                                 range(len(data['USDⓈ-M Perpetual Contract']))]
                            data['News Type'] = ['Spot Listing' for _ in
                                                 range(len(data['USDⓈ-M Perpetual Contract']))]
                            data['Exchange, market'] = prior_exchange

                            # for key, value in data.items():
                            #     print(f"{key}: {value}")

                            print('    Дата выхода новости: ',
                                  datetime.utcfromtimestamp(new_articles[j]['releaseDate'] / 1000))
                            print('    Тип новости: ', data['News Type'])
                            print('    Тикер токена: ', data['USDⓈ-M Perpetual Contract'])
                            print('    Дата и время старта торгов: ', data['Launch Time'])
                            print('    Ссылка на страницу новости: ', link)
                            print(f'    Приоритетная биржа: {data["Exchange, market"]}')
                            print(f'    Листинг пары с USDT? {data["is_pair_with_usdt"]}')



                        else:
                            data = {}
                            link = convert_title_into_link(new_articles[j]['title'], new_articles[j]['code'])
                            data['News Time'] = [str(new_articles[j]['releaseDate'])]
                            data['News Type'] = [f"Another: {new_articles[j]['title']}"]
                            data['USDⓈ-M Perpetual Contract'] = ['_']
                            data['Launch Time'] = ['_']
                            data['Exchange, market'] = ['_', '_']
                            data['is_pair_with_usdt'] = ['_']

                            print('    Новость о не о листинге на фьючерсах или споте. Текст новости: ',
                                  new_articles[j]['title'])

                    previous_articles_json = articles_json
                    f_time = time.time()
                    logging.info(f"master_parser is done. {(f_time - s_time)} sec: ")
                    return previous_articles_json, [data['News Time'], data['News Type'],
                                                    data['USDⓈ-M Perpetual Contract'],
                                                    data['Launch Time'], data['Exchange, market'],
                                                    data['is_pair_with_usdt'], link]

                except json.JSONDecodeError as e:
                    print("Ошибка при парсинге JSON:", e)
                    logging.info(f"Произошла ошибка: {e}. ")
                    asyncio.run(send_telegram_message(f"Произошла ошибка: {e}."))
                    # sys.exit(1)  # Останавливаем выполнение программы с кодом ошибки 1
            previous_articles_json = articles_json
            f_time = time.time()
            logging.info(f"master_parser is done. {(f_time - s_time)} sec: ")
            return previous_articles_json, []

        else:
            print("Не удалось получить доступ к странице. Код состояния:", response.status_code)
            response = requests.get('https://www.binance.com/ru', verify=False)
            f_time = time.time()
            logging.info(f"master_parser is done (429). {(f_time - s_time)} sec: ")
            time.sleep(101)
            return previous_articles_json, 429
    except Exception as e:
        logging.info(f"master_parser Error, {e}")
        print('master_parser Error', e)
        asyncio.run(send_telegram_message(f'master_parser Error {e}'))

        # print('Ошибка подключения. Перезапуск.')
        # asyncio.run(send_telegram_message('Ошибка подключения. Перезапуск.'))
        # main()
        return previous_articles_json, -11


# def enterPosition(ticker, amount, leverage, exchange_info):
#     try:
#         order_info = [0]
#         try:
#             if exchange_info[0] == 'bybit':
#                 if exchange_info[1] == 'spot':
#                     order_info = SpotEnterOrder(amount, ticker)
#                 if exchange_info[1] == 'futures':
#                     order_info = FuturesEnterOrder(amount, ticker, leverage)
#         except:
#             order_info = [-1]
#         return order_info
#     except Exception as e:
#         print('enterPosition Error', e)
#         return -11


def main():
    isPositionsEnabled = False
    isTestRun = False

    ### BYBIT
    # мой ключ от основного аккаунта
    API_KEY_bybit = 'TG8WOl7FiLh2SkQiRN'
    API_SECRET_bybit = 'FM9XV4TKHy8xhcUR9WKSlrgpiByMVMMcYIZK'

    # ключи Юли
    # API_KEY_bybit = 'LCkJC6eesykRNPrt9R'
    # API_SECRET_bybit = 'xebSQQWo2ZTR8lKYhGJdEvvhyyzkv6AQXqBK'

    session_bybit = HTTP(
        api_key=API_KEY_bybit,
        api_secret=API_SECRET_bybit,
    )

    ### GATE
    # мой
    # API_KEY_gate = 'f6ef804d08f28800337b5abba2c05fae'
    # API_SECRET_gate = '8c27d7168eca569e95d4f85e7f9dc09b69337ab82ac2eb2a6285a703d7cbb1d0'
    # Юли
    API_KEY_gate = '2b9d43fa62862dd40b6765e47147676f'
    API_SECRET_gate = 'b2d027cfab2bd7dfc0420a7097b1a98f820093983efbc6613648f13a28c55a7d'
    spot_api = SpotApi(ApiClient(
        gate_api.Configuration(host="https://api.gateio.ws/api/v4", key=API_KEY_gate, secret=API_SECRET_gate)))
    futures_api = FuturesApi(ApiClient(
        gate_api.Configuration(host="https://api.gateio.ws/api/v4", key=API_KEY_gate, secret=API_SECRET_gate)))

    ### OKX
    # ключи в скрипте okx

    position_count = 0
    try:
        asyncio.run(send_telegram_message_debug('Парсер New Listings запущен.'))
        logging.info('----SCRIPT IS STARTED----')  # Логирование времени обработки запроса
        url = "https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48"
        # previous_articles_json = '[]'
        # previous_articles_json = '[{"id":181528,"code":"5e5eab2a19d444898e6961ba33d04849","title":"Binance Futures Will Launch USDⓈ-M TIA Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698768499741},{"id":181463,"code":"5d8c7476197344d087b5af436bfc74ae","title":"Binance Futures Will Launch USDⓈ-M SLP Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698731158402},{"id":181434,"code":"4492f05f8b0e40f2a6dc9321aba0ba27","title":"Binance Will List Celestia (TIA) with Seed Tag Applied","type":1,"releaseDate":1698671932206},{"id":181387,"code":"8e7a24082b4f4ab39229b05cadbfce0a","title":"Binance Adds ACA, GHST, VIDT and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1698638428354},{"id":181301,"code":"90ccca2c5d6946ef9439dae41a517578","title":"Introducing Memecoin (MEME) on Binance Launchpool! Farm MEME by Staking BNB, TUSD and FDUSD","type":1,"releaseDate":1698415749172},{"id":181213,"code":"c40a1707de63466f9aa14fd046c75e81","title":"Binance Futures Will Launch USDⓈ-M POWR Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698321002985},{"id":180971,"code":"6cdb1faca0e44c188ab680494c3bfa11","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-26","type":1,"releaseDate":1698204603826},{"id":180905,"code":"d8b596b131b64130940798961d73a8b5","title":"Binance Futures Will Launch USDⓈ-M POLYX and GAS Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1698151948683},{"id":180616,"code":"cdeaa008a1484ba0974f4359a31d29c3","title":"Binance Futures Will Launch USDⓈ-M RIF Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697862003215},{"id":180345,"code":"21802d4be7ce4e4a880e2990a6775422","title":"Binance Futures Will Launch USDⓈ-M BSV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697771703998},{"id":180281,"code":"afd04e47bab84bdab855f7698bf40fb5","title":"Binance Adds ARK, OMG \u0026 More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1697688013854},{"id":180188,"code":"b68013d4a1b14c82bb019eabcc13391a","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-19","type":1,"releaseDate":1697612405894},{"id":180152,"code":"5d2d3a74fe6c4c89ac8eaac2959383d6","title":"Binance Futures Will Launch USDⓈ-M STPT and WAXP Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1697606833266},{"id":180014,"code":"93710257326b4f33aed7d8b7b73746d1","title":"Binance Futures Will Launch USDⓈ-M ORBS Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697506436276},{"id":179943,"code":"175604613129423199f61fda5ffe3615","title":"Binance Futures Will Launch USDⓈ-M BOND Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697345978273},{"id":179775,"code":"b4eb91b68a1a4dc1b2a2f45d7b8f1a1e","title":"Binance Adds NTRN on Margin","type":1,"releaseDate":1697173875790},{"id":179699,"code":"d956c31e085444c2ba4d97c554318476","title":"Binance Futures Will Launch USDⓈ-M BIGTIME Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697109442199},{"id":179392,"code":"59cba52c3bab4059897ae88d9bbb31cf","title":"Binance Futures Will Launch USDⓈ-M LOOM Perpetual Contract With Up to 10x Leverage","type":1,"releaseDate":1696997177546},{"id":179364,"code":"9ef0c43e0c06499a8cca5081883825c8","title":"Binance Adds ADA/FDUSD, FIL/FDUSD, FRONT/TUSD, LEVER/TRY, LTC/FDUSD, RUNE/TUSD \u0026 TRB/TRY Trading Pairs","type":1,"releaseDate":1696993228097}]'
        # previous_articles_json = '[{"id":181791,"code":"a33e70c5215841299b4d4614918b93a5","title":"Binance Futures Will Launch USDⓈ-M CAKE Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698910232851},{"id":181727,"code":"2e53db8e7af34d7dae7310e4a4336cdd","title":"Binance Futures Will Launch USDⓈ-M SNT Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698892513670},{"id":181528,"code":"5e5eab2a19d444898e6961ba33d04849","title":"Binance Futures Will Launch USDⓈ-M TIA Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698768499741},{"id":181463,"code":"5d8c7476197344d087b5af436bfc74ae","title":"Binance Futures Will Launch USDⓈ-M SLP Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698731158402},{"id":181434,"code":"4492f05f8b0e40f2a6dc9321aba0ba27","title":"Binance Will List Celestia (TIA) with Seed Tag Applied","type":1,"releaseDate":1698671932206},{"id":181387,"code":"8e7a24082b4f4ab39229b05cadbfce0a","title":"Binance Adds ACA, GHST, VIDT and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1698638428354},{"id":181301,"code":"90ccca2c5d6946ef9439dae41a517578","title":"Introducing Memecoin (MEME) on Binance Launchpool! Farm MEME by Staking BNB, TUSD and FDUSD","type":1,"releaseDate":1698415749172},{"id":181213,"code":"c40a1707de63466f9aa14fd046c75e81","title":"Binance Futures Will Launch USDⓈ-M POWR Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698321002985},{"id":180971,"code":"6cdb1faca0e44c188ab680494c3bfa11","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-26","type":1,"releaseDate":1698204603826},{"id":180905,"code":"d8b596b131b64130940798961d73a8b5","title":"Binance Futures Will Launch USDⓈ-M POLYX and GAS Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1698151948683},{"id":180616,"code":"cdeaa008a1484ba0974f4359a31d29c3","title":"Binance Futures Will Launch USDⓈ-M RIF Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697862003215},{"id":180345,"code":"21802d4be7ce4e4a880e2990a6775422","title":"Binance Futures Will Launch USDⓈ-M BSV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697771703998},{"id":180281,"code":"afd04e47bab84bdab855f7698bf40fb5","title":"Binance Adds ARK, OMG \u0026 More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1697688013854},{"id":180188,"code":"b68013d4a1b14c82bb019eabcc13391a","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-19","type":1,"releaseDate":1697612405894},{"id":180152,"code":"5d2d3a74fe6c4c89ac8eaac2959383d6","title":"Binance Futures Will Launch USDⓈ-M STPT and WAXP Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1697606833266},{"id":180014,"code":"93710257326b4f33aed7d8b7b73746d1","title":"Binance Futures Will Launch USDⓈ-M ORBS Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697506436276},{"id":179943,"code":"175604613129423199f61fda5ffe3615","title":"Binance Futures Will Launch USDⓈ-M BOND Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697345978273},{"id":179775,"code":"b4eb91b68a1a4dc1b2a2f45d7b8f1a1e","title":"Binance Adds NTRN on Margin","type":1,"releaseDate":1697173875790},{"id":179699,"code":"d956c31e085444c2ba4d97c554318476","title":"Binance Futures Will Launch USDⓈ-M BIGTIME Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697109442199}]'
        # previous_articles_json = '[{"id":180616,"code":"cdeaa008a1484ba0974f4359a31d29c3","title":"Binance Futures Will Launch USDⓈ-M RIF Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697862003215},{"id":180345,"code":"21802d4be7ce4e4a880e2990a6775422","title":"Binance Futures Will Launch USDⓈ-M BSV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697771703998},{"id":180281,"code":"afd04e47bab84bdab855f7698bf40fb5","title":"Binance Adds ARK, OMG \u0026 More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1697688013854},{"id":180188,"code":"b68013d4a1b14c82bb019eabcc13391a","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-19","type":1,"releaseDate":1697612405894},{"id":180152,"code":"5d2d3a74fe6c4c89ac8eaac2959383d6","title":"Binance Futures Will Launch USDⓈ-M STPT and WAXP Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1697606833266},{"id":180014,"code":"93710257326b4f33aed7d8b7b73746d1","title":"Binance Futures Will Launch USDⓈ-M ORBS Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697506436276},{"id":179943,"code":"175604613129423199f61fda5ffe3615","title":"Binance Futures Will Launch USDⓈ-M BOND Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697345978273},{"id":179775,"code":"b4eb91b68a1a4dc1b2a2f45d7b8f1a1e","title":"Binance Adds NTRN on Margin","type":1,"releaseDate":1697173875790},{"id":179699,"code":"d956c31e085444c2ba4d97c554318476","title":"Binance Futures Will Launch USDⓈ-M BIGTIME Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697109442199}]'
        # previous_articles_json = '[{"id":181528,"code":"5e5eab2a19d444898e6961ba33d04849","title":"Binance Futures Will Launch USDⓈ-M TIA Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698768499741},{"id":181463,"code":"5d8c7476197344d087b5af436bfc74ae","title":"Binance Futures Will Launch USDⓈ-M SLP Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698731158402},{"id":181434,"code":"4492f05f8b0e40f2a6dc9321aba0ba27","title":"Binance Will List Celestia (TIA) with Seed Tag Applied","type":1,"releaseDate":1698671932206},{"id":181387,"code":"8e7a24082b4f4ab39229b05cadbfce0a","title":"Binance Adds ACA, GHST, VIDT and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1698638428354},{"id":181301,"code":"90ccca2c5d6946ef9439dae41a517578","title":"Introducing Memecoin (MEME) on Binance Launchpool! Farm MEME by Staking BNB, TUSD and FDUSD","type":1,"releaseDate":1698415749172},{"id":181213,"code":"c40a1707de63466f9aa14fd046c75e81","title":"Binance Futures Will Launch USDⓈ-M POWR Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698321002985},{"id":180971,"code":"6cdb1faca0e44c188ab680494c3bfa11","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-26","type":1,"releaseDate":1698204603826},{"id":180905,"code":"d8b596b131b64130940798961d73a8b5","title":"Binance Futures Will Launch USDⓈ-M POLYX and GAS Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1698151948683},{"id":180616,"code":"cdeaa008a1484ba0974f4359a31d29c3","title":"Binance Futures Will Launch USDⓈ-M RIF Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697862003215},{"id":180345,"code":"21802d4be7ce4e4a880e2990a6775422","title":"Binance Futures Will Launch USDⓈ-M BSV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697771703998},{"id":180281,"code":"afd04e47bab84bdab855f7698bf40fb5","title":"Binance Adds ARK, OMG \u0026 More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1697688013854},{"id":180188,"code":"b68013d4a1b14c82bb019eabcc13391a","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-19","type":1,"releaseDate":1697612405894},{"id":180152,"code":"5d2d3a74fe6c4c89ac8eaac2959383d6","title":"Binance Futures Will Launch USDⓈ-M STPT and WAXP Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1697606833266},{"id":180014,"code":"93710257326b4f33aed7d8b7b73746d1","title":"Binance Futures Will Launch USDⓈ-M ORBS Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697506436276},{"id":179943,"code":"175604613129423199f61fda5ffe3615","title":"Binance Futures Will Launch USDⓈ-M BOND Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697345978273},{"id":179775,"code":"b4eb91b68a1a4dc1b2a2f45d7b8f1a1e","title":"Binance Adds NTRN on Margin","type":1,"releaseDate":1697173875790},{"id":179699,"code":"d956c31e085444c2ba4d97c554318476","title":"Binance Futures Will Launch USDⓈ-M BIGTIME Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697109442199}]'
        # previous_articles_json = '[{"id":181463,"code":"5d8c7476197344d087b5af436bfc74ae","title":"Binance Futures Will Launch USDⓈ-M SLP Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698731158402},{"id":181434,"code":"4492f05f8b0e40f2a6dc9321aba0ba27","title":"Binance Will List Celestia (TIA) with Seed Tag Applied","type":1,"releaseDate":1698671932206},{"id":181387,"code":"8e7a24082b4f4ab39229b05cadbfce0a","title":"Binance Adds ACA, GHST, VIDT and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1698638428354},{"id":181301,"code":"90ccca2c5d6946ef9439dae41a517578","title":"Introducing Memecoin (MEME) on Binance Launchpool! Farm MEME by Staking BNB, TUSD and FDUSD","type":1,"releaseDate":1698415749172},{"id":181213,"code":"c40a1707de63466f9aa14fd046c75e81","title":"Binance Futures Will Launch USDⓈ-M POWR Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698321002985},{"id":180971,"code":"6cdb1faca0e44c188ab680494c3bfa11","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-26","type":1,"releaseDate":1698204603826},{"id":180905,"code":"d8b596b131b64130940798961d73a8b5","title":"Binance Futures Will Launch USDⓈ-M POLYX and GAS Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1698151948683},{"id":180616,"code":"cdeaa008a1484ba0974f4359a31d29c3","title":"Binance Futures Will Launch USDⓈ-M RIF Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697862003215},{"id":180345,"code":"21802d4be7ce4e4a880e2990a6775422","title":"Binance Futures Will Launch USDⓈ-M BSV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697771703998},{"id":180281,"code":"afd04e47bab84bdab855f7698bf40fb5","title":"Binance Adds ARK, OMG \u0026 More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1697688013854},{"id":180188,"code":"b68013d4a1b14c82bb019eabcc13391a","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-19","type":1,"releaseDate":1697612405894},{"id":180152,"code":"5d2d3a74fe6c4c89ac8eaac2959383d6","title":"Binance Futures Will Launch USDⓈ-M STPT and WAXP Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1697606833266},{"id":180014,"code":"93710257326b4f33aed7d8b7b73746d1","title":"Binance Futures Will Launch USDⓈ-M ORBS Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697506436276},{"id":179943,"code":"175604613129423199f61fda5ffe3615","title":"Binance Futures Will Launch USDⓈ-M BOND Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697345978273},{"id":179775,"code":"b4eb91b68a1a4dc1b2a2f45d7b8f1a1e","title":"Binance Adds NTRN on Margin","type":1,"releaseDate":1697173875790},{"id":179699,"code":"d956c31e085444c2ba4d97c554318476","title":"Binance Futures Will Launch USDⓈ-M BIGTIME Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697109442199}]'
        previous_articles_json = '[{"id":181951,"code":"d047f1923f8a40be8aedcc74387f09dc","title":"Binance Futures Will Launch USDⓈ-M TOKEN Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699008602884},{"id":181934,"code":"afcf1ccc7978458d8474f500da91a00d","title":"Binance Futures Will Launch USDⓈ-M MEME Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699003203190},{"id":181878,"code":"a45e7c4a2ca44921b13da66f291e22b8","title":"Binance Futures Will Launch USDⓈ-M TWT Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698988203438},{"id":181836,"code":"b8ace6ade44740e6afc21a3e355fdac1","title":"Binance Adds TIA, SNT, STEEM and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1698918303755},{"id":181807,"code":"b8163f2f29654c2eb758d576bef95515","title":"Binance Will Open Trading for Memecoin (MEME)","type":1,"releaseDate":1698912078594},{"id":181791,"code":"a33e70c5215841299b4d4614918b93a5","title":"Binance Futures Will Launch USDⓈ-M CAKE Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698910232851},{"id":181727,"code":"2e53db8e7af34d7dae7310e4a4336cdd","title":"Binance Futures Will Launch USDⓈ-M SNT Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698892513670},{"id":181528,"code":"5e5eab2a19d444898e6961ba33d04849","title":"Binance Futures Will Launch USDⓈ-M TIA Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698768499741},{"id":181463,"code":"5d8c7476197344d087b5af436bfc74ae","title":"Binance Futures Will Launch USDⓈ-M SLP Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698731158402},{"id":181434,"code":"4492f05f8b0e40f2a6dc9321aba0ba27","title":"Binance Will List Celestia (TIA) with Seed Tag Applied","type":1,"releaseDate":1698671932206},{"id":181387,"code":"8e7a24082b4f4ab39229b05cadbfce0a","title":"Binance Adds ACA, GHST, VIDT and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1698638428354},{"id":181301,"code":"90ccca2c5d6946ef9439dae41a517578","title":"Introducing Memecoin (MEME) on Binance Launchpool! Farm MEME by Staking BNB, TUSD and FDUSD","type":1,"releaseDate":1698415749172},{"id":181213,"code":"c40a1707de63466f9aa14fd046c75e81","title":"Binance Futures Will Launch USDⓈ-M POWR Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698321002985},{"id":180971,"code":"6cdb1faca0e44c188ab680494c3bfa11","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-26","type":1,"releaseDate":1698204603826},{"id":180905,"code":"d8b596b131b64130940798961d73a8b5","title":"Binance Futures Will Launch USDⓈ-M POLYX and GAS Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1698151948683},{"id":180616,"code":"cdeaa008a1484ba0974f4359a31d29c3","title":"Binance Futures Will Launch USDⓈ-M RIF Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697862003215},{"id":180345,"code":"21802d4be7ce4e4a880e2990a6775422","title":"Binance Futures Will Launch USDⓈ-M BSV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697771703998},{"id":180281,"code":"afd04e47bab84bdab855f7698bf40fb5","title":"Binance Adds ARK, OMG \u0026 More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1697688013854},{"id":180188,"code":"b68013d4a1b14c82bb019eabcc13391a","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-19","type":1,"releaseDate":1697612405894}]'
        i = 0
        fails = 0

        # start_time = time.time()
        # pa, output = master_parser(url, previous_articles_json)
        # end_time = time.time()
        #
        # logging.info(
        #     f'Запрос {i}: {start_time} - {end_time} ({end_time - start_time})')  # Логирование времени обработки запроса
        # logging.info(f'Вывод {output}')  # Вывода
        # print(output)
        #
        # if isTestRun:
        #     if output != 429 and output != []:
        #         position_count = len(output[0])
        #         print(position_count)
        #         asyncio.run(send_telegram_message(
        #             f'Тестовый запуск. Проверка открытия фьючерсной позиции. \n ❗️Найдена новая новость!❗️ \n Время запроса и обработки:  from {datetime.utcfromtimestamp(start_time)} \n  to {datetime.utcfromtimestamp(end_time)} \n  ({end_time - start_time} sec)'))
        #
        #         for i in range(len(output[0])):
        #             if 'Another' in output[1][i]:
        #                 asyncio.run(send_telegram_message(
        #                     f"Время выхода новости: {datetime.utcfromtimestamp(int(output[0][i]) / 1000)} \n Новость незнакомого формата. \n Текст новости: {output[1][i][8:]} Ссылка на новость: {output[6]}"))
        #
        #             elif output[5]:
        #                 asyncio.run(send_telegram_message(
        #                     f"Время выхода новости: {datetime.utcfromtimestamp(int(output[0][i]) / 1000)} \n Тип новости: {output[1][i]} \n Токен: {output[2][i]} \n Начало торгов: {output[3][i]} \n Биржа для открытия лонга: {output[4][i][0]} \n Тип контракта: {output[4][i][1]} \n Ссылка на новость: {output[6]}"))
        #             elif not output[5]:
        #                 asyncio.run(send_telegram_message(
        #                     f"Время выхода новости: {datetime.utcfromtimestamp(int(output[0][i]) / 1000)} \n Новость незнакомого формата. \n Текст новости: {output[1][i]} \n Токен: {output[2][i]}   (нет торговой пары с USDT) \n Начало торгов: {output[3][i]} \n Биржа для открытия лонга: {output[4][i][0]} \n Тип контракта: {output[4][i][1]} \n Ссылка на новость: {output[6]}"))
        #
        # if isPositionsEnabled:
        #     for pos in range(position_count):
        #         if output[4][pos][1] == 'futures':
        #             if output[4][pos][0] == 'bybit':
        #                 FuturesEnterOrder(position_sum=position_margin, ticker=output[2][pos], leverage=leverage,
        #                                   session_bybit=session_bybit)
        #
        #             if output[4][pos][0] == 'okx':
        #                 FuturesEnterOrder_okx(ticker=output[2][pos], leverage=leverage, position_sum=position_margin)
        #
        #             if output[4][pos][0] == 'gateio':
        #                 placeFuturesOrder_gateio(ticker=output[2][pos], position_sum=position_margin, leverage=leverage,
        #                                          futures_api=futures_api)
        #             else:
        #                 print('Алгоритм выставление позиции на бирже', output[4][pos][0], 'ещё не реализован')
        #
        #         if output[4][pos][1] == 'spot':
        #             if output[4][pos][0] == 'bybit':
        #                 SpotEnterOrder(position_sum=position_margin, ticker=output[2][pos], session_bybit=session_bybit)
        #
        #             if output[4][pos][0] == 'okx':
        #                 SpotEnterOrder_okx(ticker=output[2][pos], position_sum=position_margin)
        #
        #             if output[4][pos][0] == 'gateio':
        #                 placeSpotOrder_gateio(ticker=output[2][pos], amount=position_margin, spot_api=spot_api)
        #
        #             else:
        #                 print('Алгоритм выставление позиции на бирже', output[4][pos][0], 'ещё не реализован')
        #
        #         else:
        #             print('Не найдено данного токена на биржах из списка')

        # isPositionsEnabled = True
        times = []
        max_attempts = 10
        pa = initial_parser(url)
        logging.info(f'Первоначальные новости {pa}')
        print(pa)
        while True:
            attempts = 0
            position_count = 0
            # asyncio.run(send_telegram_message('тестовое сообщение из вложенного цикла'))
            i += 1
            if i%(120) == 0:
                asyncio.run(send_telegram_message_debug('Парсер New Listings исправно функционирует.'))

            start_time = time.time()

            while attempts < max_attempts:
                try:
                    pa, output = master_parser(url, pa)
                    # print('!!!', output)
                    if output == -11:
                        print(
                            f"Ошибка интернет соединения: Error HTTPSConnectionPool(host='www.binance.com', port=443): Max retries exceeded with url. \n Попытка перезапуска: {attempts + 1}/{max_attempts}.")
                        logging.info(
                            f"Ошибка интернет соединения: Error HTTPSConnectionPool(host='www.binance.com', port=443): Max retries exceeded with url. Попытка перезапуска: {attempts + 1}/{max_attempts}.")
                        asyncio.run(send_telegram_message(
                            f"Ошибка интернет соединения: Error HTTPSConnectionPool(host='www.binance.com', port=443): Max retries exceeded with url. Попытка перезапуска: {attempts + 1}/{max_attempts}."))
                        attempts += 1
                        # print(attempts)
                        time.sleep(5)

                        if attempts >= max_attempts:
                            print(
                                'Переподключение не удалось. Достигнуто максимальное количество попыток. Работа парсера завершена.')
                            logging.info(
                                'Переподключение не удалось. Достигнуто максимальное количество попыток. Работа парсера завершена.')
                            asyncio.run(send_telegram_message(
                                'Переподключение не удалось. Достигнуто максимальное количество попыток. Работа парсера завершена.'))
                            sys.exit(1)
                    if output != -11:
                        if attempts >= 1:
                            asyncio.run(send_telegram_message('Подключение восстановлено.'))
                        break
                except Exception as e:
                    print(f"Ошибка master_parser в main: {e}")
                    logging.info(f"Ошибка master_parser в main: {e}")
                    asyncio.run(send_telegram_message(f"Ошибка master_parser в main: {e}"))
                    # attempts += 1
                    # time.sleep(5)

            if attempts >= max_attempts:
                print(
                    'Переподключение не удалось. Достигнуто максимальное количество попыток. Работа парсера завершена.')
                logging.info(
                    'Переподключение не удалось. Достигнуто максимальное количество попыток. Работа парсера завершена.')

                asyncio.run(send_telegram_message(
                    'Переподключение не удалось. Достигнуто максимальное количество попыток. Работа парсера завершена.'))
                sys.exit(1)

            end_time = time.time()

            logging.info(
                f'Запрос {i}: {start_time} - {end_time} ({end_time - start_time})')  # Логирование времени обработки запроса
            logging.info(f'Вывод {output}')  # Вывода

            print(output)

            if output != 429 and output != [] and output != -11:
                position_count = len(output[0])
                asyncio.run(send_telegram_message(
                    f'❗️Найдена новая новость!❗️ \n Время запроса и обработки:  from {datetime.utcfromtimestamp(start_time)} \n  to {datetime.utcfromtimestamp(end_time)} \n  ({end_time - start_time} sec)'))

                for i in range(len(output[0])):

                    if 'Another' in output[1][i]:
                        asyncio.run(send_telegram_message(
                            f"Время выхода новости: {datetime.utcfromtimestamp(int(output[0][i]) / 1000)} \n Новость незнакомого формата. \n Текст новости: {output[1][i][8:]} Ссылка на новость: {output[6]}"))
                        isPositionsEnabled = False
                    elif output[5]:
                        asyncio.run(send_telegram_message(
                            f"Время выхода новости: {datetime.utcfromtimestamp(int(output[0][i]) / 1000)} \n Тип новости: {output[1][i]} \n Токен: {output[2][i]} \n Начало торгов: {output[3][i]} \n Биржа для открытия лонга: {output[4][i][0]} \n Тип контракта: {output[4][i][1]} \n Ссылка на новость: {output[6]}"))
                    elif not output[5]:
                        asyncio.run(send_telegram_message(
                            f"Время выхода новости: {datetime.utcfromtimestamp(int(output[0][i]) / 1000)} \n Новость незнакомого формата. \n Текст новости: {output[1][i]} \n Токен: {output[2][i]}  (нет торговой пары с USDT) \n Начало торгов: {output[3][i]} \n Биржа для открытия лонга: {output[4][i][0]} \n Тип контракта: {output[4][i][1]} \n Ссылка на новость: {output[6]}"))

            if output == 429:
                fails += 1
            times.append(end_time - start_time)
            print(f"Время и обработки выполнения запроса: {end_time - start_time} секунд")
            time.sleep(30)
            logging.info(f'Среднее время на запрос: {np.mean(times)}, количество ошибок: {fails}')

            if isPositionsEnabled:
                for pos in range(position_count):
                    if output[4][pos][1] == 'futures':
                        if output[4][pos][0] == 'bybit':
                            FuturesEnterOrder(position_sum=position_margin, ticker=output[2][pos], leverage=leverage,
                                              session_bybit=session_bybit)

                        if output[4][pos][0] == 'okx':
                            FuturesEnterOrder_okx(ticker=output[2][pos], leverage=leverage,
                                                  position_sum=position_margin)

                        if output[4][pos][0] == 'gateio':
                            placeFuturesOrder_gateio(ticker=output[2][pos], position_sum=position_margin,
                                                     leverage=leverage,
                                                     futures_api=futures_api)
                        else:
                            print('Алгоритм выставления позиции на бирже', output[4][pos][0], 'ещё не реализован')

                    if output[4][pos][1] == 'spot':
                        if output[4][pos][0] == 'bybit':
                            SpotEnterOrder(position_sum=position_margin, ticker=output[2][pos],
                                           session_bybit=session_bybit)

                        if output[4][pos][0] == 'okx':
                            SpotEnterOrder_okx(ticker=output[2][pos], position_sum=position_margin)

                        if output[4][pos][0] == 'gateio':
                            placeSpotOrder_gateio(ticker=output[2][pos], amount=position_margin, spot_api=spot_api)

                        else:
                            print('Алгоритм выставления позиции на бирже', output[4][pos][0], 'ещё не реализован')

                    else:
                        print('Не найдено данного токена на биржах из списка')

            # if not isPositionsEnabled:
                # isPositionsEnabled = True
    except KeyboardInterrupt:
        # Обработка события прерывания (нажатие кнопки "Stop" в PyCharm)
        asyncio.run(send_telegram_message("Парсер новостей остановлен вручную"))

    except Exception as e:
        print(f"Произошла ошибка в main: {e}")
        logging.info(f"Произошла ошибка: {e}. Парсер новостей остановлен.")
        asyncio.run(send_telegram_message(f"Произошла ошибка : {e}. Парсер новостей остановлен."))


import warnings

warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)
# warnings.resetwarnings()

if __name__ == "__main__":
    main()
