# %%
import requests
import json

def get_coinmarketcap_top100():
    # Register for an API key on the CoinMarketCap website
    api_key = "042cd680-7fd7-4aab-a032-fba9e75b7fc2"

    # Specify the endpoint
    endpoint = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'

    # Specify the parameters
    parameters = {
        'sort': 'market_cap',
        'sort_dir': 'desc',
        'cryptocurrency_type': 'all',
        'limit': 100
    }
    # Send the request
    headers = {'X-CMC_PRO_API_KEY': api_key}
    response = requests.get(endpoint, headers=headers, params=parameters)

    # Parse the response
    data = json.loads(response.text)
    coins = data['data']
    top100_symbols = [coin['symbol'] + "USDT" for coin in data['data']]
    # print(f'Top 100 Symbols: {top100_symbols}\n')
    return top100_symbols


def get_binance_usdt_pairs():
    url = 'https://api.binance.com/api/v3/exchangeInfo'
    response = requests.get(url)
    data = response.json()
    usdt_pairs = [pair['symbol'] for pair in data['symbols'] if pair['quoteAsset'] == 'USDT' and pair['status'] == 'TRADING']
    # print(f'USDT Pairs: {usdt_pairs}\n')
    return usdt_pairs

def find_common_pairs(top100_symbols, usdt_pairs):
    common_pairs = set(top100_symbols) & set(usdt_pairs)
    return common_pairs

if __name__ == '__main__':
    top100_symbols = get_coinmarketcap_top100()
    usdt_pairs = get_binance_usdt_pairs()
    common_pairs = find_common_pairs(top100_symbols, usdt_pairs)

    print("Cryptocurrencies in the top 100 on CoinMarketCap which are tradeable on Binance (USDT pairs):")
    print(common_pairs)


# %%
def get_binance_usdt_pairs():
    url = 'https://api.binance.com/api/v3/exchangeInfo'
    response = requests.get(url)
    data = response.json()
    usdt_pairs = [pair['symbol'] for pair in data['symbols'] if pair['quoteAsset'] == 'USDT' and pair['status'] == 'TRADING']
    # print(f'USDT Pairs: {usdt_pairs}\n')
    return usdt_pairs

# %%
def find_common_pairs(top100_symbols, usdt_pairs):
    common_pairs = set(top100_symbols) & set(usdt_pairs)
    return common_pairs



