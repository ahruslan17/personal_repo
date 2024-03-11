import random
import sys
import time
import logging
import asyncio
from datetime import datetime

from pybit.unified_trading import HTTP
from pybit.unified_trading import WebSocket  # pip install pybit
import json
import asyncio
import ccxt.pro as ccxtpro
import ccxt
from telegram import Bot

log_file = 'logfile_BybitTT.log'
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

token = '6354808644:AAEA9pvVZj6YqvXKCyyyF9ay0q4mdXqXfxE'
chatId = -1001995965101  # мой тестовый чат
# chatId = -1002096660763 # наш основной чат

exchange = ccxtpro.bybit()
exchange.apiKey = 'HS398zpUdxSahhV6se'
exchange.secret = 'e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T'

# globals
ticker = 'MEMEUSDT'
leverage = 2
profit_percentage = 6
loss_percentage = profit_percentage/2
ALL_MARGIN = 5
TIMEOUT = 60  # position timeout in minutes

cum_margin = 0
enter_price = 0
pos_size_to_sell = 0

orderbook = 0
qActiveOrders = 0
qActivePositions = 0
current_position = 0
current_order_id = 0
pos_start_datetime = 0

isSold = False


async def send_telegram_message(message_text):
    try:
        bot = Bot(token=token)
        await bot.send_message(chat_id=chatId, text=message_text)
    except Exception as e:
        print('Сообщение не отправлено', e)


async def getOrderBook():
    global orderbook
    while True:
        # await asyncio.sleep(0.1)
        ob = await exchange.watch_order_book(symbol=ticker, limit=50)
        current = {}
        current['best_bid_0'] = ob['bids'][0]
        # current['best_bid_1'] = ob['bids'][1]
        # current['best_bid_2'] = ob['bids'][2]
        # current['best_bid_3'] = ob['bids'][3]
        # current['best_bid_49'] = ob['bids'][49]
        # current['best_bid_5'] = ob['bids'][5]
        # print(current['best_bid_5'])
        # current['best_ask_0'] = ob['asks'][0]
        # current['best_ask_1'] = ob['asks'][1
        # current['best_ask_2'] = ob['asks'][2]
        # current['best_ask_3'] = ob['asks'][3]
        current['best_ask_4'] = ob['asks'][4]
        # current['best_ask_5'] = ob['asks'][5]
        orderbook = [current]


# async def getOrders():
#     global isActiveOrder, qActivePositions
#     while True:
#         exchange = ccxtpro.bybit()
#         exchange.apiKey = 'HS398zpUdxSahhV6se'
#         exchange.secret = 'e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T'
#         # await asyncio.sleep(0.2)
#         orders = await exchange.watch_orders(symbol=ticker)
#         o = orders
#         # print('o: ', o)


async def getPositions():
    global qActivePositions, qActiveOrders, POS_ARCH, cum_margin, enter_price, pos_size_to_sell, pos_start_datetime
    # exchange = ccxtpro.bybit()
    # exchange.apiKey = 'HS398zpUdxSahhV6se'
    # exchange.secret = 'e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T'
    while True:
        positions = await exchange.watch_positions()
        p = positions
        for i in range(len(p)):
            if p[i]['info']['symbol'] == ticker and p[i]['info']['side'] == 'Buy':
                qActivePositions = 1

                print('Позиция: ', p[i])
                if qActivePositions > 0:
                    qActiveOrders = 0

                print('Количество позиций qActivePositions: ', qActivePositions)
                print('Размещено денег в позиции: ', cum_margin)
                print('id позиции: ', p[i]['info']['createdTime'])
                print('Цена входа в позицию: ', p[i]['entryPrice'])

                if enter_price != float(p[i]['entryPrice']):
                    enter_price = float(p[i]['entryPrice'])

                if pos_size_to_sell != float(p[i]['contracts']):
                    pos_size_to_sell = float(p[i]['contracts'])

                if pos_start_datetime == 0:
                    pos_start_datetime = float(p[i]['info']['updatedTime'])

                print(f'Баланс позиции ', p[i]['info']['positionBalance'])
                print('Осталось разместить в позиции: ', ALL_MARGIN - cum_margin)
                cum_margin = float(p[i]['info']['positionBalance'])

        await asyncio.sleep(0.2)


# def createFuturesLongOrder(exchange, position_sum, leverage):
#     amount = f"{round(leverage * position_sum / orderbook[-1]['best_bid_5'][0], 0)}"
#     order = exchange.create_order(symbol=ticker, type='Limit', side='Buy', amount=50,
#                                   price=orderbook[-1]['best_bid_5'][0])  # (symbol, type, side, amount, price)
#     if order:
#         print('Сигнал на отправку ордера. Ответ: ', order)


def FuturesEnterOrder(position_sum, leverage, session_bybit):
    global ticker, qActiveOrders
    s_time = time.time()
    print('Ордербук ', orderbook)
    qty = f"{round(leverage * position_sum / orderbook[-1]['best_ask_4'][0], 0)}"
    print('!!!!!!!!!!', qty)
    print('Количество активов для открытия позции: ', qty)
    response = session_bybit.place_order(
        category="linear",
        symbol=ticker,
        side="Buy",
        orderType="Limit",
        price=orderbook[-1]['best_ask_4'][0],
        qty=qty
    )
    f_time = time.time()
    print(response)
    print(f_time - s_time)
    try:

        if response['retCode'] == 0:
            print('Сообщение об успешном размещении ордера')
            qActiveOrders += 1
            print('Счетчик текущих ордеров увеличен на один')
        if response['retCode'] != 0:
            print('Сообщение об ошибке при размещении ордера')

        return response['retCode'], response['result']['orderId']
    except Exception as e:
        print('Futures order Error: ', e)
        return -1, -1


def FuturesExitLimitOrder(position_qty, price, session_bybit):
    global ticker, qActiveOrders
    s_time = time.time()
    print('Ордербук ', orderbook)
    print('Количество активов для открытия позции: ', position_qty)
    response = session_bybit.place_order(
        category="linear",
        symbol=ticker,
        side="Sell",
        orderType="Limit",
        price=price,
        qty=position_qty
    )
    f_time = time.time()
    print(response)
    print(f_time - s_time)
    try:

        if response['retCode'] == 0:
            print('Сообщение об успешном размещении ордера')
            qActiveOrders += 1
            print('Счетчик текущих ордеров увеличен на один')
        if response['retCode'] != 0:
            print('Сообщение об ошибке при размещении ордера')

        return response['retCode'], response['result']['orderId']
    except Exception as e:
        print('Futures order Error: ', e)
        return -1, -1


def FuturesExitOrder(amount, session_bybit):
    global ticker, qActiveOrders, qActivePositions, isSold
    s_time = time.time()
    print('Количество активов для закрытия позции: ', amount)
    response = session_bybit.place_order(
        category="linear",
        symbol=ticker,
        side="Sell",
        orderType="Market",
        qty=amount
    )
    f_time = time.time()
    print(response)
    print(f_time - s_time)
    try:

        if response['retCode'] == 0:
            print('Сообщение об успешном размещении ордера')
            qActiveOrders += 1
            isSold = True
            print('Счетчик текущих позиций уменьшен на один')
        if response['retCode'] != 0:
            print('Сообщение об ошибке при размещении ордера')

        return response['retCode'], response['result']['orderId']
    except Exception as e:
        print('Futures order Error: ', e)
        return -1, -1


def StopLossPrice(entry_price, loss_percentage, leverage):
    stop_price = entry_price * (1 - loss_percentage / 100 / leverage)
    return stop_price


def TakeProfitPrice(entry_price, profit_percentage, leverage):
    take_profit_price = entry_price * (1 + profit_percentage / 100 / leverage)
    return take_profit_price


def CancelFuturesOrder(order_id, session):
    global ticker, qActiveOrders
    try:
        response = session.cancel_order(
            category="linear",
            symbol=ticker,
            orderId=order_id,
        )
        print(response)
        if response['retCode'] == 0:
            print('Ордер успешно отменён')
            # qActiveOrders -= 1

        else:
            print('Ордер не отменен, ', response['retCode'])

        return response['retCode']
    except Exception as e:
        print('Ошибка отмены ордера: ', e)
        return -1


async def main():
    global current_order_id, positions_task, orders_task, isSold, qActiveOrders
    print('Main is started')
    asyncio.create_task(send_telegram_message('15 минут до листинга. Открываем позицию.'))

    order_book_task = asyncio.create_task(getOrderBook())

    bybit = ccxt.bybit()
    bybit.apiKey = 'HS398zpUdxSahhV6se'
    bybit.secret = 'e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T'
    session_bybit = HTTP(api_key='HS398zpUdxSahhV6se', api_secret='e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T')

    i = 0
    await asyncio.sleep(5)
    try:
        isMessageSent = False
        while True:
            positions_task = asyncio.create_task(getPositions())
            # orders_task = asyncio.create_task(getOrders())
            i += 1
            print(i)
            print('Количество ордеров в памяти qActiveOrders: ', qActiveOrders)
            print('Количество позиций qActivePositions: ', qActivePositions)
            if i > 3:

                if cum_margin >= ALL_MARGIN - 2:  # полностью вошли в позицию

                    # time_in_position += 1

                    print('Простановка ордеров на вход запрещена. ВСЕ ДЕНЬГИ ЗАГРУЖЕНЫ В ПОЗИЦИЮ.')
                    print('Отслеживание стоп-лосса и тейк профита включено. Количество активов на продажу: ',
                          pos_size_to_sell)
                    stop_price = round(StopLossPrice(entry_price=enter_price, loss_percentage=loss_percentage, leverage=leverage), 5)
                    print('--Цена стоп-лосса: ', stop_price)
                    profit_price = round(TakeProfitPrice(entry_price=enter_price, profit_percentage=profit_percentage, leverage=leverage), 5)

                    if not isMessageSent:
                        asyncio.create_task(send_telegram_message(f'Информация о входе в позицию \n Инструмент: {ticker} \n Свобственных средств: {pos_size_to_sell*enter_price/leverage} USDT \n Плечо: {leverage}x \n Размер позиции: {pos_size_to_sell*enter_price} USDT \n Было куплено: {pos_size_to_sell}{ticker.replace("USDT","")} \n Средняя цена входа: {enter_price} \n Уровень тейк-профита {profit_percentage}% \n Уровень стоп-лосса {loss_percentage}% \n Профит-цена: ${profit_price} \n Стоп-цена: ${stop_price}'))
                        isMessageSent = True

                    print('--Цена тейк профита: ', profit_price)
                    print('--Текущая цена ', orderbook[-1]['best_bid_0'][0])
                    # FuturesExitLimitOrder(pos_size_to_sell, profit_price, session_bybit)

                    if float(orderbook[-1]['best_bid_0'][0]) >= profit_price:
                        print('Цена тейк-профита достигнута. Закрыть лимиткой')
                        print('Количество позиций: ', qActivePositions)
                        FuturesExitOrder(pos_size_to_sell, session_bybit=session_bybit)
                        await asyncio.sleep(2)
                        # isSold = True
                        if isSold:
                            asyncio.create_task(send_telegram_message(f'Позиция закрыта по Take-Profit. Прибыль составила {pos_size_to_sell*enter_price*profit_percentage/100} USDT'))
                            await asyncio.sleep(2)
                            print(
                                'Все позиции закрыты. Сигнал на завершение работы торгового задания. Заполнили тейк профит.')
                            break

                    if float(orderbook[-1]['best_bid_0'][0]) <= stop_price:
                        print('Цена стоп-лосса достигнута. Закрыть по маркету')
                        print('Количество позиций: ', qActivePositions)
                        FuturesExitOrder(pos_size_to_sell, session_bybit=session_bybit)
                        await asyncio.sleep(2)
                        if isSold:
                            asyncio.create_task(send_telegram_message(f'Позиция закрыта по Stop-Loss. Убыток составил {pos_size_to_sell*enter_price*loss_percentage/100} USDT'))
                            await asyncio.sleep(2)

                            print(
                                'Все позиции закрыты. Сигнал на завершение работы торгового задания. Заполнили стоп лосс.')
                            break

                    if time.time() * 1000 >= pos_start_datetime + TIMEOUT*60*1000:
                        print('Превышен лимит по времени. Закрыть по маркету. ')
                        if qActivePositions == 1:
                            FuturesExitOrder(pos_size_to_sell, session_bybit=session_bybit)
                            await asyncio.sleep(2)
                        if isSold:
                            asyncio.create_task(send_telegram_message(f'Позиция закрыта через {TIMEOUT} минут по маркету. Прибыль составила {(orderbook[-1]["best_bid_0"][0] - enter_price)*pos_size_to_sell} USDT ({((orderbook[-1]["best_bid_0"][0] - enter_price)*pos_size_to_sell) / (pos_size_to_sell*enter_price/leverage) * 100} %)'))
                            await asyncio.sleep(2)

                            print(
                                'Все позиции закрыты. Сигнал на завершение работы торгового задания. Лимит по времени.')
                            break


                else:
                    print('Простановка ордеров разрешена')
                    if qActiveOrders > 0:
                        print('Удалить ордер')
                        CancelFuturesOrder(order_id=current_order_id, session=session_bybit)
                        qActiveOrders -= 1
                        # time.sleep(1)

                    if qActiveOrders == 0:
                        print('Текущих ордеров нет. Открыть новый ордер')
                        delay = random.uniform(2, 6)
                        print(f'Ждем {delay / 10} секунд перед открытием нового ордера. Для защиты')
                        await asyncio.sleep(delay / 10)
                        order_code, order_id = FuturesEnterOrder(ALL_MARGIN-cum_margin, leverage, session_bybit)
                        if order_code == 0:
                            current_order_id = order_id
                            print('Новый ордер ', order_id)
                            # time.sleep(1)

            # if i == 10:
            #     # await createFuturesLongOrder(bybit, 2, 2)
            #     createFuturesLongOrder(bybit, 2, 2)
            #
            await asyncio.sleep(1.5)  # Sleep for 5 seconds (adjust as needed)
        print('Работа программы завершена')
        await asyncio.sleep(1.5)
        asyncio.create_task(send_telegram_message('Выполнение торгового задания завершено без ошибок.'))
        await asyncio.sleep(1.5)
    except KeyboardInterrupt as inter:
        print(inter)
    except Exception as ex:
        pass
        # print(ex)
    finally:
        # orders_task.cancel()
        positions_task.cancel()
        order_book_task.cancel()
        try:
            await order_book_task
        except asyncio.CancelledError as e:
            print(e)


# Run the main function
if __name__ == "__main__":
    # asyncio.run(main())
    # start_time = time.time()*1000 + 60000/6
    # start_time = 1700175600*1000 + 5*60*1000 + 3*60*1000
    start_time = 1700654750706
    asyncio.run(send_telegram_message(f'Тестовое торговое задание запущено. \n Листинг {ticker} \n Дата: {datetime.utcfromtimestamp(start_time/1000)} UTC+0\n Ожидание {datetime.utcfromtimestamp(start_time/1000 - 15*60)} UTC+0'))

    while True:
        time.sleep(10)
        print('Ожидание...')
        isStarted = False
        if isStarted == False and time.time()*1000 >= start_time - 15*60*1000:
            asyncio.run(main())
            isStarted = True
            break
