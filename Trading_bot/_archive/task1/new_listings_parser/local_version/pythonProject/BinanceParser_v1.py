import requests
import json
import time
from datetime import datetime
import re
import hmac
import hashlib
from bs4 import BeautifulSoup
import logging
import numpy as np
from IsTickerOnExchange import check_token
from Notifications import send_telegram_message
import asyncio

from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext


prev = '[{"id":181463,"code":"5d8c7476197344d087b5af436bfc74ae","title":"Binance Futures Will Launch USDⓈ-M SLP Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698731158402},{"id":181434,"code":"4492f05f8b0e40f2a6dc9321aba0ba27","title":"Binance Will List Celestia (TIA) with Seed Tag Applied","type":1,"releaseDate":1698671932206},{"id":181387,"code":"8e7a24082b4f4ab39229b05cadbfce0a","title":"Binance Adds ACA, GHST, VIDT and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1698638428354},{"id":181301,"code":"90ccca2c5d6946ef9439dae41a517578","title":"Introducing Memecoin (MEME) on Binance Launchpool! Farm MEME by Staking BNB, TUSD and FDUSD","type":1,"releaseDate":1698415749172},{"id":181213,"code":"c40a1707de63466f9aa14fd046c75e81","title":"Binance Futures Will Launch USDⓈ-M POWR Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698321002985},{"id":180971,"code":"6cdb1faca0e44c188ab680494c3bfa11","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-26","type":1,"releaseDate":1698204603826},{"id":180905,"code":"d8b596b131b64130940798961d73a8b5","title":"Binance Futures Will Launch USDⓈ-M POLYX and GAS Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1698151948683},{"id":180616,"code":"cdeaa008a1484ba0974f4359a31d29c3","title":"Binance Futures Will Launch USDⓈ-M RIF Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697862003215},{"id":180345,"code":"21802d4be7ce4e4a880e2990a6775422","title":"Binance Futures Will Launch USDⓈ-M BSV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697771703998},{"id":180281,"code":"afd04e47bab84bdab855f7698bf40fb5","title":"Binance Adds ARK, OMG \u0026 More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1697688013854},{"id":180188,"code":"b68013d4a1b14c82bb019eabcc13391a","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-19","type":1,"releaseDate":1697612405894},{"id":180152,"code":"5d2d3a74fe6c4c89ac8eaac2959383d6","title":"Binance Futures Will Launch USDⓈ-M STPT and WAXP Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1697606833266},{"id":180014,"code":"93710257326b4f33aed7d8b7b73746d1","title":"Binance Futures Will Launch USDⓈ-M ORBS Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697506436276},{"id":179943,"code":"175604613129423199f61fda5ffe3615","title":"Binance Futures Will Launch USDⓈ-M BOND Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697345978273},{"id":179775,"code":"b4eb91b68a1a4dc1b2a2f45d7b8f1a1e","title":"Binance Adds NTRN on Margin","type":1,"releaseDate":1697173875790},{"id":179699,"code":"d956c31e085444c2ba4d97c554318476","title":"Binance Futures Will Launch USDⓈ-M BIGTIME Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697109442199},{"id":179392,"code":"59cba52c3bab4059897ae88d9bbb31cf","title":"Binance Futures Will Launch USDⓈ-M LOOM Perpetual Contract With Up to 10x Leverage","type":1,"releaseDate":1696997177546},{"id":179364,"code":"9ef0c43e0c06499a8cca5081883825c8","title":"Binance Adds ADA/FDUSD, FIL/FDUSD, FRONT/TUSD, LEVER/TRY, LTC/FDUSD, RUNE/TUSD \u0026 TRB/TRY Trading Pairs","type":1,"releaseDate":1696993228097},{"id":179344,"code":"01c84ac73fb442bdbeb2463ade2347f6","title":"Binance Adds New SEI \u0026 WBETH Pairs on Cross Margin","type":1,"releaseDate":1696990532517},{"id":179161,"code":"b64ac7bcfca54d2b8042c7aa0cfc5afe","title":"Binance Futures Will Launch USDⓈ-M STRAX Perpetual Contract With Up to 10x Leverage","type":1,"releaseDate":1696936465219}]'
def convert_title_into_link(text,code):
    lower_case_text = text.lower()
    hyphenated_text = lower_case_text.replace(' ', '-')
    return 'https://www.binance.com/en/support/announcement/'+hyphenated_text+'-'+code


def parse_announcement_table(url):
    response = requests.get(url)
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

    return data_dict

# data = parse_announcement_table(
#     'https://www.binance.com/en/support/announcement/binance-futures-will-launch-usd%E2%93%A2-m-powr-perpetual-contract-with-up-to-50x-leverage-c40a1707de63466f9aa14fd046c75e81')
# Выводим словарь с данными
# for key, value in data.items():
#     print(f"{key}: {value}")

def parse_announcement_table_futures(url):
    response = requests.get(url)
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
                key = None
                values = []

                for row in rows:
                    # Извлекаем текст из ячеек (td) в текущей строке
                    cells = row.find_all('td')
                    if key:
                        data_dict[key] = values
                    if len(cells) >= 2:
                        key = cells[0].text.strip()
                        values = [cell.text.strip() for cell in cells[1:]]
                    else:
                        key = None  # Сбрасываем ключ, если не хватает столбцов

                if key:
                    data_dict[key] = values

            else:
                print("Element with class 'bn-table-tbody' not found in the table.")
        else:
            print("Table with style 'table-layout:auto' not found on the page.")
    else:
        print(f"Request failed with status code {response.status_code}")

    cleaned_data_dict = {}

    for key, value in data_dict.items():
        cleaned_key = key.replace('\xa0', ' ')
        cleaned_value = value[0].replace('\xa0', ' ')
        cleaned_data_dict[cleaned_key] = [cleaned_value]

    return cleaned_data_dict


def parse_announcement_table_spot(url):
    data = {}
    is_stable_coin = False
    is_new_spot_pair = False
    is_pairs_with_usdt = False
    is_error = False
    # is_pairs_with_busd = False

    response = requests.get(url)
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
            data['Underlying Asset'] = re.findall(r'(\w+)/USDT', part2_array[0])
            if data['Underlying Asset'] == []:
                print('Совпадений не найдено. Ошибка в парсинге. parse_announcement_table_spot')
                is_error = True
            print('Список токенов в паре с USDT: ', data['Underlying Asset'])

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

    return is_error, data


def master_parser(url, previous_articles_json):
    is_with_usdt = False
    response = requests.get(url)

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

                for i in range(len(new_articles)):
                    print('---------------------------------')
                    print('Обработка ', i + 1, '-й новой записи!')

                    if 'Binance Futures Will Launch USDⓈ-M' in new_articles[i]['title']:
                        print('    Новость о листинге фьючерсов')

                        link = convert_title_into_link(new_articles[i]['title'], new_articles[i]['code'])

                        data = parse_announcement_table_futures(link)  ### именно для фьючей

                        if 'USDT' in data['Settlement Asset']:
                            is_with_usdt = True

                        data['News Time'] = [str(new_articles[i]['releaseDate'])]
                        data['News Type'] = ['Futures Listing']
                        prior_exchange = check_token(data['Underlying Asset'][0]+'USDT')
                        data['Exchange, market'] = prior_exchange
                        data['is_pair_with_usdt'] = is_with_usdt

                        # for key, value in data.items():
                        #     print(f"{key}: {value}")
                        # print(data)

                        print('    Дата выхода новости: ',
                              datetime.utcfromtimestamp(new_articles[i]['releaseDate'] / 1000))
                        print('    Тип новости: ', data['News Type'])
                        print('    Тикер токена: ', data['Underlying Asset'])
                        print('    Дата и время старта торгов: ', data['Launch Time'])
                        print('    Ссылка на страницу новости: ', link)
                        print(f'    Приоритетная биржа: {prior_exchange[0]}, рынок {prior_exchange[1]}')
                        print(f'    Листинг пары с USDT? {is_with_usdt}')

                    elif 'Binance Will List ' in new_articles[i]['title']:
                        print('    Новость о листинге на споте')

                        link = convert_title_into_link(new_articles[i]['title'], new_articles[i]['code'])

                        _, data = parse_announcement_table_spot(link)  ### именно для спота

                        # print(data)

                        prior_exchange = check_token(data['Underlying Asset'][0]+'USDT')

                        data['News Time'] = [str(new_articles[i]['releaseDate'])]
                        data['News Type'] = ['Spot Listing']
                        data['Exchange, market'] = prior_exchange

                        # for key, value in data.items():
                        #     print(f"{key}: {value}")

                        print('    Дата выхода новости: ',
                              datetime.utcfromtimestamp(new_articles[i]['releaseDate'] / 1000))
                        print('    Тип новости: ', data['News Type'])
                        print('    Тикер токена: ', data['Underlying Asset'])
                        print('    Дата и время старта торгов: ', data['Launch Time'])
                        print('    Ссылка на страницу новости: ', link)
                        print(f'    Приоритетная биржа: {prior_exchange[0]}, рынок {prior_exchange[1]}')
                        print(f'    Листинг пары с USDT? {data["is_pair_with_usdt"]}')



                    else:
                        data = {}
                        link = convert_title_into_link(new_articles[i]['title'], new_articles[i]['code'])
                        data['News Time'] = [str(new_articles[i]['releaseDate'])]
                        data['News Type'] = f"Another: {new_articles[i]['title']}"
                        data['Underlying Asset'] = '_'
                        data['Launch Time'] = '_'
                        data['Exchange, market'] = '_'
                        data['is_pair_with_usdt'] = '_'

                        print('    Новость о не о листинге на фьючерсах или споте. Текст новости: ',
                              new_articles[i]['title'])

                previous_articles_json = articles_json
                return previous_articles_json, [data['News Time'], data['News Type'], data['Underlying Asset'],
                                                data['Launch Time'], data['Exchange, market'], data['is_pair_with_usdt'], link]

            except json.JSONDecodeError as e:
                print("Ошибка при парсинге JSON:", e)
        previous_articles_json = articles_json
        return previous_articles_json, []

    else:
        print("Не удалось получить доступ к странице. Код состояния:", response.status_code)
        time.sleep(30)
        return previous_articles_json, 429

# добавить обработку поверок. передавать добавочный актив с помощью флага is_usdt, чтобы потом использовать для входа в позицию.

# Функция для обработки команды /start в Telegram
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Парсер новостей запущен.")

    # Запустите ваш асинхронный код в фоновом режиме
    asyncio.create_task(run_existing_code())

# Функция для обработки команды /stop в Telegram
def stop(update: Update, context: CallbackContext):
    update.message.reply_text("Парсер новостей остановлен.")

async def run_existing_code():
    asyncio.run(send_telegram_message('Парсер новостной страницы запущен.'))
    log_file = 'logfile.log'
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info('----SCRIPT IS STARTED----')  # Логирование времени обработки запроса
    url = "https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48"
    # previous_articles_json = '[]'
    previous_articles_json = '[{"id":181434,"code":"4492f05f8b0e40f2a6dc9321aba0ba27","title":"Binance Will List Celestia (TIA) with Seed Tag Applied","type":1,"releaseDate":1698671932206},{"id":181387,"code":"8e7a24082b4f4ab39229b05cadbfce0a","title":"Binance Adds ACA, GHST, VIDT and More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1698638428354},{"id":181301,"code":"90ccca2c5d6946ef9439dae41a517578","title":"Introducing Memecoin (MEME) on Binance Launchpool! Farm MEME by Staking BNB, TUSD and FDUSD","type":1,"releaseDate":1698415749172},{"id":181213,"code":"c40a1707de63466f9aa14fd046c75e81","title":"Binance Futures Will Launch USDⓈ-M POWR Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1698321002985},{"id":180971,"code":"6cdb1faca0e44c188ab680494c3bfa11","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-26","type":1,"releaseDate":1698204603826},{"id":180905,"code":"d8b596b131b64130940798961d73a8b5","title":"Binance Futures Will Launch USDⓈ-M POLYX and GAS Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1698151948683},{"id":180616,"code":"cdeaa008a1484ba0974f4359a31d29c3","title":"Binance Futures Will Launch USDⓈ-M RIF Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697862003215},{"id":180345,"code":"21802d4be7ce4e4a880e2990a6775422","title":"Binance Futures Will Launch USDⓈ-M BSV Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697771703998},{"id":180281,"code":"afd04e47bab84bdab855f7698bf40fb5","title":"Binance Adds ARK, OMG \u0026 More Pairs on Cross Margin \u0026 Isolated Margin","type":1,"releaseDate":1697688013854},{"id":180188,"code":"b68013d4a1b14c82bb019eabcc13391a","title":"Notice on New Trading Pairs \u0026 Trading Bots Services on Binance Spot - 2023-10-19","type":1,"releaseDate":1697612405894},{"id":180152,"code":"5d2d3a74fe6c4c89ac8eaac2959383d6","title":"Binance Futures Will Launch USDⓈ-M STPT and WAXP Perpetual Contracts With Up to 50x Leverage","type":1,"releaseDate":1697606833266},{"id":180014,"code":"93710257326b4f33aed7d8b7b73746d1","title":"Binance Futures Will Launch USDⓈ-M ORBS Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697506436276},{"id":179943,"code":"175604613129423199f61fda5ffe3615","title":"Binance Futures Will Launch USDⓈ-M BOND Perpetual Contract With Up to 50x Leverage","type":1,"releaseDate":1697345978273},{"id":179775,"code":"b4eb91b68a1a4dc1b2a2f45d7b8f1a1e","title":"Binance Adds NTRN on Margin","type":1,"releaseDate":1697173875790},{"id":179699,"code":"d956c31e085444c2ba4d97c554318476","title":"Binance Futures Will Launch USDⓈ-M BIGTIME Perpetual Contract With Up to 20x Leverage","type":1,"releaseDate":1697109442199},{"id":179392,"code":"59cba52c3bab4059897ae88d9bbb31cf","title":"Binance Futures Will Launch USDⓈ-M LOOM Perpetual Contract With Up to 10x Leverage","type":1,"releaseDate":1696997177546},{"id":179364,"code":"9ef0c43e0c06499a8cca5081883825c8","title":"Binance Adds ADA/FDUSD, FIL/FDUSD, FRONT/TUSD, LEVER/TRY, LTC/FDUSD, RUNE/TUSD \u0026 TRB/TRY Trading Pairs","type":1,"releaseDate":1696993228097},{"id":179344,"code":"01c84ac73fb442bdbeb2463ade2347f6","title":"Binance Adds New SEI \u0026 WBETH Pairs on Cross Margin","type":1,"releaseDate":1696990532517},{"id":179161,"code":"b64ac7bcfca54d2b8042c7aa0cfc5afe","title":"Binance Futures Will Launch USDⓈ-M STRAX Perpetual Contract With Up to 10x Leverage","type":1,"releaseDate":1696936465219}]'
    i = 0
    fails = 0

    start_time = time.time()
    pa, output = master_parser(url, previous_articles_json)
    end_time = time.time()

    logging.info(
        f'Запрос {i}: {start_time} - {end_time} ({end_time - start_time})')  # Логирование времени обработки запроса
    logging.info(f'Вывод {output}')  # Вывода
    if output != 429 and output != []:
        asyncio.run(send_telegram_message(
            f'Найдена новая новость! \n Время запроса и обработки: from {datetime.utcfromtimestamp(start_time)} to {datetime.utcfromtimestamp(end_time)} ({end_time - start_time} sec)'))
        asyncio.run(send_telegram_message(
            f"Время выхода новости: {datetime.utcfromtimestamp(int(output[0][0]) / 1000)} \n Тип новости: {output[1]} \n Токен: {output[2]} \n Начало торгов: {output[3]} \n Биржа для открытия лонга: {output[4]} \n Пара с USDT (про новость)?: {output[5]} \n Ссылка: {output[6]}"))

    times = []
    while True:
        # asyncio.run(send_telegram_message('тестовое сообщение из вложенного цикла'))
        i += 1
        start_time = time.time()
        pa, output = master_parser(url, pa)
        end_time = time.time()

        logging.info(
            f'Запрос {i}: {start_time} - {end_time} ({end_time - start_time})')  # Логирование времени обработки запроса
        logging.info(f'Вывод {output}')  # Вывода
        if output != 429 and output != []:
            asyncio.run(send_telegram_message(
                f'Найдена новая новость! \n Время запроса и обработки: from {datetime.utcfromtimestamp(start_time)} to {datetime.utcfromtimestamp(end_time)} ({end_time - start_time} sec)'))
            asyncio.run(send_telegram_message(
                f"Время выхода новости: {datetime.utcfromtimestamp(int(output[0][0]) / 1000)} \n Тип новости: {output[1]} \n Токен: {output[2]} \n Начало торгов: {output[3]} \n Биржа для открытия лонга: {output[4]} \n Пара с USDT (про новость)?: {output[5]} \n Ссылка: {output[6]}"))

        if output == 429:
            fails += 1
        times.append(end_time - start_time)
        print(f"Время и обработки выполнения запроса: {end_time - start_time} секунд")
        time.sleep(5)
        logging.info(f'Среднее время на запрос: {np.mean(times)}, количество ошибок: {fails}')


def main():
    updater = Update(token='6354808644:AAEA9pvVZj6YqvXKCyyyF9ay0q4mdXqXfxE', use_context=True)
    dp = updater.dispatcher

    # Добавление обработчиков команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stop", stop))
    # ... (другие обработчики команд)

    # Запуск скрипта
    updater.start_polling()


if __name__ == "__main__":
    main()

