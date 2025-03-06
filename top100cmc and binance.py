# %%
import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Constants
MAX_PAIRS = 25
TARGET_BALANCE = 200  # Fixed target balance in USDC

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
def get_binance_usdc_balance():
    binance_key = os.getenv('BINANCE_API_KEY')
    binance_secret = os.getenv('BINANCE_API_SECRET')
    
    if not binance_key or not binance_secret:
        raise ValueError("Binance API credentials not found in environment variables")
    
    endpoint = 'https://api.binance.com/api/v3/account'
    # You'll need to implement proper Binance API authentication here
    # This is a simplified version
    headers = {'X-MBX-APIKEY': binance_key}
    response = requests.get(endpoint, headers=headers)
    data = response.json()
    
    # Find USDC balance
    usdc_balance = 0
    for asset in data.get('balances', []):
        if asset['asset'] == 'USDC':
            usdc_balance = float(asset['free'])
            break
    
    return usdc_balance

# %%
top100_symbols = get_coinmarketcap_top100()
usdt_pairs = get_binance_usdt_pairs()
common_pairs = find_common_pairs(top100_symbols, usdt_pairs)

print(f"Top {MAX_PAIRS} cryptocurrencies in the top 100 on CoinMarketCap which are tradeable on Binance (USDT pairs): \n {common_pairs}")
print(f"Number of pairs selected: {len(common_pairs)}")

# Get actual balance and compare with target
actual_balance = get_binance_usdc_balance()
capital = min(TARGET_BALANCE, actual_balance)

if capital < TARGET_BALANCE:
    print(f"Warning: Available balance (${actual_balance:.2f}) is less than target balance (${TARGET_BALANCE:.2f})")

capital_per_pair = capital / len(common_pairs)
print(f"With ${capital:.2f} total capital, you can spend ${capital_per_pair:.2f} on each of the {len(common_pairs)} pairs")


