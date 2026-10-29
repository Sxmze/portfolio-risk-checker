"""
Feature 2: Sector Breakdown (FIXED)
Facts-based analysis with customizable groupings
"""

import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

# ============================================================================
# EDITABLE GROUPING SETTINGS
# ============================================================================
# Define your own risk-based groups here
# Group stocks by what actually drives them, not just Yahoo's sector labels

CUSTOM_GROUPS = {
    'Big Tech / AI': ['NVDA', 'MSFT', 'AVGO', 'NOW', 'META', 'GOOGL', 'AMZN'],
    'Satellite / Telecom': ['ASTS'],
    'Pharma': ['LLY']
}

# Warning threshold for custom groups
GROUP_WARNING_THRESHOLD = 0.40  # Warn if any group exceeds 40%

# ============================================================================

# Load portfolio
with open('portfolio.json', 'r') as f:
    portfolio = json.load(f)

print("=" * 80)
print("SECTOR BREAKDOWN & GROUPING ANALYSIS")
print("=" * 80)

# Download data
print("\nFetching stock information...")
stock_info = {}
stock_prices = {}
all_returns_1y = {}
all_returns_3y = {}

for ticker in portfolio.keys():
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Get 3 years of data
        prices_3y = stock.history(period="3y")['Close']
        if len(prices_3y) > 1:
            stock_prices[ticker] = prices_3y.iloc[-1]
            all_returns_3y[ticker] = prices_3y.pct_change().dropna()

            # Get 1 year subset
            all_returns_1y[ticker] = all_returns_3y[ticker].tail(252)

            sector = info.get('sector', None)
            industry = info.get('industry', None)

            stock_info[ticker] = {
                'sector': sector,
                'industry': industry,
                'price': prices_3y.iloc[-1]
            }

            print(f"  {ticker}: {sector if sector else 'NO SECTOR DATA'}")
    except Exception as e:
        print(f"  {ticker}: ERROR - {e}")

print(f"\nData as of: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")

# Calculate current values
stock_values = {}
total_value = 0

for ticker, shares in portfolio.items():
    if ticker in stock_prices:
        value = stock_prices[ticker] * shares
        stock_values[ticker] = value
        total_value += value

print(f"Total Portfolio Value: ${total_value:,.2f}")

# ============================================================================
# YAHOO FINANCE SECTOR ALLOCATION
# ============================================================================
print("\n" + "=" * 80)
print("YAHOO FINANCE SECTOR CLASSIFICATION")
print("=" * 80)

sector_values = {}
unknown_value = 0

for ticker, value in stock_values.items():
    sector = stock_info[ticker]['sector']
    if sector:
        if sector not in sector_values:
            sector_values[sector] = 0
        sector_values[sector] += value
    else:
        unknown_value += value
        print(f"⚠ WARNING: {ticker} has no sector data from yfinance")

# Sort by value
sector_allocations = []
for sector, value in sector_values.items():
    pct = (value / total_value) * 100
    sector_allocations.append({
        'sector': sector,
        'value': value,
        'pct': pct
    })

sector_allocations.sort(key=lambda x: x['value'], reverse=True)

print("\nYahoo Finance sectors:")
for item in sector_allocations:
    bar_length = int(item['pct'] / 2)
    bar = '█' * bar_length
    print(f"  {item['sector']:30s}: {item['pct']:>5.1f}% ${item['value']:>10,.2f} {bar}")

if unknown_value > 0:
    pct = (unknown_value / total_value) * 100
    print(f"  {'Unknown':30s}: {pct:>5.1f}% ${unknown_value:>10,.2f}")

# ============================================================================
# CUSTOM RISK-BASED GROUPING
# ============================================================================
print("\n" + "=" * 80)
print("CUSTOM RISK-BASED GROUPING")
print("=" * 80)
print("(Groups defined by what actually drives these stocks)")
print("(Edit CUSTOM_GROUPS in the script to change groupings)")

group_values = {}
ungrouped_stocks = []

for ticker, value in stock_values.items():
    # Find which group this ticker belongs to
    found_group = None
    for group_name, tickers in CUSTOM_GROUPS.items():
        if ticker in tickers:
            found_group = group_name
            break

    if found_group:
        if found_group not in group_values:
            group_values[found_group] = 0
        group_values[found_group] += value
    else:
        ungrouped_stocks.append(ticker)

# Sort by value
group_allocations = []
for group, value in group_values.items():
    pct = (value / total_value) * 100
    group_allocations.append({
        'group': group,
        'value': value,
        'pct': pct
    })

group_allocations.sort(key=lambda x: x['value'], reverse=True)

print("\nCustom groups:")
for item in group_allocations:
    bar_length = int(item['pct'] / 2)
    bar = '█' * bar_length
    print(f"  {item['group']:30s}: {item['pct']:>5.1f}% ${item['value']:>10,.2f} {bar}")

if ungrouped_stocks:
    print(f"\nUngrouped stocks: {', '.join(ungrouped_stocks)}")

# Show which stocks are in each group
print("\nStocks in each group:")
for group_name, tickers in CUSTOM_GROUPS.items():
    stocks_in_portfolio = [t for t in tickers if t in stock_values]
    if stocks_in_portfolio:
        print(f"\n  {group_name}:")
        for ticker in stocks_in_portfolio:
            value = stock_values[ticker]
            pct = (value / total_value) * 100
            print(f"    {ticker}: ${value:>10,.2f} ({pct:>5.1f}%)")

# ============================================================================
# CONCENTRATION WARNINGS (Based on Custom Groups)
# ============================================================================
print("\n" + "=" * 80)
print("CONCENTRATION WARNINGS (Based on Custom Grouping)")
print("=" * 80)

warnings_found = False

for item in group_allocations:
    if item['pct'] > GROUP_WARNING_THRESHOLD * 100:
        print(f"\n⚠️  WARNING: {item['group']} is {item['pct']:.1f}% of your portfolio")
        print(f"   (threshold: {GROUP_WARNING_THRESHOLD*100:.0f}%)")
        warnings_found = True

if not warnings_found:
    print(f"\n✓ No group exceeds {GROUP_WARNING_THRESHOLD*100:.0f}% threshold")

# ============================================================================
# CORRELATION ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("CORRELATION ANALYSIS")
print("=" * 80)

# Calculate correlations
returns_1y = pd.DataFrame(all_returns_1y)
returns_3y = pd.DataFrame(all_returns_3y)

corr_1y = returns_1y.corr()
corr_3y = returns_3y.corr()

avg_corr_1y = corr_1y.values[np.triu_indices_from(corr_1y.values, k=1)].mean()
avg_corr_3y = corr_3y.values[np.triu_indices_from(corr_3y.values, k=1)].mean()

# Tech-only correlation (Big Tech / AI group)
tech_tickers = [t for t in CUSTOM_GROUPS.get('Big Tech / AI', []) if t in returns_1y.columns]
if len(tech_tickers) >= 2:
    tech_corr_1y = returns_1y[tech_tickers].corr()
    tech_corr_3y = returns_3y[tech_tickers].corr()
    tech_avg_1y = tech_corr_1y.values[np.triu_indices_from(tech_corr_1y.values, k=1)].mean()
    tech_avg_3y = tech_corr_3y.values[np.triu_indices_from(tech_corr_3y.values, k=1)].mean()
else:
    tech_avg_1y = None
    tech_avg_3y = None

print("\nAverage pairwise correlations:")
print(f"  All stocks (1 year):  {avg_corr_1y:.3f}")
print(f"  All stocks (3 years): {avg_corr_3y:.3f}")

if tech_avg_1y is not None:
    print(f"\n  Big Tech / AI group only (1 year):  {tech_avg_1y:.3f}")
    print(f"  Big Tech / AI group only (3 years): {tech_avg_3y:.3f}")

# ============================================================================
# SUMMARY FACTS
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY FACTS")
print("=" * 80)

print(f"\nNumber of stocks: {len(portfolio)}")
print(f"Number of Yahoo sectors: {len(sector_allocations)}")
print(f"Number of custom groups: {len(group_allocations)}")

print(f"\nLargest Yahoo sector: {sector_allocations[0]['sector']} ({sector_allocations[0]['pct']:.1f}%)")
print(f"Largest custom group: {group_allocations[0]['group']} ({group_allocations[0]['pct']:.1f}%)")

print(f"\nAverage correlation:")
print(f"  1 year:  {avg_corr_1y:.3f}")
print(f"  3 years: {avg_corr_3y:.3f}")

if tech_avg_1y is not None:
    print(f"\nBig Tech / AI group correlation:")
    print(f"  1 year:  {tech_avg_1y:.3f}")
    print(f"  3 years: {tech_avg_3y:.3f}")

print("\n" + "=" * 80)
print("NOTE: Custom grouping is defined in CUSTOM_GROUPS at the top of this script.")
print("Edit those settings to change how stocks are grouped.")
print("=" * 80)
