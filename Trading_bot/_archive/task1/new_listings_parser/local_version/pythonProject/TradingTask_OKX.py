import logging

import okx.Trade as Trade
import okx.Account as Account
import okx.MarketData as MarketData
import okx.PublicData as PublicData
from datetime import datetime
import time

from Notifications import send_telegram_message
import asyncio

api_key  = '2666b857-dab7-4ad4-a557-f411fd8a9bb7'
# api_key = '65deb562-e15c-4fae-b7e3-514f5fef1b5e'
secret_key  = 'D7DB0C51E5D2ABEE4B412A985EC67F59'
# secret_key = '2DCB4772980591E2A008476BA4A25E8C'
# passphrase = 'Pass_phrase1'
passphrase = 'Pass_Phrase_1'

# passphrase ='Test_demo'

# Аккаунт Юли
# api_key = 'ad967e8c-d34f-4adf-a6b3-d04730308124'
# secret_key = '89ED836C4D004C1FF3BE73C8160CB76C'
# passphrase = 'VG82So0T5kIj#!'

flag = '0'

log_file = 'logfile.log'
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def getSpotPrice_okx(ticker):
    s_time = time.time()
    try:
        marketDataAPI = MarketData.MarketAPI(flag=flag)
        f_time = time.time()
        logging.info(f"getSpotPrice_okx is done. {(f_time - s_time)} sec: ")
        return marketDataAPI.get_ticker(instId=ticker.replace('USDT', '-USDT'))['data'][0]['last']
    except Exception as e:
        print('getSpotPrice_okx Error:', e)
        logging.info(f"getSpotPrice_okx Error: {e}")

        return -11


def getNumberAfterDot(ticker):
    s_time = time.time()
    try:
        publicDataAPI = PublicData.PublicAPI(flag=flag)
        f_time = time.time()
        logging.info(f"getNumberAfterDot is done. {(f_time - s_time)} sec: ")
        return publicDataAPI.get_instruments(instType='SWAP', instId=f'{ticker.replace("USDT", "-USDT")}-SWAP')['data'][0][
            'lotSz']
    except Exception as e:
        print('getSpotPrice_okx Error:', e)
        logging.info(f"getSpotPrice_okx Error: {e}")
        return -11


def getFuturesPrice_okx(ticker):
    s_time = time.time()
    try:
        publicDataAPI = PublicData.PublicAPI(flag=flag)
        f_time = time.time()
        logging.info(f"getFuturesPrice_okx is done. {(f_time - s_time)} sec: ")
        return publicDataAPI.get_mark_price(instType='SWAP', instId=f'{ticker.replace("USDT", "-USDT")}-SWAP')['data'][0][
            'markPx']
    except Exception as e:
        print('getSpotPrice_okx Error:', e)
        logging.info(f"getSpotPrice_okx Error: {e}")
        return -11


def getFuturesSize_okx(ticker):
    s_time = time.time()
    try:
        publicDataAPI = PublicData.PublicAPI(flag=flag)
        f_time = time.time()
        logging.info(f"getFuturesSize_okx is done. {(f_time - s_time)} sec: ")
        return publicDataAPI.get_instruments(instType='SWAP', instId=f'{ticker.replace("USDT", "-USDT")}-SWAP')['data'][0][
            'ctVal']
    except Exception as e:
        print('getFuturesPrice_okx Error', e)
        logging.info(f"getFuturesPrice_okx Error: {e}")
        return -11


def getSpotOrderInfo_okx(ticker, orderId):
    s_time = time.time()
    try:
        tradeAPI = Trade.TradeAPI(api_key, secret_key, passphrase, False, flag=flag)
        result = tradeAPI.get_order(instId=ticker.replace('USDT', '-USDT'), ordId=orderId)
        f_time = time.time()
        logging.info(f"getSpotOrderInfo_okx is done. {(f_time - s_time)} sec: ")
        return result
    except Exception as e:
        print('getSpotOrderInfo_okx Error', e)
        logging.info(f"getSpotOrderInfo_okx Error: {e}")

        return -11


def getFuturesOrderInfo_okx(ticker, orderId):
    s_time = time.time()
    try:
        tradeAPI = Trade.TradeAPI(api_key, secret_key, passphrase, False, flag=flag)
        result = tradeAPI.get_order(instId=ticker.replace('USDT', '-USDT-SWAP'), ordId=orderId)
        f_time = time.time()
        logging.info(f"getFuturesOrderInfo_okx is done. {(f_time - s_time)} sec: ")
        return result
    except Exception as e:
        print('getFuturesOrderInfo_okx Error', e)
        logging.info(f"getFuturesOrderInfo_okx Error: {e}")

        return -11


def SpotEnterOrder_okx(ticker, position_sum):
    s_time = time.time()
    try:
        # price = getSpotPrice_okx(ticker)
        # size = f"{position_sum / float(price)}"
        # print(size)
        tradeAPI = Trade.TradeAPI(api_key, secret_key, passphrase, False, flag=flag)
        result = tradeAPI.place_order(
            instId=ticker.replace('USDT', '-USDT'),
            tdMode='cash',
            side='buy',
            ordType='market',
            sz=position_sum
        )
        if result['code'] == '0':
            order_info = getSpotOrderInfo_okx(ticker, result['data'][0]['ordId'])
            # print(order_info)
            # print(
            #     f"Позиция успешно открыта. \n Было куплено: {order_info['data'][0]['accFillSz']} {ticker.replace('USDT', '')} \n По цене: ${order_info['data'][0]['avgPx']} \n Собственных средств: ${float(order_info['data'][0]['accFillSz']) * float(order_info['data'][0]['avgPx'])} \n Время заполнения ордера: {datetime.utcfromtimestamp(int(order_info['data'][0]['fillTime']) / 1000)} \n Комиссия ${float(order_info['data'][0]['fee']) * float(order_info['data'][0]['avgPx'])} \n Ссылка: https://www.okx.com/ru/trade-spot/{order_info['data'][0]['instId'].lower()}"
            #
            # )
            asyncio.run(send_telegram_message('Тест открытия позиции на споте OKX (реальная позиция)'))
            asyncio.run(send_telegram_message(
                f"Позиция успешно открыта. \n Было куплено: {order_info['data'][0]['accFillSz']} {ticker.replace('USDT', '')} \n По цене: ${order_info['data'][0]['avgPx']} \n Собственных средств: ${float(order_info['data'][0]['accFillSz']) * float(order_info['data'][0]['avgPx'])} \n Время заполнения ордера: {datetime.utcfromtimestamp(int(order_info['data'][0]['fillTime']) / 1000)} \n Комиссия ${float(order_info['data'][0]['fee']) * float(order_info['data'][0]['avgPx'])} \n Ссылка: https://www.okx.com/ru/trade-spot/{order_info['data'][0]['instId'].lower()}"
            ))

            f_time = time.time()
            logging.info(f"SpotEnterOrder_okx is done. {(f_time - s_time)} sec: ")

            return 0
        else:
            print('Error in SpotEnterOrder_okx')
            print(result)
            asyncio.run(send_telegram_message(f"Error in SpotEnterOrder_okx \n {result['data'][0]['sMsg']}"))
            return result['code']
    except Exception as e:
        print('SpotEnterOrder_okx Error',e)
        logging.info(f"SpotEnterOrder_okx Error: {e}")

        return -11


def SetLeverage_okx(ticker, leverage):
    s_time = time.time()
    try:
        accountAPI = Account.AccountAPI(api_key, secret_key, passphrase, False, flag=flag)
        result = accountAPI.set_leverage(lever=leverage, mgnMode='isolated',
                                         instId=ticker.replace('USDT', '-USDT') + '-SWAP')
        f_time = time.time()
        logging.info(f"SetLeverage_okx is done. {(f_time - s_time)} sec: ")

        return result
    except Exception as e:
        print('SetLeverage_okx Error', e)
        logging.info(f"SetLeverage_okx Error: {e}")

        return -11


def FuturesEnterOrder_okx(ticker, position_sum, leverage):
    s_time = time.time()
    try:
        start_time = time.time() * 1000
        SetLeverage_okx(ticker, leverage)
        tradeAPI = Trade.TradeAPI(api_key, secret_key, passphrase, False, flag=flag)
        multiplier = float(getFuturesSize_okx(ticker))
        pos_amount = f'{float(position_sum) * float(leverage) / multiplier /float(getFuturesPrice_okx(ticker))}'
        print('MULTIPLIER', multiplier)
        print('POS AMOUNT ', round(float(pos_amount), int(getNumberAfterDot(ticker))-1))
        result = tradeAPI.place_order(
            instId=ticker.replace('USDT', '-USDT') + '-SWAP',
            tdMode='isolated',
            side='buy',
            ordType='market',
            sz=round(float(pos_amount), int(getNumberAfterDot(ticker))-1)
        )
        if result['code'] == '0':
            order_info = getFuturesOrderInfo_okx(ticker, result['data'][0]['ordId'])
            # print(order_info)
            # print(order_info['data'][0]['fillTime'])
            # print(start_time)
            # print(type(order_info['data'][0]['fillTime']), type(start_time))
            # print(type(float(order_info['data'][0]['fillTime'])), type(float(start_time)))
            # print(float((float(order_info['data'][0]['fillTime']) - float(start_time)))/1000)

            # print(
            #     f"Позиция успешно открыта. \n Было куплено: {float(order_info['data'][0]['accFillSz'])*float(multiplier)} {ticker.replace('USDT', '')} \n По цене: ${order_info['data'][0]['avgPx']} \n Размер позиции: ${float(order_info['data'][0]['accFillSz'])*float(multiplier) * float(order_info['data'][0]['avgPx'])} \n Плечо: {leverage}x \n Собственных средств: {float(order_info['data'][0]['accFillSz'])*float(multiplier) * float(order_info['data'][0]['avgPx']) / leverage} \n Время заполнения ордера: {datetime.utcfromtimestamp(int(order_info['data'][0]['fillTime']) / 1000)} \n Потрачено времени: {float((float(order_info['data'][0]['fillTime']) - float(start_time)))/1000} секунд \n Комиссия ${float(order_info['data'][0]['accFillSz'])*float(multiplier) * float(order_info['data'][0]['avgPx'])*0.0005} \n Ссылка: https://www.okx.com/ru/trade-swap/{order_info['data'][0]['instId'].lower()}"
            #
            # )
            asyncio.run(send_telegram_message('Тест открытия позиции на фьючерсах OKX (демо-режим)'))
            asyncio.run(send_telegram_message(
                f"Позиция успешно открыта. \n Было куплено: {float(order_info['data'][0]['accFillSz']) * float(multiplier)} {ticker.replace('USDT', '')} \n По цене: ${order_info['data'][0]['avgPx']} \n Размер позиции: ${float(order_info['data'][0]['accFillSz']) * float(multiplier) * float(order_info['data'][0]['avgPx'])} \n Плечо: {leverage}x \n Собственных средств: {float(order_info['data'][0]['accFillSz']) * float(multiplier) * float(order_info['data'][0]['avgPx']) / leverage} \n Время заполнения ордера: {datetime.utcfromtimestamp(int(order_info['data'][0]['fillTime']) / 1000)} \n Потрачено времени: {float((float(order_info['data'][0]['fillTime']) - float(start_time))) / 1000} секунд \n Комиссия ${float(order_info['data'][0]['accFillSz']) * float(multiplier) * float(order_info['data'][0]['avgPx']) * 0.0005} \n Ссылка: https://www.okx.com/ru/trade-swap/{order_info['data'][0]['instId'].lower()}"
            ))
            f_time = time.time()
            logging.info(f"FuturesEnterOrder_okx is done. {(f_time - s_time)} sec: ")

            return 0
        else:
            print('Error in FutureEnterOrder_okx')
            print(result)
            asyncio.run(send_telegram_message(f"Error in FuturesEnterOrder_okx \n {result['data'][0]['sMsg']}"))
        return result
    except Exception as e:
        print('FuturesEnterOrder_okx Error', e)
        logging.info(f"FuturesEnterOrder_okx Error: {e}")

        return -11


# print(getSpotPrice_okx('DOGEUSDT'))
# print(SpotEnterOrder_okx('DOGEUSDT', 2))
# print(SetLeverage_okx('DOGEUSDT', 2))
print(FuturesEnterOrder_okx('DOGEUSDT',5,50))
# print(getFuturesSize_okx('BTCUSDT'))
# print(getFuturesSize_okx('BTCUSDT'))
# print(FuturesEnterOrder_okx('DOGEUSDT',2,2))
# print(getFuturesPrice_okx('ETHUSDT'))
# print(getSpotPrice_okx('ETHUSDT'))
# print(getNumberAfterDot('ETHUSDT'))
