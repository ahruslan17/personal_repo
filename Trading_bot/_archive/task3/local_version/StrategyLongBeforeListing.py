import time
import psycopg2
from TradingTaskClass import TradingTask
import threading


def connect_to_database():
    return psycopg2.connect(
        database='exampledb',
        user='admin',
        password='root',
        host='database',
        port=5432
    )

def fetch_data_from_database():
    conn = connect_to_database()
    cur = conn.cursor()

    # TODO Здесь нужно оптимизировать запрос, потому что когда данных станет много, он будет отрабатывать очень меделенно.
    # Можно, например, помечать строчки после открытия позиции как обработанные
    # и в этом запросе добавить условие, что берем только необработанные строчки.
    # Или можно где-то запоминать последнюю обработанную строчку.
    # К этому всему еще можно добавить индексы в бд, чтобы работало быстрее.
    select_query = 'SELECT * FROM newListings;'
    cur.execute(select_query)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows

def main():
    
    ALL_MARGIN = 5
    profit_percentage = 10
    loss_percentage = profit_percentage/2
    leverage = 3
    TIMEOUT = 60  # min
    
    previous_data = set()

    while True:
        

        current_time = time.time()*1000
        opened_positions = []
        listing_date = None
        ticker = None
        prior_exchange = None
        market_type = None

        current_data = set(fetch_data_from_database())
        # print('Current_data: ', current_data)

        # TODO Очень медленный способ поиска новых новостей. 
        # Если скрипт будет работать долго, то current_data и previous_data станут очень большими и будут 
        # медленно обрабатываться. Посмотри комментарий к функции fetch_data_from_database. 
        # Возможно, новый способ запроса данных автоматически решит эту проблему.
        new_rows = current_data - previous_data

        if new_rows:
            print("New rows processing:")
            for row in new_rows:
                print(row)
                listing_date = int(row[4])
                ticker = row[2]
                prior_exchange = row[6]
                market_type = row[7]
                if row[1] not in opened_positions:
                    print('Необходимо открыть позицию для строки с id в базе: ', row[0])
                    if int(row[4]) >= time.time()*1000 + 15*60*1000:
                        print('Это действительно новый листинг, откроем позицию')

                        
                        print(listing_date, '\n', ticker, '\n', prior_exchange, '\n', market_type, '\n')

                        # trading_task = TradingTask(ALL_MARGIN=ALL_MARGIN, exchange_name=prior_exchange, ticker=ticker, leverage=leverage,
                        #        profit_percentage=profit_percentage, loss_percentage=loss_percentage, TIMEOUT=TIMEOUT,
                        #        listing_date=listing_date)
                        # trading_task.main()

                        thread = threading.Thread(target=start_trading_task, args=(ALL_MARGIN, prior_exchange, ticker, leverage, profit_percentage, loss_percentage, TIMEOUT, listing_date))
                        thread.start()

                    else:
                        print('Этот листинг уже неактуален')
                    
                    # TODO. Почему мы здесь добавляем row[1]+row[2], а в условии выше проверяем только row[1] not in opened_positions
                    opened_positions.append(row[1]+row[2])
                    print('Текст данной новости добавлен в архив и больше не будет рассматриваться для открытия позиции')



        previous_data = current_data
        time.sleep(1)

def start_trading_task(ALL_MARGIN, prior_exchange, ticker, leverage, profit_percentage, loss_percentage, TIMEOUT, listing_date):
    trading_task = TradingTask(ALL_MARGIN=ALL_MARGIN, exchange_name=prior_exchange, ticker=ticker, leverage=leverage,
                               profit_percentage=profit_percentage, loss_percentage=loss_percentage, TIMEOUT=TIMEOUT,
                               listing_date=listing_date)
    trading_task.main()


if __name__ == "__main__":
    main()
