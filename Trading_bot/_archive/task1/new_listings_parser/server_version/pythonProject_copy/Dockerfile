FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt  IsTickerOnExchange.py Notifications.py TickersDatabase.json TickersParser.py  TradingTask_Bybit.py TradingTask_Gateio.py TradingTask_OKX.py ./
RUN pip install --no-cache-dir -r requirements.txt

# TODO зачем мы здесь еще раз все копируем, если мы уже скопировали нужные скрипты в предыдущем COPY? 
COPY  . .

# CMD [ "python", "./PingAndCashChecker.py" ]
CMD [ "python", "./BinanceParser.py" ]