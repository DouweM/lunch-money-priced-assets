# Lunch Money Priced Assets

Script to update the balances of priced assets (stocks, ETFs, etc.) in your Lunch Money account with prices from Yahoo Finance.

To qualify, an asset's name should be of the format `<label> [<symbol>]: <quantity>`, e.g. `Apple [AAPL]: 10`. The symbol needs to be available on Yahoo Finance: `https://finance.yahoo.com/quote/<symbol>`.

## Installation

```bash
# Install uv
curl -fsSL https://get.uv.dev | sh

# Move into cloned directory
cd path/to/lunch-money-priced-assets

# Install dependencies
uv sync
```

## Usage

```bash
# Set the Lunch Money access token
export LUNCHMONEY_ACCESS_TOKEN=your_access_token

# Run the script
uv run main.py
```
