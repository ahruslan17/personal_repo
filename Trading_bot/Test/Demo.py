import ccxt.pro as ccxtpro
import asyncio
import okx.Trade as Trade

exchange = ccxtpro.okex({'options': {'defaultType': 'SWAP'}})
exchange.apiKey = '2666b857-dab7-4ad4-a557-f411fd8a9bb7'
exchange.secret = 'D7DB0C51E5D2ABEE4B412A985EC67F59'
exchange.password = 'Pass_Phrase_1'
exchange.set_sandbox_mode(True)

# ticker = 'BLURUSDT'  # не работает
ticker = 'IOTAUSDT'  # не работает
# ticker = 'DOGEUSDT'  # работает


async def getOrderBook():
    while True:
        await asyncio.sleep(0.01)
        ob = await exchange.watch_order_book(symbol=ticker.replace('USDT', '/USDT'), limit=10)
        print(ob)


def connectAPI():
    tradeAPI = Trade.TradeAPI('2666b857-dab7-4ad4-a557-f411fd8a9bb7', 'D7DB0C51E5D2ABEE4B412A985EC67F59', 'Pass_Phrase_1', False, flag='1')
    print(tradeAPI)
    result = tradeAPI.place_order(
        instId=ticker.replace('USDT', '-USDT') + '-SWAP',
        tdMode='isolated',
        side='buy',
        ordType='market',
        sz=1
    )
    print(result)
#     {'msg': 'APIKey does not match current environment.', 'code': '50101'}


async def main():
    # connectAPI()
    asyncio.create_task(getOrderBook())

    while True:
        await asyncio.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
