import time
import psycopg2
import threading
import asyncio

import ccxt.pro as ccxtpro
from pybit.unified_trading import HTTP
from datetime import datetime

# from NewListingsParser import NewListingsParser
from Notifications.Notifications import NotificationsBot
from TradingTasks.TradingTaskClass import TradingTaskBybit
from TradingTasks.TradingTaskClass_Gate import TradingTaskGate
from TradingTasks.TradingTaskClass_OKX import TradingTaskOKX
from TradingTasks.TradingTaskClass_Bybit_s import TradingTaskBybit_s
from TradingTasks.TradingTaskClass_Gate_s import TradingTaskGate_s
from TradingTasks.TradingTaskClass_OKX_s import TradingTaskOKX_s
from TradingTasks.TradingTaskBinance_s import TradingTaskBinance

REAL_TRADING = False

def connect_to_database():
    return psycopg2.connect(
        database='StrategyLongBeforeListingDB',
        user='admin',
        password='root',
        host='database',
        port=5432
    )


def check_token(ticker_to_check):
        conn = connect_to_database()
        cur = conn.cursor()

        query = '''
                SELECT DISTINCT exhanges.exchange_name
                FROM tickers
                JOIN ticker_exchange_relation ON tickers.id = ticker_exchange_relation.ticker_id
                JOIN exhanges ON ticker_exchange_relation.exchange_id = exhanges.id
                WHERE tickers.ticker_name = %s;
                '''
        cur.execute(query, (ticker_to_check,))
        query_result = cur.fetchall()
        available_exchanges = [item[0] for item in query_result]
        print('available_exchanges ', available_exchanges)
        # QUERY RESULT  [('bybit_f',), ('bybit_s',), ('gate_f',), ('gate_s',), ('okx_s',), ('binance_s',)]

        if 'bybit_f' in available_exchanges:
            return ['bybit','futures']
        # elif 'kucoin_f' in available_exchanges:
        #     return 'kucoin_f'
        elif 'gate_f' in available_exchanges:
            return ['gate','futures']
        elif 'okx_f' in available_exchanges:
            return ['okx','futures']
        # elif 'huobi_f' in available_exchanges:
        #     return 'huobi_f'
        # elif 'mexc_f' in available_exchanges:
        #     return 'mexc_f'
        # elif 'bitmart_f' in available_exchanges:
        #     return 'bitmart_f'
        # elif 'xt_f' in available_exchanges:
        #     return ['xt', 'futures']
        elif 'binance_s' in available_exchanges:
            return ['binance','spot']
        elif 'bybit_s' in available_exchanges:
            return ['bybit','spot']
        # elif 'kucoin_s' in available_exchanges:
        #     return 'kucoin_s'
        elif 'gate_s' in available_exchanges:
            return ['gate','spot']
        elif 'okx_s' in available_exchanges:
            return ['okx','spot']
        # elif 'huobi_s' in available_exchanges:
        #     return 'huobi_s'
        # elif 'mexc_s' in available_exchanges:
        #     return 'mexc_s'
        # elif 'bitmart_s' in available_exchanges:
        #     return 'bitmart_s'
        # elif 'xt_s' in available_exchanges:
        #     return ['xt', 'spot']
        
        return ['nothing', 'nothing']

def fetch_data_from_database():
    conn = connect_to_database()
    cur = conn.cursor()

    select_query = 'SELECT * FROM newListings WHERE flag = 0;'
    cur.execute(select_query)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def remove_digits_before_first_letter(input_string):
    result_string = ""

    # Флаг, который показывает, была ли найдена первая буква
    found_first_letter = False

    for char in input_string:
        if not found_first_letter and char.isalpha():
            found_first_letter = True

        if found_first_letter:
            result_string += char

    return result_string

def updateFlag(record_id):
        
        conn = connect_to_database()
        cur = conn.cursor()

        update_query = '''
        UPDATE newListings
        SET flag = 1
        WHERE id = %s;
        '''

        cur.execute(update_query, (record_id,))

        conn.commit()

        cur.close()
        conn.close()

# Функция, объединяющая всю логику для работы торговой стратегии
def main():
    bybit_ccxtpro_instance = ccxtpro.bybit()
    bybit_ccxtpro_instance.apiKey = 'HS398zpUdxSahhV6se'
    bybit_ccxtpro_instance.secret = 'e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T'
    bybit_session = HTTP(api_key='HS398zpUdxSahhV6se', api_secret='e51WWAGTWXaGcFqUhlDurCV4TYGDLBVfd55T')

    url = "https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48"
    bot_instance = NotificationsBot() # Экземпляр бота, который будет передаваться в остальные классы и функции
    time.sleep(3)
    asyncio.run(bot_instance.sendMessageDebug("Основной файл стратегии StrategyLongBeforeListing.py запущен"))

    # Параметры для торговых заданий.
    ALL_MARGIN = 5
    profit_percentage = 10 # значение по умолчанию. оно используется здесь как затычка, а в стратегии берётся значение в момент выхода новости
    loss_percentage = profit_percentage/2
    leverage = 3
    TIMEOUT = 60  # Время жизни позиции В МИНУТАХ, если не достигается ни стоп-лосс, ни тейк-профит.

    asyncio.run(bot_instance.sendMessageDebug(f"Текущие параметры стратегии \n Собственных средств в позиции: {ALL_MARGIN} \n Плечо: {leverage} \n Время жизни позиции: {TIMEOUT} \n Тейк-профит: 50% роста цены в момент выхода новости \n Стоп-лосс: 25% роста цены в момент выхода новости"))

    i = 0
    while True:
        # asyncio.run(bot_instance.sendMessageDebug("Тестовое сообщение из while True"))
        if i == 60*60: # каждый час
            asyncio.run(bot_instance.sendMessageDebug("StrategyLongBeforeListing.py исправно функционирует."))
            i = 0

        i += 1

        current_time = time.time()*1000
        listing_date = None
        ticker = None
        prior_exchange = None
        market_type = None

        new_rows = set(fetch_data_from_database())

        ''' 
        Структура таблицы:
        row[0] - уникальный id новости в таблице
        row[1] - текст заголовка
        row[2] - символ токена (если в новости было сразу 2 токена, то в базе будут две строчки с разными токенами)
        row[3] - время выхода новости
        row[4] - время непосредственно листинга 
        row[5] - тип листинга (фьючерс или спот)
        row[6] - биржа для открытия позиции
        row[7] - рынок для открытия позиции (фьючерсы или спорт)
        row[8] - флаг (0 или 1), была ли данная новость уже обработана скриптом или нет
        '''

        if new_rows:
            print("New rows are detected! ")
            asyncio.run(bot_instance.sendMessageDebug("Новые записи в базе найдены"))
            for row in new_rows:
                print(row)
                row_id = row[0]
                listing_date = int(row[4])
                news_date = int(row[3])
                ticker = row[2]
                prior_exchange = row[6]
                market_type = row[7]
                print('Необходимо открыть позицию для строки с id в базе: ', row[0])
                asyncio.run(bot_instance.sendMessageDebug(f"Необходимо открыть позицию для строки с id в базе: {row[0]}"))
                
                # Если в данный момент до листинга остаётся больше 15 минут, то запустится торговое задание
                if int(row[4]) >= time.time()*1000 + 15*60*1000:
                    print('Это действительно новый листинг, откроем позицию')
                    asyncio.run(bot_instance.sendMessageDebug("Это действительно новый листинг, откроем позицию \n Сигнал на создание торгового задания"))

                    print(f'Информация о позиции \n News time: {news_date} \n Listing time: {listing_date} \n Ticker: {ticker} \n Exchagne: {prior_exchange} Market: {market_type}')                        

                    # Создание торгового задания
                    thread = threading.Thread(target=startTradingTask, args=(ALL_MARGIN, prior_exchange, market_type, ticker, leverage, profit_percentage, loss_percentage, TIMEOUT, news_date, listing_date, bot_instance, bybit_ccxtpro_instance, bybit_session))
                    thread.start()

                else:
                    print('Этот листинг уже неактуален')
                    asyncio.run(bot_instance.sendMessageDebug("Время до листинга в этой новости меньше, чем через 15 минут. Не входим в позицию."))
                    
                # Все новости, которые попали в new_rows имели flag = 0 (т.е. непросмотренные). Изменить flag = 0 -> 1 (просмотренные)
                updateFlag(row_id)
                asyncio.run(bot_instance.sendMessageDebug("Флаг обновлён"))
                print('Флаг обновлён')

        time.sleep(1)

def startTradingTask(ALL_MARGIN, prior_exchange, market_type, ticker, leverage, profit_percentage, loss_percentage, TIMEOUT, news_date, listing_date, bot_instance, bybit_ccxtpro_instance, bybit_session):

    # сообщение о запуске торгового задания.
    asyncio.run(bot_instance.sendMessageDebug(
                    f'Торговое задание запущено. \n Листинг {ticker} \n '
                    f'Дата: {datetime.utcfromtimestamp(listing_date / 1000)} UTC+0\n '
                    f'Ожидание {datetime.utcfromtimestamp(listing_date / 1000 - 15 * 60)} UTC+0'))
    
    if REAL_TRADING is True:
        asyncio.run(bot_instance.sendMessage(
                    f'Торговое задание запущено. \n Листинг {ticker} \n '
                    f'Дата: {datetime.utcfromtimestamp(listing_date / 1000)} UTC+0\n '
                    f'Ожидание {datetime.utcfromtimestamp(listing_date / 1000 - 15 * 60)} UTC+0'))
    
    if prior_exchange == 'nothing':
        asyncio.run(bot_instance.sendMessageDebug('На данный момент токен не найден ни на одной из наших бирж \n Повторная проверка за 5 минут до открытия позиции'))
        if REAL_TRADING is True:
            asyncio.run(bot_instance.sendMessage('На данный момент токен не найден ни на одной из наших бирж \n Повторная проверка за 5 минут до открытия позиции'))

    # Отработка ситуации, когда в момент выхода новости на рассматриваемых биржах токена не было, но перед самим листингом он уже есть на других биржах.
    if prior_exchange == 'nothing':
        while True:
            time.sleep(1)
            # за 5 минут до входа в позицию проверим ещё раз
            if time.time() * 1000 >= listing_date - 20 * 60 * 1000:
                prior_exchange, market_type = check_token(ticker)
                break

    # Отработка ситуации, когда токена по типу "1000SMTH" нет ни на одной из бирж, но "SMTH" есть на биржах
    if prior_exchange == 'nothing':
        # если название тикера начинается с цифры и если его нет на биржах
        if ticker[:1].isdigit():
            # убрать цифры и посмотреть, есть ли он на биржах 
            prior_exchange, market_type = check_token(remove_digits_before_first_letter(ticker))

            # если есть, то заменить тикер названием тикера без первых цифр
            if prior_exchange != 'nothing':
                ticker = remove_digits_before_first_letter(ticker)

    if market_type == 'spot':
    ### binance spot ###
        if prior_exchange == 'binance':

            trading_task = TradingTaskBinance(ALL_MARGIN=7, ticker=ticker, leverage=leverage,
                                    profit_percentage=profit_percentage, loss_percentage=loss_percentage, TIMEOUT=TIMEOUT, news_date=news_date,
                                    listing_date=listing_date, bot=bot_instance, ccxtpro_instance=None, pybit_instance=None)
            
            trading_task.main()
        
    ### bybit spot ###
        if prior_exchange == 'bybit':

            trading_task = TradingTaskBybit_s(ALL_MARGIN=ALL_MARGIN, ticker=ticker, leverage=leverage,
                                    profit_percentage=profit_percentage, loss_percentage=loss_percentage, TIMEOUT=TIMEOUT, news_date=news_date,
                                    listing_date=listing_date, bot=bot_instance, ccxtpro_instance=None, pybit_instance=None)
            
            trading_task.main()

    ### gate spot ###
        if prior_exchange == 'gate':
            trading_task = TradingTaskGate_s(ALL_MARGIN=ALL_MARGIN, ticker=ticker, leverage=leverage,
                                   profit_percentage=profit_percentage, loss_percentage=loss_percentage,
                                   news_date=news_date,
                                   TIMEOUT=TIMEOUT,
                                   listing_date=listing_date, bot=bot_instance)
            
            trading_task.main()

    ### gate spot ###
        if prior_exchange == 'okx':

            trading_task = TradingTaskOKX_s(ALL_MARGIN=ALL_MARGIN, ticker=ticker, leverage=leverage,
                                  profit_percentage=profit_percentage, loss_percentage=loss_percentage,
                                  news_date=news_date,
                                  TIMEOUT=TIMEOUT,
                                  listing_date=listing_date, bot=bot_instance)
            
            trading_task.main()
    
    
    elif market_type == 'futures':

    ### bybit futures ###
        if prior_exchange == 'bybit':

            trading_task = TradingTaskBybit(ALL_MARGIN=ALL_MARGIN, ticker=ticker, leverage=leverage,
                                    profit_percentage=profit_percentage, loss_percentage=loss_percentage, TIMEOUT=TIMEOUT, news_date=news_date,
                                    listing_date=listing_date, bot=bot_instance, ccxtpro_instance=None, pybit_instance=None)
            
            trading_task.main()

    ### gate futures ###
        if prior_exchange == 'gate':
            trading_task = TradingTaskGate(ALL_MARGIN=ALL_MARGIN, ticker=ticker, leverage=leverage,
                                   profit_percentage=profit_percentage, loss_percentage=loss_percentage,
                                   news_date=news_date,
                                   TIMEOUT=TIMEOUT,
                                   listing_date=listing_date, bot=bot_instance)
            
            trading_task.main()

    ### gate okx ###
        if prior_exchange == 'okx':

            trading_task = TradingTaskOKX(ALL_MARGIN=ALL_MARGIN, ticker=ticker, leverage=leverage,
                                  profit_percentage=profit_percentage, loss_percentage=loss_percentage,
                                  news_date=news_date,
                                  TIMEOUT=TIMEOUT,
                                  listing_date=listing_date, bot=bot_instance)
            
            trading_task.main()

        else:
            asyncio.run(bot_instance.sendMessageDebug(f"Функционал для выставления ордеров на бирже {prior_exchange} ещё не добавлен."))
    else: 
        if prior_exchange == 'nothing':
                    print('Данный токен не листится на биржах, на которых мы можем открыть позицию')
                    asyncio.run(bot_instance.sendMessageDebug('Данный токен не листится на биржах, на которых мы можем открыть позицию'))
                    if REAL_TRADING is True:
                        asyncio.run(bot_instance.sendMessage('Данный токен не листится на биржах, на которых мы можем открыть позицию'))
        
        

if __name__ == "__main__":
    time.sleep(240)
    main()
