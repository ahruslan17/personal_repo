import ccxt
import psycopg2
import requests
import time
from datetime import datetime
import re
import json
import asyncio
import logging

from Notifications.Notifications import NotificationsBot

class TickersOnExchangeParser:
    def __init__(self, telegram_bot):
        self.exchanges = [ccxt.bybit(), ccxt.gateio(), ccxt.okx()]
        self.telegram_bot = telegram_bot

    def connect_to_database(self):
        try:
            return psycopg2.connect(
                database='StrategyLongBeforeListingDB',
                user='admin',
                password='root',
                host='database',
                port=5432
            )
        except Exception as e:
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в TickersParser.py connect_to_database,{e}'))



    def get_exchange_id_by_name(self, exchange_name, cur):
        try:
            query = "SELECT id FROM exhanges WHERE exchange_name = %s;"
            cur.execute(query, (exchange_name,))
            result = cur.fetchone()    
            
            return result[0] if result else None
        except Exception as e:
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в TickersParser.py get_exchange_id_by_name,{e}'))

    
    def get_ticker_id_by_name(self, ticker_name, cur):
        try: 
            query = "SELECT id FROM tickers WHERE ticker_name = %s;"
            cur.execute(query, (ticker_name,))
            result = cur.fetchone()    

            return result[0] if result else None
        except Exception as e:
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в TickersParser.py get_ticker_id_by_name,{e}'))
    
    def writeBound(self,cur,conn,exchange_name,ticker):
        try:
            exchange_id = self.get_exchange_id_by_name(exchange_name, cur=cur)
            ticker_id = self.get_ticker_id_by_name(ticker, cur=cur)

            # Проверка, есть ли уже такая комбинация в таблице
            select_query = "SELECT COUNT(*) FROM ticker_exchange_relation WHERE exchange_id = %s AND ticker_id = %s"
            cur.execute(select_query, (exchange_id, ticker_id))
            count = cur.fetchone()[0]

            if count == 0:
                ticker_exchange_data = [(exchange_id, ticker_id)]
                insert_query = '''
                            INSERT INTO ticker_exchange_relation 
                            (exchange_id, ticker_id) 
                            VALUES (%s, %s);
                            '''
                cur.executemany(insert_query, ticker_exchange_data)
                conn.commit()
        except Exception as e:
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в TickersParser.py writeBound,{e}'))



    def writeTickerId(self, cur, conn, ticker):
        try:
            query = "SELECT id FROM tickers WHERE ticker_name = %s;"
            cur.execute(query, (ticker,))
            result = cur.fetchone()    
                    # print('RESULT', result)
            if not result:
                ticker_exchange_data = (ticker,)
                insert_query = '''
                            INSERT INTO tickers
                            (ticker_name) 
                            VALUES (%s);
                            '''
                cur.execute(insert_query, ticker_exchange_data)
                conn.commit()
            else:
                pass
                        # print(f'ticker {ticker} уже добавлен в базу!!') 
        except Exception as e:
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в TickersParser.py writeTickerId,{e}'))

    def delete_unused_ticker_exchange_relation(self, cur, conn, exchange_name, coin_list):
        cur.execute("SELECT id FROM exhanges WHERE exchange_name = %s", (exchange_name,))
        exchange_id = cur.fetchone()

        if exchange_id:
            # Получаем id токенов из списка монет, который есть на данной бирже
            cur.execute("SELECT id FROM tickers WHERE ticker_name IN %s", (tuple(coin_list),))
            coin_ids = [item[0] for item in cur.fetchall()]

            # Удаляем строки из таблицы связи, где id биржи равен exchange_id, а id токена не находится в списке coin_ids
            delete_query = "DELETE FROM ticker_exchange_relation WHERE exchange_id = %s AND ticker_id NOT IN %s"
            cur.execute(delete_query, (exchange_id, tuple(coin_ids)))

            # Подтверждаем изменения в базе данных
            conn.commit()
            print("Успешно удалено.")



    def writeIntoTickersDB(self):
        conn = self.connect_to_database()
        cur = conn.cursor()

        try:
            create_table_query = """
                            CREATE TABLE IF NOT EXISTS tickers (
                                id SERIAL PRIMARY KEY,
                                ticker_name VARCHAR(50) UNIQUE
                            );
                        """
            cur.execute(create_table_query)
            conn.commit()

            create_table_query = """
                            CREATE TABLE IF NOT EXISTS ticker_exchange_relation (
                                id SERIAL PRIMARY KEY,
                                exchange_id INTEGER,
                                ticker_id INTEGER
                            );
                        """
            cur.execute(create_table_query)
            conn.commit()
        except Exception as e:
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в TickersParser.py writeIntoTickersDB(1),{e}'))


        ### binance ###
            
        spot_url = "https://api.binance.com/api/v3/exchangeInfo?permissions=SPOT"
        spot_names = []
        try:
            response = requests.get(spot_url)
            response.raise_for_status()
            exchange_info_spot = response.json()
            for data in exchange_info_spot['symbols']:
                if data['status'] == 'TRADING' and data['isSpotTradingAllowed'] and 'USDT' in data['symbol']:
                    spot_names.append(data['symbol'])
            print(spot_names)
            print(len(spot_names))

            # удалить старые отношения, для которых сейчас нет тикеров на бирже
            self.delete_unused_ticker_exchange_relation(cur=cur,conn=conn,exchange_name='binance_s',coin_list=spot_names)

            for ticker in spot_names:
                self.writeTickerId(cur=cur,conn=conn,ticker=ticker)
                self.writeBound(cur=cur,conn=conn,exchange_name='binance_s',ticker=ticker)

        except Exception as e:
            print(f"Произошла ошибка при обращении к spot: {e}")
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в TickersParser.py writeIntoTickersDB(2),{e}'))
        

        ### bybit ###

        # self.parse_bybit(conn, cur)
        spot_url = 'https://api.bybit.com/spot/v3/public/quote/ticker/24hr'
        spot_names = []
        futures_names = []
        try:
            response = requests.get(spot_url)
            response.raise_for_status()
            exchange_info_spot = response.json()
            for data in exchange_info_spot['result']['list']:
                spot_names.append(data['s'])
            print('bybit_s', spot_names)

            # удалить старые отношения, для которых сейчас нет тикеров на бирже
            self.delete_unused_ticker_exchange_relation(cur=cur,conn=conn,exchange_name='bybit_s',coin_list=spot_names)

            for ticker in spot_names:
                self.writeTickerId(cur=cur,conn=conn,ticker=ticker)
                self.writeBound(cur=cur,conn=conn,exchange_name='bybit_s',ticker=ticker)

        except Exception as e:
            print(f"Произошла ошибка при обращении к spot: {e}")
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в TickersParser.py writeIntoTickersDB(2),{e}'))


        futures_url = 'https://api.bybit.com/derivatives/v3/public/instruments-info'
        try:
            response = requests.get(futures_url)
            response.raise_for_status()

            exchange_info_futures = response.json()
            for data in exchange_info_futures['result']['list']:
                if data['status'] == 'Trading':
                    futures_names.append(data['symbol'])
            print('bybit_f ', futures_names)
            # удалить старые отношения, для которых сейчас нет тикеров на бирже
            self.delete_unused_ticker_exchange_relation(cur=cur,conn=conn,exchange_name='bybit_f',coin_list=futures_names)

            for ticker in futures_names:
                self.writeTickerId(cur=cur,conn=conn,ticker=ticker)
                self.writeBound(cur=cur,conn=conn,exchange_name='bybit_f',ticker=ticker)

        except Exception as e:
            print(f"Произошла ошибка при обращении к futures: {e}")
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в TickersParser.py writeIntoTickersDB(3),{e}'))


        # self.parse_gate(conn, cur)

        spot_url = 'https://api.gateio.ws/api/v4/spot/currency_pairs'
        spot_names = []
        futures_names = []
        try:
            response = requests.get(spot_url)
            response.raise_for_status()
            exchange_info_spot = response.json()
            for pair in exchange_info_spot:
                if pair['trade_status'] == 'tradable':
                    spot_names.append(pair['id'].replace('_', ''))
            print('gate_s ', spot_names)

            # удалить старые отношения, для которых сейчас нет тикеров на бирже
            self.delete_unused_ticker_exchange_relation(cur=cur,conn=conn,exchange_name='gate_s',coin_list=spot_names)

            for ticker in spot_names:
                self.writeTickerId(cur=cur,conn=conn,ticker=ticker)
                self.writeBound(cur=cur,conn=conn,exchange_name='gate_s',ticker=ticker)

        except Exception as e:
            print(f"Произошла ошибка при обращении к spot: {e}")
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в TickersParser.py writeIntoTickersDB(4),{e}'))

        futures_url = 'https://api.gateio.ws/api/v4/futures/usdt/contracts'
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        try:
            response = requests.get(futures_url, headers=headers)
            response.raise_for_status()

            exchange_info_futures = response.json()
            for data in exchange_info_futures:
                if data['in_delisting'] == False:
                    futures_names.append(data['name'].replace('_', ''))
            print('gate_f' ,futures_names)

            # удалить старые отношения, для которых сейчас нет тикеров на бирже
            self.delete_unused_ticker_exchange_relation(cur=cur,conn=conn,exchange_name='gate_f',coin_list=futures_names)

            for ticker in futures_names:
                self.writeTickerId(cur=cur,conn=conn,ticker=ticker)
                self.writeBound(cur=cur,conn=conn,exchange_name='gate_f',ticker=ticker)

        except Exception as e:
            print(f"Произошла ошибка при обращении к futures: {e}")
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в TickersParser.py writeIntoTickersDB(5),{e}'))


        # self.parse_okx(conn, cur)

        spot_url = 'https://www.okex.com/api/v5/market/tickers?instType=SPOT'
        spot_names = []
        futures_names = []
        try:
            response = requests.get(spot_url)
            response.raise_for_status()
            exchange_info_spot = response.json()
            for data in exchange_info_spot['data']:
                spot_names.append(data['instId'].replace('-', ''))
            print('okx_s ', spot_names)

            # удалить старые отношения, для которых сейчас нет тикеров на бирже
            self.delete_unused_ticker_exchange_relation(cur=cur,conn=conn,exchange_name='okx_s',coin_list=spot_names)

            for ticker in spot_names:
                self.writeTickerId(cur=cur,conn=conn,ticker=ticker)
                self.writeBound(cur=cur,conn=conn,exchange_name='okx_s',ticker=ticker)

        except Exception as e:
            print(f"Произошла ошибка при обращении к spot: {e}")
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в TickersParser.py writeIntoTickersDB(7),{e}'))

        futures_url = 'https://www.okex.com/api/v5/market/tickers?instType=FUTURES'
        try:
            response = requests.get(futures_url)
            response.raise_for_status()

            exchange_info_futures = response.json()
            for data in exchange_info_futures['data']:
                futures_names.append(re.sub(r'[^a-zA-Z]', '', data['instId']))
            print('okx_f ', futures_names)

            # удалить старые отношения, для которых сейчас нет тикеров на бирже
            self.delete_unused_ticker_exchange_relation(cur=cur,conn=conn,exchange_name='okx_f',coin_list=futures_names)

            for ticker in futures_names:
                self.writeTickerId(cur=cur,conn=conn,ticker=ticker)
                self.writeBound(cur=cur,conn=conn,exchange_name='okx_f',ticker=ticker)

        except Exception as e:
            print(f"Произошла ошибка при обращении к futures: {e}")
            asyncio.run(self.telegram_bot.sendMessageDebug(f'Ошибка в TickersParser.py writeIntoTickersDB(8),{e}'))

        cur.close()
        conn.close()


if __name__ == '__main__':
    try:
        time.sleep(210) # подождать на всякий случай, чтобы контейнер с базой загрузился
        telegram_bot = NotificationsBot()
        asyncio.run(telegram_bot.sendMessageDebug('Парсер тикеров TickersParser.py запущен. Обновление базы каждый час.'))
        obj = TickersOnExchangeParser(telegram_bot)
        while True:
            asyncio.run(telegram_bot.sendMessageDebug('Обновление базы тикеров.'))
            print('Обновление базы')
            obj.writeIntoTickersDB()
            asyncio.run(telegram_bot.sendMessageDebug('База тикеров успешно обновлена.'))
            time.sleep(60*60) # обновлять каждый час
    except Exception as e:
        asyncio.run(telegram_bot.sendMessageDebug(f'Ошибка в TickersParser.py __main__, {e}'))


