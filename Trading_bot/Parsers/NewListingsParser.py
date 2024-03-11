import requests
import json
import time
from datetime import datetime
import re
from bs4 import BeautifulSoup
import logging
import numpy as np
import warnings

import asyncio

import random
import string
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from telegram import Bot
import psycopg2
import pytz


import sys
import atexit

# from Notifications import NotificationsBot
# from IsTickerOnExchange import check_token

from Notifications.Notifications import NotificationsBot

log_file = 'logfile.log'
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REAL_TRADING = True


class NewListingsParser:
    def __init__(self, url, bot):
        # "bot" is an instance of NotificationsBot class from Notifications.py 
        self.telegram_bot = bot

        # link to parse
        self.url = url 
        self.previous_articles = '[]'
        self.ticker = ''
        self.news_release_date = ''
        self.listing_date = ''
        self.listing_type = ''
        self.prior_exchange = ''
        self.text_news = ''
        self.post_code = ''
        self.is_pair_with_usdt = ''
        self.next_link = ''

    def convert_title_into_link(self):
        try:
            s_time = time.time()
            lower_case_text = self.text_news.lower()
            hyphenated_text = lower_case_text.replace(' ', '-')
            f_time = time.time()
            logging.info(f"convert_title_into_link is done. {(f_time - s_time)} sec: ")
            return 'https://www.binance.com/en/support/announcement/' + hyphenated_text + '-' + self.post_code
        except Exception as e:
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в NewListingsParser.py convert_title_into_link,{e}'))

    def parse_announcement_table(self, url):
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
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в NewListingsParser.py parse_announcement_table,{e}'))
            return -11

    def ParseAnnounceTableFutures(self, url):
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

    def ParseAnnounceTableSpot(self, url):
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
                h1_element = soup.find('h1') 
                title = h1_element.text if h1_element else "Заголовок не найден"
                # Вывести результат
                print("Заголовок:", title)
                print('')

                # Извлечь первую часть текста
                part1_element = soup.find_all('p', class_='richtext-paragraph')[1].find_all('span', class_='richtext-text')
                part1_text = ''.join([span.text for span in part1_element])
                print("Часть 1:")
                print(part1_text)

                # Извлечь вторую часть текста
                part2_element = soup.find('ul', class_='css-197cloy').find_all('li')
                part2_text = ''
                part2_array = []
                for li in part2_element:
                    spans = li.find_all('span', class_='richtext-text')
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
            asyncio.run(self.telegram_bot.sendMessageDebug(data))
            return is_error, data
        except Exception as e:
            print('parse_announcement_table_spot Error', e)
            logging.info(f"parse_announcement_table_spot Error, {e}")

            return -11

    def getModifiedUrl(self, num_params=3, param_length=3):
        s_time = time.time()
        parsed_url = urlparse(self.url)
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

    def initial_parser(self):
        articles_json = []
        try:
            s_time = time.time()
            response = requests.get(self.url)

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

    def master_message(self):
        pass

    def connect_to_database(self):
        return psycopg2.connect(
            database='StrategyLongBeforeListingDB',
            user='admin',
            password='root',
            host='database',
            port=5432
        )

    def writeIntoDataBase(self, news_title, ticker, release_date, listing_date, listing_type, prior_exchange, market):

        conn = self.connect_to_database()
        cur = conn.cursor()

        # Преобразовываем строку в объект datetime
        date_format = "%Y-%m-%d %H:%M (%Z)"
        dt = datetime.strptime(listing_date, date_format)

        # Присваиваем часовой пояс UTC
        utc_timezone = pytz.timezone('UTC')
        dt = utc_timezone.localize(dt)

        # Получаем Unix timestamp
        listing_date_timestamp = int(dt.timestamp())*1000
        listing_date_timestamp = str(listing_date_timestamp)
        release_date = str(release_date)

        flag = 0
        listing_data = [(news_title, ticker, release_date, listing_date_timestamp, listing_type, prior_exchange, market, flag)]

        insert_query = '''
        INSERT INTO newListings
        (news_title, ticker, release_date, listing_date, listing_type, prior_exchange, market, flag) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        '''

        cur.executemany(insert_query, listing_data)

        # Подтверждение транзакции
        conn.commit()

        cur.close()
        conn.close()

    def check_token(self, ticker_to_check):
        conn = self.connect_to_database()
        cur = conn.cursor()

        query = '''
                SELECT DISTINCT exhanges.exchange_name
                FROM tickers
                JOIN ticker_exchange_relation ON tickers.id = ticker_exchange_relation.ticker_id
                JOIN exhanges ON ticker_exchange_relation.exchange_id = exhanges.id
                WHERE tickers.ticker_name = %s;
                '''
        cur.execute(query, (ticker_to_check,))
        query_result = cur.fetchall()
        available_exchanges = [item[0] for item in query_result]
        print('available_exchanges ', available_exchanges)
        # QUERY RESULT  [('bybit_f',), ('bybit_s',), ('gate_f',), ('gate_s',), ('okx_s',), ('binance_s',)]

        if 'bybit_f' in available_exchanges:
            return ['bybit','futures']
        # elif 'kucoin_f' in available_exchanges:
        #     return 'kucoin_f'
        elif 'gate_f' in available_exchanges:
            return ['gate','futures']
        elif 'okx_f' in available_exchanges:
            return ['okx','futures']
        # elif 'huobi_f' in available_exchanges:
        #     return 'huobi_f'
        # elif 'mexc_f' in available_exchanges:
        #     return 'mexc_f'
        # elif 'bitmart_f' in available_exchanges:
        #     return 'bitmart_f'
        # elif 'xt_f' in available_exchanges:
        #     return ['xt', 'futures']
        elif 'binance_s' in available_exchanges:
            return ['binance','spot']
        elif 'bybit_s' in available_exchanges:
            return ['bybit','spot']
        # elif 'kucoin_s' in available_exchanges:
        #     return 'kucoin_s'
        elif 'gate_s' in available_exchanges:
            return ['gate','spot']
        elif 'okx_s' in available_exchanges:
            return ['okx','spot']
        # elif 'huobi_s' in available_exchanges:
        #     return 'huobi_s'
        # elif 'mexc_s' in available_exchanges:
        #     return 'mexc_s'
        # elif 'bitmart_s' in available_exchanges:
        #     return 'bitmart_s'
        # elif 'xt_s' in available_exchanges:
        #     return ['xt', 'spot']
        
        return ['nothing', 'nothing']
            
        

    def master_parser(self):
        try:

            self.ticker = ''
            self.news_release_date = ''
            self.listing_date = ''
            self.listing_type = ''
            self.prior_exchange = ''
            self.market = ''
            self.text_news = ''
            self.post_code = ''
            self.is_pair_with_usdt = ''
            self.next_link = ''

            s_time = time.time()
            # is_with_usdt = False
            # response = requests.get(url, verify=False, headers={'Cache-Control': 'no-cache'}, cookies=None)
            response = requests.get(self.getModifiedUrl(), verify=False, headers={'Cache-Control': 'no-store'},
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
                if articles_json == self.previous_articles:
                    print('    Нет новых записей')
                    pass
                if articles_json != self.previous_articles:
                    # Парсим JSON-данные
                    try:

                        articles = json.loads(articles_json)
                        prev_articles = json.loads(self.previous_articles)
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

                                self.text_news = new_articles[j]['title']
                                self.post_code = new_articles[j]['code']
                                self.next_link = self.convert_title_into_link()

                                data = self.ParseAnnounceTableFutures(self.next_link)  ### именно для фьючей
                                print(data)

                                print(range(len(data['USDⓈ-M Perpetual Contract'])))
                                self.ticker = data['USDⓈ-M Perpetual Contract']

                                is_pair_with_usdt = ['USDT' in data['Settlement Asset'][i] for i in
                                                     range(len(data['USDⓈ-M Perpetual Contract']))]
                                data['is_pair_with_usdt'] = is_pair_with_usdt
                                self.is_pair_with_usdt = is_pair_with_usdt
                                print(is_pair_with_usdt)

                                news_type = ['Futures Listing' for _ in range(len(data['USDⓈ-M Perpetual Contract']))]
                                data['News Type'] = news_type
                                self.listing_type = news_type
                                print(news_type)

                                prior_exchange = [self.check_token(data['USDⓈ-M Perpetual Contract'][i]) for i in
                                                  range(len(data['USDⓈ-M Perpetual Contract']))]
                                # ['bybit','futures']
                                data['Exchange, market'] = prior_exchange
                                self.prior_exchange = prior_exchange
                                print(prior_exchange)

                                data['News Time'] = [str(new_articles[j]['releaseDate']) for _ in
                                                     range(len(data['USDⓈ-M Perpetual Contract']))]
                                self.news_release_date = data['News Time']

                                self.listing_date = data['Launch Time']

                                # data['Exchange, market'] = prior_exchange
                                # data['is_pair_with_usdt'] = is_pair_with_usdt

                                # for key, value in data.items():
                                #     print(f"{key}: {value}")
                                # print(data)
                                print('    Дата выхода новости: ', self.news_release_date)
                                print('    Тип новости: ', self.listing_type)
                                print('    Тикер токена: ', self.ticker)
                                print('    Дата и время старта торгов: ', self.listing_date)
                                print('    Ссылка на страницу новости: ', self.next_link)
                                print(f'    Приоритетная биржа: ', self.prior_exchange)
                                print(f'    Листинг пары с USDT? ', self.is_pair_with_usdt)

                            elif 'Binance Will List ' in new_articles[j]['title']:
                                print('    Новость о листинге на споте')

                                self.text_news = new_articles[j]['title']
                                self.post_code = new_articles[j]['code']
                                self.next_link = self.convert_title_into_link()

                                _, data = self.ParseAnnounceTableSpot(self.next_link)  ### именно для спота

                                print(data['USDⓈ-M Perpetual Contract'])
                                data['USDⓈ-M Perpetual Contract'] = [data['USDⓈ-M Perpetual Contract'][i] + 'USDT' for i
                                                                     in
                                                                     range(len(data['USDⓈ-M Perpetual Contract']))]
                                self.ticker = data['USDⓈ-M Perpetual Contract']

                                print(range(len(data['USDⓈ-M Perpetual Contract'])))

                                prior_exchange = [self.check_token(data['USDⓈ-M Perpetual Contract'][i]) for i in
                                                  range(len(data['USDⓈ-M Perpetual Contract']))]
                                data['Exchange, market'] = prior_exchange
                                self.prior_exchange = prior_exchange
                                print(prior_exchange)

                                data['News Time'] = [str(new_articles[j]['releaseDate']) for _ in
                                                     range(len(data['USDⓈ-M Perpetual Contract']))]
                                self.news_release_date = data['News Time']

                                data['News Type'] = ['Spot Listing' for _ in
                                                     range(len(data['USDⓈ-M Perpetual Contract']))]
                                self.listing_type = data['News Type']
                                self.listing_date = data['Launch Time']
                                self.is_pair_with_usdt = data["is_pair_with_usdt"]
                                # for key, value in data.items():
                                #     print(f"{key}: {value}")

                                print('    Дата выхода новости: ',
                                      datetime.utcfromtimestamp(new_articles[j]['releaseDate'] / 1000))
                                print('    Тип новости: ', data['News Type'])
                                print('    Тикер токена: ', data['USDⓈ-M Perpetual Contract'])
                                print('    Дата и время старта торгов: ', data['Launch Time'])
                                print('    Ссылка на страницу новости: ', self.next_link)
                                print(f'    Приоритетная биржа: {data["Exchange, market"]}')
                                print(f'    Листинг пары с USDT? {data["is_pair_with_usdt"]}')
                                print('---')
                                print('    Дата выхода новости: ', self.news_release_date)
                                print('    Тип новости: ', self.listing_type)
                                print('    Тикер токена: ', self.ticker)
                                print('    Дата и время старта торгов: ', self.listing_date)
                                print('    Ссылка на страницу новости: ', self.next_link)
                                print(f'    Приоритетная биржа: ', self.prior_exchange)
                                print(f'    Листинг пары с USDT? ', self.is_pair_with_usdt)

                                asyncio.run(self.telegram_bot.sendMessageDebug(f'    Дата выхода новости: {datetime.utcfromtimestamp(new_articles[j]["releaseDate"] / 1000)}\n'
      f'    Тип новости: {data["News Type"]}\n'
      f'    Тикер токена: {data["USDⓈ-M Perpetual Contract"]}\n'
      f'    Дата и время старта торгов: {data["Launch Time"]}\n'
      f'    Ссылка на страницу новости: {self.next_link}\n'
      f'    Приоритетная биржа: {data["Exchange, market"]}\n'
      f'    Листинг пары с USDT? {data["is_pair_with_usdt"]}\n'
      f'---\n'
      f'    Дата выхода новости: {self.news_release_date}\n'
      f'    Тип новости: {self.listing_type}\n'
      f'    Тикер токена: {self.ticker}\n'
      f'    Дата и время старта торгов: {self.listing_date}\n'
      f'    Ссылка на страницу новости: {self.next_link}\n'
      f'    Приоритетная биржа: {self.prior_exchange}\n'
      f'    Листинг пары с USDT? {self.is_pair_with_usdt}'
))




                            else:
                                data = {}
                                self.text_news = new_articles[j]['title']
                                self.post_code = new_articles[j]['code']
                                self.next_link = self.convert_title_into_link()

                                data['News Time'] = [str(new_articles[j]['releaseDate'])]
                                self.news_release_date = data['News Time']

                                data['News Type'] = [f"Another: {new_articles[j]['title']}"]
                                self.listing_type = data['News Type']

                                data['USDⓈ-M Perpetual Contract'] = ['_']
                                data['Launch Time'] = ['_']
                                data['Exchange, market'] = ['_', '_']
                                data['is_pair_with_usdt'] = ['_']

                                print('    Новость не о листинге на фьючерсах или споте. Текст новости: ',
                                      new_articles[j]['title'])

                        self.previous_articles = articles_json
                        f_time = time.time()
                        logging.info(f"master_parser is done. {(f_time - s_time)} sec: ")
                        return self.previous_articles, [data['News Time'], data['News Type'],
                                                        data['USDⓈ-M Perpetual Contract'],
                                                        data['Launch Time'], data['Exchange, market'],
                                                        data['is_pair_with_usdt'], self.next_link]

                    except json.JSONDecodeError as e:
                        print("Ошибка при парсинге JSON:", e)
                        logging.info(f"Произошла ошибка: {e}. ")
                        asyncio.run(self.telegram_bot.sendMessageDebug(f"Произошла ошибка: {e}."))
                        # sys.exit(1)  # Останавливаем выполнение программы с кодом ошибки 1
                self.previous_articles = articles_json
                f_time = time.time()
                logging.info(f"master_parser is done. {(f_time - s_time)} sec: ")
                return self.previous_articles, []

            else:
                print("Не удалось получить доступ к странице. Код состояния:", response.status_code)
                response = requests.get('https://www.binance.com/ru', verify=False)
                f_time = time.time()
                logging.info(f"master_parser is done (429). {(f_time - s_time)} sec: ")
                time.sleep(101)
                return self.previous_articles, 429
        except Exception as e:
            logging.info(f"master_parser Error, {e}")
            print('master_parser Error', e)
            asyncio.run(self.telegram_bot.sendMessageDebug(f'master_parser Error {e}'))

            # print('Ошибка подключения. Перезапуск.')
            # asyncio.run(send_telegram_message('Ошибка подключения. Перезапуск.'))
            # main()
            return self.previous_articles, -11


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


    def main(self):
        conn = self.connect_to_database()
        cur = conn.cursor()
        # Создание таблицы
        #ПОТОМ УБРАТЬ СТРОЧКУ DROP TABLE IF EXISTS exhanges
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS newListings (
                id SERIAL PRIMARY KEY,
                news_title VARCHAR(1000),
                ticker VARCHAR(100),
                release_date VARCHAR(100),
                listing_date VARCHAR(100),
                listing_type VARCHAR(100),
                prior_exchange VARCHAR(100),
                market VARCHAR(100),
                flag INTEGER
                );
        '''
        cur.execute(create_table_query)
        conn.commit()

        create_table_query_exchanges = '''           
            CREATE TABLE IF NOT EXISTS exhanges (
                id SERIAL PRIMARY KEY,
                exchange_name VARCHAR(100) UNIQUE
                );
    
            INSERT INTO exhanges (exchange_name) VALUES 
                ('bybit_s'),
                ('bybit_f'),
                ('gate_s'),
                ('gate_f'),
                ('okx_s'),
                ('okx_f'),
                ('binance_s')
            ON CONFLICT (exchange_name) DO NOTHING;
            '''

        cur.execute(create_table_query_exchanges)
        conn.commit()

        cur.close()
        conn.close()

        try:
            asyncio.run(self.telegram_bot.sendMessageDebug('Парсер NewListingsParser запущен.'))
            print('Парсер NewListingsParser запущен. Выполнение кода')
            # logging.info('----SCRIPT IS STARTED----')  # Логирование времени обработки запроса
            url = "https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48"
            # previous_articles_json = '[]'
            # previous_articles_json = '[{"id":181528,"code":"5e5eab2a19d444898e6961ba33d04849","title":"Binance Futures Will Launch USDⓈ-M TIA Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698768499741},{"id":181463,"code":"5d8c7476197344d087b5af436bfc74ae","title":"Binance Futures Will Launch USDⓈ-M SLP Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698731158402},{"id":181434,"code":"4492f05f8b0e40f2a6dc9321aba0ba27","title":"Binance Will List Celestia (TIA) with Seed Tag Applied","type":1,"releaseDate":1698671932206},{"id":181387,"code":"8e7a24082b4f4ab39229b05cadbfce0a","title":"Binance Adds ACA, GHST, VIDT and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1698638428354},{"id":181301,"code":"90ccca2c5d6946ef9439dae41a517578","title":"Introducing Memecoin (MEME) on Binance Launchpool! Farm MEME by Staking BNB, TUSD and FDUSD","type":1,"releaseDate":1698415749172},{"id":181213,"code":"c40a1707de63466f9aa14fd046c75e81","title":"Binance Futures Will Launch USDⓈ-M POWR Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698321002985},{"id":180971,"code":"6cdb1faca0e44c188ab680494c3bfa11","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-26","type":1,"releaseDate":1698204603826},{"id":180905,"code":"d8b596b131b64130940798961d73a8b5","title":"Binance Futures Will Launch USDⓈ-M POLYX and GAS Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1698151948683},{"id":180616,"code":"cdeaa008a1484ba0974f4359a31d29c3","title":"Binance Futures Will Launch USDⓈ-M RIF Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697862003215},{"id":180345,"code":"21802d4be7ce4e4a880e2990a6775422","title":"Binance Futures Will Launch USDⓈ-M BSV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697771703998},{"id":180281,"code":"afd04e47bab84bdab855f7698bf40fb5","title":"Binance Adds ARK, OMG \u0026 More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1697688013854},{"id":180188,"code":"b68013d4a1b14c82bb019eabcc13391a","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-19","type":1,"releaseDate":1697612405894},{"id":180152,"code":"5d2d3a74fe6c4c89ac8eaac2959383d6","title":"Binance Futures Will Launch USDⓈ-M STPT and WAXP Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1697606833266},{"id":180014,"code":"93710257326b4f33aed7d8b7b73746d1","title":"Binance Futures Will Launch USDⓈ-M ORBS Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697506436276},{"id":179943,"code":"175604613129423199f61fda5ffe3615","title":"Binance Futures Will Launch USDⓈ-M BOND Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697345978273},{"id":179775,"code":"b4eb91b68a1a4dc1b2a2f45d7b8f1a1e","title":"Binance Adds NTRN on Margin","type":1,"releaseDate":1697173875790},{"id":179699,"code":"d956c31e085444c2ba4d97c554318476","title":"Binance Futures Will Launch USDⓈ-M BIGTIME Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697109442199},{"id":179392,"code":"59cba52c3bab4059897ae88d9bbb31cf","title":"Binance Futures Will Launch USDⓈ-M LOOM Perpetual Contract With Up to 10x Leverage","type":1,"releaseDate":1696997177546},{"id":179364,"code":"9ef0c43e0c06499a8cca5081883825c8","title":"Binance Adds ADA/FDUSD, FIL/FDUSD, FRONT/TUSD, LEVER/TRY, LTC/FDUSD, RUNE/TUSD \u0026 TRB/TRY Trading Pairs","type":1,"releaseDate":1696993228097}]'
            # previous_articles_json = '[{"id":181791,"code":"a33e70c5215841299b4d4614918b93a5","title":"Binance Futures Will Launch USDⓈ-M CAKE Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698910232851},{"id":181727,"code":"2e53db8e7af34d7dae7310e4a4336cdd","title":"Binance Futures Will Launch USDⓈ-M SNT Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698892513670},{"id":181528,"code":"5e5eab2a19d444898e6961ba33d04849","title":"Binance Futures Will Launch USDⓈ-M TIA Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698768499741},{"id":181463,"code":"5d8c7476197344d087b5af436bfc74ae","title":"Binance Futures Will Launch USDⓈ-M SLP Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698731158402},{"id":181434,"code":"4492f05f8b0e40f2a6dc9321aba0ba27","title":"Binance Will List Celestia (TIA) with Seed Tag Applied","type":1,"releaseDate":1698671932206},{"id":181387,"code":"8e7a24082b4f4ab39229b05cadbfce0a","title":"Binance Adds ACA, GHST, VIDT and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1698638428354},{"id":181301,"code":"90ccca2c5d6946ef9439dae41a517578","title":"Introducing Memecoin (MEME) on Binance Launchpool! Farm MEME by Staking BNB, TUSD and FDUSD","type":1,"releaseDate":1698415749172},{"id":181213,"code":"c40a1707de63466f9aa14fd046c75e81","title":"Binance Futures Will Launch USDⓈ-M POWR Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698321002985},{"id":180971,"code":"6cdb1faca0e44c188ab680494c3bfa11","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-26","type":1,"releaseDate":1698204603826},{"id":180905,"code":"d8b596b131b64130940798961d73a8b5","title":"Binance Futures Will Launch USDⓈ-M POLYX and GAS Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1698151948683},{"id":180616,"code":"cdeaa008a1484ba0974f4359a31d29c3","title":"Binance Futures Will Launch USDⓈ-M RIF Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697862003215},{"id":180345,"code":"21802d4be7ce4e4a880e2990a6775422","title":"Binance Futures Will Launch USDⓈ-M BSV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697771703998},{"id":180281,"code":"afd04e47bab84bdab855f7698bf40fb5","title":"Binance Adds ARK, OMG \u0026 More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1697688013854},{"id":180188,"code":"b68013d4a1b14c82bb019eabcc13391a","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-19","type":1,"releaseDate":1697612405894},{"id":180152,"code":"5d2d3a74fe6c4c89ac8eaac2959383d6","title":"Binance Futures Will Launch USDⓈ-M STPT and WAXP Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1697606833266},{"id":180014,"code":"93710257326b4f33aed7d8b7b73746d1","title":"Binance Futures Will Launch USDⓈ-M ORBS Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697506436276},{"id":179943,"code":"175604613129423199f61fda5ffe3615","title":"Binance Futures Will Launch USDⓈ-M BOND Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697345978273},{"id":179775,"code":"b4eb91b68a1a4dc1b2a2f45d7b8f1a1e","title":"Binance Adds NTRN on Margin","type":1,"releaseDate":1697173875790},{"id":179699,"code":"d956c31e085444c2ba4d97c554318476","title":"Binance Futures Will Launch USDⓈ-M BIGTIME Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697109442199}]'
            # previous_articles_json = '[{"id":180616,"code":"cdeaa008a1484ba0974f4359a31d29c3","title":"Binance Futures Will Launch USDⓈ-M RIF Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697862003215},{"id":180345,"code":"21802d4be7ce4e4a880e2990a6775422","title":"Binance Futures Will Launch USDⓈ-M BSV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697771703998},{"id":180281,"code":"afd04e47bab84bdab855f7698bf40fb5","title":"Binance Adds ARK, OMG \u0026 More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1697688013854},{"id":180188,"code":"b68013d4a1b14c82bb019eabcc13391a","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-19","type":1,"releaseDate":1697612405894},{"id":180152,"code":"5d2d3a74fe6c4c89ac8eaac2959383d6","title":"Binance Futures Will Launch USDⓈ-M STPT and WAXP Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1697606833266},{"id":180014,"code":"93710257326b4f33aed7d8b7b73746d1","title":"Binance Futures Will Launch USDⓈ-M ORBS Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697506436276},{"id":179943,"code":"175604613129423199f61fda5ffe3615","title":"Binance Futures Will Launch USDⓈ-M BOND Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697345978273},{"id":179775,"code":"b4eb91b68a1a4dc1b2a2f45d7b8f1a1e","title":"Binance Adds NTRN on Margin","type":1,"releaseDate":1697173875790},{"id":179699,"code":"d956c31e085444c2ba4d97c554318476","title":"Binance Futures Will Launch USDⓈ-M BIGTIME Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697109442199}]'
            # previous_articles_json = '[{"id":181528,"code":"5e5eab2a19d444898e6961ba33d04849","title":"Binance Futures Will Launch USDⓈ-M TIA Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698768499741},{"id":181463,"code":"5d8c7476197344d087b5af436bfc74ae","title":"Binance Futures Will Launch USDⓈ-M SLP Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698731158402},{"id":181434,"code":"4492f05f8b0e40f2a6dc9321aba0ba27","title":"Binance Will List Celestia (TIA) with Seed Tag Applied","type":1,"releaseDate":1698671932206},{"id":181387,"code":"8e7a24082b4f4ab39229b05cadbfce0a","title":"Binance Adds ACA, GHST, VIDT and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1698638428354},{"id":181301,"code":"90ccca2c5d6946ef9439dae41a517578","title":"Introducing Memecoin (MEME) on Binance Launchpool! Farm MEME by Staking BNB, TUSD and FDUSD","type":1,"releaseDate":1698415749172},{"id":181213,"code":"c40a1707de63466f9aa14fd046c75e81","title":"Binance Futures Will Launch USDⓈ-M POWR Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698321002985},{"id":180971,"code":"6cdb1faca0e44c188ab680494c3bfa11","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-26","type":1,"releaseDate":1698204603826},{"id":180905,"code":"d8b596b131b64130940798961d73a8b5","title":"Binance Futures Will Launch USDⓈ-M POLYX and GAS Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1698151948683},{"id":180616,"code":"cdeaa008a1484ba0974f4359a31d29c3","title":"Binance Futures Will Launch USDⓈ-M RIF Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697862003215},{"id":180345,"code":"21802d4be7ce4e4a880e2990a6775422","title":"Binance Futures Will Launch USDⓈ-M BSV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697771703998},{"id":180281,"code":"afd04e47bab84bdab855f7698bf40fb5","title":"Binance Adds ARK, OMG \u0026 More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1697688013854},{"id":180188,"code":"b68013d4a1b14c82bb019eabcc13391a","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-19","type":1,"releaseDate":1697612405894},{"id":180152,"code":"5d2d3a74fe6c4c89ac8eaac2959383d6","title":"Binance Futures Will Launch USDⓈ-M STPT and WAXP Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1697606833266},{"id":180014,"code":"93710257326b4f33aed7d8b7b73746d1","title":"Binance Futures Will Launch USDⓈ-M ORBS Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697506436276},{"id":179943,"code":"175604613129423199f61fda5ffe3615","title":"Binance Futures Will Launch USDⓈ-M BOND Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697345978273},{"id":179775,"code":"b4eb91b68a1a4dc1b2a2f45d7b8f1a1e","title":"Binance Adds NTRN on Margin","type":1,"releaseDate":1697173875790},{"id":179699,"code":"d956c31e085444c2ba4d97c554318476","title":"Binance Futures Will Launch USDⓈ-M BIGTIME Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697109442199}]'
            # previous_articles_json = '[{"id":181463,"code":"5d8c7476197344d087b5af436bfc74ae","title":"Binance Futures Will Launch USDⓈ-M SLP Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698731158402},{"id":181434,"code":"4492f05f8b0e40f2a6dc9321aba0ba27","title":"Binance Will List Celestia (TIA) with Seed Tag Applied","type":1,"releaseDate":1698671932206},{"id":181387,"code":"8e7a24082b4f4ab39229b05cadbfce0a","title":"Binance Adds ACA, GHST, VIDT and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1698638428354},{"id":181301,"code":"90ccca2c5d6946ef9439dae41a517578","title":"Introducing Memecoin (MEME) on Binance Launchpool! Farm MEME by Staking BNB, TUSD and FDUSD","type":1,"releaseDate":1698415749172},{"id":181213,"code":"c40a1707de63466f9aa14fd046c75e81","title":"Binance Futures Will Launch USDⓈ-M POWR Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698321002985},{"id":180971,"code":"6cdb1faca0e44c188ab680494c3bfa11","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-26","type":1,"releaseDate":1698204603826},{"id":180905,"code":"d8b596b131b64130940798961d73a8b5","title":"Binance Futures Will Launch USDⓈ-M POLYX and GAS Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1698151948683},{"id":180616,"code":"cdeaa008a1484ba0974f4359a31d29c3","title":"Binance Futures Will Launch USDⓈ-M RIF Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697862003215},{"id":180345,"code":"21802d4be7ce4e4a880e2990a6775422","title":"Binance Futures Will Launch USDⓈ-M BSV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697771703998},{"id":180281,"code":"afd04e47bab84bdab855f7698bf40fb5","title":"Binance Adds ARK, OMG \u0026 More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1697688013854},{"id":180188,"code":"b68013d4a1b14c82bb019eabcc13391a","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-19","type":1,"releaseDate":1697612405894},{"id":180152,"code":"5d2d3a74fe6c4c89ac8eaac2959383d6","title":"Binance Futures Will Launch USDⓈ-M STPT and WAXP Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1697606833266},{"id":180014,"code":"93710257326b4f33aed7d8b7b73746d1","title":"Binance Futures Will Launch USDⓈ-M ORBS Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697506436276},{"id":179943,"code":"175604613129423199f61fda5ffe3615","title":"Binance Futures Will Launch USDⓈ-M BOND Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697345978273},{"id":179775,"code":"b4eb91b68a1a4dc1b2a2f45d7b8f1a1e","title":"Binance Adds NTRN on Margin","type":1,"releaseDate":1697173875790},{"id":179699,"code":"d956c31e085444c2ba4d97c554318476","title":"Binance Futures Will Launch USDⓈ-M BIGTIME Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697109442199}]'
            # self.previous_articles = '[{"id":181836,"code":"b8ace6ade44740e6afc21a3e355fdac1","title":"Binance Adds TIA, SNT, STEEM and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1698918303755}]'
            # TODO. Почему мы хард кодим предыдущие статьи, а не берем их из базы? - Чтобы была хотя бы одна "новая" новость, на которой можно проверить работу программы
            # self.previous_articles = '[{"id":183700,"code":"7b3f500e0eec40f380023b4ff0ccca18","title":"Binance Futures Will Launch USDⓈ-M 1000BONK and PYTH Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1700649023889}, {"id":183670,"code":"399c3f8b867141eebf84c86b3d66ae7b","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-11-23","type":1,"releaseDate":1700638507088},{"id":183519,"code":"8294e4e62bf5459fb6035156437ab995","title":"Binance Adds CVC, ELF, FARM \u0026 More Pairs on Cross Margin and Isolated Margin","type":1,"releaseDate":1700532306626},{"id":183383,"code":"25c05ab82d674c7396eab887d1384b05","title":"Binance Futures Will Launch USDⓈ-M BEAMX Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1700203809901},{"id":183310,"code":"104db5d54d024410bfb3ec21b33aa010","title":"Binance Adds ACA, AMP, GHST \u0026 More Pairs on Cross Margin and Isolated Margin","type":1,"releaseDate":1700187322012},{"id":183275,"code":"7cda5be3429d4e1da2ad8e23c120a7fb","title":"Binance Futures Will Launch USDⓈ-M KAS Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1700141887548},{"id":183194,"code":"1280c17d1e504bbf86b7a85ca6ae3649","title":"Binance Adds BEAMX and More Pairs on Cross Margin and Isolated Margin","type":1,"releaseDate":1700104203117},{"id":183037,"code":"c2a6e8df46de4105b0ccb607b6260b8c","title":"Notice on New Trading Pairs on Binance Spot - 2023-11-16","type":1,"releaseDate":1700035809038},{"id":182945,"code":"d7e84d0cbade4525bd55e61e7ee0f83a","title":"Binance Futures Will Launch USDⓈ-M MBL Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699956293099},{"id":182853,"code":"d79d3c8148194528865eff197578f803","title":"Binance Adds FIS and More Pairs on Cross Margin","type":1,"releaseDate":1699933803477},{"id":182837,"code":"ef915dd89edb4fa7a7438362bfb146d2","title":"Binance Futures Will Launch USDⓈ-M NTRN Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699929174947},{"id":182707,"code":"7af5eefa0e1c433c996aadce389bafe5","title":"Binance Futures Will Launch USDⓈ-M ILV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699613867763},{"id":182569,"code":"ed2fd215f6884f14a0a321e70f1fa5be","title":"Binance Futures Will Launch USDⓈ-M BADGER Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699503088430},{"id":182549,"code":"995efa57e37241a6a73c9e1fcd9e4ced","title":"Binance Adds AST, GNO, ORDI and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1699499194853},{"id":182452,"code":"742c9bbb9ebf4f68b0ca372615e86ee7","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-11-09","type":1,"releaseDate":1699437614062},{"id":182420,"code":"cc99eaae257f4443bfcee68d39092620","title":"Binance Futures Will Launch USDⓈ-M STEEM Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699431187566},{"id":182171,"code":"75e3a7471697451c8ef75c037f93082a","title":"Binance Adds MEME, MULTI, UFT and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1699346703988},{"id":182201,"code":"5b64c7eaf295445584f222adfbf8d723","title":"Binance Futures Will Launch USDⓈ-M ORDI Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699342203152},{"id":182168,"code":"4bd64404aa384fe5a00e0f9b131035db","title":"Binance Will List ORDI (ORDI) with Seed Tag Applied","type":1,"releaseDate":1699339453500},{"id":181951,"code":"d047f1923f8a40be8aedcc74387f09dc","title":"Binance Futures Will Launch USDⓈ-M TOKEN Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699008602884}]'
            # self.previous_articles = '[{"id":183700,"code":"7b3f500e0eec40f380023b4ff0ccca18","title":"Binance Futures Will Launch USDⓈ-M 1000BONK and PYTH Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1700649023889}, {"id":183670,"code":"399c3f8b867141eebf84c86b3d66ae7b","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-11-23","type":1,"releaseDate":1700638507088},{"id":183519,"code":"8294e4e62bf5459fb6035156437ab995","title":"Binance Adds CVC, ELF, FARM \u0026 More Pairs on Cross Margin and Isolated Margin","type":1,"releaseDate":1700532306626},{"id":183383,"code":"25c05ab82d674c7396eab887d1384b05","title":"Binance Futures Will Launch USDⓈ-M BEAMX Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1700203809901},{"id":183310,"code":"104db5d54d024410bfb3ec21b33aa010","title":"Binance Adds ACA, AMP, GHST \u0026 More Pairs on Cross Margin and Isolated Margin","type":1,"releaseDate":1700187322012},{"id":183275,"code":"7cda5be3429d4e1da2ad8e23c120a7fb","title":"Binance Futures Will Launch USDⓈ-M KAS Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1700141887548},{"id":183194,"code":"1280c17d1e504bbf86b7a85ca6ae3649","title":"Binance Adds BEAMX and More Pairs on Cross Margin and Isolated Margin","type":1,"releaseDate":1700104203117},{"id":183037,"code":"c2a6e8df46de4105b0ccb607b6260b8c","title":"Notice on New Trading Pairs on Binance Spot - 2023-11-16","type":1,"releaseDate":1700035809038},{"id":182945,"code":"d7e84d0cbade4525bd55e61e7ee0f83a","title":"Binance Futures Will Launch USDⓈ-M MBL Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699956293099},{"id":182853,"code":"d79d3c8148194528865eff197578f803","title":"Binance Adds FIS and More Pairs on Cross Margin","type":1,"releaseDate":1699933803477},{"id":182837,"code":"ef915dd89edb4fa7a7438362bfb146d2","title":"Binance Futures Will Launch USDⓈ-M NTRN Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699929174947},{"id":182707,"code":"7af5eefa0e1c433c996aadce389bafe5","title":"Binance Futures Will Launch USDⓈ-M ILV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699613867763},{"id":182569,"code":"ed2fd215f6884f14a0a321e70f1fa5be","title":"Binance Futures Will Launch USDⓈ-M BADGER Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699503088430},{"id":182549,"code":"995efa57e37241a6a73c9e1fcd9e4ced","title":"Binance Adds AST, GNO, ORDI and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1699499194853},{"id":182452,"code":"742c9bbb9ebf4f68b0ca372615e86ee7","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-11-09","type":1,"releaseDate":1699437614062},{"id":182420,"code":"cc99eaae257f4443bfcee68d39092620","title":"Binance Futures Will Launch USDⓈ-M STEEM Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699431187566},{"id":182171,"code":"75e3a7471697451c8ef75c037f93082a","title":"Binance Adds MEME, MULTI, UFT and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1699346703988},{"id":182201,"code":"5b64c7eaf295445584f222adfbf8d723","title":"Binance Futures Will Launch USDⓈ-M ORDI Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699342203152},{"id":182168,"code":"4bd64404aa384fe5a00e0f9b131035db","title":"Binance Will List ORDI (ORDI) with Seed Tag Applied","type":1,"releaseDate":1699339453500},{"id":181951,"code":"d047f1923f8a40be8aedcc74387f09dc","title":"Binance Futures Will Launch USDⓈ-M TOKEN Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699008602884}]'
            # self.previous_articles = '[{"id":184042,"code":"0712d23fc1934e17996a8c7a58716d30","title":"Binance Futures Will Launch USDⓈ-M SUPER Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1700988341945},{"id":183919,"code":"85306854c60347a6a4131493ec8d26a6","title":"Binance Will List Blur (BLUR) with Seed Tag Applied","type":1,"releaseDate":1700806187186},{"id":183700,"code":"7b3f500e0eec40f380023b4ff0ccca18","title":"Binance Futures Will Launch USDⓈ-M 1000BONK and PYTH Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1700649023889},{"id":183670,"code":"399c3f8b867141eebf84c86b3d66ae7b","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-11-23","type":1,"releaseDate":1700638507088},{"id":183519,"code":"8294e4e62bf5459fb6035156437ab995","title":"Binance Adds CVC, ELF, FARM \u0026 More Pairs on Cross Margin and Isolated Margin","type":1,"releaseDate":1700532306626},{"id":183383,"code":"25c05ab82d674c7396eab887d1384b05","title":"Binance Futures Will Launch USDⓈ-M BEAMX Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1700203809901},{"id":183310,"code":"104db5d54d024410bfb3ec21b33aa010","title":"Binance Adds ACA, AMP, GHST \u0026 More Pairs on Cross Margin and Isolated Margin","type":1,"releaseDate":1700187322012},{"id":183275,"code":"7cda5be3429d4e1da2ad8e23c120a7fb","title":"Binance Futures Will Launch USDⓈ-M KAS Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1700141887548},{"id":183194,"code":"1280c17d1e504bbf86b7a85ca6ae3649","title":"Binance Adds BEAMX and More Pairs on Cross Margin and Isolated Margin","type":1,"releaseDate":1700104203117},{"id":183037,"code":"c2a6e8df46de4105b0ccb607b6260b8c","title":"Notice on New Trading Pairs on Binance Spot - 2023-11-16","type":1,"releaseDate":1700035809038},{"id":182945,"code":"d7e84d0cbade4525bd55e61e7ee0f83a","title":"Binance Futures Will Launch USDⓈ-M MBL Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699956293099},{"id":182853,"code":"d79d3c8148194528865eff197578f803","title":"Binance Adds FIS and More Pairs on Cross Margin","type":1,"releaseDate":1699933803477},{"id":182837,"code":"ef915dd89edb4fa7a7438362bfb146d2","title":"Binance Futures Will Launch USDⓈ-M NTRN Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699929174947},{"id":182707,"code":"7af5eefa0e1c433c996aadce389bafe5","title":"Binance Futures Will Launch USDⓈ-M ILV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699613867763},{"id":182569,"code":"ed2fd215f6884f14a0a321e70f1fa5be","title":"Binance Futures Will Launch USDⓈ-M BADGER Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699503088430},{"id":182549,"code":"995efa57e37241a6a73c9e1fcd9e4ced","title":"Binance Adds AST, GNO, ORDI and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1699499194853},{"id":182452,"code":"742c9bbb9ebf4f68b0ca372615e86ee7","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-11-09","type":1,"releaseDate":1699437614062},{"id":182420,"code":"cc99eaae257f4443bfcee68d39092620","title":"Binance Futures Will Launch USDⓈ-M STEEM Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699431187566}]'
            i = 0
            fails = 0

            times = []
            max_attempts = 10
            self.previous_articles = self.initial_parser()
            # self.previous_articles = '[{"id":185030,"code":"84ca9ad73b3643beba825689409e053a","title":"Notice on New Trading Pairs on Binance Spot - 2023-12-05","type":1,"releaseDate":1701684035267},{"id":184909,"code":"e1f106b5767546faa4c16751d8410a89","title":"Binance Will List Anchored Coins EUR (AEUR) and Introduce AEUR Zero Trading Fee Promotions","type":1,"releaseDate":1701663251934},{"id":184701,"code":"1bbc5f62d1444d7197e4a3bbf27f28c2","title":"Binance Adds GFT \u0026 More Pairs on Cross Margin and Isolated Margin","type":1,"releaseDate":1701403803065},{"id":184341,"code":"72a2e4427f84455d8d0bbd0a0f4e557a","title":"Notice on New Trading Pairs on Binance Spot - 2023-11-30","type":1,"releaseDate":1701234023462},{"id":184271,"code":"57d1c97e35d84f278b071bd092626f51","title":"Binance Futures Will Launch USDⓈ-M ETHW Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1701154262129},{"id":184222,"code":"7eac169f9d4041bc8c5955778ca85467","title":"Binance Adds BLUR, VIC \u0026 More Pairs on Cross Margin and Isolated Margin","type":1,"releaseDate":1701137106893},{"id":184205,"code":"fc5b48ff9a6f4d01abd2acff0eee0c83","title":"Binance Futures Will Launch USDⓈ-M ONG Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1701081932675},{"id":184139,"code":"91deccb2e146483383617db8b8fcaba1","title":"Binance Futures Will Launch USDⓈ-M USTC Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1701066903333},{"id":184042,"code":"0712d23fc1934e17996a8c7a58716d30","title":"Binance Futures Will Launch USDⓈ-M SUPER Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1700988341945},{"id":183919,"code":"85306854c60347a6a4131493ec8d26a6","title":"Binance Will List Blur (BLUR) with Seed Tag Applied","type":1,"releaseDate":1700806187186},{"id":183700,"code":"7b3f500e0eec40f380023b4ff0ccca18","title":"Binance Futures Will Launch USDⓈ-M 1000BONK and PYTH Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1700649023889},{"id":183670,"code":"399c3f8b867141eebf84c86b3d66ae7b","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-11-23","type":1,"releaseDate":1700638507088},{"id":183519,"code":"8294e4e62bf5459fb6035156437ab995","title":"Binance Adds CVC, ELF, FARM \u0026 More Pairs on Cross Margin and Isolated Margin","type":1,"releaseDate":1700532306626},{"id":183383,"code":"25c05ab82d674c7396eab887d1384b05","title":"Binance Futures Will Launch USDⓈ-M BEAMX Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1700203809901},{"id":183310,"code":"104db5d54d024410bfb3ec21b33aa010","title":"Binance Adds ACA, AMP, GHST \u0026 More Pairs on Cross Margin and Isolated Margin","type":1,"releaseDate":1700187322012},{"id":183275,"code":"7cda5be3429d4e1da2ad8e23c120a7fb","title":"Binance Futures Will Launch USDⓈ-M KAS Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1700141887548},{"id":183194,"code":"1280c17d1e504bbf86b7a85ca6ae3649","title":"Binance Adds BEAMX and More Pairs on Cross Margin and Isolated Margin","type":1,"releaseDate":1700104203117},{"id":183037,"code":"c2a6e8df46de4105b0ccb607b6260b8c","title":"Notice on New Trading Pairs on Binance Spot - 2023-11-16","type":1,"releaseDate":1700035809038},{"id":182945,"code":"d7e84d0cbade4525bd55e61e7ee0f83a","title":"Binance Futures Will Launch USDⓈ-M MBL Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1699956293099}]'
            print('PREV ARTICLES: ', self.previous_articles)
            asyncio.run(self.telegram_bot.sendMessageDebug(self.previous_articles))
            while True:
                print('-----',i,'-----')
                if i == 60:
                    asyncio.run(self.telegram_bot.sendMessageDebug('Парсер NewListingsParser исправно функционирует.'))
                    i = 0
                # if i < 10:
                    # asyncio.run(self.telegram_bot.sendMessageDebug('Парсер NewListingsParser исправно функционирует.'))
                attempts = 0
                i += 1
                start_time = time.time()

                while attempts < max_attempts:
                    try:
                        pa, output = self.master_parser()
                        # asyncio.run(self.telegram_bot.sendMessageDebug(output))

                        if output == -11:
                            print(
                                f"Ошибка интернет соединения: Error HTTPSConnectionPool(host='www.binance.com', port=443): Max retries exceeded with url. \n Попытка перезапуска: {attempts + 1}/{max_attempts}.")
                            # logging.info(
                                # f"Ошибка интернет соединения: Error HTTPSConnectionPool(host='www.binance.com', port=443): Max retries exceeded with url. Попытка перезапуска: {attempts + 1}/{max_attempts}.")
                            asyncio.run(self.telegram_bot.sendMessageDebug(
                                f"Ошибка интернет соединения: Error HTTPSConnectionPool(host='www.binance.com', port=443): Max retries exceeded with url. Попытка перезапуска: {attempts + 1}/{max_attempts}."))
                            attempts += 1
                            time.sleep(5)

                            if attempts >= max_attempts:
                                print(
                                    'Переподключение не удалось. Достигнуто максимальное количество попыток. Работа парсера завершена.')
                                # logging.info(
                                    # 'Переподключение не удалось. Достигнуто максимальное количество попыток. Работа парсера завершена.')
                                asyncio.run(self.telegram_bot.sendMessageDebug(
                                    'Переподключение не удалось. Достигнуто максимальное количество попыток. Работа парсера завершена.'))
                                break
                        if output != -11:
                            break
                    except Exception as e:
                        print(f"Ошибка master_parser в main: {e}")
                        # logging.info(f"Ошибка master_parser в main: {e}")
                        asyncio.run(self.telegram_bot.sendMessageDebug(f"Ошибка master_parser в main: {e}"))

                end_time = time.time()

                # logging.info(
                    # f'Запрос {i}: {start_time} - {end_time} ({end_time - start_time})')  # Логирование времени обработки запроса
                # logging.info(f'Вывод {output}')  # Вывода

                print('OUTPUT: ', output)

                if output != 429 and output != [] and output != -11:
                    asyncio.run(self.telegram_bot.sendMessageDebug(output))
                    asyncio.run(self.telegram_bot.sendMessageDebug(
                        f'❗️Найдена новая новость!❗️ \n Время запроса и обработки:  from {datetime.utcfromtimestamp(start_time)} \n  to {datetime.utcfromtimestamp(end_time)} \n  ({end_time - start_time} sec)'))
                    
                    for i in range(len(output[0])):
                        if 'Another' in output[1][i]:
                            # asyncio.run(self.telegram_bot.sendMessageDebug(
                                # f"Время выхода новости: {datetime.utcfromtimestamp(int(output[0][i]) / 1000)} \n Новость незнакомого формата. \n Текст новости: {output[1][i][8:]} Ссылка на новость: {output[6]}"))
                            asyncio.run(self.telegram_bot.sendMessageDebug(
                            f"Время выхода новости: {datetime.utcfromtimestamp(int(self.news_release_date[i]) / 1000)} \n Новость незнакомого формата. \n Текст новости: {self.text_news} Ссылка на новость: {self.next_link}"))

                        elif output[5]:
                            # asyncio.run(self.telegram_bot.sendMessageDebug(
                                # f"Время выхода новости: {datetime.utcfromtimestamp(int(output[0][i]) / 1000)} \n Текст новости {self.text_news} \n Тип новости: {output[1][i]} \n Токен: {output[2][i]} \n Начало торгов: {output[3][i]} \n Биржа для открытия лонга: {output[4][i][0]} \n Тип контракта: {output[4][i][1]} \n Ссылка на новость: {output[6]}"))
                            if REAL_TRADING is True:
                                asyncio.run(self.telegram_bot.sendMessage(
                                    f'❗️Найдена новая новость!❗️ \n Время запроса и обработки:  from {datetime.utcfromtimestamp(start_time)} \n  to {datetime.utcfromtimestamp(end_time)} \n  ({end_time - start_time} sec)'))
                            asyncio.run(self.telegram_bot.sendMessageDebug(
                                f"Время выхода новости: {datetime.utcfromtimestamp(int(self.news_release_date[i]) / 1000)}\n Текст новости {self.text_news}  \n Тип новости: {self.listing_type[i]} \n Токен: {self.ticker[i]} \n Начало торгов: {self.listing_date[i]} \n Биржа для открытия лонга: {self.prior_exchange[i][0]} \n Тип контракта: {self.prior_exchange[i][1]} \n Ссылка на новость: {self.next_link}"))
                            if REAL_TRADING is True:
                                asyncio.run(self.telegram_bot.sendMessage(
                                    f"Время выхода новости: {datetime.utcfromtimestamp(int(self.news_release_date[i]) / 1000)}\n Текст новости {self.text_news}  \n Тип новости: {self.listing_type[i]} \n Токен: {self.ticker[i]} \n Начало торгов: {self.listing_date[i]} \n Биржа для открытия лонга: {self.prior_exchange[i][0]} \n Тип контракта: {self.prior_exchange[i][1]} \n Ссылка на новость: {self.next_link}"))

                            self.writeIntoDataBase(listing_date=self.listing_date[i],listing_type=self.listing_type[i],ticker=self.ticker[i],release_date=self.news_release_date[i],prior_exchange=self.prior_exchange[i][0],market=self.prior_exchange[i][1],news_title=self.text_news)

                        elif not output[5]:
                            if REAL_TRADING is True:
                                asyncio.run(self.telegram_bot.sendMessage(
                                    f'❗️Найдена новая новость!❗️ \n Время запроса и обработки:  from {datetime.utcfromtimestamp(start_time)} \n  to {datetime.utcfromtimestamp(end_time)} \n  ({end_time - start_time} sec)'))
                            asyncio.run(self.telegram_bot.sendMessageDebug(
                                f"Время выхода новости: {datetime.utcfromtimestamp(int(output[0][i]) / 1000)} \n Текст новости {self.text_news} \n Тип листинга: {self.listing_type[i]}  \n Токен: {output[2][i]}  (не листится торговая пара с USDT -  не открываем позицию) \n Начало торгов: {output[3][i]} \n Биржа для открытия лонга: {output[4][i][0]} \n Тип контракта: {output[4][i][1]} \n Ссылка на новость: {output[6]}"))
                            if REAL_TRADING is True:
                                asyncio.run(self.telegram_bot.sendMessage(
                                    f"Время выхода новости: {datetime.utcfromtimestamp(int(output[0][i]) / 1000)} \n Текст новости {self.text_news} \n Тип листинга: {self.listing_type[i]}  \n Токен: {output[2][i]}  (не листится торговая пара с USDT -  не открываем позицию) \n Начало торгов: {output[3][i]} \n Биржа для открытия лонга: {output[4][i][0]} \n Тип контракта: {output[4][i][1]} \n Ссылка на новость: {output[6]}"))
                            # self.writeIntoDataBase(listing_date=self.listing_date[i],listing_type=self.listing_type[i],ticker=self.ticker[i],release_date=self.news_release_date[i],prior_exchange=self.prior_exchange[i][0],market=self.prior_exchange[i][1],news_title=self.text_news[i])

                # print('!!!!')
                if output == 429:
                    fails += 1
                times.append(end_time - start_time)
                print(f"Время и обработки выполнения запроса: {end_time - start_time} секунд")
                time.sleep(60)
                # logging.info(f'Среднее время на запрос: {np.mean(times)}, количество ошибок: {fails}')

        except KeyboardInterrupt:
            asyncio.run(self.telegram_bot.sendMessageDebug("Парсер новостей остановлен вручную"))

        except Exception as e:
            print(f"Произошла ошибка в main: {e}")
            # logging.info(f"Произошла ошибка: {e}. Парсер новостей остановлен.")
            asyncio.run(self.telegram_bot.sendMessageDebug(f"Произошла ошибка : {e}. Парсер новостей остановлен."))



warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

if __name__ == "__main__":
    bot_instance = NotificationsBot()
    asyncio.run(bot_instance.sendMessageDebug('Запуск NewListingsParser.'))
    time.sleep(180)
    url = "https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48"
    ob = NewListingsParser(url, bot=bot_instance)
    ob.main()
    # main()
