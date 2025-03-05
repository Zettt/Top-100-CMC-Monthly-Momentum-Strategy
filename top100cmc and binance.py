# %%
import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Add this near the top with other constants
MAX_PAIRS = 25

# %%
def get_coinmarketcap_top100():
    # Get API key from environment variables
    cmc_key = os.getenv('CMC_KEY')
    if not cmc_key:
        raise ValueError("CoinMarketCap API key not found in environment variables")

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
    headers = {'X-CMC_PRO_API_KEY': cmc_key}
    response = requests.get(endpoint, headers=headers, params=parameters)

    # Parse the response
    data = json.loads(response.text)
    coins = data['data']
    # Filter out stablecoins and create pairs
    stablecoins = ['USDC', 'USDT', 'BUSD', 'DAI', 'TUSD']
    top100_symbols = [coin['symbol'] + "USDC" for coin in data['data'] 
                     if coin['symbol'] not in stablecoins]
    # print(f'Top 100 Symbols: {top100_symbols}\n')
    return top100_symbols

# %%
def get_binance_usdt_pairs():
    url = 'https://api.binance.com/api/v3/exchangeInfo'
    response = requests.get(url)
    data = response.json()
    stablecoins = ['USDC', 'USDT', 'BUSD', 'DAI', 'TUSD']
    usdt_pairs = [pair['symbol'] for pair in data['symbols'] 
                 if pair['quoteAsset'] == 'USDC' 
                 and pair['status'] == 'TRADING'
                 and pair['baseAsset'] not in stablecoins]
    # print(f'USDT Pairs: {usdt_pairs}\n')
    return usdt_pairs

# %%
def find_common_pairs(top100_symbols, usdt_pairs):
    common_pairs = set(top100_symbols) & set(usdt_pairs)
    # Convert to list and take only the first MAX_PAIRS pairs
    # Since common_pairs is a set, we sort it to ensure consistent results
    return list(sorted(common_pairs))[:MAX_PAIRS]

# %%
top100_symbols = get_coinmarketcap_top100()
usdt_pairs = get_binance_usdt_pairs()
common_pairs = find_common_pairs(top100_symbols, usdt_pairs)

print(f"Top {MAX_PAIRS} cryptocurrencies in the top 100 on CoinMarketCap which are tradeable on Binance (USDT pairs): \n {common_pairs}")
print(f"Number of pairs selected: {len(common_pairs)}")

# %%
capital= 200
capital_per_pair = capital / len(common_pairs)
print(f"With ${capital} total capital, you can spend ${capital_per_pair:.2f} on each of the {len(common_pairs)} pairs")


