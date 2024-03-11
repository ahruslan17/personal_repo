FROM python:3.12

WORKDIR /usr/src/app

COPY Parsers/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY Parsers/NewListingsParser.py ./
COPY Notifications ./Notifications
COPY TickerOnExchangesDatabase ./TickerOnExchangesDatabase
COPY TickersDatabase.json ./



CMD ["python", "NewListingsParser.py"]
