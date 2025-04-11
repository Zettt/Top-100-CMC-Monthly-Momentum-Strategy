# %%
import requests
import json
from dotenv import load_dotenv
import os
import ccxt

# Load environment variables
load_dotenv()

# Constants
MAX_PAIRS = 25
TRADING_ENABLED = True  # Set to True to enable real trading
TARGET_BALANCE = 200  # Target balance if trading is disabled

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
def get_binance_usdc_pairs():
    markets = exchange.load_markets()
    stablecoins = ['USDC', 'USDT', 'BUSD', 'DAI', 'TUSD']
    usdc_pairs = [symbol for symbol in markets.keys() 
                  if symbol.endswith('/USDC') 
                  and not any(coin in symbol.split('/')[0] for coin in stablecoins)]
    return [pair.replace('/', '') for pair in usdc_pairs]

# %%
def find_common_pairs(top100_symbols, usdc_pairs):
    common_pairs = []
    for symbol in top100_symbols:
        if symbol in usdc_pairs:
            common_pairs.append(symbol)
            if len(common_pairs) >= MAX_PAIRS:
                break
    return common_pairs

# %%
def get_account_balance():
    if not TRADING_ENABLED:
        return TARGET_BALANCE
        
    try:
        total_usd = 0
        balance = exchange.fetch_balance()
        stablecoins = ['USDC', 'USDT', 'BUSD', 'DAI', 'TUSD']
        
        for currency, details in balance['total'].items():
            amount = float(details)
            if amount <= 0:
                continue
                
            if currency == 'USDC':
                total_usd += amount
            elif currency in stablecoins:
                continue  # Skip other stablecoins
            else:
                try:
                    ticker = exchange.fetch_ticker(f"{currency}/USDC")
                    usd_value = amount * ticker['last']
                    if usd_value >= 0.5:  # Ignore small balances
                        total_usd += usd_value
                except Exception as e:
                    print(f"Error pricing {currency}: {e}")
        
        return total_usd
    except Exception as e:
        print(f"Error fetching balance: {e}")
        return 0

# %%
# Calculate portfolio value
def get_portfolio_value(exchange, common_pairs):
    balance = exchange.fetch_balance()
    usd_balances = {}
    
    for pair in common_pairs:
        base_currency = pair[:-4]
        amount = float(balance['total'].get(base_currency, 0))
        
        if amount > 0:
            try:
                ticker = exchange.fetch_ticker(pair)
                price = ticker['last']
                usd_value = amount * price
                usd_balances[base_currency] = {
                    'amount': amount,
                    'usd_value': usd_value
                }
            except Exception as e:
                print(f"Could not fetch price for {pair}: {e}")

    # Print portfolio
    for currency, data in usd_balances.items():
        print(f"{currency}: {data['amount']:.8f} coins = ${data['usd_value']:.2f}")

    total_usd_value = sum(data['usd_value'] for data in usd_balances.values())
    print(f"\nTotal portfolio value: ${total_usd_value:.2f}")
    return total_usd_value

def find_coins_to_sell(exchange, common_pairs, capital_per_pair):
    balance = exchange.fetch_balance()
    coins_to_sell = []
    
    for currency in balance['free'].keys():
        if currency == 'USDC' or float(balance['free'][currency]) == 0:
            continue
        
        pair = f"{currency}/USDC"
        if pair not in common_pairs and pair in exchange.markets:
            try:
                amount = float(balance['free'][currency])
                ticker = exchange.fetch_ticker(pair)
                usd_value = amount * ticker['last']
                
                if usd_value >= capital_per_pair: # and usd_value >= 0.5 to filter out small coins
                    coins_to_sell.append(currency)
                else:
                    print(f"Skipping {currency} (value: ${usd_value:.2f} < ${capital_per_pair:.2f})")
            except Exception as e:
                print(f"Error checking {pair}: {str(e)}")
    
    return coins_to_sell

def execute_sells(exchange, coins_to_sell, capital_per_pair):
    balance = exchange.fetch_balance()

    for currency in coins_to_sell:
        try:
            pair = f"{currency}/USDC"
            if pair not in exchange.markets:
                print(f"Skipping {currency}: No USDC market")
                continue
                
            # Get current price and available balance
            ticker = exchange.fetch_ticker(pair)
            current_price = ticker['last']
            free_amount = float(balance['free'].get(currency, 0))
            current_value = free_amount * current_price
            
            if current_value <= capital_per_pair:
                print(f"Skipping {currency}: Value ${current_value:.2f} <= ${capital_per_pair:.2f}")
                continue
                
            # Calculate amount to sell
            excess_value = current_value - capital_per_pair
            amount_to_sell = min(free_amount, excess_value / current_price)
            
            if TRADING_ENABLED and amount_to_sell > 0:
                # Check market minimums
                market = exchange.market(pair)
                if amount_to_sell < market['limits']['amount']['min']:
                    print(f"Skipping {currency}: Amount {amount_to_sell} below minimum")
                    continue
                    
                # Execute sell
                exchange.create_market_sell_order(
                    symbol=pair,
                    amount=round(amount_to_sell, market['precision']['amount']),
                    params={'type': 'MARKET'}
                )
            
            print(f"{'[SIMULATION] ' if not TRADING_ENABLED else ''}Sold {amount_to_sell:.8f} {currency} (${excess_value:.2f} excess)")
            
        except Exception as e:
            print(f"Error selling {currency}: {str(e)}")
        finally:
            exchange.sleep(1000)  # Rate limit compliance

def rebalance_portfolio(exchange, common_pairs, capital_per_pair):
    for pair in common_pairs:
        base_currency = pair[:-4]
        
        try:
            # Fetch once per pair to avoid stale data
            balance = exchange.fetch_balance()
            ticker = exchange.fetch_ticker(pair)
            current_price = ticker['last']
            market = exchange.markets[pair]

            # Calculate current position
            current_amount = float(balance['total'].get(base_currency, 0))
            current_value = current_amount * current_price
            value_difference = capital_per_pair - current_price * current_amount

            # Check if rebalancing is needed (add 1% buffer to avoid micro-adjustments)
            if abs(value_difference) < max(1, capital_per_pair * 0.01):
                continue  # Skip small differences

            # Handle buy/sell logic
            if value_difference > 0:  # Buy
                # Check available USDC balance
                usdc_balance = float(balance['total'].get('USDC', 0))
                if TRADING_ENABLED and (value_difference > usdc_balance):
                    print(f"Skip buying {pair}: Insufficient USDC (Needed: ${value_difference:.2f}, Available: ${usdc_balance:.2f})")
                    continue

                amount_to_buy = round(value_difference / current_price, market['precision']['amount'])
                
                if amount_to_buy >= market['limits']['amount']['min']:
                    if TRADING_ENABLED:
                        # Verify order success
                        order = exchange.create_market_buy_order(
                            symbol=pair,
                            amount=amount_to_buy
                        )
                        # Check if order was filled
                        if order['status'] != 'closed':
                            print(f"Warning: Buy order for {pair} not fully filled")
                    print(f"{'[SIMULATION] ' if not TRADING_ENABLED else ''}Bought {amount_to_buy:.8f} {base_currency} (Target: ${capital_per_pair:.2f}, Actual: ${amount_to_buy * current_price:.2f})")
                else:
                    print(f"Skip buying {pair}: Amount {amount_to_buy} below minimum")

            else:  # Sell
                amount_to_sell = round(abs(value_difference) / current_price, market['precision']['amount'])
                
                if amount_to_sell >= market['limits']['amount']['min']:
                    if TRADING_ENABLED:
                        order = exchange.create_market_sell_order(
                            symbol=pair,
                            amount=amount_to_sell
                        )
                        if order['status'] != 'closed':
                            print(f"Warning: Sell order for {pair} not fully filled")
                    print(f"{'[SIMULATION] ' if not TRADING_ENABLED else ''}Sold {amount_to_sell:.8f} {base_currency} (Target: ${capital_per_pair:.2f}, Actual: ${amount_to_sell * current_price:.2f})")
                else:
                    print(f"Skip selling {pair}: Amount {amount_to_sell} below minimum")

            exchange.sleep(1000)  # Rate limit

        except Exception as e:
            print(f"Error balancing {pair}: {str(e)}")
            continue

# Execute the portfolio management
if __name__ == "__main__":
    # Initialize top-level variables
    top100_symbols = get_coinmarketcap_top100()
    usdt_pairs = get_binance_usdc_pairs()
    common_pairs = find_common_pairs(top100_symbols, usdt_pairs)

    print(f"Top {MAX_PAIRS} cryptocurrencies in the top 100 on CoinMarketCap which are tradeable on Binance (USDT pairs): \n {common_pairs}")
    print(f"Number of pairs selected: {len(common_pairs)}\n")

    # Get actual balance and compare with target
    account_balance = get_account_balance()
    capital = account_balance if TRADING_ENABLED else TARGET_BALANCE
    capital_per_pair = capital / len(common_pairs)

    print(f"Account balance: ${account_balance:.2f}\n")
    print(f"With ${capital:.2f} total capital, you can spend ${capital_per_pair:.2f} on each of the {len(common_pairs)} pairs\n")

    # Get current portfolio value
    total_value = get_portfolio_value(exchange, common_pairs)
    
    # Find and sell non-target coins
    coins_to_sell = find_coins_to_sell(exchange, common_pairs, capital_per_pair)
    print(f"Coins to sell: {coins_to_sell}")
    execute_sells(exchange, coins_to_sell, capital_per_pair) if TRADING_ENABLED else print("Trading disabled, skipping sells.")

    # Recalculate capital post-sale
    updated_balance = get_account_balance()
    capital = updated_balance if TRADING_ENABLED else TARGET_BALANCE
    capital_per_pair = capital / len(common_pairs)
    
    # Rebalance portfolio
    print("\nRebalancing portfolio...")
    rebalance_portfolio(exchange, common_pairs, capital_per_pair)
