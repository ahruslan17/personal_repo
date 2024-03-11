from huobi.linear_swap.rest.market import Market



API_KEY = '02cd5753-401781ee-zrfc4v5b6n-fa81f'
API_SECRET = '6d28a4f6-ebd86348-5839575e-558c6'

client = Market()
result = client.get_contract_info({"contract_code": "btc-usdt", "support_margin_mode": "all"})
print(result)

# // Create a TradeClient instance with API Key and customized host
trade_client = TradeClient(api_key=API_KEY, secret_key=API_SECRET, url="https://api-aws.huobi.pro")

market_client = MarketClient()
list_obj = market_client.get_market_trade(symbol="btcusdt")