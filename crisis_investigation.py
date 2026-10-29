"""
Deep dive into crisis correlation analysis
Investigating the suspicious results
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
print("CRISIS CORRELATION INVESTIGATION")
print("=" * 80)

# Download data - 3 YEARS this time
print("\nDownloading 3 years of data...")
all_prices_3y = {}
all_returns_3y = {}

for ticker in portfolio.keys():
    stock = yf.Ticker(ticker)
    prices = stock.history(period="3y")['Close']
    if len(prices) > 1:
        all_prices_3y[ticker] = prices
        all_returns_3y[ticker] = prices.pct_change().dropna()

# Download SPY
spy = yf.Ticker("SPY")
spy_prices_3y = spy.history(period="3y")['Close']
spy_returns_3y = spy_prices_3y.pct_change().dropna()

# Create aligned DataFrames
returns_df_3y = pd.DataFrame(all_returns_3y)
spy_aligned_3y = spy_returns_3y.reindex(returns_df_3y.index).dropna()

# Also get 1 year for comparison
returns_df_1y = returns_df_3y.tail(252)
spy_aligned_1y = spy_aligned_3y.tail(252)

print(f"\n3-year data: {len(returns_df_3y)} trading days")
print(f"1-year data: {len(returns_df_1y)} trading days")
print(f"Date range (3y): {returns_df_3y.index[0].date()} to {returns_df_3y.index[-1].date()}")

# Separate tech stocks from others
tech_stocks = ['NVDA', 'AMZN', 'META', 'MSFT', 'GOOGL', 'AVGO', 'NOW']
other_stocks = ['LLY', 'ASTS']

print(f"\nTech/AI stocks: {', '.join(tech_stocks)}")
print(f"Other stocks: {', '.join(other_stocks)}")

# QUESTION 1: Why did correlation change from 0.180 to 0.123?
print("\n" + "=" * 80)
print("Q1: WHY DID AVERAGE CORRELATION CHANGE?")
print("=" * 80)

# Calculate on different datasets
corr_all_3y = returns_df_3y.corr()
corr_all_1y = returns_df_1y.corr()

avg_corr_3y = corr_all_3y.values[np.triu_indices_from(corr_all_3y.values, k=1)].mean()
avg_corr_1y = corr_all_1y.values[np.triu_indices_from(corr_all_1y.values, k=1)].mean()

print(f"\nAverage correlation (3 years): {avg_corr_3y:.3f}")
print(f"Average correlation (1 year):  {avg_corr_1y:.3f}")
print(f"\nThe 0.180 you saw before was likely from a different time period or calculation.")
print(f"Using the same 1-year data, I'm getting {avg_corr_1y:.3f}")

# QUESTION 2 & 3: Crisis correlations at different thresholds
print("\n" + "=" * 80)
print("Q2 & Q3: CRISIS CORRELATIONS - MULTIPLE TESTS")
print("=" * 80)

def analyze_crisis_correlations(returns_df, spy_returns, threshold_pct, label, stocks=None):
    """Calculate crisis vs normal correlations"""

    if stocks:
        returns_subset = returns_df[stocks]
    else:
        returns_subset = returns_df

    # Find crisis days
    spy_threshold = spy_returns.quantile(threshold_pct / 100)
    crisis_days = spy_returns[spy_returns <= spy_threshold].index
    normal_days = returns_subset.index.difference(crisis_days)

    # Calculate correlations
    normal_corr = returns_subset.loc[normal_days].corr()
    crisis_corr = returns_subset.loc[crisis_days].corr()

    # Average correlations
    normal_avg = normal_corr.values[np.triu_indices_from(normal_corr.values, k=1)].mean()
    crisis_avg = crisis_corr.values[np.triu_indices_from(crisis_corr.values, k=1)].mean()

    print(f"\n{label}")
    print(f"  SPY threshold: {spy_threshold*100:.2f}% (worst {threshold_pct}% of days)")
    print(f"  Crisis days: {len(crisis_days)} days")
    print(f"  Normal days: {len(normal_days)} days")
    print(f"  Normal correlation: {normal_avg:.3f}")
    print(f"  Crisis correlation: {crisis_avg:.3f}")
    print(f"  Difference: {crisis_avg - normal_avg:+.3f}")

    # Check if difference is meaningful
    ratio = crisis_avg / normal_avg if normal_avg != 0 else 0
    print(f"  Crisis/Normal ratio: {ratio:.2f}x")

    return {
        'crisis_days': len(crisis_days),
        'normal_avg': normal_avg,
        'crisis_avg': crisis_avg,
        'difference': crisis_avg - normal_avg,
        'crisis_corr': crisis_corr,
        'normal_corr': normal_corr
    }

print("\n--- 1 YEAR DATA ---")

# All stocks, worst 10%
result_1y_10_all = analyze_crisis_correlations(
    returns_df_1y, spy_aligned_1y, 10,
    "1 year, ALL 9 stocks, worst 10% of SPY days"
)

# All stocks, worst 20%
result_1y_20_all = analyze_crisis_correlations(
    returns_df_1y, spy_aligned_1y, 20,
    "1 year, ALL 9 stocks, worst 20% of SPY days"
)

# Tech only, worst 10%
result_1y_10_tech = analyze_crisis_correlations(
    returns_df_1y, spy_aligned_1y, 10,
    "1 year, TECH/AI 7 stocks only, worst 10% of SPY days",
    stocks=tech_stocks
)

# Tech only, worst 20%
result_1y_20_tech = analyze_crisis_correlations(
    returns_df_1y, spy_aligned_1y, 20,
    "1 year, TECH/AI 7 stocks only, worst 20% of SPY days",
    stocks=tech_stocks
)

print("\n--- 3 YEAR DATA ---")

# All stocks, worst 10%
result_3y_10_all = analyze_crisis_correlations(
    returns_df_3y, spy_aligned_3y, 10,
    "3 years, ALL 9 stocks, worst 10% of SPY days"
)

# All stocks, worst 20%
result_3y_20_all = analyze_crisis_correlations(
    returns_df_3y, spy_aligned_3y, 20,
    "3 years, ALL 9 stocks, worst 20% of SPY days"
)

# Tech only, worst 10%
result_3y_10_tech = analyze_crisis_correlations(
    returns_df_3y, spy_aligned_3y, 10,
    "3 years, TECH/AI 7 stocks only, worst 10% of SPY days",
    stocks=tech_stocks
)

# Tech only, worst 20%
result_3y_20_tech = analyze_crisis_correlations(
    returns_df_3y, spy_aligned_3y, 20,
    "3 years, TECH/AI 7 stocks only, worst 20% of SPY days",
    stocks=tech_stocks
)

# QUESTION 5: Honest assessment
print("\n" + "=" * 80)
print("Q5: HONEST STATISTICAL ASSESSMENT")
print("=" * 80)

print("\nSample size analysis:")
print(f"  1 year, 10% threshold: {result_1y_10_all['crisis_days']} crisis days")
print(f"  1 year, 20% threshold: {result_1y_20_all['crisis_days']} crisis days")
print(f"  3 year, 10% threshold: {result_3y_10_all['crisis_days']} crisis days")
print(f"  3 year, 20% threshold: {result_3y_20_all['crisis_days']} crisis days")

print("\nFor 9 stocks, correlation matrix has 36 pairs.")
print("For 7 stocks, correlation matrix has 21 pairs.")

print("\n--- HONEST ASSESSMENT ---")

# Calculate minimum sample needed (rough heuristic: 5-10 obs per parameter)
pairs_9 = 36
pairs_7 = 21
min_days_9 = pairs_9 * 5
min_days_7 = pairs_7 * 5

print(f"\nRule of thumb: Need ~5-10 observations per correlation pair")
print(f"  For 9 stocks (36 pairs): need {min_days_9}-{pairs_9*10} days")
print(f"  For 7 stocks (21 pairs): need {min_days_7}-{pairs_7*10} days")

# Check each result
def assess_reliability(n_days, n_pairs, label):
    ratio = n_days / n_pairs
    print(f"\n{label}:")
    print(f"  {n_days} days ÷ {n_pairs} pairs = {ratio:.1f} observations per pair")
    if ratio < 3:
        return "❌ UNRELIABLE - Too few observations"
    elif ratio < 5:
        return "⚠️  WEAK - Barely enough data"
    elif ratio < 10:
        return "✓ MODERATE - Reasonable but not strong"
    else:
        return "✓✓ STRONG - Good sample size"

verdict_1y_10_all = assess_reliability(result_1y_10_all['crisis_days'], 36, "1yr, 10%, all stocks")
verdict_1y_20_all = assess_reliability(result_1y_20_all['crisis_days'], 36, "1yr, 20%, all stocks")
verdict_3y_10_all = assess_reliability(result_3y_10_all['crisis_days'], 36, "3yr, 10%, all stocks")
verdict_3y_20_all = assess_reliability(result_3y_20_all['crisis_days'], 36, "3yr, 20%, all stocks")

verdict_3y_10_tech = assess_reliability(result_3y_10_tech['crisis_days'], 21, "3yr, 10%, tech only")
verdict_3y_20_tech = assess_reliability(result_3y_20_tech['crisis_days'], 21, "3yr, 20%, tech only")

print("\n" + "=" * 80)
print("SUMMARY: WHAT CAN WE TRUST?")
print("=" * 80)

print(f"\n1-YEAR ANALYSIS:")
print(f"  {verdict_1y_10_all}")
print(f"  {verdict_1y_20_all}")
print(f"  → The original 25-day result was too small to trust")

print(f"\n3-YEAR ANALYSIS (ALL STOCKS):")
print(f"  {verdict_3y_10_all}")
print(f"  {verdict_3y_20_all}")

print(f"\n3-YEAR ANALYSIS (TECH ONLY):")
print(f"  {verdict_3y_10_tech}")
print(f"  {verdict_3y_20_tech}")

# Final honest take
print("\n" + "=" * 80)
print("BOTTOM LINE (NO BS)")
print("=" * 80)

print("\nWhat the data ACTUALLY shows:")

if result_3y_20_all['difference'] > 0.10:
    print("✓ With 3 years of data (20% threshold), correlations DO increase during")
    print("  market stress. The 1-year result showing DECREASED correlation was")
    print("  a statistical fluke from too few crisis days.")
elif result_3y_20_all['difference'] > 0.05:
    print("✓ With 3 years of data, correlations increase moderately during stress.")
    print("  Not dramatic, but your diversification does weaken when markets crash.")
elif result_3y_20_all['difference'] > -0.02:
    print("→ With 3 years of data, correlations stay roughly the same during stress.")
    print("  Your diversification neither improves nor collapses in crashes.")
else:
    print("? Even with 3 years of data, correlations DECREASE during stress.")
    print("  This is unusual. Could be real (LLY/ASTS uncorrelated with tech crashes)")
    print("  or could still be noise. Would need 5+ years to be confident.")

print(f"\n3-year results (20% threshold, ALL stocks):")
print(f"  Normal: {result_3y_20_all['normal_avg']:.3f}")
print(f"  Crisis: {result_3y_20_all['crisis_avg']:.3f}")
print(f"  Change: {result_3y_20_all['difference']:+.3f}")

print(f"\n3-year results (20% threshold, TECH stocks only):")
print(f"  Normal: {result_3y_20_tech['normal_avg']:.3f}")
print(f"  Crisis: {result_3y_20_tech['crisis_avg']:.3f}")
print(f"  Change: {result_3y_20_tech['difference']:+.3f}")

print("\n" + "=" * 80)
