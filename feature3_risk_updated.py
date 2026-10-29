"""
Feature 3: Risk Contribution (UPDATED)
Shows risk contribution on 1 year and 3 years side by side
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

# Download data - get 3 years
print("\nFetching data...")
all_prices_3y = {}
all_returns_1y = {}
all_returns_3y = {}

for ticker in portfolio.keys():
    stock = yf.Ticker(ticker)
    prices = stock.history(period="3y")['Close']
    if len(prices) > 1:
        all_prices_3y[ticker] = prices
        all_returns_3y[ticker] = prices.pct_change().dropna()
        # Get 1 year subset
        all_returns_1y[ticker] = all_returns_3y[ticker].tail(252)

# Create aligned DataFrames
returns_1y = pd.DataFrame(all_returns_1y)
returns_3y = pd.DataFrame(all_returns_3y)

# Get most recent date from the data
most_recent_date = max(prices.index[-1] for prices in all_prices_3y.values())

print(f"\nData as of: {most_recent_date.strftime('%Y-%m-%d')}")
print(f"1 year period: {returns_1y.index[0].date()} to {returns_1y.index[-1].date()} ({len(returns_1y)} days)")
print(f"3 year period: {returns_3y.index[0].date()} to {returns_3y.index[-1].date()} ({len(returns_3y)} days)")

# Calculate portfolio weights using most recent prices
stock_values = {}
total_value = 0

for ticker in portfolio.keys():
    if ticker in all_prices_3y:
        current_price = all_prices_3y[ticker].iloc[-1]
        value = current_price * portfolio[ticker]
        stock_values[ticker] = value
        total_value += value

weights = {}
weights_array = []
tickers_ordered = []

for ticker in returns_1y.columns:
    weight = stock_values[ticker] / total_value
    weights[ticker] = weight
    weights_array.append(weight)
    tickers_ordered.append(ticker)

weights_array = np.array(weights_array)

print(f"\nTotal Portfolio Value: ${total_value:,.2f}")

# ============================================================================
# CALCULATE RISK CONTRIBUTIONS FOR BOTH PERIODS
# ============================================================================

def calculate_risk_contributions(returns_df, weights_array, tickers):
    """Calculate risk contributions for a given period"""
    cov_matrix = returns_df.cov()
    portfolio_variance = weights_array @ cov_matrix.values @ weights_array
    portfolio_volatility = np.sqrt(portfolio_variance) * np.sqrt(252)

    cov_times_weights = cov_matrix.values @ weights_array

    risk_contributions = {}
    for i, ticker in enumerate(tickers):
        risk_contrib = (weights_array[i] * cov_times_weights[i]) / portfolio_variance
        risk_contributions[ticker] = risk_contrib

    return risk_contributions, portfolio_volatility

risk_1y, vol_1y = calculate_risk_contributions(returns_1y, weights_array, tickers_ordered)
risk_3y, vol_3y = calculate_risk_contributions(returns_3y, weights_array, tickers_ordered)

# Verify sums
sum_1y = sum(risk_1y.values())
sum_3y = sum(risk_3y.values())

print(f"\nPortfolio annual volatility (1 year): {vol_1y*100:.2f}%")
print(f"Portfolio annual volatility (3 years): {vol_3y*100:.2f}%")

print(f"\nVerification:")
print(f"  1 year risk contributions sum to: {sum_1y:.6f}")
print(f"  3 year risk contributions sum to: {sum_3y:.6f}")

if abs(sum_1y - 1.0) < 0.0001 and abs(sum_3y - 1.0) < 0.0001:
    print("  ✓ Both correctly sum to 100%")
else:
    print("  ⚠ WARNING: Risk contributions do not sum to 100%")

# ============================================================================
# SIDE BY SIDE COMPARISON
# ============================================================================
print("\n" + "=" * 80)
print("PORTFOLIO WEIGHT vs RISK CONTRIBUTION (1 Year & 3 Years)")
print("=" * 80)

# Create comparison data
comparison_data = []
for ticker in tickers_ordered:
    weight_pct = weights[ticker] * 100
    risk_1y_pct = risk_1y[ticker] * 100
    risk_3y_pct = risk_3y[ticker] * 100

    mult_1y = risk_1y_pct / weight_pct if weight_pct > 0 else 0
    mult_3y = risk_3y_pct / weight_pct if weight_pct > 0 else 0

    comparison_data.append({
        'ticker': ticker,
        'weight_pct': weight_pct,
        'risk_1y_pct': risk_1y_pct,
        'risk_3y_pct': risk_3y_pct,
        'mult_1y': mult_1y,
        'mult_3y': mult_3y
    })

# Sort by 1-year risk contribution
comparison_data.sort(key=lambda x: x['risk_1y_pct'], reverse=True)

print("\n        |           |      1 YEAR      |      3 YEARS     |")
print("Stock   | Money %   | Risk %  | Mult   | Risk %  | Mult   |")
print("-" * 80)

for item in comparison_data:
    ticker = item['ticker']
    weight = item['weight_pct']
    risk_1y_val = item['risk_1y_pct']
    risk_3y_val = item['risk_3y_pct']
    mult_1y_val = item['mult_1y']
    mult_3y_val = item['mult_3y']

    print(f"{ticker:6s}  | {weight:>8.1f}% | {risk_1y_val:>6.1f}% | {mult_1y_val:>4.2f}x | {risk_3y_val:>6.1f}% | {mult_3y_val:>4.2f}x |")

# ============================================================================
# STOCKS WITH HIGH MULTIPLIERS
# ============================================================================
print("\n" + "=" * 80)
print("STOCKS WITH RISK MULTIPLIER > 1.5x")
print("=" * 80)

flagged_1y = [item for item in comparison_data if item['mult_1y'] > 1.5]
flagged_3y = [item for item in comparison_data if item['mult_3y'] > 1.5]

if flagged_1y:
    print("\n1 Year:")
    for item in flagged_1y:
        ticker = item['ticker']

        # Calculate individual volatility and correlation
        stock_returns = returns_1y[ticker]
        stock_vol = stock_returns.std() * np.sqrt(252) * 100

        correlations = returns_1y.corr()[ticker]
        other_stocks = [t for t in tickers_ordered if t != ticker]
        avg_corr = correlations[other_stocks].mean()

        print(f"  {ticker}:")
        print(f"    Portfolio weight: {item['weight_pct']:.1f}%")
        print(f"    Risk contribution: {item['risk_1y_pct']:.1f}%")
        print(f"    Multiplier: {item['mult_1y']:.2f}x")
        print(f"    Individual volatility: {stock_vol:.1f}%")
        print(f"    Avg correlation with other stocks: {avg_corr:.3f}")
else:
    print("\n1 Year: No stocks have multiplier > 1.5x")

if flagged_3y:
    print("\n3 Years:")
    for item in flagged_3y:
        ticker = item['ticker']

        # Calculate individual volatility and correlation
        stock_returns = returns_3y[ticker]
        stock_vol = stock_returns.std() * np.sqrt(252) * 100

        correlations = returns_3y.corr()[ticker]
        other_stocks = [t for t in tickers_ordered if t != ticker]
        avg_corr = correlations[other_stocks].mean()

        print(f"  {ticker}:")
        print(f"    Portfolio weight: {item['weight_pct']:.1f}%")
        print(f"    Risk contribution: {item['risk_3y_pct']:.1f}%")
        print(f"    Multiplier: {item['mult_3y']:.2f}x")
        print(f"    Individual volatility: {stock_vol:.1f}%")
        print(f"    Avg correlation with other stocks: {avg_corr:.3f}")
else:
    print("\n3 Years: No stocks have multiplier > 1.5x")

# ============================================================================
# DIVERSIFIERS (Multiplier < 0.5x)
# ============================================================================
print("\n" + "=" * 80)
print("STOCKS ACTING AS DIVERSIFIERS (Multiplier < 0.5x)")
print("=" * 80)

diversifiers_1y = [item for item in comparison_data if item['mult_1y'] < 0.5]
diversifiers_3y = [item for item in comparison_data if item['mult_3y'] < 0.5]

if diversifiers_1y:
    print("\n1 Year:")
    for item in diversifiers_1y:
        print(f"  {item['ticker']}: {item['weight_pct']:.1f}% of money, {item['risk_1y_pct']:.1f}% of risk ({item['mult_1y']:.2f}x)")
else:
    print("\n1 Year: No stocks acting as strong diversifiers")

if diversifiers_3y:
    print("\n3 Years:")
    for item in diversifiers_3y:
        print(f"  {item['ticker']}: {item['weight_pct']:.1f}% of money, {item['risk_3y_pct']:.1f}% of risk ({item['mult_3y']:.2f}x)")
else:
    print("\n3 Years: No stocks acting as strong diversifiers")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

# Top 3 risk contributors
top_3_1y = sum(sorted([item['risk_1y_pct'] for item in comparison_data], reverse=True)[:3])
top_3_3y = sum(sorted([item['risk_3y_pct'] for item in comparison_data], reverse=True)[:3])

print(f"\nTop 3 stocks account for:")
print(f"  1 year:  {top_3_1y:.1f}% of total portfolio risk")
print(f"  3 years: {top_3_3y:.1f}% of total portfolio risk")

# Individual volatilities
print("\n" + "-" * 80)
print("Individual stock volatilities:")
print("-" * 80)

vol_data_1y = []
vol_data_3y = []

for ticker in tickers_ordered:
    vol_1y_val = returns_1y[ticker].std() * np.sqrt(252) * 100
    vol_3y_val = returns_3y[ticker].std() * np.sqrt(252) * 100
    vol_data_1y.append({'ticker': ticker, 'volatility': vol_1y_val})
    vol_data_3y.append({'ticker': ticker, 'volatility': vol_3y_val})

vol_data_1y.sort(key=lambda x: x['volatility'], reverse=True)
vol_data_3y.sort(key=lambda x: x['volatility'], reverse=True)

print("\n        |  1 Year  | 3 Years |")
print("--------|----------|---------|")

for i in range(len(tickers_ordered)):
    ticker_1y = vol_data_1y[i]['ticker']
    ticker_3y = vol_data_3y[i]['ticker']
    vol_1y_val = vol_data_1y[i]['volatility']
    vol_3y_val = vol_data_3y[i]['volatility']
    print(f"{ticker_1y:6s}  | {vol_1y_val:>6.1f}% | {vol_3y_val:>6.1f}% | {ticker_3y}")

# ============================================================================
# EXPLANATION
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

Multiplier = Risk % ÷ Money %
  >1.5x = Stock contributes more risk than its weight suggests
  <0.5x = Stock acts as a diversifier, reducing overall risk
  ~1.0x = Balanced contribution

This is NOT just "weight × volatility". A highly volatile stock with low
correlation to your other holdings might contribute less risk than a moderately
volatile stock that's highly correlated with everything else.
""")

print("=" * 80)
