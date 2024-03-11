FROM python:3.12

WORKDIR /usr/src/app

COPY StrategyLongBeforeListing/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install python-binance

COPY StrategyLongBeforeListing/StrategyLongBeforeListing.py ./
COPY StrategyLongBeforeListing/credentials.json ./
COPY Notifications ./Notifications
COPY TradingTasks ./TradingTasks

CMD ["python", "StrategyLongBeforeListing.py"]
