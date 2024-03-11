import requests
import time
from datetime import datetime
import re
import json
from Notifications import send_telegram_message
import asyncio
import logging


def binance_request_token():
    s_time = time.time()
    spot_names = []
    futures_names = []
    spot_url = f"https://api.binance.com/api/v3/ticker/24hr"

    try:
        response = requests.get(spot_url)
        response.raise_for_status()

        exchange_info_spot = response.json()
        # print(exchange_info_spot)

        for data in exchange_info_spot:
            spot_names.append(data['symbol'])
        # print(spot_names)
    except Exception as e:
        print(f"Произошла ошибка binance_request_token при обращении к spot: {e}")

    futures_url = 'https://fapi.binance.com/fapi/v1/ticker/24hr'

    try:
        response = requests.get(futures_url)
        response.raise_for_status()

        exchange_info_futures = response.json()
        # print(exchange_info_futures)

        for data in exchange_info_futures:
            futures_names.append(data['symbol'])
        # print(futures_names)


    except Exception as e:
        print(f"Произошла ошибка binance_request_token при обращении к futures: {e}")
    f_time = time.time()

    return {"spot": spot_names, "futures": futures_names}


def bybit_request_token():
    # spot_url = 'https://api.bybit.com/spot/v3/public/symbols'
    spot_url = 'https://api.bybit.com/spot/v3/public/quote/ticker/24hr'
    spot_names = []
    futures_names = []
    try:
        response = requests.get(spot_url)
        response.raise_for_status()

        exchange_info_spot = response.json()
        # print(exchange_info_spot['result']['list'])

        for data in exchange_info_spot['result']['list']:
            spot_names.append(data['s'])
        # print(spot_names)

    except Exception as e:
        print(f"Произошла ошибка при обращении к spot: {e}")
        asyncio.run(send_telegram_message(f'Парсер бирж Error. Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    futures_url = 'https://api.bybit.com/derivatives/v3/public/instruments-info'

    try:
        response = requests.get(futures_url)
        response.raise_for_status()

        exchange_info_futures = response.json()
        # print(exchange_info_futures['result']['list'])
        for data in exchange_info_futures['result']['list']:
            if data['status'] == 'Trading':
                futures_names.append(data['symbol'])
        print(futures_names)
    except Exception as e:
        print(f"Произошла ошибка при обращении к futures: {e}")
        asyncio.run(send_telegram_message(f'Парсер бирж Error. Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    # print(spot_names)
    # print(futures_names)
    return {"spot": spot_names, "futures": futures_names}


def kucoin_request_token():
    spot_url = 'https://api.kucoin.com/api/v2/symbols'
    spot_names = []
    futures_names = []

    try:
        response = requests.get(spot_url)
        response.raise_for_status()

        exchange_info_spot = response.json()
        # print(exchange_info_spot)

        for data in exchange_info_spot['data']:
            if data['enableTrading'] == True:
                spot_names.append(data['symbol'].replace('-',''))
        # print(spot_names)
    except Exception as e:
        print(f"Произошла ошибка при обращении к spot: {e}")
        asyncio.run(send_telegram_message(f'Парсер бирж Error. Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    # Замените на соответствующий URL для фьючерсов KuCoin, если такой доступен
    futures_url = 'https://api-futures.kucoin.com/api/v1/contracts/active'

    try:
        response = requests.get(futures_url)
        response.raise_for_status()

        exchange_info_futures = response.json()
        # print(exchange_info_futures)

        for data in exchange_info_futures['data']:
            if data['status'] == 'Open':
                futures_names.append(data['symbol'][:-1])
        print(futures_names)

    except Exception as e:
        print(f"Произошла ошибка при обращении к futures: {e}")
        asyncio.run(send_telegram_message(f'Парсер бирж Error. Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    return {"spot": spot_names, "futures": futures_names}


def gateio_request_token():
    spot_url = 'https://api.gateio.ws/api/v4/spot/currency_pairs'

    spot_names = []
    futures_names = []

    try:
        response = requests.get(spot_url)
        response.raise_for_status()

        exchange_info_spot = response.json()
        # print(exchange_info_spot)


        for pair in exchange_info_spot:
            if pair['trade_status'] == 'tradable':
                spot_names.append(pair['id'].replace('_', ''))
        # print(spot_names)
    except Exception as e:
        print(f"Произошла ошибка при обращении к spot: {e}")
        asyncio.run(send_telegram_message(f'Парсер бирж Error. Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    # Замените на соответствующий URL для фьючерсов Gate.io, если такой доступен
    futures_url = 'https://api.gateio.ws/api/v4/futures/usdt/contracts'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    try:
        response = requests.get(futures_url, headers=headers)
        response.raise_for_status()

        exchange_info_futures = response.json()
        # print(exchange_info_futures)

        for data in exchange_info_futures:
            if data['in_delisting'] == False:
                futures_names.append(data['name'].replace('_', ''))
        print(futures_names)

    except Exception as e:
        print(f"Произошла ошибка при обращении к futures: {e}")
        asyncio.run(send_telegram_message(f'Парсер бирж Error. Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    return {"spot": spot_names, "futures": futures_names}


def okex_request_token():
    spot_url = 'https://www.okex.com/api/v5/market/tickers?instType=SPOT'
    spot_names = []
    futures_names = []

    try:
        response = requests.get(spot_url)
        response.raise_for_status()

        exchange_info_spot = response.json()
        # print(exchange_info_spot)

        for data in exchange_info_spot['data']:
            spot_names.append(data['instId'].replace('-', ''))
        # print(spot_names)

    except Exception as e:
        print(f"Произошла ошибка при обращении к spot: {e}")
        asyncio.run(send_telegram_message(f'Парсер бирж Error. Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    # Замените на соответствующий URL для фьючерсов OKEx, если такой доступен
    futures_url = 'https://www.okex.com/api/v5/market/tickers?instType=FUTURES'

    try:
        response = requests.get(futures_url)
        response.raise_for_status()

        exchange_info_futures = response.json()
        # print(exchange_info_futures)

        for data in exchange_info_futures['data']:
            futures_names.append(re.sub(r'[^a-zA-Z]', '', data['instId']))
        # print(futures_names)

    except Exception as e:
        print(f"Произошла ошибка при обращении к futures: {e}")
        asyncio.run(send_telegram_message(f'Парсер бирж Error. Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    return {"spot": spot_names, "futures": futures_names}


def htx_request_token():
    spot_url = 'https://api.huobi.com/market/tickers'
    spot_names = []
    futures_names = []

    try:
        response = requests.get(spot_url)
        response.raise_for_status()

        exchange_info_spot = response.json()
        # print(exchange_info_spot)

        for data in exchange_info_spot['data']:
            spot_names.append(data['symbol'].upper())
        # print(spot_names)

    except Exception as e:
        print(f"Произошла ошибка при обращении к spot: {e}")
        asyncio.run(send_telegram_message(f'Парсер бирж Error. Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    futures_url = 'https://api.hbdm.com/linear-swap-api/v1/swap_contract_info'

    # timestamp = str(int(time.time()))
    # signature = generate_signature('35fd9199-d8f3deeb-xa2b53ggfc-8a3b2', 'ed53a0bd-32de72d3-0c43de83-84297', timestamp)

    # headers = {
    #     'Content-Type': 'application/x-www-form-urlencoded',
    #     'accessKeyId': '35fd9199-d8f3deeb-xa2b53ggfc-8a3b2',
    #     'timestamp': timestamp,
    #     'Signature': signature
    # }

    try:
        response = requests.get(futures_url)
        response.raise_for_status()

        exchange_info_futures = response.json()
        # print(exchange_info_futures)

        for data in exchange_info_futures['data']:
            if data['contract_status'] == 1:
                futures_names.append(data['contract_code'].replace('-',''))
        # print(futures_names)

    except Exception as e:
        print(f"Произошла ошибка при обращении к futures: {e}")
        asyncio.run(send_telegram_message(f'Парсер бирж Error. Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    return {"spot": spot_names, "futures": futures_names}


def mexc_request_token():
    spot_url = 'https://api.mexc.com/api/v3/exchangeInfo'
    spot_names = []
    futures_names = []

    try:
        response = requests.get(spot_url)
        response.raise_for_status()

        exchange_info_spot = response.json()
        # print(exchange_info_spot)

        for data in exchange_info_spot['symbols']:
            if data['status'] == 'ENABLED':
                spot_names.append(data['symbol'])
        # print(spot_names)

    except Exception as e:
        print(f"Произошла ошибка при обращении к spot: {e}")
        asyncio.run(send_telegram_message(f'Парсер бирж Error. Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    # Замените на соответствующий URL для фьючерсов MEXC, если такой доступен
    futures_url = 'https://contract.mexc.com/api/v1/contract/detail'

    try:
        response = requests.get(futures_url)
        response.raise_for_status()

        exchange_info_futures = response.json()
        # print(exchange_info_futures)

        for data in exchange_info_futures['data']:
            if data['state'] == 0:
                futures_names.append(data['symbol'].replace('_', ''))
        # print(futures_names)

    except Exception as e:
        print(f"Произошла ошибка при обращении к futures: {e}")
        asyncio.run(send_telegram_message(f'Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    return {"spot": spot_names, "futures": futures_names}


def bitmart_request_token():
    spot_url = 'https://api-cloud.bitmart.com/spot/v1/symbols/details'
    spot_names = []
    futures_names = []

    try:
        response = requests.get(spot_url)
        response.raise_for_status()

        exchange_info_spot = response.json()
        # print(exchange_info_spot)

        for data in exchange_info_spot['data']['symbols']:
            if data['trade_status'] == 'trading':
                spot_names.append(data['symbol'].replace('_', ''))
        # print(spot_names)

    except Exception as e:
        print(f"Произошла ошибка при обращении к spot: {e}")
        asyncio.run(send_telegram_message(f'Парсер бирж Error. Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    # Замените на соответствующий URL для фьючерсов MEXC, если такой доступен
    futures_url = 'https://api-cloud.bitmart.com/contract/public/details'

    try:
        response = requests.get(futures_url)
        response.raise_for_status()

        exchange_info_futures = response.json()
        # print(exchange_info_futures)

        for data in exchange_info_futures['data']['symbols']:
            futures_names.append(data['symbol'])
        # print(futures_names)

    except Exception as e:
        print(f"Произошла ошибка при обращении к futures: {e}")
        asyncio.run(send_telegram_message(f'Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    return {"spot": spot_names, "futures": futures_names}


def xt_request_token():
    spot_url = 'https://sapi.xt.com/v4/public/symbol'
    spot_names = []
    futures_names = []

    try:
        response = requests.get(spot_url)
        response.raise_for_status()

        exchange_info_spot = response.json()
        # print(exchange_info_spot)

        for data in exchange_info_spot['result']['symbols']:
            if data['state'] == 'ONLINE' and data['tradingEnabled'] == True:
                spot_names.append(data['symbol'].replace('_', '').upper())
        # print(spot_names)

    except Exception as e:
        print(f"Произошла ошибка при обращении к spot: {e}")
        asyncio.run(send_telegram_message(f'Парсер бирж Error. Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    # Замените на соответствующий URL для фьючерсов MEXC, если такой доступен
    futures_url = 'https://fapi.xt.com/future/market/v1/public/cg/contracts'
    try:
        response = requests.get(futures_url)
        response.raise_for_status()

        exchange_info_futures = response.json()
        # print(exchange_info_futures)

        for data in exchange_info_futures:
            futures_names.append(data['ticker_id'].replace('-', ''))
        # print(futures_names)

    except Exception as e:
        print(f"Произошла ошибка при обращении к futures: {e}")
        asyncio.run(send_telegram_message(f'Парсер бирж Error. Возникла ошибка: {e}'))
        logging.info(f"Произошла ошибка: {e}")

    return {"spot": spot_names, "futures": futures_names}


def main():
    try:
        i = 0
        log_file = 'logfile_ExchangeParser.log'
        logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info('----SCRIPT IS STARTED----')  # Логирование времени обработки запроса
        asyncio.run(
            send_telegram_message('Парсер бирж на предмет наличия токенов запущен. Обновление базы каждый час.'))
        print('Парсер бирж на предмет наличия токенов запущен.')

        while True:
            i += 1
            logging.info(f'Начало цикла на обновление базы')  # Вывода
            local_time = datetime.now().replace(microsecond=0)
            formatted_time = local_time.strftime("%Y-%m-%d %H:%M:%S")

            # file_path = f"TickerDatabase/TickersDatabase_{formatted_time}.json"
            file_path = "TickersDatabase.json"

            database = {'bybit_data': bybit_request_token(), 'kucoin_data': kucoin_request_token(),
                        'gateio_data': gateio_request_token(), 'okex_data': okex_request_token(),
                        'htx_data': htx_request_token(), 'mexc_data': mexc_request_token(),
                        'bitmart_data': bitmart_request_token(), 'xtcom_data': xt_request_token(), 'binance_data': binance_request_token()}
            with open(file_path, 'w') as file:
                json.dump(database, file)

            logging.info(f"База данных успешно сохранена в файл: {file_path}")  # Вывода
            print("База данных успешно сохранена в файл:", file_path)
            if i > 0:
                asyncio.run(send_telegram_message(f"{formatted_time} (UTC+3) - Обновление базы \n База данных успешно сохранена в файл: {file_path}"))

            time.sleep(3600)
    except KeyboardInterrupt:
        # Обработка события прерывания (нажатие кнопки "Stop" в PyCharm)
        asyncio.run(send_telegram_message("Парсер тикеров на биржах остановлен вручную"))

    except Exception as e:
        logging.info(f"Произошла ошибка: {e}")
        asyncio.run(send_telegram_message(f'Парсер бирж Error Возникла ошибка: {e}'))
        print("Произошла ошибка:", e)


if __name__ == "__main__":
    main()
