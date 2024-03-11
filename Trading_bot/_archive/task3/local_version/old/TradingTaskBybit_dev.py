import time
import logging
import asyncio
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

# globals
ALL_MARGIN = 10
POS_ARCH = []
cum_margin = 0
orderbook = []
qActiveOrders = 0
qActivePositions = 0
current_position = 0
current_order_id = 0
ticker = 'MEMEUSDT'
pip_size = 0


async def getOrderBook():
    global orderbook
    exchange = ccxtpro.bybit()
    exchange.apiKey = 'HS398zpUdxSahhV6se'
    exchange.secret = 'e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T'
    while True:
        await asyncio.sleep(0.1)
        ob = await exchange.watch_order_book(symbol=ticker, limit=50)
        current = {}
        # current['best_bid_0'] = ob['bids'][0]
        # current['best_bid_1'] = ob['bids'][1]
        # current['best_bid_2'] = ob['bids'][2]
        # current['best_bid_3'] = ob['bids'][3]
        # current['best_bid_4'] = ob['bids'][4]
        # current['best_bid_5'] = ob['bids'][5]
        # print(current['best_bid_5'])
        current['best_ask_0'] = ob['asks'][0]
        # current['best_ask_1'] = ob['asks'][1]
        # current['best_ask_2'] = ob['asks'][2]
        # current['best_ask_3'] = ob['asks'][3]
        current['best_ask_4'] = ob['asks'][4]
        # current['best_ask_5'] = ob['asks'][5]
        orderbook.append(current)


async def getOrders():
    global isActiveOrder, qActivePositions
    while True:
        exchange = ccxtpro.bybit()
        exchange.apiKey = 'HS398zpUdxSahhV6se'
        exchange.secret = 'e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T'
        # await asyncio.sleep(0.2)
        orders = await exchange.watch_orders(symbol=ticker)
        o = orders
        print('o: ', o)




async def getPositions():
    global qActivePositions, qActiveOrders, POS_ARCH, cum_margin
    while True:
        exchange = ccxtpro.bybit()
        exchange.apiKey = 'HS398zpUdxSahhV6se'
        exchange.secret = 'e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T'
        positions = await exchange.watch_positions()
        p = positions
        print('p: ', p)

        for i in range(len(p)):
            if p[i]['info']['position_id'] not in POS_ARCH:
                POS_ARCH.append(p[i]['info']['position_id'])
                cum_margin += p[i]['info']['positionValue']
        print('Количество позиций: ', len(p))
        print('Архив позиций: ', POS_ARCH)
        print('Размещено денег в позиции: ', cum_margin)
        if p:
            if qActivePositions == 0:
                qActiveOrders -= 1

            qActivePositions = len(p)
        # await asyncio.sleep(0.1)




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
            print('Счетчик текущих позиций увеличен на один')
        if response['retCode'] != 0:
            print('Сообщение об ошибке при размещении ордера')

        return response['retCode'], response['result']['orderId']
    except Exception as e:
        print('Futures order Error: ', e)
        return -1, -1

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
            qActiveOrders -= 1

        else:
            print('Ордер не отменен, ', response['retCode'])

        return response['retCode']
    except Exception as e:
        print('Ошибка отмены ордера: ', e)
        return -1


async def main():
    global current_order_id, positions_task, orders_task
    print('Main is started')

    order_book_task = asyncio.create_task(getOrderBook())

    bybit = ccxt.bybit()
    bybit.apiKey = 'HS398zpUdxSahhV6se'
    bybit.secret = 'e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T'
    session_bybit = HTTP(api_key='HS398zpUdxSahhV6se', api_secret='e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T')

    i = 0
    await asyncio.sleep(10)
    try:
        while True:
            positions_task = asyncio.create_task(getPositions())
            orders_task = asyncio.create_task(getOrders())
            i += 1
            print(i)
            print('Количество ордеров в памяти: ', qActiveOrders)
            if i > 3:

                if qActivePositions > 0:
                    print('Простановка ордеров запрещена')
                elif qActivePositions == 0:
                    print('Простановка ордеров разрешена')


                if qActiveOrders > 0:
                    print('Удалить ордер')
                    CancelFuturesOrder(order_id=current_order_id, session=session_bybit)
                    time.sleep(1)

                if qActiveOrders == 0 and qActivePositions == 0:
                    print('Можно открыть новый ордер')
                    order_code, order_id = FuturesEnterOrder(1, 2, session_bybit)
                    if order_code == 0:
                        current_order_id = order_id
                        print('Новый ордер ', order_id)
                        time.sleep(1)

            # if i == 10:
            #     # await createFuturesLongOrder(bybit, 2, 2)
            #     createFuturesLongOrder(bybit, 2, 2)
            #
            await asyncio.sleep(0.01)  # Sleep for 5 seconds (adjust as needed)

    except KeyboardInterrupt:
        pass
    finally:
        orders_task.cancel()
        positions_task.cancel()
        order_book_task.cancel()
        try:
            await order_book_task
        except asyncio.CancelledError:
            pass


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
