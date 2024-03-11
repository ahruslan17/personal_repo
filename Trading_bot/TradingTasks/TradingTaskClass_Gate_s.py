import random
import time
import logging
from datetime import datetime
from pybit.unified_trading import HTTP
import asyncio
import ccxt.pro as ccxtpro
import ccxt
from telegram import Bot
import requests

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from gate_api import SpotApi, ApiClient, FuturesApi, FuturesOrder, FuturesTrade, Order, \
    Configuration  # pip install gate_api

import time
import hashlib
import hmac
import requests
import json

from Notifications.Notifications import NotificationsBot


# import gate_api
# 'apiKey': '',
# 'secret': '',

class TradingTaskGate_s:
    def __init__(self, ticker, news_date, listing_date, leverage, profit_percentage, loss_percentage, ALL_MARGIN,
                 TIMEOUT, bot):


        self.telegram_bot = bot
        self.multiplier = 0

        self.api_key = ''
        self.secret_key = ''

        # экземпляр ccxtpro
        self.exchange = ccxtpro.gateio({
            'apiKey': '',
            'secret': '',
            'uid': ''})
        self.exchange.options['defaultType'] = 'spot'

        # экземпляр ccxt
        self.gate = ccxt.gateio()
        self.gate.apiKey = ''
        self.gate.secret = ''
        self.gate.uid = '14274293'
        self.gate.options['defaultType'] = 'spot'

        # экземпляр их библиотеки
        self.gate_futures_api = FuturesApi(
            ApiClient(Configuration(host="https://api.gateio.ws/api/v4", key='',
                                    secret='')))
        self.gate_spot_api = SpotApi(
            ApiClient(Configuration(host="https://api.gateio.ws/api/v4", key='',
                                    secret='')))

        self.ticker = ticker
        self.news_date = news_date
        self.listing_date = listing_date
        self.leverage = 1
        self.profit_percentage = profit_percentage
        self.loss_percentage = loss_percentage
        self.ALL_MARGIN = ALL_MARGIN
        self.TIMEOUT = TIMEOUT  # minutes

        self.cum_margin = 0
        self.bal = 0
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
        self.start_price_15min_before = 0
        self.isSold = False

    # считывает баланс токена. нужно, чтобы отслеживать купленные активы на споте
    def getBalance(self,flag='Enter'):
        balance_info = self.gate.fetch_balance()

        if self.ticker.replace('USDT', '') in balance_info:
            print(
                f"Balance information for {self.ticker.replace('USDT', '')}: {balance_info[self.ticker.replace('USDT', '')]['total']}")
            print(self.enter_price)
            if flag == 'Enter':
                self.cum_margin = float(balance_info[self.ticker.replace('USDT', '')]['total']) * float(self.enter_price)
                self.pos_size_to_sell = float(balance_info[self.ticker.replace('USDT', '')]['total'])
            self.bal = float(balance_info[self.ticker.replace('USDT', '')]['total']) * float(self.enter_price)
        else:
            print(f"Token {self.ticker.replace('USDT', '')} not found in the balance information.")

    # async def getOrderBook(self):
    #     while True:
    #         await asyncio.sleep(0.0001)
    #         ob = await self.exchange.watch_order_book(symbol=self.ticker.replace('USDT', '_USDT'),
    #                                                   limit=5)  # чтобы был спот, надо /USDT
    #
    #         current = {'best_bid_4': ob['bids'][4], 'best_bid_0': ob['bids'][0], 'best_ask_4': ob['asks'][4],
    #                    'best_ask_0': ob['asks'][0]}
    #         # print(current)
    #         self.orderbook = [current]

    # Ордербуки через ccxtpro плохо работат, а именно, когда цена идёт вверх, не обновляется цена бидов
    # Пока не знаю, как исправить, поэтому буду запрашивать через REST
    def getBestBidPrice(self):
        host = "https://api.gateio.ws"
        prefix = "/api/v4"
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        url = '/spot/order_book'
        query_param = f"currency_pair={self.ticker.replace('USDT', '_USDT')}"

        r = requests.request('GET', host + prefix + url + "?" + query_param, headers=headers)
        print('R ', r.json())
        print('OB', r.json()['bids'])
        print('BEST BID PRICE ', r.json()['bids'][0][0])
        return float(r.json()['bids'][0][0])

    def getBestBid10Price(self):
        host = "https://api.gateio.ws"
        prefix = "/api/v4"
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        url = '/spot/order_book'
        query_param = f"currency_pair={self.ticker.replace('USDT', '_USDT')}"

        r = requests.request('GET', host + prefix + url + "?" + query_param, headers=headers)
        print('R ', r.json())
        print('BEST BID 10 PRICE ', r.json()['bids'][9][0])
        return float(r.json()['bids'][9][0])

    def getBestAskPrice(self):
        host = "https://api.gateio.ws"
        prefix = "/api/v4"
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        url = '/spot/order_book'
        query_param = f"currency_pair={self.ticker.replace('USDT', '_USDT')}"
        r = requests.request('GET', host + prefix + url + "?" + query_param, headers=headers)
        print('BEST ASK PRICE', r.json()['asks'][0][0])
        return r.json()['asks'][0][0]

    def gen_sign(self, method, url, query_string=None, payload_string=None):
        key = self.api_key
        secret = self.secret_key
        t = time.time()
        m = hashlib.sha512()
        m.update((payload_string or "").encode('utf-8'))
        hashed_payload = m.hexdigest()
        s = '%s\n%s\n%s\n%s\n%s' % (method, url, query_string or "", hashed_payload, t)
        sign = hmac.new(secret.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
        return {'KEY': key, 'Timestamp': str(t), 'SIGN': sign}

    def SpotEnterOrder(self, position_sum):
        try:

            contract = self.ticker.replace('USDT', '_USDT')

            print('ОРДЕРБУК ', self.orderbook)
            self.enter_price = self.getBestBidPrice()
            pos_amount = float(position_sum) * float(self.leverage) / self.multiplier / self.enter_price
            print('pos_amount ', pos_amount)

            print('Выставить ордер')
            order = Order(amount=str(pos_amount), type='limit', side='buy', currency_pair=contract,
                          price=f"{self.enter_price}",
                          time_in_force='gtc')
            order_response = self.gate_spot_api.create_order(order)
            print('ORDER RESPONSE ', order_response)

            self.current_order_id = order_response.id
            print('order_id ', self.current_order_id)
            self.qActiveOrders = 1

            # если ордер полностью заполнился
            if order_response.status == 'finished':
                print('Ордер заполнен полностью')

            # если ордер заполнился частично или вообще не заполнился
            elif order_response.status == 'open':
                print('Заполнение ордера в процессе ')


        except Exception as e:
            print('placeFuturesOrder_gateio Error', e)

    def SpotExitOrder(self):
        contract = self.ticker.replace('USDT', '_USDT')
        print('SIZE TO EXIT', float(self.pos_size_to_sell))
        order = Order(amount=str(float(self.pos_size_to_sell) * 0.99), type='market', side='sell',
                      price=f"{self.getBestBid10Price()}",
                      currency_pair=contract,
                      time_in_force='ioc')
        order_response = self.gate_spot_api.create_order(order)
        print(order_response)
        self.isSold = True
        if order_response.status == 'closed':
            print('Ордер успешно закрыт')
        else:
            print('Проблемы с закрытием ордера или ещё не исполнился. Статус: ', order_response.status)

    def SpotExitOrderLimit(self):
        contract = self.ticker.replace('USDT', '_USDT')
        print('SIZE TO EXIT', float(self.pos_size_to_sell))
        order = Order(amount=str(float(self.pos_size_to_sell) * 0.99), type='limit', side='sell',
                      price='',
                      currency_pair=contract,
                      time_in_force='gtc')
        order_response = self.gate_spot_api.create_order(order)
        print(order_response)
        # self.isSold = True
        if order_response.status == 'closed':
            print('Ордер успешно закрыт')
        else:
            print('Проблемы с закрытием ордера или ещё не исполнился. Статус: ', order_response.status)

    def StopLossPrice(self, price):
        stop_price = price * (1 - self.loss_percentage / 100 / self.leverage)
        return stop_price

    def TakeProfitPrice(self, price):
        take_profit_price = price * (1 + self.profit_percentage / 100 / self.leverage)
        return take_profit_price

    def CancelSpotOrder(self):
        print('Отмена ордеров на гейте.')

        if self.gate_spot_api.get_order(str(self.current_order_id),
                                        currency_pair=self.ticker.replace('USDT', '_USDT')).status == 'open':
            print('ДЕЙСТВИТЕЛЬНО ОТМЕНИТЬ ОРДЕР')
            cancel_order_response = self.gate_spot_api.cancel_order(str(self.current_order_id),
                                                                    self.ticker.replace('USDT', '_USDT'))
            print(cancel_order_response)

            # если ничего не отменилось
            if not cancel_order_response:
                print('НЕТ ОРДЕРОВ ДЛЯ ОТМЕНЫ')

            # если что-то отменилось
            else:
                print('ОРДЕР ОТМЕНЕН')

                time.sleep(2)

                if int(cancel_order_response.fill_price) != 0:
                    print('order_response.fill_price != 0')
                    # self.cum_margin = self.ALL_MARGIN - float(cancel_order_response.left) * self.multiplier * float(
                    #     cancel_order_response.fill_price) / self.leverage
                    print('self.cum_margin ', self.cum_margin)
                else:
                    print('order_response.fill_price == 0')
                    # self.cum_margin = 0
                    print('self.cum_margin ', self.cum_margin)

        else:
            print('Ордер успел исполниться')
            pass

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

    async def main_logic(self):

        print('Main is started')
        asyncio.create_task(self.telegram_bot.sendMessageDebug('TradingTaskGate_s Main is started'))

        i = 0
        isMessageSent = False
        await asyncio.sleep(10)
        self.start_price_15min_before = self.getBestBidPrice()

        try:
            i = 0
            while True:
                i += 1
                print('-------------------')
                print(i)
                print('Количество ордеров в памяти qActiveOrders: ', self.qActiveOrders)
                print('Количество позиций qActivePositions: ', self.qActivePositions)
                print('GET POSITIONS')
                self.getBalance()
                print('ALL MARGIN ', self.ALL_MARGIN)
                print('CUM MARGIN ', self.cum_margin)
                print('SIZE TO SELL ', self.pos_size_to_sell)
                print('CONDITION ', self.cum_margin >= self.ALL_MARGIN - 1)

                if self.cum_margin >= self.ALL_MARGIN - 1:
                    print('Простановка ордеров на вход запрещена. ВСЕ ДЕНЬГИ ЗАГРУЖЕНЫ В ПОЗИЦИЮ.')
                    print('Отслеживание стоп-лосса и тейк профита включено. Количество активов на продажу: ',
                          self.pos_size_to_sell)
                    stop_price = round(
                        self.StopLossPrice(self.start_price_15min_before), 5)
                    profit_price = round(self.TakeProfitPrice(self.start_price_15min_before), 5)
                    print('--Цена стоп-лосса: ', stop_price)
                    print('--Цена тейк профита: ', profit_price)
                    print('--Текущая цена ', self.getBestBidPrice())
                    time.sleep(1)

                    if not isMessageSent:
                        asyncio.create_task(self.telegram_bot.sendMessageDebug(
                            f'Информация о входе в позицию \n Инструмент: {self.ticker} \n Свобственных средств: '
                            f'{self.pos_size_to_sell * self.multiplier * self.enter_price / self.leverage} USDT \n Плечо: '
                            f'{self.leverage}x \n Размер позиции: {self.pos_size_to_sell * self.enter_price * self.multiplier} USDT'
                            f' \n Было куплено: {self.pos_size_to_sell * self.multiplier} {self.ticker.replace("USDT", "")} \n '
                            f'Средняя цена входа: ${self.enter_price} \n Рост на выходе новости: {self.profit_percentage * 2}% \n Уровень тейк-профита '
                            f'{self.profit_percentage}% \n Уровень стоп-лосса {self.loss_percentage}% \n '
                            f'Профит-цена: ${profit_price} \n Стоп-цена: ${stop_price}'))
                        asyncio.create_task(self.telegram_bot.sendMessage(
                            f'Информация о входе в позицию \n Инструмент: {self.ticker} \n Свобственных средств: '
                            f'{self.pos_size_to_sell * self.multiplier * self.enter_price / self.leverage} USDT \n Плечо: '
                            f'{self.leverage}x \n Размер позиции: {self.pos_size_to_sell * self.enter_price * self.multiplier} USDT'
                            f' \n Было куплено: {self.pos_size_to_sell * self.multiplier} {self.ticker.replace("USDT", "")} \n '
                            f'Средняя цена входа: ${self.enter_price} \n Рост на выходе новости: {self.profit_percentage * 2}% \n Уровень тейк-профита '
                            f'{self.profit_percentage}% \n Уровень стоп-лосса {self.loss_percentage}% \n '
                            f'Профит-цена: ${profit_price} \n Стоп-цена: ${stop_price}'))
                        isMessageSent = True

                    if float(self.getBestBidPrice()) >= profit_price:
                        print('Цена тейк-профита достигнута. Закрыть лимиткой')
                        print('Количество позиций: ', self.qActivePositions)
                        self.SpotExitOrder()
                        self.out_price = self.getBestBidPrice()
                        await asyncio.sleep(1)

                        if self.isSold:
                            asyncio.create_task(self.telegram_bot.sendMessageDebug(
                                f'Позиция {self.ticker} закрыта по Take-Profit. Прибыль составила '
                                f'{round(((self.out_price - self.enter_price) / self.enter_price) * self.cum_margin * self.leverage, 3)} USDT'))
                            asyncio.create_task(self.telegram_bot.sendMessage(
                                f'Позиция {self.ticker} закрыта по Take-Profit. Прибыль составила '
                                f'{round(((self.out_price - self.enter_price) / self.enter_price) * self.cum_margin * self.leverage, 3)} USDT'))
                            await asyncio.sleep(2)
                            self.updateResultTable(end_signal='takeprofit')
                            print(
                                'Все позиции закрыты. Сигнал на завершение работы торгового задания. '
                                'Заполнили тейк профит.')
                            break

                    if float(self.getBestBidPrice()) <= stop_price:
                        print('Цена стоп-лосса достигнута. Закрыть по маркету')
                        print('Количество позиций: ', self.qActivePositions)
                        self.SpotExitOrder()
                        self.out_price = self.getBestBidPrice()
                        await asyncio.sleep(1)

                        if self.isSold:
                            asyncio.create_task(self.telegram_bot.sendMessageDebug(
                                f'Позиция {self.ticker} закрыта по Stop-Loss. Убыток составил '
                                f'{round(((self.out_price - self.enter_price) / self.enter_price) * self.cum_margin * self.leverage, 3)} USDT'))
                            asyncio.create_task(self.telegram_bot.sendMessage(
                                f'Позиция {self.ticker} закрыта по Stop-Loss. Убыток составил '
                                f'{round(((self.out_price - self.enter_price) / self.enter_price) * self.cum_margin * self.leverage, 3)} USDT'))
                            await asyncio.sleep(2)
                            self.updateResultTable(end_signal='stoploss')
                            print(
                                'Все позиции закрыты. Сигнал на завершение работы торгового задания. '
                                'Заполнили стоп лосс.')
                            break

                    if time.time() * 1000 >= self.pos_start_datetime + self.TIMEOUT * 60 * 1000:
                        print('Превышен лимит по времени. Закрыть по limit. ')
                        self.SpotExitOrderLimit()

                        while self.bal > 1:
                            self.getBalance(flag='Exit')
                            self.isSold = True

                        if self.bal < 1:
                            self.getBalance(flag='Exit')
                            self.isSold = True


                        if self.isSold:
                            print('ПОЗИЦИЯ ПРОДАНА')
                            self.out_price = self.getBestBidPrice()
                            asyncio.create_task(self.telegram_bot.sendMessageDebug(
                                f'Позиция {self.ticker} закрыта через {self.TIMEOUT} минут по limit. Прибыль составила {round(((self.out_price - self.enter_price) / self.enter_price) * self.cum_margin * self.leverage, 3)} USDT ({round(((self.out_price - self.enter_price) / self.enter_price) * 100 * self.leverage, 3)} %)'))
                            asyncio.create_task(self.telegram_bot.sendMessage(
                                f'Позиция {self.ticker} закрыта через {self.TIMEOUT} минут по limit. Прибыль составила {round(((self.out_price - self.enter_price) / self.enter_price) * self.cum_margin * self.leverage, 3)} USDT ({round(((self.out_price - self.enter_price) / self.enter_price) * 100 * self.leverage, 3)} %)'))
                            
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

                    if self.qActiveOrders == 0:
                        print('Текущих ордеров нет. Открыть новый ордер')
                        delay = random.uniform(1, 5)
                        print(f'Ждем {delay / 20} секунд перед открытием нового ордера. Для защиты')
                        await asyncio.sleep(delay / 10)
                        print('ОТКРЫТЬ ПОЗИЦИЮ НА СУММУ ', self.ALL_MARGIN - self.cum_margin)
                        self.SpotEnterOrder(self.ALL_MARGIN - self.cum_margin)
                        time.sleep(10)

            await self.exchange.close()
        except KeyboardInterrupt as inter:
            print(inter)
        except Exception as ex:
            await self.exchange.close()
            print('ОШИБКА ', ex)
            asyncio.create_task(
                self.telegram_bot.sendMessageDebug('TradingTaskClass_gate_s main error'))
            
        finally:
            # order_book_task.cancel()
            await self.exchange.close()
            # positions_task.cancel()
            # try:
            # await order_book_task
            # except asyncio.CancelledError as e:
            #     print(e)

    def getNewGrowthPercentage(self):
        # если не вычитать, то он не спарсит нулевую свечу
        # вычитать нужно 59, чтобы не вывалиться на предыдущую минутную свечу (протестировано).
        # если новость вышла между 11:45:00 и 11:45:59 включительно, то этот скрипт за нулевую свечу примет ту, которая открылась в 11:45
        start_timestamp = self.news_date - 59 * 1000

        # это стандартный экземпляр без api ключей, поэтому таких можно создавать сколько угодно

        symbol = self.ticker.replace('USDT', '_USDT')

        candles = self.gate.fetch_ohlcv(symbol, '1m', since=start_timestamp, limit=10)
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

    def main(self):

        # заранее установить плечо
        # self.gate_futures_api.update_position_leverage('usdt', self.ticker.replace('USDT', '_USDT'), str(self.leverage))
        # заполнить self.multiplier, так как он используется для входа в позиции
        # futures_contract = self.gate_futures_api.get_futures_contract('usdt', self.ticker.replace('USDT', '_USDT'))
        # self.multiplier = float(futures_contract.quanto_multiplier)
        self.multiplier = 1

        # сообщение о запуске торгового задания.
        # asyncio.run(self.telegram_bot.sendMessageDebug(
        #     f'Тестовое торговое задание запущено. \n Листинг {self.ticker} \n '
        #     f'Дата: {datetime.utcfromtimestamp(self.listing_date / 1000)} UTC+0\n '
        #     f'Ожидание {datetime.utcfromtimestamp(self.listing_date / 1000 - 15 * 60)} UTC+0'))
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
                break


# if __name__ == '__main__':
#     ALL_MARGIN = 3
#     ticker = 'DOGEUSDT'
#     leverage = 2
#     news_date = 1701508500000
#     listing_date = 1701376800000
#     # listing_date = time.time()*1000 + 60*1000
#
#     profit_percentage = 10
#     loss_percentage = profit_percentage / 2
#     TIMEOUT = 60  # min
#     bot_instance = NotificationsBot()
#     trading_task = TradingTaskGate_s(ALL_MARGIN=ALL_MARGIN, ticker=ticker, leverage=leverage,
#                                      profit_percentage=profit_percentage, loss_percentage=loss_percentage,
#                                      news_date=news_date,
#                                      TIMEOUT=TIMEOUT,
#                                      listing_date=listing_date, bot=bot_instance)
#     trading_task.main()
