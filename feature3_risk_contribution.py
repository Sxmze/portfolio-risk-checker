"""
Feature 3: Risk Contribution
Shows which stocks contribute most to total portfolio risk
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
print("RISK CONTRIBUTION ANALYSIS")
print("=" * 80)

# Download data
print("\nFetching data...")
all_prices = {}
all_returns = {}

for ticker in portfolio.keys():
    stock = yf.Ticker(ticker)
    prices = stock.history(period="1y")['Close']
    if len(prices) > 1:
        all_prices[ticker] = prices
        all_returns[ticker] = prices.pct_change().dropna()

# Create aligned DataFrame
returns_df = pd.DataFrame(all_returns)

print(f"Data as of: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
print(f"Analysis period: {returns_df.index[0].date()} to {returns_df.index[-1].date()}")
print(f"Trading days: {len(returns_df)}")

# Calculate portfolio weights
stock_values = {}
total_value = 0

for ticker in portfolio.keys():
    if ticker in all_prices:
        current_price = all_prices[ticker].iloc[-1]
        value = current_price * portfolio[ticker]
        stock_values[ticker] = value
        total_value += value

weights = {}
weights_array = []
tickers_ordered = []

for ticker in returns_df.columns:
    weight = stock_values[ticker] / total_value
    weights[ticker] = weight
    weights_array.append(weight)
    tickers_ordered.append(ticker)

weights_array = np.array(weights_array)

print(f"\nTotal Portfolio Value: ${total_value:,.2f}")

# Calculate covariance matrix
cov_matrix = returns_df.cov()

# Calculate portfolio variance
portfolio_variance = weights_array @ cov_matrix.values @ weights_array

# Calculate portfolio volatility (annualized)
portfolio_volatility = np.sqrt(portfolio_variance) * np.sqrt(252)

print(f"Portfolio annual volatility: {portfolio_volatility*100:.2f}%")

# ============================================================================
# RISK CONTRIBUTION CALCULATION
# ============================================================================
print("\n" + "=" * 80)
print("RISK CONTRIBUTION BY STOCK")
print("=" * 80)

# Formula: Risk contribution of asset i = (weight_i * (Cov × weights)_i) / portfolio_variance
# This captures both the asset's own volatility AND how it correlates with other assets

cov_times_weights = cov_matrix.values @ weights_array

risk_contributions = {}
for i, ticker in enumerate(tickers_ordered):
    risk_contrib = (weights_array[i] * cov_times_weights[i]) / portfolio_variance
    risk_contributions[ticker] = risk_contrib

# Verify risk contributions sum to 1.0
total_risk_contribution = sum(risk_contributions.values())

print(f"\nVerification: Risk contributions sum to {total_risk_contribution:.6f}")
if abs(total_risk_contribution - 1.0) < 0.0001:
    print("✓ Risk contributions correctly sum to 100%")
else:
    print(f"⚠ WARNING: Risk contributions sum to {total_risk_contribution*100:.4f}%, not 100%!")
    print("   This indicates a calculation error. Results may be unreliable.")

# Create comparison table
print("\n" + "=" * 80)
print("PORTFOLIO WEIGHT vs RISK CONTRIBUTION")
print("=" * 80)
print("\nStock  | Portfolio % | Risk %  | Difference | Status")
print("-" * 80)

comparison_data = []
for ticker in tickers_ordered:
    weight_pct = weights[ticker] * 100
    risk_pct = risk_contributions[ticker] * 100
    diff = risk_pct - weight_pct
    ratio = risk_pct / weight_pct if weight_pct > 0 else 0

    comparison_data.append({
        'ticker': ticker,
        'weight_pct': weight_pct,
        'risk_pct': risk_pct,
        'diff': diff,
        'ratio': ratio
    })

# Sort by risk contribution (highest first)
comparison_data.sort(key=lambda x: x['risk_pct'], reverse=True)

for item in comparison_data:
    ticker = item['ticker']
    weight_pct = item['weight_pct']
    risk_pct = item['risk_pct']
    diff = item['diff']
    ratio = item['ratio']

    # Flag if risk is significantly higher than weight
    if ratio > 1.5:
        status = "⚠ HIGH RISK"
    elif ratio > 1.2:
        status = "↑ Above avg"
    elif ratio < 0.8:
        status = "↓ Below avg"
    else:
        status = "≈ Balanced"

    print(f"{ticker:6s} | {weight_pct:>10.1f}% | {risk_pct:>6.1f}% | {diff:>+9.1f}% | {status}")

# ============================================================================
# DETAILED ANALYSIS OF TOP RISK CONTRIBUTORS
# ============================================================================
print("\n" + "=" * 80)
print("TOP RISK CONTRIBUTORS")
print("=" * 80)

print("\nStocks where risk % significantly exceeds portfolio %:")
flagged_count = 0

for item in comparison_data:
    if item['ratio'] > 1.5:
        ticker = item['ticker']
        weight_pct = item['weight_pct']
        risk_pct = item['risk_pct']
        ratio = item['ratio']

        # Calculate stock's individual volatility
        stock_returns = returns_df[ticker]
        stock_vol = stock_returns.std() * np.sqrt(252) * 100

        # Calculate average correlation with other stocks
        correlations = cov_matrix[ticker] / (returns_df[ticker].std() * returns_df.std())
        other_stocks = [t for t in tickers_ordered if t != ticker]
        avg_corr = correlations[other_stocks].mean()

        print(f"\n  {ticker}:")
        print(f"    Portfolio weight: {weight_pct:.1f}%")
        print(f"    Risk contribution: {risk_pct:.1f}%")
        print(f"    Risk/Weight ratio: {ratio:.2f}x")
        print(f"    Individual volatility: {stock_vol:.1f}%")
        print(f"    Avg correlation with other stocks: {avg_corr:.3f}")
        flagged_count += 1

if flagged_count == 0:
    print("\n✓ No stocks have risk contribution >1.5x their portfolio weight")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

# Find stocks with highest/lowest risk contribution
max_risk_ticker = max(comparison_data, key=lambda x: x['risk_pct'])['ticker']
min_risk_ticker = min(comparison_data, key=lambda x: x['risk_pct'])['ticker']

max_risk_pct = risk_contributions[max_risk_ticker] * 100
min_risk_pct = risk_contributions[min_risk_ticker] * 100

print(f"\nHighest risk contributor: {max_risk_ticker} ({max_risk_pct:.1f}%)")
print(f"Lowest risk contributor: {min_risk_ticker} ({min_risk_pct:.1f}%)")

# Calculate concentration metrics
top_3_risk = sum(sorted([item['risk_pct'] for item in comparison_data], reverse=True)[:3])
print(f"\nTop 3 stocks account for {top_3_risk:.1f}% of total portfolio risk")

# Individual volatilities
print("\n" + "-" * 80)
print("Individual stock volatilities (annual):")
print("-" * 80)

vol_data = []
for ticker in tickers_ordered:
    stock_vol = returns_df[ticker].std() * np.sqrt(252)
    vol_data.append({
        'ticker': ticker,
        'volatility': stock_vol
    })

vol_data.sort(key=lambda x: x['volatility'], reverse=True)

for item in vol_data:
    print(f"  {item['ticker']:6s}: {item['volatility']*100:>5.1f}%")

# ============================================================================
# EXPLANATION FOR INTERVIEWS
# ============================================================================
print("\n" + "=" * 80)
print("HOW RISK CONTRIBUTION IS CALCULATED")
print("=" * 80)

print("""
Risk contribution measures how much each stock adds to your total portfolio
risk, accounting for:
  1. The stock's own volatility (how much it bounces around)
  2. How much of this stock you own (portfolio weight)
  3. How the stock moves with your other holdings (correlation)

Formula: Risk contribution = (weight × (covariance matrix × weights)) / portfolio variance

This is NOT just "weight × volatility". A highly volatile stock with low
correlation to your other holdings might contribute LESS risk than a moderately
volatile stock that's highly correlated with everything else.

Example: If NVDA is 18% of your portfolio but 22% of your risk, the extra 4%
comes from NVDA's high correlation with your other tech holdings. When tech
crashes, NVDA amplifies the damage instead of cushioning it.
""")

print("=" * 80)
