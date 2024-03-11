import random
import time
import logging
from datetime import datetime
from pybit.unified_trading import HTTP
import asyncio
import ccxt.pro as ccxtpro
import ccxt
from telegram import Bot



class TradingTask:
    def __init__(self, exchange_name, ticker, listing_date, leverage, profit_percentage, loss_percentage, ALL_MARGIN,
                 TIMEOUT):
        self.bot_token = '6354808644:AAEA9pvVZj6YqvXKCyyyF9ay0q4mdXqXfxE'
        # self.chatId = -1002096660763 # general
        self.chatId = -1001995965101  # debug
        self.exchange_name = exchange_name

        # TODO Лучше не создавать экземпляр биржи внутри класса, так как при одноверменном запуске многих торговых заданий
        # у тебя будет много экземпляров одной биржи с одним и тем же ключем и секреткой (что не очень хорошо)
        if exchange_name == 'bybit':
            self.exchange = ccxtpro.bybit()
            self.exchange.apiKey = 'HS398zpUdxSahhV6se'
            self.exchange.secret = 'e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T'
            self.session_bybit = HTTP(api_key='HS398zpUdxSahhV6se', api_secret='e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T')

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

    # TODO. У тебя класс определяет логику торгового задания, поэтому, вообще говоря, 
    # не очень правильно добавлять здесь функции, отвечающие за уведомления. Плюс,
    # ты при каждом вызове функции будешь создавать новый экземпляр того же самого бота,
    # что тоже плохо
    async def send_telegram_message(self, message_text):
        try:
            bot = Bot(token=self.bot_token)
            await bot.send_message(chat_id=self.chatId, text=message_text)
        except Exception as e:
            print('Сообщение не отправлено', e)

    async def getOrderBook(self):
        while True:
            # await asyncio.sleep(0.1)
            ob = await self.exchange.watch_order_book(symbol=self.ticker, limit=50)
            current = {'best_bid_0': ob['bids'][0], 'best_bid_1': ob['bids'][1], 'best_ask_4': ob['asks'][4]}
            self.orderbook = [current]

    async def getPositions(self):
        while True:
            positions = await self.exchange.watch_positions()
            p = positions
            print('ПОЗИЦИЯ ', p)
            for i in range(len(p)):
                if p[i]['info']['symbol'] == self.ticker and p[i]['info']['side'] == 'Buy':
                    print('НОВАЯ ПОЗИЦИЯ ОКТЫТА!!!!!')
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

                    # TODO Здесь ты сначала печатаешь, сколько осталось разместить и только потом обновляешь self.cum_margin
                    # По-моему, нужно наоборот.
                    print(f'Баланс позиции ', p[i]['info']['positionBalance'])
                    print('Осталось разместить в позиции: ', self.ALL_MARGIN - self.cum_margin)
                    self.cum_margin = float(p[i]['info']['positionBalance'])

            await asyncio.sleep(0.01)

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
            # TODO. Не очень хороший способ отлова ошибки, потому что если проблема со switch_margin_mode будет не в том,
            # что она уже установлена, а, например, в том, что отвалился интернет, то тебе все равно выведется сообщение, 
            # что маржа уже установлена
            print('Изолированная маржа уже установлена')
            try:
                print(self.session_bybit.set_leverage(
                    category="linear",
                    symbol=self.ticker,
                    buyLeverage=f"{self.leverage}",
                    sellLeverage=f"{self.leverage}",
                ))
            except Exception as e:
                # TODO. Здесь аналогично
                print('Плечо x2 уже установлено')
            return -11

    def FuturesEnterOrder(self, position_sum):
        if self.exchange_name == 'bybit':
            s_time = time.time()
            print('Ордербук ', self.orderbook)
            # qty = f"{round(self.leverage * position_sum / self.orderbook[-1]['best_ask_4'][0], self.round_number)}"
            qty = f"{round(self.leverage * position_sum / self.orderbook[-1]['best_bid_1'][0], self.round_number)}"
            print('!!!!!!!!!!', qty)
            print('Количество активов для открытия позции: ', qty)
            response = self.session_bybit.place_order(
                category="linear",
                symbol=self.ticker,
                side="Buy",
                orderType="Limit",
                price=self.orderbook[-1]['best_bid_1'][0],
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
        if self.exchange_name == 'gateio':
            pass

    def FuturesExitOrder(self):
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

    def StopLossPrice(self, start_price):
        stop_price = start_price * (1 - self.loss_percentage / 100)
        return stop_price

    def TakeProfitPrice(self, start_price):
        take_profit_price = start_price * (1 + self.profit_percentage / 100)
        return take_profit_price

    def CancelFuturesOrder(self):
        # global ticker, qActiveOrders
        try:
            response = self.session_bybit.cancel_order(
                category="linear",
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
            print('Ошибка отмены ордера: ', e)
            return -1

    async def main_logic(self):
        global positions_task
        print('Main is started')
        asyncio.create_task(self.send_telegram_message('15 минут до листинга. Открываем позицию.'))

        order_book_task = asyncio.create_task(self.getOrderBook())

        # bybit = ccxt.bybit()
        # bybit.apiKey = 'HS398zpUdxSahhV6se'
        # bybit.secret = 'e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T'

        i = 0
        await asyncio.sleep(10)
        print(self.orderbook)
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
                            asyncio.create_task(self.send_telegram_message(
                                f'Информация о входе в позицию \n Инструмент: {self.ticker} \n Свобственных средств: '
                                f'{self.pos_size_to_sell * self.enter_price / self.leverage} USDT \n Плечо: '
                                f'{self.leverage}x \n Размер позиции: {self.pos_size_to_sell * self.enter_price} USDT'
                                f' \n Было куплено: {self.pos_size_to_sell}{self.ticker.replace("USDT", "")} \n '
                                f'Средняя цена входа: {self.enter_price} \n Уровень тейк-профита '
                                f'{self.profit_percentage}% \n Уровень стоп-лосса {self.loss_percentage}% \n '
                                f'Профит-цена: ${profit_price} \n Стоп-цена: ${stop_price}'))
                            isMessageSent = True

                        print('--Цена тейк профита: ', profit_price)
                        print('--Текущая цена ', self.orderbook[-1]['best_bid_0'][0])
                        # FuturesExitLimitOrder(pos_size_to_sell, profit_price, session_bybit)

                        if float(self.orderbook[-1]['best_bid_0'][0]) >= profit_price:
                            print('Цена тейк-профита достигнута. Закрыть лимиткой')
                            print('Количество позиций: ', self.qActivePositions)
                            self.FuturesExitOrder()
                            await asyncio.sleep(2)
                            # isSold = True
                            if self.isSold:
                                asyncio.create_task(self.send_telegram_message(
                                    f'Позиция {self.ticker} закрыта по Take-Profit. Прибыль составила '
                                    f'{self.pos_size_to_sell * self.enter_price * self.profit_percentage / 100} USDT'))
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
                                asyncio.create_task(self.send_telegram_message(
                                    f'Позиция {self.ticker} закрыта по Stop-Loss. Убыток составил '
                                    f'{self.pos_size_to_sell * self.enter_price * self.loss_percentage / 100} USDT'))
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
                                asyncio.create_task(self.send_telegram_message(
                                    f'Позиция {self.ticker} закрыта через {self.TIMEOUT} минут по маркету. Прибыль составила {(self.orderbook[-1]["best_bid_0"][0] - self.enter_price) * self.pos_size_to_sell} USDT ({((self.orderbook[-1]["best_bid_0"][0] - self.enter_price) * self.pos_size_to_sell) / (self.pos_size_to_sell * self.enter_price / self.leverage) * 100} %)'))
                                await asyncio.sleep(2)

                                print(
                                    'Все позиции закрыты. Сигнал на завершение работы торгового задания. Лимит по времени.')
                                break


                    else:
                        print('Простановка ордеров разрешена')
                        if self.qActiveOrders > 0:
                            print('Удалить ордер')
                            self.CancelFuturesOrder()
                            self.qActiveOrders -= 1
                            time.sleep(1)

                        if self.qActiveOrders == 0:
                            print('Текущих ордеров нет. Открыть новый ордер')
                            delay = random.uniform(2, 6)
                            print(f'Ждем {delay / 10} секунд перед открытием нового ордера. Для защиты')
                            await asyncio.sleep(delay / 10)
                            order_code, order_id = self.FuturesEnterOrder(1)
                            if order_code == 0:
                                self.current_order_id = order_id
                                print('Новый ордер ', order_id)
                                print('SLEEP 2')
                                await asyncio.sleep(1)
                                positions_task = asyncio.create_task(self.getPositions())
                                await asyncio.sleep(1)

                # if i == 10:
                #     # await createFuturesLongOrder(bybit, 2, 2)
                #     createFuturesLongOrder(bybit, 2, 2)
                #
                await asyncio.sleep(1)  # Sleep for 5 seconds (adjust as needed)
            print('Работа программы завершена')
            await asyncio.sleep(1.5)
            asyncio.create_task(self.send_telegram_message('Выполнение торгового задания завершено без ошибок.'))
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

    def main(self):

        # TODO. Зачем мы здесь задаем еще один экземпляр биржи?
        exchange = ccxt.bybit({
            'apiKey': 'HS398zpUdxSahhV6se',
            'secret': 'e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T',
            'enableRateLimit': True,
            'options': {
                'defaultType': 'linear',  # Specify the type as 'future' for futures trading
            }
        })

        if self.exchange_name == 'bybit':
            self.changeMarginModeAndLeverageBybit(exchange)
            response = self.session_bybit.get_instruments_info(
                category="linear",
                symbol=self.ticker,
            )
            print(response)
            number = response['result']['list'][0]['lotSizeFilter']['qtyStep']
            print(number)
            if float(number) == 1:
                self.round_number = 0
            if float(number) > 1:
                self.round_number = -1 * len(number) + 1
            if float(number) < 1:
                self.round_number = len(number) - 2



        asyncio.run(self.send_telegram_message(
            f'Тестовое торговое задание запущено. \n Листинг {self.ticker} \n '
            f'Дата: {datetime.utcfromtimestamp(self.listing_date / 1000)} UTC+0\n '
            f'Ожидание {datetime.utcfromtimestamp(self.listing_date / 1000 - 15 * 60)} UTC+0'))
        while True:
            time.sleep(10)
            print('Ожидание...')

            # TODO. Добавил условие, что листинг еще не наступил, 
            # чтобы мы случайно не начали входить в лилстинг, который уже прошел
            if time.time() * 1000 >= self.listing_date - 15 * 60 * 1000 and time.time() * 1000  <= self.listing_date:
                asyncio.run(self.main_logic())
                break


if __name__ == '__main__':
    ALL_MARGIN = 10
    exchange_name = 'bybit'
    ticker = 'BLURUSDT'
    leverage = 3
    listing_date = 1700654750706
    # listing_date = time.time()*1000 + 60*1000

    profit_percentage = 10
    loss_percentage = profit_percentage / 2
    TIMEOUT = 60  # min

    trading_task = TradingTask(ALL_MARGIN=ALL_MARGIN, exchange_name=exchange_name, ticker=ticker, leverage=leverage,
                               profit_percentage=profit_percentage, loss_percentage=loss_percentage, TIMEOUT=TIMEOUT,
                               listing_date=listing_date)
    trading_task.main()
