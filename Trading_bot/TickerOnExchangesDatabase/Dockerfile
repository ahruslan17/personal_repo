FROM python:3.12

WORKDIR /usr/src/app

COPY TickerOnExchangesDatabase/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# COPY Parsers/NewListingsParser.py ./
# COPY Notifications ./Notifications
COPY Notifications ./Notifications
COPY TickerOnExchangesDatabase/TickersParser.py ./


CMD ["python", "TickersParser.py"]
