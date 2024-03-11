FROM python:3.12

WORKDIR /usr/src/app

COPY requirements.txt Demo.py NewListingsParser.py IsTickerOnExchange.py ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "./NewListingsParser.py"]
