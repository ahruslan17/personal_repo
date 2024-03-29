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

import logging

import okx.Trade as Trade
import okx.Account as Account
import okx.MarketData as MarketData
import okx.PublicData as PublicData
import okx.SpreadTrading as SpreadTrading
from datetime import datetime
import time

import asyncio

from Notifications.Notifications import NotificationsBot


# api_key  = '9730c4fe-3cdf-4c21-a527-eca09a8ec3ff'
# api_key = '65deb562-e15c-4fae-b7e3-514f5fef1b5e'
# secret_key  = '73CEACCAECA8849C6CF1F92240CDF122'
# secret_key = '2DCB4772980591E2A008476BA4A25E8C'
# passphrase = 'Pass_phrase1'

#
# 2666b857-dab7-4ad4-a557-f411fd8a9bb7
# D7DB0C51E5D2ABEE4B412A985EC67F59
# Pass_Phrase_1

class TradingTaskOKX:
    def __init__(self, ticker, news_date, listing_date, leverage, profit_percentage, loss_percentage, ALL_MARGIN,
                 TIMEOUT, bot):
        # "bot" is an instance of NotificationsBot class from Notifications.py
        self.telegram_bot = bot

        self.exchange = ccxtpro.okex({'options': {'defaultType': 'SWAP'}})
        self.exchange.apiKey = '2666b857-dab7-4ad4-a557-f411fd8a9bb7'
        self.exchange.secret = 'D7DB0C51E5D2ABEE4B412A985EC67F59'
        self.exchange.password = 'Pass_Phrase_1'
        # self.exchange.set_sandbox_mode(True)

        self.accountAPI = Account.AccountAPI('2666b857-dab7-4ad4-a557-f411fd8a9bb7', 'D7DB0C51E5D2ABEE4B412A985EC67F59',
                                             'Pass_Phrase_1', False, flag='0')
        self.tradeAPI = Trade.TradeAPI('2666b857-dab7-4ad4-a557-f411fd8a9bb7', 'D7DB0C51E5D2ABEE4B412A985EC67F59',
                                       'Pass_Phrase_1', False, flag='0')
        self.spreadAPI = SpreadTrading.SpreadTradingAPI('2666b857-dab7-4ad4-a557-f411fd8a9bb7',
                                                        'D7DB0C51E5D2ABEE4B412A985EC67F59', 'Pass_Phrase_1', False,
                                                        flag='0')

        # данные для открытия позиции
        self.ticker = ticker
        self.news_date = news_date
        self.listing_date = listing_date
        self.leverage = leverage
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
        self.multiplier = 0
        self.isSold = False

    async def getOrderBook(self):
        while True:
            await asyncio.sleep(0.01)
            ob = await self.exchange.watch_order_book(symbol=self.ticker.replace('USDT', '/USDT'), limit=10)
            print(ob)
            current = {'best_bid_0': ob['bids'][0], 'best_bid_10': ob['bids'][9], 'best_ask_4': ob['asks'][4]}
            self.orderbook = [current]

    # def getBestBidPrice(self):
    #     marketDataAPI = MarketData.MarketAPI(flag='0')
    #     ob = marketDataAPI.get_orderbook(instId=f'{self.ticker.replace("USDT", "-USDT")}-SWAP')['data'][0]
    #     print('ob', ob)
    #     return float(ob['bids'][0][0])

    # def getBestAskPrice(self):
    #     marketDataAPI = MarketData.MarketAPI(flag='0')
    #     ob = marketDataAPI.get_orderbook(instId=f'{self.ticker.replace("USDT", "-USDT")}-SWAP')['data'][0]
    #     print('ob', ob)
    #     return float(ob['asks'][0][0])

    # def getFuturesPrice_okx(self):
    #     s_time = time.time()
    #     try:
    #         publicDataAPI = PublicData.PublicAPI(flag='0')
    #
    #         f_time = time.time()
    #         logging.info(f"getFuturesPrice_okx is done. {(f_time - s_time)} sec: ")
    #         return \
    #         publicDataAPI.get_mark_price(instType='SWAP', instId=f'{self.ticker.replace("USDT", "-USDT")}-SWAP')['data'][0][
    #             'markPx']
    #     except Exception as e:
    #         print('getSpotPrice_okx Error:', e)
    #         logging.info(f"getSpotPrice_okx Error: {e}")
    #         return -11


    def SetLeverage_okx(self):
        s_time = time.time()
        try:
            result = self.accountAPI.set_leverage(lever=self.leverage, mgnMode='isolated',
                                                  instId=self.ticker.replace('USDT', '-USDT') + '-SWAP')
            f_time = time.time()
            logging.info(f"SetLeverage_okx is done. {(f_time - s_time)} sec: ")

            return result
        except Exception as e:
            print('SetLeverage_okx Error', e)
            logging.info(f"SetLeverage_okx Error: {e}")

            return -11

    def setMultipliers(self):
        s_time = time.time()
        try:
            publicDataAPI = PublicData.PublicAPI(flag='0')
            f_time = time.time()
            logging.info(f"getFuturesSize_okx is done. {(f_time - s_time)} sec: ")
            self.multiplier = \
            publicDataAPI.get_instruments(instType='SWAP', instId=f'{self.ticker.replace("USDT", "-USDT")}-SWAP')['data'][0][
                'ctVal']
            self.round_number = \
            publicDataAPI.get_instruments(instType='SWAP', instId=f'{self.ticker.replace("USDT", "-USDT")}-SWAP')['data'][0][
                'lotSz']

        except Exception as e:
            print('getFuturesPrice_okx Error', e)
            logging.info(f"getFuturesPrice_okx Error: {e}")
            return -11

    def FuturesEnterOrder_okx(self, position_sum):
        s_time = time.time()
        try:
            start_time = time.time() * 1000


            # pos_amount = f'{float(position_sum) * float(self.leverage) / float(self.multiplier) / float(
            # self.orderbook[-1]["best_bid_1"][0])}'
            pos_amount = f'{float(position_sum) * float(self.leverage) / float(self.multiplier) / float(self.orderbook[-1]["best_bid_0"][0])}'

            print('pos_amount', pos_amount)
            print(self.multiplier, self.round_number)
            result = self.tradeAPI.place_order(
                instId=self.ticker.replace('USDT', '-USDT') + '-SWAP',
                tdMode='isolated',
                side='buy',
                ordType='limit',
                px=f'{float(self.orderbook[-1]["best_bid_0"][0])}',
                sz=round(float(pos_amount), int(self.round_number) - 1)
            )
            print('RESULT', result)

            self.current_order_id = result['data'][0]['ordId']
            print('self.current_order_id', self.current_order_id)

            if result['code'] == '0':
                order_info = self.tradeAPI.get_order(instId=self.ticker.replace('USDT', '-USDT-SWAP'),
                                                     ordId=self.current_order_id)
                print('ОРДЕР', order_info)

                # Если успешно разместили ордер, помечаем, что есть ордер. Чтобы не выставлялось два ордера одновременно.
                self.qActiveOrders = 1

                # Смотрим, сколько удалось разместить в позиции (накопленное) - смотрим в другом месте.
                # self.cum_margin = self.cum_margin + float(order_info['data'][0]['accFillSz'])*float(order_info['data'][0]['avgPx']) * float(self.multiplier) / self.leverage

                f_time = time.time()
                logging.info(f"FuturesEnterOrder_okx is done. {(f_time - s_time)} sec: ")
                return 0
            else:
                print('Error in FutureEnterOrder_okx')
                print(result)
                # asyncio.run(send_telegram_message(f"Error in FuturesEnterOrder_okx \n {result['data'][0]['sMsg']}"))
            return result
        except Exception as e:
            print('FuturesEnterOrder_okx Error', e)
            logging.info(f"FuturesEnterOrder_okx Error: {e}")
            return -1

    def FuturesCancelOrder_okx(self):
        s_time = time.time()
        try:
            result = self.tradeAPI.cancel_order(instId=self.ticker.replace('USDT', '-USDT-SWAP'),
                                                ordId=self.current_order_id)
            print(result)
            f_time = time.time()
            logging.info(f"FuturesCancelOrder_okx is done. {(f_time - s_time)} sec: ")

            return result
        except Exception as e:
            print('SetLeverage_okx Error', e)
            logging.info(f"SetLeverage_okx Error: {e}")

            return -11
    def FuturesExitOrder_okx(self):
        s_time = time.time()
        try:
            result = self.tradeAPI.place_order(
                instId=self.ticker.replace('USDT', '-USDT') + '-SWAP',
                tdMode='isolated',
                side='sell',
                ordType='market',
                sz=self.pos_size_to_sell
            )
            print('SELL RESULT', result)
            self.isSold = True

            if result['code'] == '0':
                return 0

            else:
                print('Error in FutureExitOrder_okx')
                print(result)
                # asyncio.run(send_telegram_message(f"Error in FuturesEnterOrder_okx \n {result['data'][0]['sMsg']}"))
            return result
        except Exception as e:
            print('FuturesEnterOrder_okx Error', e)
            logging.info(f"FuturesEnterOrder_okx Error: {e}")
            return -1

    def FuturesExitOrderLimit_okx(self):
        s_time = time.time()
        try:
            result = self.tradeAPI.place_order(
                instId=self.ticker.replace('USDT', '-USDT') + '-SWAP',
                tdMode='isolated',
                side='sell',
                ordType='limit',
                px=f'{float(self.orderbook[-1]["best_bid_10"][0])}',
                sz=self.pos_size_to_sell
            )
            print('SELL RESULT', result)
            # self.isSold = True

            if result['code'] == '0':
                return 0

            else:
                print('Error in FutureExitOrder_okx')
                print(result)
                # asyncio.run(send_telegram_message(f"Error in FuturesEnterOrder_okx \n {result['data'][0]['sMsg']}"))
            return result
        except Exception as e:
            print('FuturesEnterOrder_okx Error', e)
            logging.info(f"FuturesEnterOrder_okx Error: {e}")
            return -1
    def StopLossPrice(self, start_price):
        stop_price = start_price * (1 - self.loss_percentage / 100)
        return stop_price

    def TakeProfitPrice(self, start_price):
        take_profit_price = start_price * (1 + self.profit_percentage / 100)
        return take_profit_price

    # async def main_logic_test(self):
    #     print('Main is started')
    #     self.SetLeverage_okx()
    #     self.setMultipliers()
    #     print('BEST BID', self.getBestBidPrice())
    #     print('BEST ASK', self.getBestAskPrice())
    #
    #
    #     # order_book_task = asyncio.create_task(self.getOrderBook())
    #
    #     i = 0
    #     await asyncio.sleep(1)
    #     try:
    #         isMessageSent = False
    #         while True:
    #             i += 1
    #             await asyncio.sleep(5)
    #             print(i)
    #             if i == 2:
    #                 print('ОКРЫТЬ ТЕСТ ПОЗИЦИЮ')
    #                 self.FuturesEnterOrder_okx(5)
    #             # if i == 3:
    #             #     print('ОТМЕНИТЬ ОРДЕР')
    #             #     self.FuturesCancelOrder_okx()
    #
    #             if self.current_order_id != 0:
    #                 order_info = self.tradeAPI.get_order(instId=self.ticker.replace('USDT', '-USDT-SWAP'),
    #                                                  ordId=self.current_order_id)
    #                 print('ОРДЕР', order_info)
    #     except:
    #         pass

    def getNewGrowthPercentage(self):
        # если не вычитать, то он не спарсит нулевую свечу
        # вычитать нужно 59, чтобы не вывалиться на предыдущую минутную свечу (протестировано).
        # если новость вышла между 11:45:00 и 11:45:59 включительно, то этот скрипт за нулевую свечу примет ту, которая открылась в 11:45
        start_timestamp = self.news_date - 59 * 1000

        # это стандартный экземпляр без api ключей, поэтому таких можно создавать сколько угодно
        exchange = ccxt.okx()
        exchange.options['defaultType'] = 'future'
        symbol = self.ticker.replace('USDT', '-USDT-SWAP')

        candles = exchange.fetch_ohlcv(symbol, '1m', since=start_timestamp, limit=10)
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

    async def main_logic(self):
        print('Main is started')
        asyncio.create_task(self.telegram_bot.sendMessageDebug('15 минут до листинга. Открываем позицию.'))
        asyncio.create_task(self.telegram_bot.sendMessage('15 минут до листинга. Открываем позицию.'))

        order_book_task = asyncio.create_task(self.getOrderBook())
        
        await asyncio.sleep(10)

        # start_price_15min_before = self.getBestBidPrice()
        start_price_15min_before = self.orderbook[-1]['best_bid_0'][0]

        try:
            i = 0
            isMessageSent = False
            while True:
                i += 1
                print('----------------------------------------------------------------')
                print(i)
                print('Количество ордеров в памяти qActiveOrders: ', self.qActiveOrders)
                print('Количество позиций qActivePositions: ', self.qActivePositions)
                print('CUM MARGIN', self.cum_margin)
                print('ALL MARGIN', self.ALL_MARGIN)
                if i > 3:
                    if self.cum_margin >= self.ALL_MARGIN - 1:  # полностью вошли в позицию

                        if not isMessageSent: # опеделяет первый заход в этот цикл
                            self.pos_start_datetime = time.time()*1000 # с момента загрузки начинаем отслеживать таймаут (проверяется далее)
                            self.qActivePositions = 1

                        # Если полностью вошли в позицию, запоминаем цену, по которой зашли
                        self.enter_price = float(self.tradeAPI.get_order(instId=self.ticker.replace('USDT', '-USDT-SWAP'),
                                                     ordId=self.current_order_id)['data'][0]['avgPx'])
                        if not self.enter_price:
                            self.enter_price = self.orderbook[-1]['best_bid_0'][0]




                        print('Простановка ордеров на вход запрещена. ВСЕ ДЕНЬГИ ЗАГРУЖЕНЫ В ПОЗИЦИЮ.')
                        print('Отслеживание стоп-лосса и тейк профита включено. Количество активов на продажу: ',
                              self.pos_size_to_sell)
                        stop_price = round(
                            self.StopLossPrice(start_price_15min_before), 5)
                        profit_price = round(self.TakeProfitPrice(start_price_15min_before), 5)

                        print('FLOAT(MULTIPLIER)', float(self.multiplier))

                        if not isMessageSent:
                            asyncio.create_task(self.telegram_bot.sendMessageDebug(
                                f'Информация о входе в позицию \n Инструмент: {self.ticker} \n Свобственных средств: '
                                f'{float(self.pos_size_to_sell) * float(self.multiplier) * float(self.enter_price) / float(self.leverage)} USDT \n Плечо: '
                                f'{self.leverage}x \n Размер позиции: {float(self.pos_size_to_sell) * float(self.enter_price) * float(self.multiplier)} USDT'
                                f' \n Было куплено: {float(self.pos_size_to_sell)*float(self.multiplier)} {self.ticker.replace("USDT", "")} \n '
                                f'Средняя цена входа: {self.enter_price} \n Уровень тейк-профита '
                                f'{self.profit_percentage}% \n Уровень стоп-лосса {self.loss_percentage}% \n '
                                f'Профит-цена: ${profit_price} \n Стоп-цена: ${stop_price}'))
                            asyncio.create_task(self.telegram_bot.sendMessage(
                                f'Информация о входе в позицию \n Инструмент: {self.ticker} \n Свобственных средств: '
                                f'{float(self.pos_size_to_sell) * float(self.multiplier) * float(self.enter_price) / float(self.leverage)} USDT \n Плечо: '
                                f'{self.leverage}x \n Размер позиции: {float(self.pos_size_to_sell) * float(self.enter_price) * float(self.multiplier)} USDT'
                                f' \n Было куплено: {float(self.pos_size_to_sell)*float(self.multiplier)} {self.ticker.replace("USDT", "")} \n '
                                f'Средняя цена входа: {self.enter_price} \n Уровень тейк-профита '
                                f'{self.profit_percentage}% \n Уровень стоп-лосса {self.loss_percentage}% \n '
                                f'Профит-цена: ${profit_price} \n Стоп-цена: ${stop_price}'))
                            isMessageSent = True

                        print('--Цена стоп-лосса: ', stop_price)
                        print('--Цена тейк профита: ', profit_price)
                        print('--Текущая цена ', self.orderbook[-1]['best_bid_0'][0])

                        if float(self.orderbook[-1]['best_bid_0'][0]) >= profit_price:
                            print('Цена тейк-профита достигнута. Закрыть лимиткой')
                            # print('Количество позиций: ', self.qActivePositions)
                            self.FuturesExitOrder_okx()
                            await asyncio.sleep(2)
                            self.out_price = self.orderbook[-1]['best_bid_0'][0]
                            # isSold = True
                            if self.isSold:
                                asyncio.create_task(self.telegram_bot.sendMessageDebug(
                                    f'Позиция {self.ticker} закрыта по Take-Profit. Прибыль составила '
                                    f'{round(((self.out_price - self.enter_price) / self.enter_price) * self.cum_margin * self.leverage,3)} USDT'))
                                asyncio.create_task(self.telegram_bot.sendMessage(
                                    f'Позиция {self.ticker} закрыта по Take-Profit. Прибыль составила '
                                    f'{round(((self.out_price - self.enter_price) / self.enter_price) * self.cum_margin * self.leverage,3)} USDT'))
                                await asyncio.sleep(2)
                                self.updateResultTable(end_signal='takeprofit')
                                print(
                                    'Все позиции закрыты. Сигнал на завершение работы торгового задания. '
                                    'Заполнили тейк профит.')
                                break

                        if float(self.orderbook[-1]['best_bid_0'][0]) <= stop_price:
                            print('Цена стоп-лосса достигнута. Закрыть по маркету')
                            # print('Количество позиций: ', self.qActivePositions)
                            self.FuturesExitOrder_okx()
                            await asyncio.sleep(2)
                            self.out_price = self.orderbook[-1]['best_bid_0'][0]

                            if self.isSold:
                                asyncio.create_task(self.telegram_bot.sendMessageDebug(
                                    f'Позиция {self.ticker} закрыта по Stop-Loss. Убыток составил '
                                    f'{round(((self.out_price - self.enter_price) / self.enter_price) * self.cum_margin * self.leverage,3)} USDT'))
                                asyncio.create_task(self.telegram_bot.sendMessage(
                                    f'Позиция {self.ticker} закрыта по Stop-Loss. Убыток составил '
                                    f'{round(((self.out_price - self.enter_price) / self.enter_price) * self.cum_margin * self.leverage,3)} USDT'))
                                await asyncio.sleep(2)
                                self.updateResultTable(end_signal='stoploss')
                                print(
                                    'Все позиции закрыты. Сигнал на завершение работы торгового задания. '
                                    'Заполнили стоп лосс.')
                                break

                        if time.time() * 1000 >= self.pos_start_datetime + self.TIMEOUT * 60 * 1000:
                            print('Превышен лимит по времени. Закрыть по limit. ')
                            self.FuturesExitOrderLimit_okx()
                            await asyncio.sleep(2)
                            self.isSold = True

                            if self.isSold:
                                print('ПОЗИЦИЯ ПРОДАНА')
                                self.out_price = self.orderbook[-1]['best_bid_0'][0]
                                asyncio.create_task(self.telegram_bot.sendMessageDebug(
                                    f'Позиция {self.ticker} закрыта через {self.TIMEOUT} минут по limit. Прибыль составила {round(((self.out_price - self.enter_price) / self.enter_price) * self.cum_margin * self.leverage,3)} USDT ({round(((self.out_price - self.enter_price) / self.enter_price) * 100 * self.leverage, 3)} %)'))
                                asyncio.create_task(self.telegram_bot.sendMessage(
                                    f'Позиция {self.ticker} закрыта через {self.TIMEOUT} минут по limit. Прибыль составила {round(((self.out_price - self.enter_price) / self.enter_price) * self.cum_margin * self.leverage,3)} USDT ({round(((self.out_price - self.enter_price) / self.enter_price) * 100 * self.leverage, 3)} %)'))
                                await asyncio.sleep(2)
                                self.updateResultTable(end_signal='timeout')
                                print(
                                    'Все позиции закрыты. Сигнал на завершение работы торгового задания. Лимит по времени.')
                                break


                    else:
                        print('Простановка ордеров разрешена')
                        if self.qActiveOrders > 0:
                            print('Удалить ордер')
                            # если ордер исполнен, то отменить его не получится, но ошибки не будет, поэтому исключение можно не обрабатывать
                            self.FuturesCancelOrder_okx()
                            # после отмены ордера помечаем, что нет активных ордеров, и можно открывать новые
                            self.qActiveOrders = 0
                            time.sleep(1) # пауза, чтобы ордер успел отмениться


                        if self.qActiveOrders == 0:
                            print('Текущих ордеров нет. Открыть новый ордер')
                            delay = random.uniform(2, 6)
                            print(f'Ждем {delay / 10} секунд перед открытием нового ордера. Для защиты')
                            await asyncio.sleep(delay / 10)
                            print('ОТКРЫТЬ ПОЗИЦИЮ НА СУММУ ', self.ALL_MARGIN-self.cum_margin)
                            order_code = self.FuturesEnterOrder_okx(self.ALL_MARGIN-self.cum_margin)
                            if order_code == 0:
                                print('Новый ордер ', self.current_order_id)
                                print('SLEEP 10')
                                await asyncio.sleep(5)
                                time.sleep(5)
                                # Проверка на случай, если сразу после выставления ордера он не активировался, но через 5 секунды активировался
                                # плюс если постоянно переставлять ордер, то это плохо, т.к. цена может его не зацепить при колебаниях из-за постоянной перестановки
                                info = self.tradeAPI.get_order(instId=self.ticker.replace('USDT', '-USDT-SWAP'), ordId=self.current_order_id)
                                print('POS INFO IN MAIN', info)
                                # если ордер исполнился, полностью или частично, нужно запомнить, сколько исполнилось, чтобы отслеживать вход в позицию
                                if info['data'][0]['avgPx']:
                                    self.cum_margin += float(info['data'][0]['accFillSz']) * float(info['data'][0]['avgPx']) * float(self.multiplier) / self.leverage

                                    #аналогично накопительным образом запоминаем количество лотов, которые потом надо продать
                                    # и количество лотов, на которое зашли (по нему легко продавать, т.к. оно уже как надо округленное)
                                    self.pos_size_to_sell += float(info['data'][0]['accFillSz'])

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
            print('ОШИБКА ', ex)
            asyncio.create_task(
                self.telegram_bot.sendMessageDebug('TradingTaskClass_okx main error'))
        finally:
            await self.exchange.close()



    def main(self):
        # сообщение о запуске торгового задания.
        # asyncio.run(self.telegram_bot.sendMessageDebug(
        #     f'Торговое задание запущено. \n Листинг {self.ticker} \n '
        #     f'Дата: {datetime.utcfromtimestamp(self.listing_date / 1000)} UTC+0\n '
        #     f'Ожидание {datetime.utcfromtimestamp(self.listing_date / 1000 - 15 * 60)} UTC+0'))
        # asyncio.run(self.telegram_bot.sendMessage(
        #     f'Торговое задание запущено. \n Листинг {self.ticker} \n '
        #     f'Дата: {datetime.utcfromtimestamp(self.listing_date / 1000)} UTC+0\n '
        #     f'Ожидание {datetime.utcfromtimestamp(self.listing_date / 1000 - 15 * 60)} UTC+0'))

        # заранее установить плечо и тип маржи
        self.SetLeverage_okx()

        # заранее подгрузить требуемые константы
        self.setMultipliers()

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
            # if time.time() * 1000 >= self.listing_date - 15 * 60 * 1000:  # для теста
            if time.time() * 1000 >= self.listing_date - 15 * 60 * 1000 - 10 * 1000 and time.time() * 1000 <= self.listing_date:

                asyncio.run(self.main_logic())
                break


# if __name__ == '__main__':
#
#     ALL_MARGIN = 9
#     exchange_name = 'okx'
#     ticker = 'IOTAUSDT'
#     leverage = 2
#     news_date = 1701508500000
#     listing_date = 1701262560000
#     # listing_date = time.time()*1000 + 60*1000
#
#     profit_percentage = 1
#     loss_percentage = profit_percentage / 2
#     TIMEOUT = 60  # min
#     bot_instance = NotificationsBot()
#     trading_task = TradingTaskOKX(ALL_MARGIN=ALL_MARGIN, ticker=ticker, leverage=leverage,
#                                   profit_percentage=profit_percentage, loss_percentage=loss_percentage,
#                                   news_date=news_date,
#                                   TIMEOUT=TIMEOUT,
#                                   listing_date=listing_date, bot=bot_instance)
#     trading_task.main()
