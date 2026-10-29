"""
Feature 2: Sector Breakdown
Shows sector concentration and smarter diversification assessment
"""

import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

# Load portfolio
with open('portfolio.json', 'r') as f:
    portfolio = json.load(f)

print("=" * 80)
print("SECTOR BREAKDOWN & DIVERSIFICATION ANALYSIS")
print("=" * 80)

# Download current prices and sector info
print("\nFetching stock information...")
stock_info = {}
stock_prices = {}
all_returns = {}

for ticker in portfolio.keys():
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        prices = stock.history(period="1y")['Close']

        if len(prices) > 1:
            stock_prices[ticker] = prices.iloc[-1]
            all_returns[ticker] = prices.pct_change().dropna()

            # Get sector - be explicit about what we find
            sector = info.get('sector', None)
            industry = info.get('industry', None)

            stock_info[ticker] = {
                'sector': sector,
                'industry': industry,
                'price': prices.iloc[-1]
            }

            print(f"  {ticker}: {sector if sector else 'NO SECTOR DATA'}")
    except Exception as e:
        print(f"  {ticker}: ERROR - {e}")

# Get data timestamp
most_recent = max(stock_prices.keys(), key=lambda t: stock_info[t]['price'])
print(f"\nData as of: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")

# Calculate current values
print("\n" + "=" * 80)
print("PORTFOLIO VALUE BY STOCK")
print("=" * 80)

stock_values = {}
total_value = 0

for ticker, shares in portfolio.items():
    if ticker in stock_prices:
        value = stock_prices[ticker] * shares
        stock_values[ticker] = value
        total_value += value
        sector = stock_info[ticker]['sector'] if stock_info[ticker]['sector'] else 'Unknown'
        print(f"{ticker:6s}: ${value:>10,.2f} ({shares:>6.2f} shares) - {sector}")

print(f"\nTotal Portfolio Value: ${total_value:,.2f}")

# Calculate sector allocation
print("\n" + "=" * 80)
print("SECTOR ALLOCATION")
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

print("\nSector breakdown:")
for item in sector_allocations:
    bar_length = int(item['pct'] / 2)  # Scale to fit in 50 chars
    bar = '█' * bar_length
    print(f"  {item['sector']:30s}: {item['pct']:>5.1f}% ${item['value']:>10,.2f} {bar}")

if unknown_value > 0:
    pct = (unknown_value / total_value) * 100
    print(f"  {'Unknown':30s}: {pct:>5.1f}% ${unknown_value:>10,.2f}")

# Check for concentration warnings
print("\n" + "=" * 80)
print("CONCENTRATION WARNINGS")
print("=" * 80)

warnings_found = False

for item in sector_allocations:
    if item['pct'] > 40:
        print(f"\n⚠️  WARNING: {item['sector']} is {item['pct']:.1f}% of your portfolio!")
        print(f"   This is heavy concentration. If this sector crashes, your whole")
        print(f"   portfolio could suffer. Consider diversifying into other sectors.")
        warnings_found = True
    elif item['pct'] > 30:
        print(f"\n⚠  CAUTION: {item['sector']} is {item['pct']:.1f}% of your portfolio.")
        print(f"   This is notable concentration. Watch this sector's performance closely.")
        warnings_found = True

if not warnings_found:
    print("\n✓ No extreme sector concentrations detected (no sector >30%)")

# Calculate correlation matrix
returns_df = pd.DataFrame(all_returns)
corr_matrix = returns_df.corr()
avg_correlation = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()

# Smart diversification check
print("\n" + "=" * 80)
print("DIVERSIFICATION QUALITY ASSESSMENT")
print("=" * 80)

print("\nFactors considered:")
print(f"  1. Number of stocks: {len(portfolio)}")
print(f"  2. Number of sectors: {len(sector_allocations)}")
print(f"  3. Largest sector: {sector_allocations[0]['pct']:.1f}%")
print(f"  4. Average correlation: {avg_correlation:.3f}")

# Calculate diversification score
diversification_score = 0
issues = []
strengths = []

# Factor 1: Number of stocks
if len(portfolio) >= 8:
    diversification_score += 2
    strengths.append("Good number of stocks (8+)")
elif len(portfolio) >= 5:
    diversification_score += 1
    strengths.append("Reasonable number of stocks (5-7)")
else:
    issues.append(f"Only {len(portfolio)} stocks - limited diversification")

# Factor 2: Sector diversity
unique_sectors = len(sector_allocations)
if unique_sectors >= 5:
    diversification_score += 2
    strengths.append(f"Well diversified across {unique_sectors} sectors")
elif unique_sectors >= 3:
    diversification_score += 1
    strengths.append(f"Moderate sector diversity ({unique_sectors} sectors)")
else:
    issues.append(f"Only {unique_sectors} sectors - limited sector diversity")

# Factor 3: Sector concentration
max_sector_pct = sector_allocations[0]['pct']
if max_sector_pct < 30:
    diversification_score += 2
    strengths.append("No dominant sector (<30%)")
elif max_sector_pct < 50:
    diversification_score += 1
    issues.append(f"Largest sector is {max_sector_pct:.1f}% - some concentration")
else:
    issues.append(f"Heavy concentration in {sector_allocations[0]['sector']} ({max_sector_pct:.1f}%)")

# Factor 4: Correlation
if avg_correlation < 0.20:
    diversification_score += 2
    strengths.append("Low correlation between stocks (<0.20)")
elif avg_correlation < 0.35:
    diversification_score += 1
    strengths.append("Moderate correlation (0.20-0.35)")
else:
    issues.append(f"High correlation ({avg_correlation:.2f}) - stocks move together")

# Overall assessment
print("\n" + "-" * 80)
print("OVERALL DIVERSIFICATION RATING")
print("-" * 80)

if diversification_score >= 7:
    rating = "EXCELLENT"
    emoji = "✓✓"
    comment = "Your portfolio is well-diversified across stocks, sectors, and has low correlation."
elif diversification_score >= 5:
    rating = "GOOD"
    emoji = "✓"
    comment = "Your portfolio has solid diversification with room for minor improvements."
elif diversification_score >= 3:
    rating = "FAIR"
    emoji = "→"
    comment = "Your portfolio has some diversification but significant concentration risks."
else:
    rating = "POOR"
    emoji = "⚠"
    comment = "Your portfolio lacks diversification. You're exposed to concentrated risks."

print(f"\n{emoji} Rating: {rating} (Score: {diversification_score}/8)")
print(f"\n{comment}")

if strengths:
    print("\nStrengths:")
    for strength in strengths:
        print(f"  ✓ {strength}")

if issues:
    print("\nAreas for improvement:")
    for issue in issues:
        print(f"  • {issue}")

# Show which stocks are in the largest sector
print("\n" + "=" * 80)
print(f"STOCKS IN LARGEST SECTOR: {sector_allocations[0]['sector']}")
print("=" * 80)

largest_sector = sector_allocations[0]['sector']
sector_stocks = []

for ticker in stock_values.keys():
    if stock_info[ticker]['sector'] == largest_sector:
        value = stock_values[ticker]
        pct = (value / total_value) * 100
        sector_stocks.append({
            'ticker': ticker,
            'value': value,
            'pct': pct,
            'industry': stock_info[ticker]['industry']
        })

sector_stocks.sort(key=lambda x: x['value'], reverse=True)

for item in sector_stocks:
    print(f"  {item['ticker']:6s}: ${item['value']:>10,.2f} ({item['pct']:>5.1f}%)")
    if item['industry']:
        print(f"          Industry: {item['industry']}")

print(f"\nTotal in {largest_sector}: ${sector_allocations[0]['value']:,.2f} ({sector_allocations[0]['pct']:.1f}%)")

# Recommendation
print("\n" + "=" * 80)
print("ACTIONABLE RECOMMENDATION")
print("=" * 80)

if max_sector_pct > 50:
    print(f"\n🔴 URGENT: Reduce {largest_sector} exposure from {max_sector_pct:.1f}% to under 40%.")
    print(f"   Consider selling some {largest_sector} holdings and buying into:")
    # Suggest underrepresented sectors
    if len(sector_allocations) > 1:
        print("   Underweight sectors in your portfolio:")
        for item in sector_allocations[-3:]:
            print(f"     • {item['sector']} (currently {item['pct']:.1f}%)")
elif max_sector_pct > 40:
    print(f"\n🟡 IMPORTANT: Consider reducing {largest_sector} exposure from {max_sector_pct:.1f}%.")
    print(f"   Add positions in other sectors for better balance.")
elif avg_correlation > 0.40:
    print(f"\n🟡 Your stocks have high correlation ({avg_correlation:.2f}).")
    print(f"   Even with {len(portfolio)} stocks, they tend to move together.")
    print(f"   Consider adding stocks from different sectors or with different drivers.")
else:
    print(f"\n🟢 Your portfolio shows good diversification.")
    print(f"   Continue monitoring sector allocation and correlation over time.")

print("\n" + "=" * 80)
