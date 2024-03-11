import random
import time
import logging
from datetime import datetime
from pybit.unified_trading import HTTP
import asyncio
import ccxt.pro as ccxtpro
import ccxt
# from telegram import Bot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from binance.client import Client
import requests
# import hashlib
# import hmac
import time

import asyncio

# from Notifications.Notifications import NotificationsBot
# from binance.spot import Spot as SpotClient
# from binance.lib.utils import config_logging
# from binance.error import ClientError
import asyncio
# from telegram import Bot
REAL_TRADING = True
class TradingTaskBinance:
    def __init__(self, ticker, news_date, listing_date, leverage, profit_percentage, loss_percentage, ALL_MARGIN,
                 TIMEOUT, bot, ccxtpro_instance, pybit_instance):

        # "bot" is an instance of NotificationsBot class from Notifications.py
        self.telegram_bot = bot
        # экземпляр ccxtpro. Для получения данных о цене и позициях через web-сокеты
        self.exchange = ccxtpro.binance()
        self.exchange.apiKey = ''
        self.exchange.secret = ''
        self.exchange.options['defaultType'] = 'spot'

        self.API_KEY = ''
        self.API_SECRET = ''

        # экземпляр ccxt. Для получения данных о балансе активов на споте
        self.binance = ccxt.binance({
            'apiKey': "",
            'secret': ""
        })
        self.binance.options['defaultType'] = 'spot'

        self.client = Client(api_key='', api_secret='')
        # self.client = SpotClient('8zLkbIU4hUJQulanxmU00j4O4TQkd0C1GNmgShHZ3FwkNehVV8MknzcJ3Mk3aPFd','NuyZ2RbNTQgU0ErSYAhSBx3a314k006OZ9OrzWFLQu7Jd75wLPhZvJTP0FC4vdKD')


        # данные для открытия позиции
        self.ticker = ticker
        self.news_date = news_date
        self.listing_date = listing_date
        self.leverage = 1  # чтобы не менять логику вычислений, которая взята с фьючей, просто сделаем плечо = 1
        self.profit_percentage = profit_percentage
        self.loss_percentage = loss_percentage
        self.ALL_MARGIN = ALL_MARGIN
        self.TIMEOUT = TIMEOUT  # minutes

        # переменные для отслеживания и отмены ордеров и вывода сообщений о позиции
        self.bal = 0
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
            balance_info = self.binance.fetch_balance()

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
            print(f'Error in TradingTaskClass_Binance_s getBalance: {e}')
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Error in TradingTaskClass_Binance_s getBalance: {e}'))

    # async def getOrderBook(self):
    #     try:
    #         while True:
    #             await asyncio.sleep(0.01)
    #             ob = await self.exchange.watch_order_book(symbol=self.ticker, limit=15)
    #             current = {'best_bid_0': ob['bids'][0], 'best_bid_15': ob['bids'][14], 'best_ask_4': ob['asks'][4]}
    #             self.orderbook = [current]
    #             # print(self.orderbook)
    #     except Exception as e:
    #         print(f'Error in TradingTaskClass_Binance_s getOrderBook: {e}')
    #         asyncio.run(self.telegram_bot.sendMessageDebug(f'Error in TradingTaskClass_Binance_s getOrderBook: {e}'))
    
    def getOrderBook(self):
        try:
            ob = self.client.get_order_book(symbol=self.ticker, limit=15)
            # print(ob)
            current = {'best_bid_0': float(ob['bids'][0][0]), 'best_bid_15': float(ob['bids'][14][0]), 'best_ask_4': float(ob['asks'][4][0])}
            print(current)
            self.orderbook = [current]
        except Exception as e:
            print(f'Error in TradingTaskClass_Binance_s getOrderBook: {e}')
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Error in TradingTaskClass_Binance_s getOrderBook: {e}'))
            self.orderbook = 0
    

    def SpotEnterOrder(self, position_sum):
        try:
            self.getOrderBook()
            print('Ордербук ', self.orderbook)
            qty = round(self.leverage * position_sum / self.orderbook[-1]['best_bid_0'], self.round_number)
            print('!!!!!!!!!!', qty)
            print('Количество активов для открытия позции: ', qty)
            self.getOrderBook()
            order = self.client.create_order(
                symbol=self.ticker,
                side="BUY",
                timeInForce='GTC',
                type="LIMIT",
                quantity=qty,
                price=self.orderbook[-1]['best_bid_0']
            )
            print(order)

            if order['orderId']:
                print('Сообщение об успешном размещении ордера')
                self.qActiveOrders = 1
                print('Счетчик текущих ордеров увеличен на один')
                return 0, order['orderId']
            else:
                print('Ошибка открытия ордера')
                return -1, -1
        except Exception as e:
            print('Futures order Error: ', e)
            return -1, -1

    def SpotExitOrder(self):
        try:
            print('Ордербук ', self.orderbook)
            print('Количество активов для закрытия позции: ', self.pos_size_to_sell)
            self.getOrderBook()
            order = self.client.create_order(
                symbol=self.ticker,
                side="SELL",
                timeInForce='GTC',
                type="LIMIT",
                quantity=round(self.pos_size_to_sell * 0.99, self.round_number),
                price=self.orderbook[-1]['best_bid_15']
            )
            print(order)

            if order['orderId']:
                print('Сообщение об успешном размещении ордера')
                print('Счетчик текущих ордеров увеличен на один')
                return 0, order['orderId']
            else:
                print('Ошибка открытия ордера')
                return -1, -1
        except Exception as e:
            print('Futures EXIT order Error: ', e)
            return -1, -1

    # цена стоп лосс и тейк профита вычисляется относительно подаваемой цены без учёта плеча
    # т.е. если изначальная цена была 100, а процент прибыли 5%, то цена тейк профита будет 105 при любом плече
    def StopLossPrice(self, start_price):
        stop_price = start_price * (1 - self.loss_percentage / 100)
        return stop_price

    def TakeProfitPrice(self, start_price):
        take_profit_price = start_price * (1 + self.profit_percentage / 100)
        return take_profit_price

    def CancelSpotOrder(self):
        # global ticker, qActiveOrders
        try:
            cancel_order = self.client.cancel_order(
            symbol=self.ticker,
            orderId=self.current_order_id)

            print(cancel_order)

            if cancel_order['status'] == 'CANCELED':
                print('Ордер успешно отменён.')
            else:
                print('Ошибка отмены ордера.')

        except Exception as e:
            print('Ошибка отмены ордера: ', e)

    async def main_logic(self):
        global positions_task
        print('Main is started')
        asyncio.create_task(self.telegram_bot.sendMessageDebug('15 минут до листинга. Открываем позицию.'))
        if REAL_TRADING is True:
            asyncio.create_task(self.telegram_bot.sendMessage('15 минут до листинга. Открываем позицию.'))

        # order_book_task = asyncio.create_task(self.getOrderBook())

        i = 0
        await asyncio.sleep(10)
        self.getOrderBook()
        asyncio.create_task(self.telegram_bot.sendMessageDebug(f'ОРДЕРБУК: {self.orderbook}'))
        print(self.orderbook)

        if self.orderbook == 0 or self.orderbook == []:
            asyncio.create_task(self.telegram_bot.sendMessageDebug('ОРДЕРБУК НЕ ПРОГРУЗИЛСЯ'))

        self.getOrderBook()
        start_price_15min_before = self.orderbook[-1]['best_bid_0']

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
                        self.getOrderBook()
                        print('--Текущая цена ', self.orderbook[-1]['best_bid_0'])
                        # FuturesExitLimitOrder(pos_size_to_sell, profit_price, session_bybit)

                        if float(self.orderbook[-1]['best_bid_0']) >= profit_price:
                            print('Цена тейк-профита достигнута. Закрыть лимиткой')
                            print('Количество позиций: ', self.qActivePositions)
                            self.SpotExitOrder()
                            self.getOrderBook()
                            self.out_price = self.orderbook[-1]['best_bid_0']
                            await asyncio.sleep(1)

                            while self.bal*self.enter_price > 2:
                                time.sleep(1)
                                self.getBalance(flag='Exit')
                                print('self.bal*self.enter_price', self.bal*self.enter_price)
                                self.isSold = True
                            
                            if self.bal*self.enter_price < 1:
                                self.getBalance(flag='Exit')
                                self.isSold = True

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

                        if float(self.orderbook[-1]['best_bid_0']) <= stop_price:
                            print('Цена стоп-лосса достигнута. Закрыть по маркету')
                            print('Количество позиций: ', self.qActivePositions)
                            self.SpotExitOrder()
                            self.getOrderBook()
                            self.out_price = self.orderbook[-1]['best_bid_0']
                            await asyncio.sleep(1)

                            while self.bal*self.enter_price > 2:
                                time.sleep(1)
                                self.getBalance(flag='Exit')
                                print('self.bal*self.enter_price', self.bal*self.enter_price)
                                self.isSold = True
                            
                            if self.bal*self.enter_price < 1:
                                self.getBalance(flag='Exit')
                                self.isSold = True

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

                        if time.time() * 1000 >= self.pos_start_datetime + self.TIMEOUT * 60 * 1000:
                            print('Превышен лимит по времени. Закрыть по маркету. ')
                                
                            self.SpotExitOrder()
                            self.getOrderBook()
                            self.out_price = self.orderbook[-1]['best_bid_0']
                            await asyncio.sleep(1)

                            while self.bal*self.enter_price > 2:
                                time.sleep(1)
                                self.getBalance(flag='Exit')
                                print('self.bal*self.enter_price', self.bal*self.enter_price)
                                self.isSold = True
                            
                            if self.bal*self.enter_price < 1:
                                self.getBalance(flag='Exit')
                                self.isSold = True

                            if self.isSold:
                                print('ПОЗИЦИЯ ПРОДАНА')
                                self.getOrderBook()
                                asyncio.create_task(self.telegram_bot.sendMessageDebug(
                                    f'Позиция {self.ticker} закрыта через {self.TIMEOUT} минут по limit. Прибыль составила {(self.orderbook[-1]["best_bid_0"] - self.enter_price) * self.pos_size_to_sell} USDT ({((self.orderbook[-1]["best_bid_0"] - self.enter_price) * self.pos_size_to_sell) / (self.pos_size_to_sell * self.enter_price / self.leverage) * 100} %)'))
                                if REAL_TRADING is True:
                                    asyncio.create_task(self.telegram_bot.sendMessage(
                                    f'Позиция {self.ticker} закрыта через {self.TIMEOUT} минут по limit. Прибыль составила {(self.orderbook[-1]["best_bid_0"] - self.enter_price) * self.pos_size_to_sell} USDT ({((self.orderbook[-1]["best_bid_0"] - self.enter_price) * self.pos_size_to_sell) / (self.pos_size_to_sell * self.enter_price / self.leverage) * 100} %)'))
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
                                self.getOrderBook()
                                self.enter_price = self.orderbook[-1]['best_bid_0']
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
            pass
            print(ex)
        finally:
            # orders_task.cancel()
            await self.exchange.close()
            # positions_task.cancel()
            # order_book_task.cancel()
            try:
                # await order_book_task
                pass
            except asyncio.CancelledError as e:
                print(e)

    def getNewGrowthPercentage(self):
        # если не вычитать, то он не спарсит нулевую свечу
        # вычитать нужно 59, чтобы не вывалиться на предыдущую минутную свечу (протестировано).
        # если новость вышла между 11:45:00 и 11:45:59 включительно, то этот скрипт за нулевую свечу примет ту, которая открылась в 11:45
        start_timestamp = self.news_date - 59 * 1000

        # это стандартный экземпляр без api ключей, поэтому таких можно создавать сколько угодно
        candles = self.binance.fetch_ohlcv(self.ticker, '1m', since=start_timestamp, limit=10)
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

    def updateResultTable(self, end_signal):
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

    # заполняет round_number для количества активов
    def detertime_constants(self):
        spot_url = "https://api.binance.com/api/v3/exchangeInfo?permissions=SPOT"
        try:
            response = requests.get(spot_url)
            response.raise_for_status()
            info = response.json()
            for data in info['symbols']:
                if data['status'] == 'TRADING' and data['isSpotTradingAllowed'] and data['symbol']==self.ticker:
                    ticker_info = data
            # print(ticker_info)
            step_size = ticker_info['filters'][1]['stepSize']
            print('step_size', step_size)
            if float(step_size) == 1:
                self.round_number = 0
            if float(step_size) > 1:
                self.round_number = -1 * len(str(float(step_size))) + 3
            if float(step_size) < 1:
                self.round_number = len(str(float(step_size))) - 2
            print('self.round_number', self.round_number)

        except Exception as e:
            print(f"Произошла ошибка при обращении к spot: {e}")
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в TickersParser.py writeIntoTickersDB(2),{e}'))
        




    def main(self):
        try:
            self.detertime_constants()
            # сообщение о запуске торгового задания.
            # asyncio.run(self.telegram_bot.sendMessageDebug(
            #         f'Тестовое торговое задание запущено. \n Листинг {self.ticker} \n '
            #         f'Дата: {datetime.utcfromtimestamp(self.listing_date / 1000)} UTC+0\n '
            #         f'Ожидание {datetime.utcfromtimestamp(self.listing_date / 1000 - 15 * 60)} UTC+0'))
                
            # if REAL_TRADING is True:
                # asyncio.run(self.telegram_bot.sendMessage(
            #         f'Тестовое торговое задание запущено. \n Листинг {self.ticker} \n '
            #         f'Дата: {datetime.utcfromtimestamp(self.listing_date / 1000)} UTC+0\n '
            #         f'Ожидание {datetime.utcfromtimestamp(self.listing_date / 1000 - 15 * 60)} UTC+0'))
            
            t = 0
            is_done = False # флаг, чтобы заполнить стоп лосс и тейк профит только один раз
            while True:
                time.sleep(1)
                t += 1
                print('Ожидание...')
            
                # когда наступает момент за 20 минут до листинга, запускается логика заполнения тейк профита и стоп лосса
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
                if time.time() * 1000 >= self.listing_date - 15 * 60 * 1000 and time.time() * 1000 <= self.listing_date:
                    asyncio.run(self.main_logic())
                    break
        except Exception as e:
            print(f'TradingTaskClass_binance_s main error: {e}')
            asyncio.create_task(self.telegram_bot.sendMessageDebug(f'TradingTaskClass_binance_s main error: {e}'))

    async def main_logic_1(self):
        print('start')
        # order_book_task = asyncio.create_task(self.getOrderBook())
        await asyncio.sleep(10)
        asyncio.create_task(self.telegram_bot.sendMessageDebug(f'ОРДЕРБУК: {self.orderbook}'))
        print(self.orderbook)
        self.getBalance()
        try:
            # self.getOrderBook()
            i = 0
            while True:
                i += 1
                print(i)
                await asyncio.sleep(1)
                if i == 5:
                    order_info = self.SpotEnterOrder(6)
                    if order_info[0] == 0: # успешно
                        self.current_order_id = order_info[1]
                if i == 10:
                    self.CancelSpotOrder()
        except Exception as e:
            print(f'ERROR {e}')
            await self.exchange.close()
            # order_book_task.cancel()
        finally:
            await self.exchange.close()
            # order_book_task.cancel()



# if __name__ == '__main__':
#     ALL_MARGIN = 6
#     ticker = '1000SATSUSDT'
#     leverage = 2
#     news_date = 1701598740000
#     listing_date = 1701262560000
#     # listing_date = time.time()*1000 + 60*1000

#     profit_percentage = 10
#     loss_percentage = profit_percentage / 2
#     TIMEOUT = 1  # min
#     bot_instance = NotificationsBot()
#     trading_task = TradingTaskBinance(ALL_MARGIN=ALL_MARGIN, ticker=ticker, leverage=leverage,
#                                       profit_percentage=profit_percentage, loss_percentage=loss_percentage,
#                                       news_date=news_date,
#                                       TIMEOUT=TIMEOUT,
#                                       listing_date=listing_date, bot=bot_instance, ccxtpro_instance=None,
#                                       pybit_instance=None)
#     trading_task.main()
