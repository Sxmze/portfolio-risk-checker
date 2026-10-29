"""
Quick demo of the new data freshness feature
"""
import yfinance as yf
import json
from datetime import datetime

# Load your portfolio
with open('portfolio.json', 'r') as f:
    portfolio = json.load(f)

print("=" * 70)
print("DATA FRESHNESS DEMO")
print("=" * 70)

# Download price data
all_prices = {}
print("\nFetching data for your 9 stocks...")
for ticker in portfolio.keys():
    stock = yf.Ticker(ticker)
    prices = stock.history(period="1y")['Close']
    if len(prices) > 1:
        all_prices[ticker] = prices

# Show data freshness (this is what you'll see in the main program)
print("\n--- Data Freshness ---")
latest_dates = {}
for ticker, prices in all_prices.items():
    latest_dates[ticker] = prices.index[-1]

# Find the most recent data point across all stocks
most_recent = max(latest_dates.values())
oldest_recent = min(latest_dates.values())

print(f"Most recent price data: {most_recent.strftime('%Y-%m-%d %I:%M %p %Z')}")
if most_recent.date() != oldest_recent.date():
    print(f"Oldest recent price: {oldest_recent.strftime('%Y-%m-%d %I:%M %p %Z')}")
    print("⚠ Note: Not all stocks have data from the same date")

# Calculate how old the data is
now = datetime.now(most_recent.tzinfo)
data_age = now - most_recent
hours_old = data_age.total_seconds() / 3600

if hours_old < 24:
    print(f"Data age: {hours_old:.1f} hours old")
else:
    print(f"Data age: {data_age.days} days old")

# Market status hint
if most_recent.weekday() >= 5:  # Saturday or Sunday
    print("(Markets are closed on weekends)")
elif hours_old < 1:
    print("(Live market data)")
elif hours_old > 24:
    print("(Historical data - markets may have closed)")

print("\n" + "=" * 70)
print("This information now appears automatically when you analyze risk!")
print("=" * 70)
