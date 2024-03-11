# from __future__ import print_function
import logging

from gate_api import SpotApi, ApiClient, FuturesApi, FuturesOrder, FuturesTrade, Order
from datetime import datetime
from Notifications import send_telegram_message
import asyncio
import time

# API_KEY = 'c1a1f7ae13be0492eb25e4cea848d84f'  # test
API_KEY = 'f6ef804d08f28800337b5abba2c05fae'
# API_SECRET = 'b38ab690a39b9e4f56b766c24456a84ff62509413f219fff1ebf9f27a9aeb5d3'  # test
API_SECRET = '8c27d7168eca569e95d4f85e7f9dc09b69337ab82ac2eb2a6285a703d7cbb1d0'

# spot_api = SpotApi(ApiClient(gate_api.Configuration(host="https://api.gateio.ws/api/v4", key=API_KEY, secret=API_SECRET)))
# futures_api = FuturesApi(ApiClient(gate_api.Configuration(host="https://api.gateio.ws/api/v4", key=API_KEY, secret=API_SECRET)))

log_file = 'logfile.log'
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def getSpotPrice_gateio(ticker, spot_api):
    s_time = time.time()
    try:
        tickers = spot_api.list_tickers(currency_pair=ticker.replace('USDT', '_USDT'))
        price = tickers[0].last
        f_time = time.time()
        logging.info(f"getSpotPrice_gateio is done. {(f_time - s_time)} sec: ")

        return price
    except Exception as e:
        print('getSpotPrice_gateio Error', e)
        logging.info(f"getSpotPrice_gateio Error: {e}")

        return -11


def placeSpotOrder_gateio(ticker, amount, spot_api):
    s_time = time.time()
    try:
        start_time = time.time() * 1000
        currency_pair = ticker.replace('USDT', '_USDT')
        # pair = spot_api.get_currency_pair(currency_pair)
        # min_amount = pair.min_base_amount
        # position_amount = float(amount)/float(getSpotPrice_gateio(ticker))
        order = Order(amount=str(amount), type='market', side='buy', currency_pair=currency_pair, time_in_force='ioc')
        created = spot_api.create_order(order)
        print(order)
        print(created)

        if created.status == 'closed':
            print('Позиция открыта')
            order_result = spot_api.get_order(created.id, currency_pair)
            print(order_result)
            print(
                f"Информация о позиции \n Позиция успешно открыта на GateIo Spot Market \n Было куплено: {amount / float(order_result.avg_deal_price)} {ticker.replace('USDT', '')} \n По цене: ${order_result.avg_deal_price} \n Собственных средств: {amount} \n Время заполнения ордера: {datetime.utcfromtimestamp(order_result.create_time_ms / 1000)} \n Время исполнения {float(float(int(order_result.create_time_ms)) - float(start_time)) / 1000} \n Комиссия ${amount * 0.2 / 100} \n Ссылка: https://www.gate.io/ru/USDT/{order_result.currency_pair}"
            )
            asyncio.run(send_telegram_message(
                f"Информация о позиции \n Позиция успешно открыта на GateIo Spot Market \n Было куплено: {amount / float(order_result.avg_deal_price)} {ticker.replace('USDT', '')} \n По цене: ${order_result.avg_deal_price} \n Собственных средств: {amount} \n Время заполнения ордера: {datetime.utcfromtimestamp(order_result.create_time_ms / 1000)} \n Время исполнения {float(float(int(order_result.create_time_ms)) - float(start_time)) / 1000} \n Комиссия ${amount * 0.2 / 100} \n Ссылка: https://www.gate.io/ru/USDT/{order_result.currency_pair}"
            ))
            f_time = time.time()
            logging.info(f"placeSpotOrder_gateio is done. {(f_time - s_time)} sec: ")

            return 0
        else:
            print('Позиция не открыта')
            logging.info(f"Позиция не открыта")

            return -1

    except Exception as e:
        print('placeSpotOrder_gateio Error', e)
        logging.info(f"placeSpotOrder_gateio Error: {e}")

        return -11


def placeFuturesOrder_gateio(ticker, position_sum, leverage, futures_api):
    s_time = time.time()
    try:
        start_time = time.time() * 1000
        settle = 'usdt'
        leverage = str(leverage)
        contract = ticker.replace('USDT', '_USDT')
        futures_api.update_position_leverage(settle, contract, leverage)
        last_price = getFuturesPrice_gateio(ticker, futures_api)

        futures_contract = futures_api.get_futures_contract(settle, contract)
        # print(futures_contract)
        # print(futures_contract.quanto_multiplier)

        pos_amount = float(position_sum) * float(leverage) / float(futures_contract.quanto_multiplier) / float(
            last_price)

        # print(pos_amount)
        # print(round(pos_amount))

        order = FuturesOrder(contract=contract, size=round(pos_amount), price="0", tif='ioc')
        order_response = futures_api.create_futures_order(settle, order)

        if order_response.status == 'finished':
            futures_order = futures_api.get_futures_order(settle, str(order_response.id))
            print(futures_order)

            # print(int(futures_order.finish_time * 1000))
            # print(float(float(int(futures_order.finish_time * 1000)) - float(start_time)) / 1000)
            print(
                f"Информация о позиции \n Позиция успешно открыта на GateIo Futures Market \n Было куплено: {float(futures_order.size) * float(futures_contract.quanto_multiplier)} {ticker.replace('USDT', '')} \n По цене: ${futures_order.fill_price} \n Размер позиции: ${futures_order.size * float(futures_contract.quanto_multiplier) * float(futures_order.fill_price)} \n Плечо: {leverage}x \n Собственных средств: {futures_order.size * float(futures_contract.quanto_multiplier) * float(futures_order.fill_price) / float(leverage)} \n Время заполнения ордера: {datetime.utcfromtimestamp(int(futures_order.finish_time))} \n Время исполнения {float(float(int(futures_order.finish_time * 1000)) - float(start_time)) / 1000} \n Комиссия ${0.05 / 100 * float(futures_order.size) * float(futures_contract.quanto_multiplier) * float(futures_order.fill_price)} \n Ссылка: https://www.gate.io/ru/futures/USDT/{futures_order.contract}"
            )

            # asyncio.run(send_telegram_message('Тест открытия позиции на фьючерсах Gate.io (демо-режим)'))
            asyncio.run(send_telegram_message(
                f"Информация о позиции \n Позиция успешно открыта на GateIo Futures Market \n Было куплено: {float(futures_order.size) * float(futures_contract.quanto_multiplier)} {ticker.replace('USDT', '')} \n По цене: ${futures_order.fill_price} \n Размер позиции: ${futures_order.size * float(futures_contract.quanto_multiplier) * float(futures_order.fill_price)} \n Плечо: {leverage}x \n Собственных средств: {futures_order.size * float(futures_contract.quanto_multiplier) * float(futures_order.fill_price) / float(leverage)} \n Время заполнения ордера: {datetime.utcfromtimestamp(int(futures_order.finish_time))} \n Время исполнения {float(float(int(futures_order.finish_time * 1000)) - float(start_time)) / 1000} \n Комиссия ${0.05 / 100 * float(futures_order.size) * float(futures_contract.quanto_multiplier) * float(futures_order.fill_price)} \n Ссылка: https://www.gate.io/ru/futures/USDT/{futures_order.contract}"
            ))
        f_time = time.time()
        logging.info(f"placeFuturesOrder_gateio is done. {(f_time - s_time)} sec: ")

        return order_response
    except Exception as e:
        print('placeFuturesOrder_gateio Error', e)
        logging.info(f"placeFuturesOrder_gateio Error: {e}")

        return -11


def getFuturesPrice_gateio(ticker, futures_api):
    s_time = time.time()
    try:
        tickers = futures_api.get_futures_contract('usdt', ticker.replace('USDT', '_USDT')).last_price
        f_time = time.time()
        logging.info(f"getFuturesPrice_gateio is done. {(f_time - s_time)} sec: ")

        return tickers
    except Exception as e:
        print('getFuturesPrice_gateio Error', e)
        logging.info(f"getFuturesPrice_gateio Error: {e}")
        return -11

# placeFuturesOrder_gateio('YGGUSDT', 1, 2)
# placeSpotOrder_gateio('YGGUSDT', 2)
