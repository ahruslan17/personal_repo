from binance.client import Client
from binance.cm_futures import CMFutures


api_key ='SpLiXl4qyZSBTKNO5G8yddgnliuV3GP6r0KgrIrEmck1gaynGA7ob2Oc8xX4laEB'
api_secret ='9EBCGpg7s8IWets5VP8kDvaBSxlmMkKM2LAymLeMRuioyi1HQVmflHkhNm7Pc7vl'

client = Client(api_key, api_secret)
f_client = CMFutures(key=api_key, secret=api_secret)

# client.API_URL = 'https://fapi.binance.com/fapi'
# client.API_URL = 'https://api.binance.com/api'

# print(client.get_asset_balance(asset='BTC'))
# print(client.futures_account_balance())

def getSpotPrice_binance(ticker, client):
    return client.get_symbol_ticker(symbol=ticker)['price']

def getFuturesPrice_binance(ticker, client):
    return client.ticker_price('BTCUSDT')

print(getSpotPrice_binance('DOGEUSDT', client))
print(getFuturesPrice_binance('DOGEUSDT', f_client))





