import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

# Quick test of the data freshness feature
with open('portfolio.json', 'r') as f:
    portfolio = json.load(f)

print("Testing data freshness display...\n")

# Get one stock as example
ticker = "NVDA"
stock = yf.Ticker(ticker)
prices = stock.history(period="1y")['Close']

latest_date = prices.index[-1]
print(f"Latest data timestamp: {latest_date}")
print(f"Formatted: {latest_date.strftime('%Y-%m-%d %I:%M %p %Z')}")

# Calculate age
now = datetime.now(latest_date.tzinfo)
data_age = now - latest_date
hours_old = data_age.total_seconds() / 3600

print(f"\nCurrent time (with timezone): {now}")
print(f"Data age: {hours_old:.1f} hours ({data_age.days} days)")
print(f"Weekday: {latest_date.weekday()} (5=Saturday, 6=Sunday)")

if hours_old < 24:
    print(f"Display: {hours_old:.1f} hours old")
else:
    print(f"Display: {data_age.days} days old")
