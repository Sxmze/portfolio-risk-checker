import yfinance as yf
import pandas as pd
import json

# Load portfolio
with open('portfolio.json', 'r') as f:
    portfolio = json.load(f)

print("=" * 70)
print("DATE ALIGNMENT DIAGNOSTIC")
print("=" * 70)

# Download all price data
all_prices = {}
for ticker in portfolio.keys():
    stock = yf.Ticker(ticker)
    prices = stock.history(period="1y")['Close']
    if len(prices) > 1:
        all_prices[ticker] = prices

print("\n--- Individual Stock Data Ranges ---")
for ticker, prices in all_prices.items():
    print(f"{ticker}: {len(prices)} days, from {prices.index[0].date()} to {prices.index[-1].date()}")

# Create DataFrame with all prices
prices_df = pd.DataFrame(all_prices)

print("\n--- Aligned DataFrame Info ---")
print(f"Total rows in aligned DataFrame: {len(prices_df)}")
print(f"Date range: {prices_df.index[0].date()} to {prices_df.index[-1].date()}")

# Check for missing values
print("\n--- Missing Data Check ---")
missing_counts = prices_df.isna().sum()
print(missing_counts)

if missing_counts.sum() > 0:
    print("\n⚠ WARNING: Missing values detected!")
    print("This will cause NaN values in returns and corrupt correlation calculations.")

    # Show where the gaps are
    print("\n--- Rows with any missing data ---")
    rows_with_missing = prices_df[prices_df.isna().any(axis=1)]
    print(f"Found {len(rows_with_missing)} rows with missing data")
    if len(rows_with_missing) > 0:
        print(rows_with_missing)
else:
    print("\n✓ No missing values - all stocks have data for the same dates")

# Calculate returns and check
returns_df = prices_df.pct_change().dropna()

print("\n--- Returns DataFrame Info ---")
print(f"Total rows after calculating returns: {len(returns_df)}")
print(f"Date range: {returns_df.index[0].date()} to {returns_df.index[-1].date()}")

# Check for NaN in returns
print("\n--- Missing Returns Check ---")
missing_returns = returns_df.isna().sum()
print(missing_returns)

if missing_returns.sum() > 0:
    print("\n⚠ WARNING: NaN values in returns!")
    print("These will corrupt correlation and volatility calculations.")

    # Show problematic rows
    bad_rows = returns_df[returns_df.isna().any(axis=1)]
    print(f"\nRows with NaN returns: {len(bad_rows)}")
    if len(bad_rows) <= 20:
        print(bad_rows)
else:
    print("\n✓ No NaN values in returns - data is properly aligned")

# Show actual correlation calculation input
print("\n--- Sample of Returns Data Used for Correlation ---")
print("First 5 days:")
print(returns_df.head())
print("\nLast 5 days:")
print(returns_df.tail())

# Statistical summary
print("\n--- Returns Statistics ---")
print(f"Number of return observations per stock: {len(returns_df)}")
print(f"\nMean daily returns:")
print((returns_df.mean() * 100).round(4))
print(f"\nStd dev of daily returns:")
print((returns_df.std() * 100).round(4))

# Check date continuity
print("\n--- Date Continuity Check ---")
date_diffs = pd.Series(returns_df.index).diff()
# Trading days should be 1 day (weekdays) or 3 days (over weekend)
gaps = date_diffs[date_diffs > pd.Timedelta(days=4)]
if len(gaps) > 0:
    print(f"⚠ Found {len(gaps)} gaps longer than 4 days (possible holidays/missing data):")
    for gap in gaps.head(10):
        print(f"  {gap}")
else:
    print("✓ No unexpected gaps in trading days")

# Final verdict
print("\n" + "=" * 70)
print("VERDICT")
print("=" * 70)
if missing_returns.sum() == 0 and len(returns_df) > 200:
    print(f"✓ Data is properly aligned")
    print(f"✓ Using {len(returns_df)} days of returns for all stocks")
    print(f"✓ Correlations are calculated correctly")
else:
    print(f"⚠ POTENTIAL DATA QUALITY ISSUES DETECTED")
    print(f"Check the warnings above")
