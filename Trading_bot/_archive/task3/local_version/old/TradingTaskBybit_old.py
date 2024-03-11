import time
import logging
import asyncio
from pybit.unified_trading import HTTP

from pybit.unified_trading import WebSocket  # pip install pybit

import json

import asyncio
from telegram import Bot

# key = 'TG8WOl7FiLh2SkQiRN'
# secret = 'FM9XV4TKHy8xhcUR9WKSlrgpiByMVMMcYIZK'

key = 'HS398zpUdxSahhV6se'
secret = 'e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T'
session_bybit = HTTP(api_key=key, api_secret=secret)
public = WebSocket(channel_type='linear', testnet=False)
private = WebSocket(channel_type='private',
                    api_key=key,
                    api_secret=secret,
                    testnet=False)

log_file = 'logfile.log'
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

token = '6354808644:AAEA9pvVZj6YqvXKCyyyF9ay0q4mdXqXfxE'
chatId = -1001995965101  # мой тестовый чат
# chatId = -1002096660763 # наш основной чат

##globals
orderbook = []
isActiveOrder = False
isPosition = False
current_position = 0
ticker = 'MEMEUSDT'
pip_size = 0


async def send_telegram_message(message_text):
    try:
        bot = Bot(token=token)
        await bot.send_message(chat_id=chatId, text=message_text)
    except Exception as e:
        print('Сообщение не отправлено', e)


def getDecimal(session_bybit):
    global ticker
    s_time = time.time()
    try:
        # session = HTTP()
        response = session_bybit.get_instruments_info(
            category="linear",
            symbol=ticker,
        )

        number = response['result']['list'][0]['lotSizeFilter']['qtyStep']
        if '.' in number:
            integer_part, decimal_part = number.split('.')
            f_time = time.time()
            logging.info(f"getNumberAfterDot is done. {(f_time - s_time)} sec: ")
            return (len(decimal_part))
        else:
            f_time = time.time()
            logging.info(f"getInfo is done. {(f_time - s_time)} sec: ")
            return 0
    except Exception as e:
        print('Произошла ошибка в функции getInfo', e)
        logging.info(f"getInfo Error: {e}")

        return -11


def CancelFuturesOrder(order_id, session):
    global ticker
    try:
        response = session.cancel_order(
            category="linear",
            symbol=ticker,
            orderId=order_id,
        )
        print(response)
        if response['retCode'] == 0:
            print('Ордер успешно отменён')
        else:
            print('Ордер не отменен, ', response['retCode'])

        return response['retCode']
    except Exception as e:
        print('Ошибка отмены ордера: ', e)
        return -1


def FuturesEnterOrder(position_sum, leverage, session_bybit):
    global ticker
    s_time = time.time()
    try:
        # start_time = time.time() * 1000

        # changeMarginModeAndLeverageBybit(ticker, leverage, session_bybit)
        # price = orderbook[-1]['best_bid_3']
        # print("orderbook[-1]['best_bid_3']", price)
        qty = f"{round(leverage * position_sum / orderbook[-1]['best_bid_1'], getDecimal(session_bybit))}"
        # qty = f"{round(leverage * position_sum / orderbook[-1]['best_bid_3'], 0)}"

        response = session_bybit.place_order(
            category="linear",
            symbol=ticker,
            side="Buy",
            orderType="Limit",
            price=orderbook[-1]['best_bid_1'],
            qty=qty
        )
        f_time = time.time()
        print(response)
        print(f_time - s_time)

        if response['retCode'] == 0:
            print('Сообщение об успешном размещении ордера')
        if response['retCode'] != 0:
            print('Сообщение об ошибке при размещении ордера')

        return response['retCode'], response['result']['orderId']
    except Exception as e:
        print('Futures order Error: ', e)
        return -1, -1

        # info = PositionInfo(ticker, 'linear', session_bybit)['result']['list'][0]
    #     print(info)
    #     if info['side'] != 'None':
    #         asyncio.run(send_telegram_message(
    #             f"Информация о позиции: \n Позиция успешно открыта на Bybit Futures Market \n Инструмент: {info['symbol']}, \n Тип позиции: {info['side']}, \n Было куплено: {info['size']} {info['symbol'].replace('USDT', '')} \n По цене ${info['avgPrice']} \n Размер позиции: ${info['positionValue']}, \n Плечо: x{info['leverage']}, \n Своих средств: ${info['positionBalance']}, \n Время открытия: {datetime.utcfromtimestamp(float(info['updatedTime']) / 1000)},\n Время на обработку: {float(float(info['updatedTime']) - float(start_time)) / 1000} секунд, \n Link: https://www.bybit.com/trade/usdt/{info['symbol']}"))
    #         print(
    #             f"Информация о позиции: \n Позиция успешно открыта на Bybit Futures Market \n Инструмент: {info['symbol']}, \n Тип позиции: {info['side']}, \n Было куплено: {info['size']} {info['symbol'].replace('USDT', '')} \n По цене ${info['avgPrice']} \n Размер позиции: ${info['positionValue']}, \n Плечо: x{info['leverage']}, \n Своих средств: ${info['positionBalance']}, \n Время открытия: {datetime.utcfromtimestamp(float(info['updatedTime']) / 1000)},\n Время на обработку: {float(float(info['updatedTime']) - float(start_time)) / 1000} секунд, \n Link: https://www.bybit.com/trade/usdt/{info['symbol']}")
    #     elif info['side'] == 'None':
    #         print('Open Error')
    #         asyncio.run(send_telegram_message('Open Error'))
    # except Exception as e:
    #     print('Возникла ошибка в FuturesEnterOrder', e)
    #     response = -11
    # f_time = time.time()
    # logging.info(f"FuturesEnterOrder is done. {(f_time - s_time)} sec: ")
    # return response


def handle_orderbook_message(message):
    global orderbook
    # orderbook = []

    # print('m: ', message)
    # print('!!!')
    timestamp = message.get('ts')
    data = message.get('data')
    # message.get('data')
    # print(data.get('b'))
    current = 0
    if len(data) > 0:
        current = {}
        current['timestamp'] = timestamp
        current['best_bid_1'] = float(data.get('b')[0][0])
        # current['best_bid_2'] = float(data.get('b')[1][0])
        # current['best_bid_3'] = float(data.get('b')[2][0])
        # print('bid_3: ', current['best_bid_3'])


        # print('bid_1: ', current['best_bid_1'])

        current['best_ask_1'] = float(data.get('a')[0][0])
        # print('ask_1: ', current['best_ask_1'])

        orderbook.append(current)
        # print(orderbook[-1])


def handle_position_message(message):
    global current_position, isPosition, ticker, current_order_id
    try:
        data = message.get('data', [])
        print('MESSAGE: ', message)
        # print(data)
        for pos in data:
            if pos['symbol'] == ticker:
                if pos['side'] == 'Sell':
                    current_position = - float(pos['size'])
                elif pos['side'] == 'Buy':
                    current_position = float(pos['size'])
                    print(f'Сообщение о покупке. Появилась позиция. Отключаем простановку ордеров')
                    isPosition = True
                    CancelFuturesOrder(current_order_id, session_bybit)

                else:
                    current_position = 0
                    print(f'Waiting for you to buy a {ticker}')
            else:
                pass
    except (IndexError, AttributeError, TypeError):
        pass


def pips_size(rational):
    str_number = str(rational)

    last_digit = str_number.split('.')[-1]

    result = '0.' + '0' * (len(last_digit) - 1) + '1'

    return float(result)



current_order_id = ''


def main():
    global orderbook, current_position, isActiveOrder, isPosition, ticker, current_order_id, pip_size
    public.orderbook_stream(depth=1, symbol=ticker, callback=handle_orderbook_message)
    private.position_stream(callback=handle_position_message)

    time.sleep(1)
    pip_size = pips_size(orderbook[-1]['best_bid_1'])
    print(pip_size)


    i = 0
    while True:
        time.sleep(0.1)
        print(orderbook[-1]['best_bid_1'] - 5*pip_size)

    # while True:
    #     print(f'---{i}---')
    #     i += 1
    #
    #     if not isPosition:
    #         print('--Нет позиции')
    #         time.sleep(1)
    #         # print(orderbook[-1])
    #         # print(orderbook[-1]['best_ask_3'])
    #         if isActiveOrder:
    #             print('--Есть активный ордер')
    #             print('--Отменяем его')
    #
    #             resp = CancelFuturesOrder(current_order_id, session_bybit)
    #
    #             if resp:
    #                 isActiveOrder = False
    #                 current_order_id = ''
    #                 print('--Успешно отменили')
    #
    #         if not isActiveOrder:
    #             print('--Нет активного ордера, проставить активный ордер')
    #             print("orderbook[0]['best_bid_1']", orderbook[-1]['best_bid_1'])
    #             order, order_id = FuturesEnterOrder(1, 2, session_bybit)
    #             current_order_id = order_id
    #             print('--Присваиваем id и получаем код ответ')
    #             if order == 0:
    #                 print('--Ордер успешно выставлен')
    #                 isActiveOrder = True
    #                 print('--Ждём 1 сек')
    #                 time.sleep(2)
    #
    #     if isPosition:
    #         print('Есть позиция. Выход из цикла')
    #         break


if __name__ == "__main__":
    ticker = 'MEMEUSDT'
    main()
