import random
import time
import logging
from datetime import datetime
from pybit.unified_trading import HTTP
import asyncio
import ccxt.pro as ccxtpro
import ccxt
from telegram import Bot
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import asyncio

from Notifications.Notifications import NotificationsBot

REAL_TRADING = True
class TradingTaskBybit_s:
    def __init__(self, ticker, news_date, listing_date, leverage, profit_percentage, loss_percentage, ALL_MARGIN,
                 TIMEOUT, bot, ccxtpro_instance, pybit_instance):

        # "bot" is an instance of NotificationsBot class from Notifications.py 

        self.telegram_bot = bot

        # экземпляр ccxtpro. Для получения данных о цене и позициях через web-сокеты
        self.exchange = ccxtpro.bybit()
        self.exchange.apiKey = ''
        self.exchange.secret = ''
        self.exchange.options['defaultType'] = 'spot'

        # экземпляр ccxt. Для получения данных о балансе активов на споте
        self.bybit = ccxt.bybit({
            'apiKey': "",
            'secret': ""
        })
        # self.bybit.options['defaultType'] = 'spot'

        # self.exchange = ccxtpro_instance  # получение экземпляра биржи из вне пока не работает

        # экземпляр библиотеки pybit. Для запроса информации о тикерах (её нет в ccxt) и для работы с ордерами.
        self.session_bybit = HTTP(api_key='HS398zpUdxSahhV6se', api_secret='e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T')
        # self.session_bybit = pybit_instance  # получение экземпляра биржи из вне пока не работает

        # данные для открытия позиции
        self.bal = 0
        self.ticker = ticker
        self.news_date = news_date
        self.listing_date = listing_date
        self.leverage = 1  # чтобы не менять логику вычислений, которая взята с фьючей, просто сделаем плечо = 1
        self.profit_percentage = profit_percentage
        self.loss_percentage = loss_percentage
        self.ALL_MARGIN = ALL_MARGIN
        self.TIMEOUT = TIMEOUT  # minutes

        # переменные для отслеживания и отмены ордеров и вывода сообщений о позиции
        self.cum_margin = 0
        self.enter_price = 0
        self.out_price = 0
        self.pos_size_to_sell = 0
        self.orderbook = 0
        self.qActiveOrders = 0
        self.qActivePositions = 0
        self.round_number = 0
        # self.current_position = 0
        self.current_order_id = 0
        self.pos_start_datetime = 0
        self.isSold = False

    def getBalance(self, flag='Enter'):
        try:
            balance_info = self.bybit.fetch_balance()

            if self.ticker.replace('USDT', '') in balance_info:
                print(
                    f"Balance information for {self.ticker.replace('USDT', '')}: {balance_info[self.ticker.replace('USDT', '')]['total']}")
                print(self.enter_price)
                if flag == 'Enter':
                    self.cum_margin = float(balance_info[self.ticker.replace('USDT', '')]['total']) * float(
                        self.enter_price)
                    self.pos_size_to_sell = float(balance_info[self.ticker.replace('USDT', '')]['total'])
                self.bal = float(balance_info[self.ticker.replace('USDT', '')]['total'])
            else:
                print(f"Token {self.ticker.replace('USDT', '')} not found in the balance information.")
        except Exception as e:
            print(f'Error in TradingTaskClass_Bybit_s getBalance: {e}')
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Error in TradingTaskClass_Bybit_s getBalance: {e}'))

    async def getOrderBook(self):
        try:
            while True:
                await asyncio.sleep(0.01)
                ob = await self.exchange.watch_order_book(symbol=self.ticker, limit=50)
                current = {'best_bid_0': ob['bids'][0], 'best_bid_15': ob['bids'][15], 'best_ask_4': ob['asks'][4]}
                self.orderbook = [current]
        except Exception as e:
            print(f'Error in TradingTaskClass_Bybit_s getOrderBook: {e}')
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Error in TradingTaskClass_Bybit_s getOrderBook: {e}'))

    # async def getPositions(self, flag='Enter'):
    #     while True:
    #         positions = await self.exchange.watch_positions()
    #         p = positions
    #         print('ПОЗИЦИЯ ', p)
    #         for i in range(len(p)):
    #             if p[i]['info']['symbol'] == self.ticker and p[i]['info']['side'] == 'Buy' and flag == 'Enter':
    #                 print('НОВАЯ ПОЗИЦИЯ ОКТЫТА!!!!!')
    #                 self.qActivePositions = 1
    #
    #                 print('Позиция: ', p[i])
    #
    #                 print('Количество позиций qActivePositions: ', self.qActivePositions)
    #                 print('Размещено денег в позиции: ', self.cum_margin)
    #                 print('id позиции: ', p[i]['info']['createdTime'])
    #                 print('Цена входа в позицию: ', p[i]['entryPrice'])
    #
    #                 if self.enter_price != float(p[i]['entryPrice']):
    #                     self.enter_price = float(p[i]['entryPrice'])
    #
    #                 if self.pos_size_to_sell != float(p[i]['contracts']):
    #                     self.pos_size_to_sell = float(p[i]['contracts'])
    #
    #                 if self.pos_start_datetime == 0:
    #                     self.pos_start_datetime = float(p[i]['info']['updatedTime'])
    #
    #                 print(f'Баланс позиции ', p[i]['info']['positionBalance'])
    #                 self.cum_margin = float(p[i]['info']['positionBalance'])
    #
    #                 print('Осталось разместить в позиции: ', self.ALL_MARGIN - self.cum_margin)
    #
    #             if p[i]['info']['symbol'] == self.ticker and p[i]['info']['side'] == 'None' and flag == 'Exit':
    #                 print('ПОЗИЦИЯ ПРОДАНА!!!!!')
    #                 print('Позиция: ', p[i])
    #                 self.isSold = True
    #
    #         await asyncio.sleep(0.01)

    def changeMarginModeAndLeverageBybit(self):
        try:
            response = self.session_bybit.switch_margin_mode(
                category="linear",
                symbol=self.ticker,
                tradeMode=1,
                buyLeverage=f'{self.leverage}',
                sellLeverage=f'{self.leverage}',
            )
            print('Изолированная маржа и плечо х2 успешно установлены')
            asyncio.run(self.telegram_bot.sendMessageDebug('Error in TradingTaskClass_Bybit_s getOrderBook'))

            return response
        except Exception as e:
            # TODO. Не очень хороший способ отлова ошибки, потому что если проблема со switch_margin_mode будет не в том,
            # что она уже установлена, а, например, в том, что отвалился интернет, то тебе все равно выведется сообщение, 
            # что маржа уже установлена

            # -- пока не придумал, как исправить. Проблема в том, что если плечо уже установлено, то функция выдаёт прям ошибку и завершает работу скрипта
            # -- буду отправлять message в тг, чтобы было ясно, что за ошибка
            print(f'Error in TradingTaskClass_Bybit_s changeMarginModeAndLeverageBybit: {e}')
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Error in TradingTaskClass_Bybit_s changeMarginModeAndLeverageBybit: {e}'))
            try:
                print(self.session_bybit.set_leverage(
                    category="linear",
                    symbol=self.ticker,
                    buyLeverage=f"{self.leverage}",
                    sellLeverage=f"{self.leverage}",
                ))
            except Exception as e:
                # TODO. Здесь аналогично
                print(f'Error in TradingTaskClass_Bybit_s changeMarginModeAndLeverageBybit: {e}')
                asyncio.run(self.telegram_bot.sendMessageDebug(f'Error in TradingTaskClass_Bybit_s changeMarginModeAndLeverageBybit: {e}'))
            return -11

    def SpotEnterOrder(self, position_sum):
        try:
            s_time = time.time()
            print('Ордербук ', self.orderbook)
            # qty = f"{round(self.leverage * position_sum / self.orderbook[-1]['best_ask_4'][0], self.round_number)}"
            qty = f"{round(self.leverage * position_sum / self.orderbook[-1]['best_bid_0'][0], self.round_number)}"
            print('!!!!!!!!!!', qty)
            print('Количество активов для открытия позции: ', qty)
            response = self.session_bybit.place_order(
                category="spot",
                symbol=self.ticker,
                side="Buy",
                orderType="Limit",
                price=self.orderbook[-1]['best_bid_0'][0],
                qty=qty
            )
            f_time = time.time()
            print(response)
            print(f_time - s_time)
            try:
                if response['retCode'] == 0:
                    print('Сообщение об успешном размещении ордера')
                    self.qActiveOrders = 1
                    print('Счетчик текущих ордеров увеличен на один')
                if response['retCode'] != 0:
                    print('Сообщение об ошибке при размещении ордера')

                return response['retCode'], response['result']['orderId']
            except Exception as e:
                print('Futures order Error: ', e)
                return -1, -1
        except Exception as e:
            print(f'Error in TradingTaskClass_Bybit_s SpotEnterOrder: {e}')
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Error in TradingTaskClass_Bybit_s SpotEnterOrder: {e}'))


    def SpotExitOrder(self):
        try:
            # global ticker, qActiveOrders, qActivePositions, isSold
            s_time = time.time()
            print('Количество активов для закрытия позции: ', self.pos_size_to_sell)
            response = self.session_bybit.place_order(
                category="spot",
                symbol=self.ticker,
                side="Sell",
                orderType="Market",
                qty=round(self.pos_size_to_sell * 0.99, self.round_number)
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
        except Exception as e:
            print(f'Error in TradingTaskClass_Bybit_s SpotExitOrder: {e}')
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Error in TradingTaskClass_Bybit_s SpotExitOrder: {e}'))
            

    def SpotExitOrderLimit(self):
        try:
            # global ticker, qActiveOrders, qActivePositions, isSold
            s_time = time.time()
            print('Количество активов для закрытия позции: ', self.pos_size_to_sell)
            response = self.session_bybit.place_order(
                category="spot",
                symbol=self.ticker,
                side="Sell",
                orderType="Limit",
                price=self.orderbook[-1]['best_bid_15'][0],
                qty=round(self.pos_size_to_sell * 0.99, self.round_number)
            )
            f_time = time.time()
            print(response)
            print(f_time - s_time)
            try:
                if response['retCode'] == 0:
                    print('Сообщение об успешном размещении ордера')
                    self.qActiveOrders += 1
                    print('Счетчик текущих позиций уменьшен на один')
                if response['retCode'] != 0:
                    print('Сообщение об ошибке при размещении ордера')

                return response['retCode'], response['result']['orderId']
            except Exception as e:
                print('Futures order Error: ', e)
                return -1, -1
        except Exception as e:
            print(f'Error in TradingTaskClass_Bybit_s SpotExitOrderLimit: {e}')
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Error in TradingTaskClass_Bybit_s SpotExitOrderLimit: {e}'))


    # цена стоп лосс и тейк профита вычисляется относительно подаваемой цены без учёта плеча
    # т.е. если изначальная цена была 100, а процент прибыли 5%, то цена тейк профита будет 105 при любом плече
    def StopLossPrice(self, start_price):
        stop_price = start_price * (1 - self.loss_percentage / 100)
        print('stop_price StopLossPrice', stop_price)
        return stop_price

    def TakeProfitPrice(self, start_price):
        take_profit_price = start_price * (1 + self.profit_percentage / 100)
        print('take_profit_price TakeProfitPrice', take_profit_price)
        return take_profit_price

    def CancelSpotOrder(self):
        # global ticker, qActiveOrders
        try:
            response = self.session_bybit.cancel_order(
                category="spot",
                symbol=self.ticker,
                orderId=self.current_order_id,
            )
            print(response)
            if response['retCode'] == 0:
                print('Ордер успешно отменён')
                # self.qActiveOrders = 0

            else:
                print('Ордер не отменен, ', response['retCode'])

            return response['retCode']
        except Exception as e:
            print(f'Error in TradingTaskClass_Bybit_s CancelSpotOrder: {e}')
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Error in TradingTaskClass_Bybit_s CancelSpotOrder: {e}'))

            return -1

    async def main_logic(self):
        global positions_task
        print('Main is started')
        asyncio.create_task(self.telegram_bot.sendMessageDebug('15 минут до листинга. Открываем позицию.'))
        if REAL_TRADING is True:
            asyncio.create_task(self.telegram_bot.sendMessage('15 минут до листинга. Открываем позицию.'))

        order_book_task = asyncio.create_task(self.getOrderBook())

        i = 0
        await asyncio.sleep(10)
        asyncio.create_task(self.telegram_bot.sendMessageDebug(f'ОРДЕРБУК: {self.orderbook}'))
        print(self.orderbook)

        if self.orderbook == 0 or self.orderbook == []:
            asyncio.create_task(self.telegram_bot.sendMessageDebug('ОРДЕРБУК НЕ ПРОГРУЗИЛСЯ'))

        start_price_15min_before = self.orderbook[-1]['best_bid_0'][0]

        try:
            isMessageSent = False
            while True:
                # orders_task = asyncio.create_task(getOrders())
                i += 1
                print('--------------')
                print(i)
                print('Количество ордеров в памяти qActiveOrders: ', self.qActiveOrders)
                print('Количество позиций qActivePositions: ', self.qActivePositions)
                self.getBalance()
                print('CONDITION ', self.cum_margin >= self.ALL_MARGIN - 1)

                if i > 3:

                    if self.cum_margin >= self.ALL_MARGIN - 1:  # полностью вошли в позицию

                        # time_in_position += 1

                        print('Простановка ордеров на вход запрещена. ВСЕ ДЕНЬГИ ЗАГРУЖЕНЫ В ПОЗИЦИЮ.')
                        print('Отслеживание стоп-лосса и тейк профита включено. Количество активов на продажу: ',
                              self.pos_size_to_sell)
                        stop_price = round(
                            self.StopLossPrice(start_price_15min_before), 5)
                        print('--Цена стоп-лосса: ', stop_price)
                        profit_price = round(self.TakeProfitPrice(start_price_15min_before), 5)

                        if not isMessageSent:
                            self.pos_start_datetime = time.time()*1000
                            asyncio.create_task(self.telegram_bot.sendMessageDebug(
                                f'Информация о входе в позицию \n Инструмент: {self.ticker} \n Свобственных средств: '
                                f'{self.pos_size_to_sell * self.enter_price / self.leverage} USDT \n Плечо: '
                                f'{self.leverage}x \n Размер позиции: {self.pos_size_to_sell * self.enter_price} USDT'
                                f' \n Было куплено: {self.pos_size_to_sell}{self.ticker.replace("USDT", "")} \n '
                                f'Средняя цена входа: {self.enter_price} \n Рост на выходе новости: {self.getNewGrowthPercentage()}\n Уровень тейк-профита: '
                                f'{self.profit_percentage}% \n Уровень стоп-лосса {self.loss_percentage}% \n '
                                f'Профит-цена: ${profit_price} \n Стоп-цена: ${stop_price}'))
                            if REAL_TRADING is True:
                                asyncio.create_task(self.telegram_bot.sendMessage(
                                f'Информация о входе в позицию \n Инструмент: {self.ticker} \n Свобственных средств: '
                                f'{self.pos_size_to_sell * self.enter_price / self.leverage} USDT \n Плечо: '
                                f'{self.leverage}x \n Размер позиции: {self.pos_size_to_sell * self.enter_price} USDT'
                                f' \n Было куплено: {self.pos_size_to_sell}{self.ticker.replace("USDT", "")} \n '
                                f'Средняя цена входа: {self.enter_price} \n Рост на выходе новости: {self.getNewGrowthPercentage()}\n Уровень тейк-профита: '
                                f'{self.profit_percentage}% \n Уровень стоп-лосса {self.loss_percentage}% \n '
                                f'Профит-цена: ${profit_price} \n Стоп-цена: ${stop_price}'))
                            isMessageSent = True

                        print('--Цена тейк профита: ', profit_price)
                        print('--Текущая цена ', self.orderbook[-1]['best_bid_0'][0])
                        # FuturesExitLimitOrder(pos_size_to_sell, profit_price, session_bybit)

                        if float(self.orderbook[-1]['best_bid_0'][0]) >= profit_price:
                            print('Цена тейк-профита достигнута. Закрыть лимиткой')
                            print('Количество позиций: ', self.qActivePositions)
                            self.SpotExitOrder()
                            self.out_price = self.orderbook[-1]['best_bid_0'][0]
                            await asyncio.sleep(1)

                            # isSold = True
                            if self.isSold:
                                asyncio.create_task(self.telegram_bot.sendMessageDebug(
                                    f'Позиция {self.ticker} закрыта по Take-Profit. Прибыль составила '
                                    f'{self.pos_size_to_sell * self.enter_price * self.profit_percentage / 100} USDT'))
                                if REAL_TRADING is True:
                                    asyncio.create_task(self.telegram_bot.sendMessage(
                                    f'Позиция {self.ticker} закрыта по Take-Profit. Прибыль составила '
                                    f'{self.pos_size_to_sell * self.enter_price * self.profit_percentage / 100} USDT'))
                                await asyncio.sleep(2)
                                self.updateResultTable(end_signal='takeprofit')
                                print(
                                    'Все позиции закрыты. Сигнал на завершение работы торгового задания. '
                                    'Заполнили тейк профит.')
                                break

                        if float(self.orderbook[-1]['best_bid_0'][0]) <= stop_price:
                            print('Цена стоп-лосса достигнута. Закрыть по маркету')
                            print('Количество позиций: ', self.qActivePositions)
                            self.SpotExitOrder()
                            self.out_price = self.orderbook[-1]['best_bid_0'][0]
                            await asyncio.sleep(1)

                            if self.isSold:
                                asyncio.create_task(self.telegram_bot.sendMessageDebug(
                                    f'Позиция {self.ticker} закрыта по Stop-Loss. Убыток составил '
                                    f'{self.pos_size_to_sell * self.enter_price * self.loss_percentage / 100} USDT'))
                                if REAL_TRADING is True:
                                    asyncio.create_task(self.telegram_bot.sendMessage(
                                    f'Позиция {self.ticker} закрыта по Stop-Loss. Убыток составил '
                                    f'{self.pos_size_to_sell * self.enter_price * self.loss_percentage / 100} USDT'))
                                await asyncio.sleep(2)
                                self.updateResultTable(end_signal='stoploss')
                                print(
                                    'Все позиции закрыты. Сигнал на завершение работы торгового задания. '
                                    'Заполнили стоп лосс.')
                                break
                        print('POS START TIME', self.pos_start_datetime)
                        print('CURR TIME', time.time() * 1000)
                        print('DIFF', time.time() * 1000 - self.pos_start_datetime)
                        if time.time() * 1000 >= self.pos_start_datetime + self.TIMEOUT * 60 * 1000:
                            print('Превышен лимит по времени. Закрыть по limit. ')
                            self.SpotExitOrderLimit()

                            while self.bal*self.enter_price > 1:
                                self.getBalance(flag='Exit')
                                self.isSold = True

                            if self.bal*self.enter_price < 1:
                                self.getBalance(flag='Exit')
                                self.isSold = True


                            if self.isSold:
                                print('ПОЗИЦИЯ ПРОДАНА')
                                self.out_price = self.orderbook[-1]['best_bid_0'][0]
                                asyncio.create_task(self.telegram_bot.sendMessageDebug(
                                    f'Позиция {self.ticker} закрыта через {self.TIMEOUT} минут по limit. Прибыль составила {(self.orderbook[-1]["best_bid_0"][0] - self.enter_price) * self.pos_size_to_sell} USDT ({((self.orderbook[-1]["best_bid_0"][0] - self.enter_price) * self.pos_size_to_sell) / (self.pos_size_to_sell * self.enter_price / self.leverage) * 100} %)'))
                                if REAL_TRADING is True:
                                    asyncio.create_task(self.telegram_bot.sendMessage(
                                    f'Позиция {self.ticker} закрыта через {self.TIMEOUT} минут по limit. Прибыль составила {(self.orderbook[-1]["best_bid_0"][0] - self.enter_price) * self.pos_size_to_sell} USDT ({((self.orderbook[-1]["best_bid_0"][0] - self.enter_price) * self.pos_size_to_sell) / (self.pos_size_to_sell * self.enter_price / self.leverage) * 100} %)'))
                                await asyncio.sleep(2)
                                self.updateResultTable(end_signal='timeout')
                                print(
                                    'Все позиции закрыты. Сигнал на завершение работы торгового задания. Лимит по времени.')
                                break

                    else:
                        print('Простановка ордеров разрешена')
                        if self.qActiveOrders > 0:
                            print('Удалить ордер')
                            self.CancelSpotOrder()
                            self.qActiveOrders = 0
                            time.sleep(1)

                        if self.qActiveOrders == 0:
                            print('Текущих ордеров нет. Открыть новый ордер')
                            delay = random.uniform(2, 6)
                            print(f'Ждем {delay / 10} секунд перед открытием нового ордера. Для защиты')
                            await asyncio.sleep(delay / 10)
                            order_code, order_id = self.SpotEnterOrder(self.ALL_MARGIN - self.cum_margin)
                            if order_code == 0:
                                self.current_order_id = order_id
                                self.enter_price = self.orderbook[-1]['best_bid_0'][0]
                                print('Новый ордер ', order_id)
                                print('SLEEP 10')
                                await asyncio.sleep(10)
                                # positions_task = asyncio.create_task(self.getPositions())
                                # await asyncio.sleep(2)
                # if i == 10:
                #     # await createFuturesLongOrder(bybit, 2, 2)
                #     createFuturesLongOrder(bybit, 2, 2)
                #
                await asyncio.sleep(1)  # Sleep for 5 seconds (adjust as needed)
            print('Работа программы завершена')
            await self.exchange.close()
            await asyncio.sleep(1.5)
            asyncio.create_task(
                self.telegram_bot.sendMessageDebug('Выполнение торгового задания завершено без ошибок.'))
            await asyncio.sleep(1.5)
        except KeyboardInterrupt as inter:
            print(inter)
        except Exception as ex:
            print(f'TradingTaskClass_bybit_s main_logic error {ex}')
            asyncio.create_task(self.telegram_bot.sendMessageDebug(f'TradingTaskClass_bybit_s main_logic error {ex}'))
            await self.exchange.close()
        finally:
            # orders_task.cancel()
            await self.exchange.close()
            # positions_task.cancel()
            order_book_task.cancel()
            try:
                await order_book_task
            except asyncio.CancelledError as e:
                print(e)

    def getNewGrowthPercentage(self):
        try:
            # если не вычитать, то он не спарсит нулевую свечу
            # вычитать нужно 59, чтобы не вывалиться на предыдущую минутную свечу (протестировано).
            # если новость вышла между 11:45:00 и 11:45:59 включительно, то этот скрипт за нулевую свечу примет ту, которая открылась в 11:45
            start_timestamp = self.news_date - 59 * 1000
            ticker = ticker.replace('USDT', '/USDT')

            # это стандартный экземпляр без api ключей, поэтому таких можно создавать сколько угодно
            candles = self.bybit.fetch_ohlcv(ticker, '1m', since=start_timestamp, limit=10)
            print(len(candles))

            for i in range(len(candles)):
                candle = candles[i]
                candle_timestamp = datetime.utcfromtimestamp(candle[0] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                print(
                    f"Candle for {candle_timestamp} - Open: {candle[1]}, High: {candle[2]}, Low: {candle[3]}, Close: {candle[4]}")

                # Проверяем, является ли свеча "красной"
                if candle[4] < candle[1]:
                    print(f"Red candle found: {i}. Stopping the loop.")
                    if i == 0:
                        # Если первая же свеча красная, значит с токеном что-то не так и позицию не открываем.
                        # Запишем -10, чтобы потом проверить на это значение и не входить в позицию
                        growth_percentage = -10
                    else:
                        previous_candle = candles[i - 1]
                        start_candle = candles[0]
                        growth_percentage = (previous_candle[2] - start_candle[1]) / start_candle[1] * 100
                    return growth_percentage

            # если нет красных свеч (что очень маловероятно), возвращаем процент относительно последней (самой большой)
            return (candles[-1][2] - candles[0][1]) / candles[0][1] * 100
    
        except Exception as e:
            print(f'TradingTaskClass_bybit_s getNewGrowthPercentage error: {e}')
            asyncio.create_task(self.telegram_bot.sendMessageDebug(f'TradingTaskClass_bybit_s getNewGrowthPercentage error: {e}'))


    def updateResultTable(self, end_signal):
        try:
            json_keyfile_path = 'credentials.json'
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            credentials = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
            gc = gspread.authorize(credentials)
            spreadsheet_name = 'Торговля на листинге фьючерсов (лог)'
            worksheet = gc.open(spreadsheet_name).sheet1

            news_date = datetime.utcfromtimestamp(self.news_date / 1000.0).strftime("%d.%m.%Y")
            news_time = datetime.utcfromtimestamp(self.news_date / 1000.0).strftime("%H:%M")
            listing_time = datetime.utcfromtimestamp(self.listing_date / 1000.0).strftime("%H:%M")

            if end_signal == 'stoploss':
                new_row = [news_date, self.ticker.replace('USDT', ''), news_time,
                        f'{round(self.profit_percentage * 2, 2)}%', listing_time,
                        f'{round(self.profit_percentage, 2)}%', f'{round(self.loss_percentage, 2)}%',
                        round(self.enter_price, 6),
                        round(self.TakeProfitPrice(self.enter_price), 6), round(self.StopLossPrice(self.enter_price), 6),
                        round(self.out_price, 6),
                        'да', 'нет', 'нет',
                        round(((self.out_price - self.enter_price) / self.enter_price) * 100 * self.leverage, 6),
                        round(((self.out_price - self.enter_price) / self.enter_price) * self.cum_margin * self.leverage,
                                6)]
            elif end_signal == 'takeprofit':
                new_row = [news_date, self.ticker.replace('USDT', ''), news_time,
                        f'{round(self.profit_percentage * 2, 2)}%', listing_time,
                        f'{round(self.profit_percentage, 2)}%', f'{round(self.loss_percentage, 2)}%',
                        round(self.enter_price, 6),
                        round(self.TakeProfitPrice(self.enter_price), 6), round(self.StopLossPrice(self.enter_price), 6),
                        round(self.out_price, 6),
                        'нет', 'да', 'нет',
                        round(((self.out_price - self.enter_price) / self.enter_price) * 100 * self.leverage, 6),
                        round(((self.out_price - self.enter_price) / self.enter_price) * self.cum_margin * self.leverage,
                                6)]
            elif end_signal == 'timeout':
                new_row = [news_date, self.ticker.replace('USDT', ''), news_time,
                        f'{round(self.profit_percentage * 2, 2)}%', listing_time,
                        f'{round(self.profit_percentage, 2)}%', f'{round(self.loss_percentage, 2)}%',
                        round(self.enter_price, 6),
                        round(self.TakeProfitPrice(self.enter_price), 6), round(self.StopLossPrice(self.enter_price), 6),
                        round(self.out_price, 6),
                        'нет', 'нет', 'да',
                        round(((self.out_price - self.enter_price) / self.enter_price) * 100 * self.leverage, 6),
                        round(((self.out_price - self.enter_price) / self.enter_price) * self.cum_margin * self.leverage,
                                6)]

            worksheet.append_row(new_row)
        except Exception as e:
            print(f'TradingTaskClass_bybit_s updateResultTable error: {e}')
            asyncio.create_task(self.telegram_bot.sendMessageDebug(f'TradingTaskClass_bybit_s updateResultTable error: {e}'))

    # async def main_logic_1(self):
    #     order_book_task = asyncio.create_task(self.getOrderBook())
    #     while True:
    #         await asyncio.sleep(1)

    def main(self):
        try:
            # заполнить self.round_number, чтобы знать, до какого числа округлять
            response = self.session_bybit.get_instruments_info(
                category="spot",
                symbol=self.ticker,
            )
            print(response)
            number = response['result']['list'][0]['lotSizeFilter']['basePrecision']
            print(number)
            if float(number) == 1:
                self.round_number = 0
            if float(number) > 1:
                self.round_number = -1 * len(number) + 1
            if float(number) < 1:
                self.round_number = len(number) - 2
            print(self.round_number)

            # сообщение о запуске торгового задания.
            # asyncio.run(self.telegram_bot.sendMessageDebug(
            #     f'Тестовое торговое задание запущено. \n Листинг {self.ticker} \n '
            #     f'Дата: {datetime.utcfromtimestamp(self.listing_date / 1000)} UTC+0\n '
            #     f'Ожидание {datetime.utcfromtimestamp(self.listing_date / 1000 - 15 * 60)} UTC+0'))
            
            # if REAL_TRADING is True:
                # asyncio.run(self.telegram_bot.sendMessage(
            #     f'Тестовое торговое задание запущено. \n Листинг {self.ticker} \n '
            #     f'Дата: {datetime.utcfromtimestamp(self.listing_date / 1000)} UTC+0\n '
            #     f'Ожидание {datetime.utcfromtimestamp(self.listing_date / 1000 - 15 * 60)} UTC+0'))

            t = 0
            is_done = False # флаг, чтобы заполнить стоп лосс и тейк профит только один раз
            while True:
                time.sleep(1)
                t += 1
                print('Ожидание...')

                if not is_done:
                    if time.time() * 1000 >= self.listing_date - 20 * 60 * 1000 and time.time() * 1000 <= self.listing_date:
                        print('Прошло 15 минут с момента выхода новости. Время заполнять тейк профит.')
                        print('Рост на выходе новости: ', self.getNewGrowthPercentage())
                        self.profit_percentage = self.getNewGrowthPercentage() / 2
                        print('Процент тейк-профита: ', self.profit_percentage)
                        self.loss_percentage = self.profit_percentage / 2
                        print('Процент стоп-лосса: ', self.loss_percentage)
                        is_done = True
                if self.profit_percentage == -5.0:
                    asyncio.create_task(self.telegram_bot.sendMessageDebug(f'Позиция {self.ticker} не будет открыта, так свеча на выходе новосте красная. Break'))
                    asyncio.create_task(self.telegram_bot.sendMessage(f'Позиция {self.ticker} не будет открыта, так свеча на выходе новосте красная.'))
                    break # завершение

                # когда наступает момент за 15 минут до листинга, запускается логика выставления позиции.
                # if time.time() * 1000 >= self.listing_date - 15 * 60 * 1000:  # for test
                if time.time() * 1000 >= self.listing_date - 15 * 60 * 1000 - 10 * 1000 and time.time() * 1000 <= self.listing_date:
                    asyncio.run(self.main_logic())
                    # asyncio.run(self.main_logic_1())
                    break
        except Exception as e:
            print(f'TradingTaskClass_bybit_s main error: {e}')
            asyncio.create_task(self.telegram_bot.sendMessageDebug(f'TradingTaskClass_bybit_s main error: {e}'))

# if __name__ == '__main__':
#     ALL_MARGIN = 5
#     exchange_name = 'bybit'
#     ticker = 'PYTHUSDT'
#     leverage = 2
#     news_date = 1701663300000
#     listing_date = 1701262560000
#     # listing_date = time.time()*1000 + 60*1000
#
#     profit_percentage = 10
#     loss_percentage = profit_percentage / 2
#     TIMEOUT = 0.5  # min
#     bot_instance = NotificationsBot()
#     trading_task = TradingTaskBybit_s(ALL_MARGIN=ALL_MARGIN, ticker=ticker, leverage=leverage,
#                                     profit_percentage=profit_percentage, loss_percentage=loss_percentage,
#                                     news_date=news_date,
#                                     TIMEOUT=TIMEOUT,
#                                     listing_date=listing_date, bot=bot_instance, ccxtpro_instance=None,
#                                     pybit_instance=None)
#     trading_task.main()
