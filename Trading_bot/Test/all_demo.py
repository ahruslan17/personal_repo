
import random
import time
import logging
from datetime import datetime
from pybit.unified_trading import HTTP
import asyncio
import ccxt.pro as ccxtpro
import ccxt
from telegram import Bot
import requests

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from gate_api import SpotApi, ApiClient, FuturesApi, FuturesOrder, FuturesTrade, Order, \
    Configuration  # pip install gate_api

import time
import hashlib
import hmac
import requests
import json
ticker = 'DOGEUSDT'
pos_size_to_sell = 25.97

gate = ccxt.gate()
gate.apiKey = '7c23279c9e4fc1f29fae8d422416cf3d'
gate.secret = '806ed766381651e4a6ce3197ff462b680dc53a2998b5b381033061a775d06953'
gate.uid = '14274293'
gate.options['defaultType'] = 'spot'

gate_futures_api = FuturesApi(
    ApiClient(Configuration(host="https://api.gateio.ws/api/v4", key='f6ef804d08f28800337b5abba2c05fae',
                            secret='8c27d7168eca569e95d4f85e7f9dc09b69337ab82ac2eb2a6285a703d7cbb1d0')))
gate_spot_api = SpotApi(
    ApiClient(Configuration(host="https://api.gateio.ws/api/v4", key='f6ef804d08f28800337b5abba2c05fae',
                            secret='8c27d7168eca569e95d4f85e7f9dc09b69337ab82ac2eb2a6285a703d7cbb1d0')))

def SpotExitOrder():
    settle = 'usdt'
    contract = ticker.replace('USDT', '_USDT')
    print('SIZE TO EXIT', float(pos_size_to_sell))
    order = Order(amount=str(1 * float(pos_size_to_sell) * 0.99), type='market', side='sell',
                  currency_pair=contract,
                  time_in_force='ioc')
    order_response = gate_spot_api.create_order(order)
    print(order_response)
    isSold = True
    if order_response.status == 'closed':
        print('Ордер успешно закрыт')
    else:
        print('Проблемы с закрытием ордера или ещё не исполнился. Статус: ', order_response.status)

SpotExitOrder()