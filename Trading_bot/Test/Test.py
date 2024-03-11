import random
import time
import logging
from datetime import datetime
from pybit.unified_trading import HTTP
import asyncio
import ccxt.pro as ccxtpro
import ccxt
from telegram import Bot

from gate_api import SpotApi, ApiClient, FuturesApi, FuturesOrder, FuturesTrade, Order, \
    Configuration  # pip install gate_api


# import gate_api


# 'apiKey': '7c23279c9e4fc1f29fae8d422416cf3d',
# 'secret': '806ed766381651e4a6ce3197ff462b680dc53a2998b5b381033061a775d06953',
class TradingTask:
    def __init__(self, exchange_name, ticker, listing_date, leverage, profit_percentage, loss_percentage, ALL_MARGIN,
                 TIMEOUT):
        self.bot_token = '6354808644:AAEA9pvVZj6YqvXKCyyyF9ay0q4mdXqXfxE'
        # self.chatId = -1002096660763 # general
        self.chatId = -1001995965101  # debug
        self.exchange_name = exchange_name

        if exchange_name == 'bybit':
            self.exchange = ccxtpro.bybit()
            self.exchange.apiKey = 'HS398zpUdxSahhV6se'
            self.exchange.secret = 'e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T'
            self.session_bybit = HTTP(api_key='HS398zpUdxSahhV6se', api_secret='e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T')

        if exchange_name == 'gateio':
            API_KEY = 'f6ef804d08f28800337b5abba2c05fae'
            API_SECRET = '8c27d7168eca569e95d4f85e7f9dc09b69337ab82ac2eb2a6285a703d7cbb1d0'
            # API_KEY_test = 'c1a1f7ae13be0492eb25e4cea848d84f'
            # API_SECRET_test = 'b38ab690a39b9e4f56b766c24456a84ff62509413f219fff1ebf9f27a9aeb5d3'
            self.multiplier = 0
            self.exchange = ccxtpro.gate({
                'apiKey': API_KEY,
                'secret': API_SECRET,
                'uid': '14274293'
                # 'options': {
                #     'defaultType': 'future'
                # }
            })  # для спота выбрать спот

            self.gate_futures_api = FuturesApi(
                ApiClient(Configuration(host="https://api.gateio.ws/api/v4", key=API_KEY, secret=API_SECRET)))
            # ApiClient(Configuration(host="https://fx-api-testnet.gateio.ws/api/v4", key=API_KEY_test, secret=API_SECRET_test)))

            # self.exchange.apiKey = '7c23279c9e4fc1f29fae8d422416cf3d'
            # self.exchange.secret = '806ed766381651e4a6ce3197ff462b680dc53a2998b5b381033061a775d06953'
            # self.exchange.uid = '14274293'

        self.ticker = ticker
        self.listing_date = listing_date
        self.leverage = leverage
        self.profit_percentage = profit_percentage
        self.loss_percentage = loss_percentage
        self.ALL_MARGIN = ALL_MARGIN
        self.TIMEOUT = TIMEOUT  # minutes

        self.cum_margin = 0
        self.enter_price = 0
        self.pos_size_to_sell = 0
        self.orderbook = 0
        self.qActiveOrders = 0
        self.qActivePositions = 0
        self.round_number = 0
        # self.current_position = 0
        self.current_order_id = 0
        self.pos_start_datetime = 0
        self.isSold = False

    async def send_telegram_message(self, message_text):
        try:
            bot = Bot(token=self.bot_token)
            await bot.send_message(chat_id=self.chatId, text=message_text)
        except Exception as e:
            print('Сообщение не отправлено', e)

    async def getOrderBook(self):

        if self.exchange_name == 'bybit':
            while True:
                # await asyncio.sleep(0.1)
                ob = await self.exchange.watch_order_book(symbol=self.ticker, limit=50)
                current = {'best_bid_0': ob['bids'][0], 'best_ask_4': ob['asks'][4]}
                self.orderbook = [current]

        if self.exchange_name == 'gateio':
            while True:
                # await asyncio.sleep(0.1)
                ob = await self.exchange.watch_order_book(symbol=self.ticker.replace('USDT', '_USDT'),
                                                          limit=5)  # чтобы был спот, надо /USDT
                # print(ob)
                current = {'best_bid_4': ob['bids'][4], 'best_bid_0': ob['bids'][0], 'best_ask_4': ob['asks'][4],
                           'best_ask_0': ob['asks'][0]}
                self.orderbook = [current]

    async def getPositions(self):
        if self.exchange_name == 'bybit':
            while True:
                positions = await self.exchange.watch_positions()
                p = positions
                for i in range(len(p)):
                    if p[i]['info']['symbol'] == self.ticker and p[i]['info']['side'] == 'Buy':
                        self.qActivePositions = 1

                        print('Позиция: ', p[i])
                        if self.qActivePositions > 0:
                            self.qActiveOrders = 0

                        print('Количество позиций qActivePositions: ', self.qActivePositions)
                        print('Размещено денег в позиции: ', self.cum_margin)
                        print('id позиции: ', p[i]['info']['createdTime'])
                        print('Цена входа в позицию: ', p[i]['entryPrice'])

                        if self.enter_price != float(p[i]['entryPrice']):
                            self.enter_price = float(p[i]['entryPrice'])

                        if self.pos_size_to_sell != float(p[i]['contracts']):
                            self.pos_size_to_sell = float(p[i]['contracts'])

                        if self.pos_start_datetime == 0:
                            self.pos_start_datetime = float(p[i]['info']['updatedTime'])

                        print(f'Баланс позиции ', p[i]['info']['positionBalance'])
                        print('Осталось разместить в позиции: ', self.ALL_MARGIN - self.cum_margin)
                        self.cum_margin = float(p[i]['info']['positionBalance'])

                await asyncio.sleep(0.2)

        if self.exchange_name == 'gateio':
            while True:
                positions = await self.exchange.watch_positions()
                p = positions
                print(p)
                for i in range(len(p)):
                    if p[i]['info']['contract'] == self.ticker.replace('USDT', '_USDT') and p[i]['side'] == 'long' and \
                            p[i]['lastUpdateTimestamp'] is not None:
                        print('--------------------------------------------')
                        print('Новый ордер найден')
                        self.qActivePositions = 1

                        print('Позиция: ', p[i])
                        if self.qActivePositions > 0:
                            self.qActiveOrders = 0

                        # print('Количество позиций qActivePositions: ', self.qActivePositions)
                        # print('Размещено денег в позиции: ', self.cum_margin)
                        print('id позиции: ', p[i]['lastUpdateTimestamp'])
                        print('Цена входа в позицию: ', p[i]['info']['entry_price'])

                        if self.enter_price != float(p[i]['info']['entry_price']):
                            self.enter_price = float(p[i]['info']['entry_price'])
                        print('self.enter_price', self.enter_price)

                        if self.pos_size_to_sell != float(p[i]['contractSize']) * float(p[i]['contracts']):
                            self.pos_size_to_sell = float(p[i]['contractSize']) * float(p[i]['contracts'])
                        print('self.pos_size_to_sell ', self.pos_size_to_sell)

                        if self.pos_start_datetime == 0:
                            self.pos_start_datetime = float(p[i]['lastUpdateTimestamp'])
                        print('self.pos_start_datetime ', self.pos_start_datetime)

                        print("float(p[i]['info']['margin']) ", float(p[i]['info']['margin']))
                        print("float(p['info']['leverage']) ", float(p[i]['info']['leverage']))
                        print(f'Баланс позиции ', float(p[i]['info']['margin']) * float(p[i]['info']['leverage']))
                        # print('Осталось разместить в позиции: ', self.ALL_MARGIN - self.cum_margin)
                        self.cum_margin = float(p[i]['info']['margin'])
                        print('self.cum_margin ', self.cum_margin)
                await asyncio.sleep(2)

    def changeMarginModeAndLeverageBybit(self, exchange):
        # try:
        #     response = exchange.set_margin_mode('isolated', self.ticker, params={'leverage': self.leverage})
        #     print(response)
        # except:
        #     print('Всё уже выставлено')
        #     try:
        #         response = exchange.set_leverage(self.leverage, self.ticker)
        #         print(response)
        #     except:
        #         print('Плечо уже выставлено')
        try:
            response = self.session_bybit.switch_margin_mode(
                category="linear",
                symbol=self.ticker,
                tradeMode=1,
                buyLeverage=f'{self.leverage}',
                sellLeverage=f'{self.leverage}',
            )
            print('Изолированная маржа и плечо х2 успешно установлены')
            return response
        except Exception as e:
            print('Изолированная маржа уже установлена')
            try:
                print(self.session_bybit.set_leverage(
                    category="linear",
                    symbol=self.ticker,
                    buyLeverage=f"{self.leverage}",
                    sellLeverage=f"{self.leverage}",
                ))
            except Exception as e:
                print('Плечо x2 уже установлено')
            return -11

    def FuturesEnterOrder(self, position_sum):
        if self.exchange_name == 'bybit':
            s_time = time.time()
            print('Ордербук ', self.orderbook)
            # qty = f"{round(self.leverage * position_sum / self.orderbook[-1]['best_ask_4'][0], self.round_number)}"
            qty = f"{round(self.leverage * position_sum / self.orderbook[-1]['best_ask_4'][0], self.round_number)}"
            print('!!!!!!!!!!', qty)
            print('Количество активов для открытия позции: ', qty)
            response = self.session_bybit.place_order(
                category="linear",
                symbol=self.ticker,
                side="Buy",
                orderType="Limit",
                price=self.orderbook[-1]['best_ask_4'][0],
                qty=qty
            )
            f_time = time.time()
            print(response)
            print(f_time - s_time)
            try:

                if response['retCode'] == 0:
                    print('Сообщение об успешном размещении ордера')
                    self.qActiveOrders += 1
                    print('Счетчик текущих ордеров увеличен на один')
                if response['retCode'] != 0:
                    print('Сообщение об ошибке при размещении ордера')

                return response['retCode'], response['result']['orderId']
            except Exception as e:
                print('Futures order Error: ', e)
                return -1, -1
        if self.exchange_name == 'gateio':
            try:
                settle = 'usdt'
                lever = str(self.leverage)
                contract = ticker.replace('USDT', '_USDT')
                self.gate_futures_api.update_position_leverage(settle, contract, lever)

                futures_contract = self.gate_futures_api.get_futures_contract(settle, contract)
                self.multiplier = float(futures_contract.quanto_multiplier)
                print('ОРДЕРБУК ', self.orderbook)
                pos_amount = float(position_sum) * float(self.leverage) / self.multiplier / \
                             self.orderbook[-1]['best_ask_4'][0]
                print('pos_amount ', pos_amount)

                print('Выставить ордер')
                order = FuturesOrder(contract=contract, size=round(pos_amount),
                                     price=f"{self.orderbook[-1]['best_ask_4'][0]}", tif='gtc')
                order_response = self.gate_futures_api.create_futures_order(settle, order)
                self.current_order_id = order_response.id
                print('order_id ', self.current_order_id)
                time.sleep(2)
                order_response = self.gate_futures_api.get_futures_order('usdt', str(order_response.id))
                print('ORDER INFO BY ID ', order_response)
                print('STATUS ', order_response.status)

                if order_response.status == 'finished':
                    print('Ордер заполнен полностью')
                    self.qActivePositions = 1
                    self.qActiveOrders = 0

                    self.enter_price = float(order_response.fill_price)
                    print('self.enter_price', self.enter_price)

                    self.pos_size_to_sell = float(order_response.size) * self.multiplier
                    print('self.pos_size_to_sell ', self.pos_size_to_sell)

                    self.pos_start_datetime = float(order_response.create_time * 1000)
                    print('self.pos_start_datetime ', self.pos_start_datetime)

                    print("Осталось заполнить ", float(order_response.left) * self.multiplier)

                    print('Маржа в позиции: ',
                          float(order_response.size) * self.multiplier * float(
                              order_response.fill_price) / self.leverage)
                    self.cum_margin = float(order_response.size) * self.multiplier * float(
                        order_response.fill_price) / self.leverage
                    print('self.cum_margin ', self.cum_margin)

                if order_response.status == 'open':
                    print('Заполнение ордера в процессе ')
                    self.qActivePositions = 0
                    self.qActiveOrders = 1

                    self.enter_price = float(order_response.fill_price)
                    print('self.enter_price', self.enter_price)

                    self.pos_size_to_sell = float(order_response.size) * self.multiplier
                    print('self.pos_size_to_sell ', self.pos_size_to_sell)

                    self.pos_start_datetime = float(order_response.create_time * 1000)
                    print('self.pos_start_datetime ', self.pos_start_datetime)

                    print("Осталось заполнить ", float(order_response.left) * self.multiplier)

                    print('Маржа в позиции: ',
                          float(order_response.size) * self.multiplier * float(
                              order_response.fill_price) / self.leverage)

                    print('order_response.fill_price ', order_response.fill_price)
                    if int(order_response.fill_price) != 0:
                        print('order_response.fill_price != 0')
                        self.cum_margin = self.ALL_MARGIN - float(order_response.left) * float(
                            futures_contract.quanto_multiplier) * float(
                            order_response.fill_price) / self.leverage
                        print('self.cum_margin ', self.cum_margin)
                    else:
                        print('order_response.fill_price == 0')
                        self.cum_margin = 0
                        print('self.cum_margin ', self.cum_margin)

            except Exception as e:
                print('placeFuturesOrder_gateio Error', e)

    def FuturesExitOrder(self):
        if self.exchange_name == 'bybit':
            # global ticker, qActiveOrders, qActivePositions, isSold
            s_time = time.time()
            print('Количество активов для закрытия позции: ', self.pos_size_to_sell)
            response = self.session_bybit.place_order(
                category="linear",
                symbol=self.ticker,
                side="Sell",
                orderType="Market",
                qty=self.pos_size_to_sell
            )
            f_time = time.time()
            print(response)
            print(f_time - s_time)
            try:
                if response['retCode'] == 0:
                    print('Сообщение об успешном размещении ордера')
                    self.qActiveOrders += 1
                    self.isSold = True
                    print('Счетчик текущих позиций уменьшен на один')
                if response['retCode'] != 0:
                    print('Сообщение об ошибке при размещении ордера')

                return response['retCode'], response['result']['orderId']
            except Exception as e:
                print('Futures order Error: ', e)
                return -1, -1

        if self.exchange_name == 'gateio':

            settle = 'usdt'
            contract = ticker.replace('USDT', '_USDT')
            print('SIZE TO EXIT', int(float(self.pos_size_to_sell) / float(self.multiplier)))

            order = FuturesOrder(contract=contract,
                                 size=-1 * int(float(self.pos_size_to_sell) / float(self.multiplier)),
                                 price=f"{self.orderbook[-1]['best_bid_4'][0]}",
                                 tif='gtc')  # делить на модификатор
            order_response = self.gate_futures_api.create_futures_order(settle, order)
            print(order_response)

            if order_response.status == 'finished':
                self.isSold = True
                print('Ордер успешно закрыт. self.isSold = True')
            else:
                print('Проблемы с закрытием ордера. Статус: ', order_response.status)

    def StopLossPrice(self):
        stop_price = self.enter_price * (1 - self.loss_percentage / 100 / self.leverage)
        return stop_price

    def TakeProfitPrice(self):
        take_profit_price = self.enter_price * (1 + self.profit_percentage / 100 / self.leverage)
        return take_profit_price

    def CancelFuturesOrder(self):
        # global ticker, qActiveOrders
        if self.exchange_name == 'bybit':
            try:
                response = self.session_bybit.cancel_order(
                    category="linear",
                    symbol=self.ticker,
                    orderId=self.current_order_id,
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

        if self.exchange_name == 'gateio':

            futures_contract = self.gate_futures_api.get_futures_contract('usdt', self.ticker.replace('USDT', '_USDT'))
            print('Отмена ордеров на гейте.')

            if self.gate_futures_api.get_futures_order('usdt', str(self.current_order_id)).status == 'open':
                print('ДЕЙСТВИТЕЛЬНО ОТМЕНИТЬ ОРДЕР')
                cancel_order_response = self.gate_futures_api.cancel_futures_orders('usdt', self.ticker.replace('USDT',
                                                                                                                '_USDT'))
                print(cancel_order_response)

                if cancel_order_response == []:
                    print('НЕТ ОРДЕРОВ ДЛЯ ОТМЕНЫ')
                    self.qActiveOrders = 0
                    self.qActivePositions = 1

                else:
                    cancel_order_response = cancel_order_response[0]
                    print('ОРДЕР ОТМЕНЕН')

                    time.sleep(2)

                    self.qActivePositions = 0
                    self.qActiveOrders = 0

                    self.enter_price = float(cancel_order_response.fill_price)
                    print('self.enter_price', self.enter_price)

                    self.pos_size_to_sell = float(cancel_order_response.size) * self.multiplier
                    print('self.pos_size_to_sell ', self.pos_size_to_sell)

                    self.pos_start_datetime = float(cancel_order_response.create_time * 1000)
                    print('self.pos_start_datetime ', self.pos_start_datetime)

                    print("Осталось заполнить ",
                          float(cancel_order_response.left) * self.multiplier)

                    print('Маржа в позиции: ',
                          float(cancel_order_response.size) * self.multiplier * float(
                              cancel_order_response.fill_price) / self.leverage)

                    if int(cancel_order_response.fill_price) != 0:
                        print('order_response.fill_price != 0')
                        self.cum_margin = self.ALL_MARGIN - float(cancel_order_response.left) * self.multiplier * float(
                            cancel_order_response.fill_price) / self.leverage
                        print('self.cum_margin ', self.cum_margin)
                    else:
                        print('order_response.fill_price == 0')
                        self.cum_margin = 0
                        print('self.cum_margin ', self.cum_margin)

            else:
                print('Такого случая не должно произойти. Необычный исход')
                pass

    async def main_logic(self):
        global positions_task
        print('Main is started')
        asyncio.create_task(self.send_telegram_message('Test gateio'))
        print(self.exchange_name)
        order_book_task = asyncio.create_task(self.getOrderBook())

        i = 0
        await asyncio.sleep(10)
        try:
            # positions_task = asyncio.create_task(self.getPositions())
            # isMessageSent = False
            i = 0
            while True:
                i += 1
                print('-------------------')
                print(i)
                print('Количество ордеров в памяти qActiveOrders: ', self.qActiveOrders)
                print('Количество позиций qActivePositions: ', self.qActivePositions)
                print('ALL MARGIN ', self.ALL_MARGIN)
                print('CUM MARGIN ', self.cum_margin)
                print('CONDITION ', self.cum_margin >= self.ALL_MARGIN - 1)

                if self.cum_margin >= self.ALL_MARGIN - 1:
                    print('Простановка ордеров на вход запрещена. ВСЕ ДЕНЬГИ ЗАГРУЖЕНЫ В ПОЗИЦИЮ.')
                    print('Отслеживание стоп-лосса и тейк профита включено. Количество активов на продажу: ',
                          self.pos_size_to_sell)
                    stop_price = round(
                        self.StopLossPrice(), 5)
                    profit_price = round(self.TakeProfitPrice(), 5)
                    print('--Цена стоп-лосса: ', stop_price)
                    print('--Цена тейк профита: ', profit_price)
                    print('--Текущая цена ', self.orderbook[-1]['best_bid_0'][0])

                    if float(self.orderbook[-1]['best_bid_0'][0]) >= profit_price:
                        print('Цена тейк-профита достигнута. Закрыть лимиткой')
                        print('Количество позиций: ', self.qActivePositions)
                        self.FuturesExitOrder()
                        await asyncio.sleep(2)
                        if self.isSold:
                            # asyncio.create_task(self.send_telegram_message(
                            #     f'Позиция закрыта по Take-Profit. Прибыль составила '
                            #     f'{self.pos_size_to_sell * self.enter_price * self.profit_percentage / 100} USDT'))
                            await asyncio.sleep(2)
                            print(
                                'Все позиции закрыты. Сигнал на завершение работы торгового задания. '
                                'Заполнили тейк профит.')
                            break

                    if float(self.orderbook[-1]['best_bid_0'][0]) <= stop_price:
                        print('Цена стоп-лосса достигнута. Закрыть по маркету')
                        print('Количество позиций: ', self.qActivePositions)
                        self.FuturesExitOrder()
                        await asyncio.sleep(2)
                        if self.isSold:
                            # asyncio.create_task(self.send_telegram_message(
                            #     f'Позиция закрыта по Stop-Loss. Убыток составил '
                            #     f'{self.pos_size_to_sell * self.enter_price * self.loss_percentage / 100} USDT'))
                            await asyncio.sleep(2)

                            print(
                                'Все позиции закрыты. Сигнал на завершение работы торгового задания. '
                                'Заполнили стоп лосс.')
                            break

                    if time.time() * 1000 >= self.pos_start_datetime + self.TIMEOUT * 60 * 1000:
                        print('Превышен лимит по времени. Закрыть по маркету. ')
                        if self.qActivePositions == 1:
                            self.FuturesExitOrder()
                            await asyncio.sleep(2)
                        if self.isSold:
                            # asyncio.create_task(self.send_telegram_message(
                            #     f'Позиция закрыта через {self.TIMEOUT} минут по маркету. Прибыль составила {(self.orderbook[-1]["best_bid_0"][0] - self.enter_price) * self.pos_size_to_sell} USDT ({((self.orderbook[-1]["best_bid_0"][0] - self.enter_price) * self.pos_size_to_sell) / (self.pos_size_to_sell * self.enter_price / self.leverage) * 100} %)'))
                            await asyncio.sleep(2)
                            print(
                                'Все позиции закрыты. Сигнал на завершение работы торгового задания. Лимит по времени.')
                            break

                else:
                    print('Простановка ордеров разрешена')
                    if self.qActiveOrders == 1:
                        print('Удалить ордер')
                        self.CancelFuturesOrder()

                    if self.qActiveOrders == 0:
                        print('Текущих ордеров нет. Открыть новый ордер')
                        self.FuturesEnterOrder(self.ALL_MARGIN - self.cum_margin)

                await asyncio.sleep(5)
        except KeyboardInterrupt as inter:
            print(inter)
        except Exception as ex:
            pass
            # print(ex)
        finally:
            order_book_task.cancel()
            # positions_task.cancel()
            try:
                await order_book_task
            except asyncio.CancelledError as e:
                print(e)

    def main(self):
        asyncio.run(self.main_logic())


if __name__ == '__main__':
    ALL_MARGIN =5
    exchange_name = 'gateio'
    ticker = 'PYTHUSDT'
    leverage = 2
    listing_date = 1700654750706
    # listing_date = time.time()*1000 + 60*1000

    profit_percentage = 2
    loss_percentage = profit_percentage / 2
    TIMEOUT = 60  # min

    trading_task = TradingTask(ALL_MARGIN=ALL_MARGIN, exchange_name=exchange_name, ticker=ticker, leverage=leverage,
                               profit_percentage=profit_percentage, loss_percentage=loss_percentage, TIMEOUT=TIMEOUT,
                               listing_date=listing_date)
    trading_task.main()
