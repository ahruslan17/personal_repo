import hashlib
import hmac
import json
import time
from datetime import datetime

# мои ключи
API_KEY = 'TG8WOl7FiLh2SkQiRN'
API_SECRET = 'FM9XV4TKHy8xhcUR9WKSlrgpiByMVMMcYIZK'

# ключи Юли
# API_KEY = 'LCkJC6eesykRNPrt9R'
# API_SECRET = 'xebSQQWo2ZTR8lKYhGJdEvvhyyzkv6AQXqBK'


import asyncio
import logging
import requests
from pybit.unified_trading import HTTP
from Notifications import send_telegram_message

log_file = 'logfile.log'
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def changeMarginModeAndLeverageBybit(ticker, leverage, session_bybit):
    s_time = time.time()
    try:
        response = session_bybit.switch_margin_mode(
            category="linear",
            symbol=ticker,
            tradeMode=1,
            buyLeverage=f'{leverage}',
            sellLeverage=f'{leverage}',
        )
        print('Изолированная маржа и плечо х2 успешно установлены')
        f_time = time.time()
        logging.info(f"changeMarginModeAndLeverageBybit is done. {(f_time - s_time)} sec: ")
        return response
    except Exception as e:
        print('Изолированная маржа уже установлена')
        try:
            print(session_bybit.set_leverage(
                category="linear",
                symbol=ticker,
                buyLeverage=f"{leverage}",
                sellLeverage=f"{leverage}",
            ))
            f_time = time.time()
            logging.info(f"changeMarginModeAndLeverageBybit is done. {(f_time - s_time)} sec: ")
        except Exception as e:
            f_time = time.time()
            logging.info(f"changeMarginModeAndLeverageBybit is done. {(f_time - s_time)} sec: ")
            print('Плечо x2 уже установлено')
        return -11


def getCurrentPriceSpot(ticker):
    s_time = time.time()
    current_price = 0
    spot_url = f'https://api.bybit.com/spot/v3/public/quote/ticker/price?symbol={ticker}'
    try:
        response = requests.get(spot_url)
        response.raise_for_status()
        exchange_info_spot = response.json()
        current_price = float(exchange_info_spot['result']['price'])

    except Exception as e:
        print(f"Произошла ошибка в функции getCurrentPriceSpot: {e}")
        asyncio.run(send_telegram_message(f"Произошла ошибка в функции getCurrentPriceSpot: {e}"))
        logging.info(f"Произошла ошибка в функции getCurrentPriceSpot: {e}")

    f_time = time.time()
    logging.info(f"getCurrentPriceSpot is done. {(f_time - s_time)} sec: ")
    return current_price


def getCurrentPriceFutures(ticker):
    s_time = time.time()
    current_price = 0
    futures_url = f'https://api.bybit.com/v2/public/tickers?symbol={ticker}'
    try:
        response = requests.get(futures_url)
        response.raise_for_status()
        exchange_info_futures = response.json()
        # print(exchange_info_spot)
        current_price = float(exchange_info_futures['result'][0]['last_price'])

    except Exception as e:
        print(f"Произошла ошибка в функции getCurrentPriceFutures: {e}")
        asyncio.run(send_telegram_message(f"Произошла ошибка в функции getCurrentPriceFutures: {e}"))
        logging.info(f"Произошла ошибка в функции getCurrentPriceFutures: {e}")

    f_time = time.time()
    logging.info(f"getCurrentPriceFutures is done. {(f_time - s_time)} sec: ")
    return current_price


def getInfo(ticker, session_bybit):
    s_time = time.time()
    try:
        # session = HTTP()
        response = session_bybit.get_instruments_info(
            category="linear",
            symbol=ticker,
        )
        print(response)
        number = response['result']['list'][0]['lotSizeFilter']['qtyStep']
        print(number)

        # Находим порядок величины (степень десятки)
        order_of_magnitude = 0
        if float(number) == 1:
            return 0
        if float(number) > 1:
            return -1*len(number) + 1
        if float(number) < 1:
            return len(number) - 2

    except Exception as e:
        print('Произошла ошибка в функции getInfo', e)
        logging.info(f"getInfo Error: {e}")

        return -11


def SpotEnterOrder(position_sum, ticker, session_bybit):
    s_time = time.time()
    try:
        start_time = time.time() * 1000
        # print('Открыть позицию по инструменту', ticker,
        #       f'на бирже bybit, тип позиции spot. Собственный капитал ${position_sum}')
        # asyncio.run(send_telegram_message(
        #     f'Открыть позицию по инструменту {ticker}, на бирже bybit, тип позиции spot. Cобственный капитал ${position_sum}.'))

        # session = HTTP(
        #     api_key=API_KEY,
        #     api_secret=API_SECRET,
        # )

        # price = f"{getCurrentPriceSpot(ticker) + getCurrentPriceSpot(ticker)*0.01}"
        # qty = f"{round(position_sum / float(price), getInfo(ticker)+2)}"

        # print(price)
        # print(qty)
        response = session_bybit.place_order(
            category="spot",
            symbol=ticker,
            side="Buy",
            orderType="Market",
            # price=5,
            qty=position_sum,
        )

        info, c_price = response, getCurrentPriceSpot(ticker)
        # print(response)
        # print(info)
        # print(PositionInfo(ticker., 'linear', session_bybit))
        if info['retMsg'] == 'OK':
            asyncio.run(send_telegram_message(
                f"Информация о позиции: \n Позиция успешно открыта на Bybit Spot Market \n Инструмент: {ticker}, \n Было куплено: {position_sum / c_price} {ticker.replace('USDT', '')} \n По цене: {c_price} \n Размер позиции: ${position_sum}, \n Время заполнения ордера: {datetime.utcfromtimestamp(float(info['time']) / 1000)}, \n Время на исполнение: {float(float(info['time']) - float(start_time)) / 1000}, \n Ссылка: https://www.bybit.com/en/trade/spot/{ticker.replace('USDT', '')}/USDT"))
            print(
                f"Информация о позиции: \n Позиция успешно открыта на Bybit Spot Market \n Инструмент: {ticker}, \n Было куплено: {position_sum / c_price} {ticker.replace('USDT', '')} \n По цене: {c_price} \n Размер позиции: ${position_sum}, \n Время заполнения ордера: {datetime.utcfromtimestamp(float(info['time']) / 1000)}, \n Время на исполнение: {float(float(info['time']) - float(start_time)) / 1000}, \n Ссылка: https://www.bybit.com/en/trade/spot/{ticker.replace('USDT', '')}/USDT")
        elif info['side'] == 'None':
            print('Error in SpotEnterOrder bybit')
            asyncio.run(send_telegram_message('Error in SpotEnterOrder bybit'))
    except Exception as e:
        response = -11
        print('Возникла ошибка в функции SpotEnterOrder bybit: ', e)
        asyncio.run(send_telegram_message(f'Возникла ошибка в функции SpotEnterOrder bybit: {e}'))
    f_time = time.time()
    logging.info(f"SpotEnterOrder is done. {(f_time - s_time)} sec: ")
    return response


def FuturesEnterOrder(position_sum, ticker, leverage, session_bybit):
    s_time = time.time()
    try:
        # print('Открыть позицию по инструменту', ticker,
        #       f'на бирже bybit, тип позиции futures. Плечо {leverage}x, собственный капитал ${position_sum}')
        # asyncio.run(send_telegram_message(
        #     f'Открыть позицию по инструменту {ticker}, на бирже bybit, тип позиции futures. Плечо {leverage}x, собственный капитал ${position_sum}.'))

        # session = HTTP(
        #     api_key=API_KEY,
        #     api_secret=API_SECRET )
        start_time = time.time() * 1000

        changeMarginModeAndLeverageBybit(ticker, leverage, session_bybit)

        # price = f"{getCurrentPriceFutures(ticker) + 10}"
        qty = f"{round(leverage * position_sum / getCurrentPriceFutures(ticker), getInfo(ticker, session_bybit))}"

        response = session_bybit.place_order(
            category="linear",
            symbol=ticker,
            side="Buy",
            orderType="Market",
            # price=price,
            qty=qty
        )

        info = PositionInfo(ticker, 'linear', session_bybit)['result']['list'][0]
        print(info)
        if info['side'] != 'None':
            asyncio.run(send_telegram_message(
                f"Информация о позиции: \n Позиция успешно открыта на Bybit Futures Market \n Инструмент: {info['symbol']}, \n Тип позиции: {info['side']}, \n Было куплено: {info['size']} {info['symbol'].replace('USDT', '')} \n По цене ${info['avgPrice']} \n Размер позиции: ${info['positionValue']}, \n Плечо: x{info['leverage']}, \n Своих средств: ${info['positionBalance']}, \n Время открытия: {datetime.utcfromtimestamp(float(info['updatedTime']) / 1000)},\n Время на обработку: {float(float(info['updatedTime']) - float(start_time)) / 1000} секунд, \n Link: https://www.bybit.com/trade/usdt/{info['symbol']}"))
            print(
                f"Информация о позиции: \n Позиция успешно открыта на Bybit Futures Market \n Инструмент: {info['symbol']}, \n Тип позиции: {info['side']}, \n Было куплено: {info['size']} {info['symbol'].replace('USDT', '')} \n По цене ${info['avgPrice']} \n Размер позиции: ${info['positionValue']}, \n Плечо: x{info['leverage']}, \n Своих средств: ${info['positionBalance']}, \n Время открытия: {datetime.utcfromtimestamp(float(info['updatedTime']) / 1000)},\n Время на обработку: {float(float(info['updatedTime']) - float(start_time)) / 1000} секунд, \n Link: https://www.bybit.com/trade/usdt/{info['symbol']}")
        elif info['side'] == 'None':
            print('Open Error')
            asyncio.run(send_telegram_message('Open Error'))
    except Exception as e:
        print('Возникла ошибка в FuturesEnterOrder', e)
        response = -11
    f_time = time.time()
    logging.info(f"FuturesEnterOrder is done. {(f_time - s_time)} sec: ")
    return response


def PositionInfo(ticker, category, session_bybit):
    s_time = time.time()
    try:
        # session = HTTP(
        #     api_key=API_KEY,
        #     api_secret=API_SECRET,
        # )
        response = session_bybit.get_positions(
            category=category,
            symbol=ticker,
        )
        f_time = time.time()
        logging.info(f"PositionInfo is done. {(f_time - s_time)} sec: ")
        return response
    except Exception as e:
        print('Ошибка в функции PositionInfo', e)
        logging.info(f"PositionInfo is done: {e} ")

        return -11

# print(SpotEnterOrder(5, 'DOGEUSDT', session_bybit=HTTP(api_key=API_KEY, api_secret=API_SECRET)))

# print(FuturesEnterOrder(2, 'DOGEUSDT', 2, session_bybit=HTTP(api_key=API_KEY, api_secret=API_SECRET)))
# print(PositionInfo('POLYXUSDT', 'linear'))
# changeMarginModeAndLeverageBybit('1000FLOKIUSDT', 2, session_bybit=HTTP(api_key=API_KEY, api_secret=API_SECRET))
print(getInfo('PYTHUSDT',session_bybit=HTTP(api_key=API_KEY, api_secret=API_SECRET)))