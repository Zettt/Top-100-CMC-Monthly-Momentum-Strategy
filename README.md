# Top 100 CoinMarketCap Monthly Momentum Strategy

A Python-based tool that analyzes cryptocurrency data from CoinMarketCap (CMC) and Binance to identify trading opportunities and market trends.

The idea is based on a *monthly* momentum strategy where we would buy the best performing assets in a universe, to speculate on a continued rally. I believe I got the idea after watching [this video](https://www.youtube.com/watch?v=L2nhNvIAyBI). After a month, we would sell the ones that are not performing anymore, and use our freed up capital to buy the next best performers. 

## Overview

This project fetches and compares data from both CoinMarketCap and Binance to:
- Track the top 100 cryptocurrencies by market cap
- Analyze price discrepancies between exchanges
- Monitor market movements and trading volumes

## Features

- Real-time data fetching from CoinMarketCap API
- Integration with Binance API for price comparison
- Market cap ranking analysis
- Price movement tracking
- Volume analysis
- Data filtering capabilities

## Requirements

- Python 3.8+
- CoinMarketCap API key (free)
- Binance API credentials (with trading enabled). Requires IP whitelisting.

## Installation

1. Clone the repository
2. Install required dependencies:
```bash
pip install -r requirements.txt
```
3. Configure your API keys in the `.env` file. Example `env.example` provided. 

## Usage

Run the main script to start the analysis:
```bash
python main.py
```

## Configuration

Rename a `env.exmaple` to `.env` and insert your API keys:
```
CMC_API_KEY=your_cmc_api_key
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
```

In `top100cmc.py`:
```python
MAX_PAIRS = 25
TRADING_ENABLED = False  # Set to True to enable real trading
TARGET_BALANCE = 200  # Fixed target balance in USDC
DEBUG = False  # Set to True to enable debug prints
```
