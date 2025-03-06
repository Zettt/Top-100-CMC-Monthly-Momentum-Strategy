# %%
import requests
import json
from dotenv import load_dotenv
import os
import ccxt

load_dotenv()

# %%
# max number of pairs to be processed
# this also influences how much capital is dispersed among the pairs
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
    stablecoins = ['USDC', 'USDT', 'BUSD', 'DAI', 'TUSD', 'FDUSD']
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
# Get API credentials from environment variables
binance_api_key = os.getenv('BINANCE_API_KEY')
binance_api_secret = os.getenv('BINANCE_API_SECRET')

if not binance_api_key or not binance_api_secret:
    raise ValueError("Binance API credentials not found in environment variables")

# Initialize Binance exchange
exchange = ccxt.binance({
    'apiKey': binance_api_key,
    'secret': binance_api_secret,
    'enableRateLimit': True
})



# %%
# Fetch balance
balance = exchange.fetch_balance()

# Calculate USD equivalent for each coin in common_pairs
usd_balances = {}
for pair in common_pairs:
    # Extract base currency (remove 'USDC' from the end)
    base_currency = pair[:-4]
    
    # Get the balance for this currency
    amount = float(balance['total'].get(base_currency, 0))
    
    if amount > 0:
        # Fetch current price in USDC
        try:
            ticker = exchange.fetch_ticker(pair)
            price = ticker['last']
            usd_value = amount * price
            usd_balances[base_currency] = {
                'amount': amount,
                'usd_value': usd_value
            }
        except:
            print(f"Could not fetch price for {pair}")

# Print results
for currency, data in usd_balances.items():
    print(f"{currency}: {data['amount']:.8f} coins = ${data['usd_value']:.2f}")

total_usd_value = sum(data['usd_value'] for data in usd_balances.values())
print(f"\nTotal portfolio value: ${total_usd_value:.2f}")

# %%
# We need to sell all coins first to free up capital before buying new coins

# Calculate which coins to sell (coins in balance but not in common_pairs)
coins_to_sell = []
for currency in balance['total'].keys():
    # Skip USDC and coins with 0 balance
    if currency == 'USDC' or float(balance['total'][currency]) == 0:
        continue
    
    # Check if this currency has a USDC pair in common_pairs
    pair = f"{currency}USDC"
    if pair not in common_pairs:
        # Check if the market exists and is active
        markets = exchange.load_markets()
        if pair not in markets or not markets[pair]['active']:
            print(f"Market {pair} inactive or delisted")
            continue
            
        # Check USD value before adding to sell list
        try:
            amount = float(balance['total'][currency])
            ticker = exchange.fetch_ticker(pair)
            usd_value = amount * ticker['last']
            
            # Only add to sell list if USD value is >= 0.5
            if usd_value >= 0.5:
                coins_to_sell.append(currency)
            else:
                print(f"Skipping {currency} (value: ${usd_value:.2f} < $0.5)")
        except Exception as e:
            print(f"Error checking {pair}: {str(e)}")

print(f"Coins to sell: {coins_to_sell}")

# %%
# Execute sell orders for coins not in common_pairs
for currency in coins_to_sell:
    try:
        pair = f"{currency}USDC"
        # Get current balance
        amount = float(balance['total'][currency])
        
        # Fetch current market price
        ticker = exchange.fetch_ticker(pair)
        
        # Create market sell order
        order = exchange.create_market_sell_order(
            symbol=pair,
            amount=amount,
            params={'type': 'MARKET'}
        )
        
        print(f"Sold {amount} {currency} at market price")
        print(f"Order details: {order}")
        
    except Exception as e:
        print(f"Error selling {currency}: {str(e)}")
        continue
    
    # Add delay to avoid rate limits
    exchange.sleep(1000)  # 1 second delay between orders

# %%
# Calculate total spot balance including all assets
total_spot_balance = total_usd_value  # Start with previously calculated crypto values

# Add USDC balance if any
usdc_balance = float(balance['total'].get('USDC', 0))
total_spot_balance += usdc_balance

print(f"USDC balance: ${usdc_balance:.2f}")
print(f"Total spot account valuei (including all assets): ${total_usd_value:.2f}")

capital_per_pair = total_spot_balance / len(common_pairs)
print(f"With ${total_spot_balance} total capital, you can spend ${capital_per_pair:.2f} on each of the {len(common_pairs)} pairs")

# %%
for pair in common_pairs:
    base_currency = pair[:-4]  # Remove 'USDC' from the end
    
    try:
        # Get current balance and price
        current_amount = float(balance['total'].get(base_currency, 0))
        ticker = exchange.fetch_ticker(pair)
        current_price = ticker['last']
        
        # Get market information for precision
        market = exchange.markets[pair]
        amount_precision = market['precision']['amount']
        
        # Calculate current value in USDC
        current_value = current_amount * current_price
        
        # Calculate difference from target
        value_difference = capital_per_pair - current_value
        
        # If difference is significant (more than $1), execute trade
        if abs(value_difference) >= 1:
            if value_difference > 0:  # Need to buy
                # Calculate amount to buy with precision
                amount_to_buy = round(value_difference / current_price, amount_precision)
                
                # Check minimum trade amount
                if amount_to_buy >= market['limits']['amount']['min']:
                    # Create market buy order
                    order = exchange.create_market_buy_order(
                        symbol=pair,
                        amount=amount_to_buy,
                        params={'type': 'MARKET'}
                    )
                    print(f"Bought {amount_to_buy:.8f} {base_currency} for ${value_difference:.2f}")
                else:
                    print(f"Skip buying {pair}: Amount {amount_to_buy} below minimum {market['limits']['amount']['min']}")
                
            else:  # Need to sell
                # Calculate amount to sell with precision
                amount_to_sell = round(abs(value_difference) / current_price, amount_precision)
                
                # Check minimum trade amount
                if amount_to_sell >= market['limits']['amount']['min']:
                    # Create market sell order
                    order = exchange.create_market_sell_order(
                        symbol=pair,
                        amount=amount_to_sell,
                        params={'type': 'MARKET'}
                    )
                    print(f"Sold {amount_to_sell:.8f} {base_currency} for ${abs(value_difference):.2f}")
                else:
                    print(f"Skip selling {pair}: Amount {amount_to_sell} below minimum {market['limits']['amount']['min']}")
        
        # Add delay to avoid rate limits
        exchange.sleep(1000)  # 1 second delay between orders
        
    except Exception as e:
        print(f"Error balancing {pair}: {str(e)}")
        continue


