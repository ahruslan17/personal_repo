import os
import json

#TODO: сделать как класс и в дальнейшем переписать для опроса postgres бд.
def check_token(symbol):
    # result = [[], [], [], [], [], [], [],
    #           []]  # bybit -> kucoin -> gateio -> okx -> htx -> mexc -> bitmart -> xtcom [0] - spot, [1] - futures

    file = 'TickersDatabase.json'

    with open(file, 'r') as file:
        loaded_database = json.load(file)

    if symbol in loaded_database['bybit_data']['futures']:
        return ['bybit', 'futures']

    # if symbol in loaded_database['kucoin_data']['futures']:
    #     return ['kucoin', 'futures']
    #
    if symbol in loaded_database['gateio_data']['futures']:
        return ['gateio', 'futures']

    if symbol in loaded_database['okex_data']['futures']:
        return ['okx', 'futures']

    # if symbol in loaded_database['htx_data']['futures']:
    #     return ['htx', 'futures']
    #
    # if symbol in loaded_database['mexc_data']['futures']:
    #     return ['mexc', 'futures']
    #
    # if symbol in loaded_database['bitmart_data']['futures']:
    #     return ['bitmart', 'futures']
    #
    # if symbol in loaded_database['xtcom_data']['futures']:
    #     return ['xtcom', 'futures']
    #
    if symbol in loaded_database['binance_data']['spot']:
        return ['binance', 'spot']
    #
    if symbol in loaded_database['bybit_data']['spot']:
        return ['bybit', 'spot']
    #
    # if symbol in loaded_database['kucoin_data']['spot']:
    #     return ['kucoin', 'spot']
    #
    if symbol in loaded_database['gateio_data']['spot']:
        return ['gateio', 'spot']

    if symbol in loaded_database['okex_data']['spot']:
        return ['okx', 'spot']

    # if symbol in loaded_database['htx_data']['spot']:
    #     return ['htx', 'spot']
    #
    # if symbol in loaded_database['mexc_data']['spot']:
    #     return ['mexc', 'spot']
    #
    # if symbol in loaded_database['bitmart_data']['spot']:
    #     return ['bitmart', 'spot']
    #
    # if symbol in loaded_database['xtcom_data']['spot']:
    #     return ['xtcom', 'spot']

    return ['nothing', 'nothing']

# print(check_token('FLOKIUSDT'))
