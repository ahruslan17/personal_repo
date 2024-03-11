from kucoin.client import Client

api_key = '65478e1825bfab0001eeb1ae'
api_secret = 'dcfe2364-1d70-476e-ab68-399392851a7d'
api_passphrase = 'ahruslan17@gmail.com'


# client = Client(api_key, api_secret, api_passphrase, sandbox=True)

def getPriceSpot(ticker):
    client = Client(api_key, api_secret, api_passphrase)
    price = client.get_ticker(ticker.replace('USDT', '-USDT'))['price']

    return price


def placeSpotOrder_kucoin(ticker):
    pass


print(getPriceSpot('DOGEUSDT'))
