import requests
import json
import time
from datetime import datetime
import re
from bs4 import BeautifulSoup
import logging
import numpy as np
import asyncio

import random
import string
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import sys
import atexit
from telegram import Bot

token = '6354808644:AAEA9pvVZj6YqvXKCyyyF9ay0q4mdXqXfxE'
chatId = -1001995965101  # мой тестовый чат


# chatId = -1002096660763 # наш основной чат
def convert_title_into_link(text):
    return f'https://www.binance.com{text}'


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


async def send_telegram_message(message_text):
    try:
        bot = Bot(token=token)
        await bot.send_message(chat_id=chatId, text=message_text)
    except Exception as e:
        print('Сообщение не отправлено', e)


async def send_telegram_message_debug(message_text):
    try:
        bot = Bot(token=token)
        await bot.send_message(chat_id=-1001995965101, text=message_text)
    except Exception as e:
        print('Сообщение не отправлено', e)


def master_parser(url, previous_articles, ordinal):
    s_time = time.time()
    try:
        # response = requests.get(add_random_params(url), verify=False, cookies=None)
        response = requests.get(url, verify=False, cookies=None, headers={'Cache-Control': 'no-cache, max-age=0'})
        print(f'----Текущее время ---- {datetime.utcfromtimestamp(time.time())} ---- {time.time()}')
        cache_hit = response.headers.get('X-Cache-Proxy')
        print('Ordinal: ', ordinal)
        print('X-Cache-Proxy: ', cache_hit)
        cache_control = response.headers.get('Cache-Control')
        print('Cache-Control: ', cache_control)

        # response = requests.get(url)

        if response.status_code == 429:
            print('Response 429. Sleep 10 sec.')
            time.sleep(10)
            return previous_articles, [], 0, []

        if response.status_code == 200:

            soup = BeautifulSoup(response.text, 'html.parser')
            ul_elements = soup.find('ul', class_='css-dhmrnb')
            articles = []
            links = []

            if ul_elements:
                li_elements = ul_elements.find_all(['li'], class_=['css-1rm1dv7', 'css-vvvv13'])
                for li in li_elements:
                    link = li.find('a')['href'] if li.find('a') else None  # Получаем ссылку, если она есть
                    articles.append(li.text)
                    links.append(link)
            # print(articles)

            if previous_articles == articles:
                print('Нет новых новостей')
                print('-----------------------------')
                return previous_articles, [], 0, []

            if previous_articles != articles:
                new_articles = [article for article in articles if article not in previous_articles]
                # print(len(new_articles))
                # new_links = links[:len(new_articles)]
                # print(len(new_links))
                # print(new_articles)
                # print(new_links)

                # print(convert_title_into_link('https://www.binance.com',new_links[0]))

                previous_articles = articles
                return previous_articles, new_articles, time.time(), links
    except Exception as e:
        print(f'Error: {e}')
        asyncio.run(send_telegram_message_debug(f'Error master parser all news parser: {e}'))
        return previous_articles, [], -1, []


def master_message(new_articles, date, links):
    for j in range(len(new_articles)):
        print(
            f'Новая новость! \n Заголовок: {new_articles[j]} \n Время получения новости:  {datetime.utcfromtimestamp(date)} \n Unix: {date} \n Ссылка: {convert_title_into_link(links[j])}')
        asyncio.run(send_telegram_message(
            f'Новая новость! \n Заголовок: {new_articles[j]} \n Время получения новости:  {datetime.utcfromtimestamp(date)} \n Unix: {date} \n Ссылка: {convert_title_into_link(links[j])}'))


def main():
    print('Парсер All News запущен')
    asyncio.run(send_telegram_message_debug('Парсер All News запущен'))
    init_pa = ['Binance Futures Will Launch USDⓈ-M ILV Perpetual Contract With Up to 50x Leverage',
               'Updates on Russian Ruble (RUB) Deposits',
               '“ACH Simple Earn Products” Activity Has Now Concluded',
               'Removal of Selected Spot Trading Pairs Will Be Postponed (2023-11-10)',
               'Light Festival P2P Merchant Trading Challenge: Get a Share of 2,000 USDT!',
               'Expand Your Crypto Journey: Embrace the Full Binance Suite to Share Over 50,000 USDT!',
               'Locked Products Update: Enjoy Up to 10.9% APR with SOL & NEAR!',
               'Binance Opens Deposits, Withdrawals and Conversions of USD Coin Bridged (USDC.e) on Arbitrum Network',
               'Binance Futures Will Launch USDⓈ-M BADGER Perpetual Contract With Up to 50x Leverage',
               'Binance Adds AST, GNO, ORDI and More Pairs on Cross Margin & Isolated Margin']

    url1 = 'https://www.binance.com/en/support/announcement/binance-futures-will-launch-usd%E2%93%A2-m-ilv-perpetual-contract-with-up-to-50x-leverage-7af5eefa0e1c433c996aadce389bafe5'
    url2 = 'https://www.binance.com/en/support/announcement/qtum-mainnet-upgrade-115001733592'
    url3 = 'https://www.binance.com/en/support/announcement/fetch-ai-fet-token-sale-rate-set-on-binance-launchpad-360024243592'
    url4 = 'https://www.binance.com/en/support/announcement/mana-trading-competition-115003015751'
    url5 = 'https://www.binance.com/en/support/announcement/binance-will-delist-multiple-american-style-daily-options-8f74739047874206827f0fcbd1c3ae6b'
    url6 = 'https://www.binance.com/en/support/announcement/binance-will-support-the-boba-token-boba-airdrop-program-for-omg-network-omg-holders-ccb567574cb14c528b3e5e8e69752c6a'

    pa1, _, _, _ = master_parser(url1, init_pa, 1)
    pa2, _, _, _ = master_parser(url2, init_pa, 2)
    pa3, _, _, _ = master_parser(url3, init_pa, 3)

    pa4, _, _, _ = master_parser(url4, init_pa, 4)
    pa5, _, _, _ = master_parser(url5, init_pa, 5)
    pa6, _, _, _ = master_parser(url6, init_pa, 6)

    all_na = []
    max_attempts = 10
    i = 0
    while True:
        i += 1
        if i % 300 == 0:
            asyncio.run(send_telegram_message_debug('Парсер New Listings исправно функционирует.'))
        try:
            attempts = 0

            while attempts < max_attempts:
                try:
                    time.sleep(2)
                    pa1, na1, d1, l1 = master_parser(url1, pa1, 1)
                    if d1 == -1:
                        attempts += 1
                        time.sleep(5)
                    if d1 != -1:
                        break
                except:
                    pass

            if na1 and na1 not in all_na:
                all_na.append(na1)
                master_message(na1, d1, l1)
            time.sleep(2)

            while attempts < max_attempts:
                try:
                    time.sleep(2)
                    pa2, na2, d2, l2 = master_parser(url2, pa2, 1)
                    if d2 == -1:
                        attempts += 1
                        time.sleep(5)
                    if d2 != -1:
                        break
                except:
                    pass

            if na2 and na2 not in all_na:
                all_na.append(na2)
                master_message(na2, d2, l2)
            time.sleep(2)

            while attempts < max_attempts:
                try:
                    time.sleep(2)
                    pa3, na3, d3, l3 = master_parser(url3, pa3, 1)
                    if d3 == -1:
                        attempts += 1
                        time.sleep(5)
                    if d3 != -1:
                        break
                except:
                    pass

            if na3 and na3 not in all_na:
                all_na.append(na3)
                master_message(na3, d3, l3)
            time.sleep(2)

            while attempts < max_attempts:
                try:
                    time.sleep(2)
                    pa4, na4, d4, l4 = master_parser(url4, pa4, 1)
                    if d4 == -1:
                        attempts += 1
                        time.sleep(5)
                    if d4 != -1:
                        break
                except:
                    pass

            if na4 and na4 not in all_na:
                all_na.append(na4)
                master_message(na4, d4, l4)
            time.sleep(2)

            while attempts < max_attempts:
                try:
                    time.sleep(2)
                    pa5, na5, d5, l5 = master_parser(url5, pa5, 1)
                    if d5 == -1:
                        attempts += 1
                        time.sleep(5)
                    if d5 != -1:
                        break
                except:
                    pass

            if na5 and na5 not in all_na:
                all_na.append(na5)
                master_message(na5, d5, l5)
            time.sleep(2)

            while attempts < max_attempts:
                try:
                    time.sleep(2)
                    pa6, na6, d6, l6 = master_parser(url6, pa6, 1)
                    if d6 == -1:
                        attempts += 1
                        time.sleep(5)
                    if d6 != -1:
                        break
                except:
                    pass

            if na6 and na6 not in all_na:
                all_na.append(na6)
                master_message(na6, d6, l6)

        except KeyboardInterrupt:
            # Обработка события прерывания (нажатие кнопки "Stop" в PyCharm)
            asyncio.run(send_telegram_message_debug("Парсер всех новостей остановлен вручную"))

        except Exception as e:
            print(f"Произошла ошибка в main all news: {e}")
            asyncio.run(send_telegram_message_debug(f"Произошла ошибка в main all news: {e}."))


import warnings

warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

if __name__ == "__main__":
    main()
