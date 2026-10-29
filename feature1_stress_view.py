"""
Feature 1: Stress View
Shows how your portfolio behaves during market crashes
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
print("PORTFOLIO STRESS TEST")
print("=" * 80)

# Step 1: Download all stock data
print("\nDownloading data...")
all_prices = {}
all_returns = {}

for ticker in portfolio.keys():
    stock = yf.Ticker(ticker)
    prices = stock.history(period="1y")['Close']
    if len(prices) > 1:
        all_prices[ticker] = prices
        all_returns[ticker] = prices.pct_change().dropna()

# Download SPY (S&P 500 index) for market comparison
spy = yf.Ticker("SPY")
spy_prices = spy.history(period="1y")['Close']
spy_returns = spy_prices.pct_change().dropna()

# Create aligned DataFrames
returns_df = pd.DataFrame(all_returns)
most_recent = max(prices.index[-1] for prices in all_prices.values())

print(f"Data as of: {most_recent.strftime('%Y-%m-%d %I:%M %p %Z')}")
print(f"Analysis period: {returns_df.index[0].date()} to {returns_df.index[-1].date()}")
print(f"Total trading days: {len(returns_df)}")

# Step 2: Calculate portfolio weights and daily returns
print("\n" + "=" * 80)
print("CALCULATING PORTFOLIO DAILY RETURNS")
print("=" * 80)

# Get current values and weights
stock_values = {}
total_value = 0
for ticker in portfolio.keys():
    if ticker in all_prices:
        current_price = all_prices[ticker].iloc[-1]
        value = current_price * portfolio[ticker]
        stock_values[ticker] = value
        total_value += value

weights = {}
for ticker in returns_df.columns:
    weights[ticker] = stock_values[ticker] / total_value

print("\nPortfolio weights:")
for ticker, weight in weights.items():
    print(f"  {ticker}: {weight*100:.2f}%")

# Calculate portfolio daily returns (weighted sum)
portfolio_returns = pd.Series(0, index=returns_df.index)
for ticker in returns_df.columns:
    portfolio_returns += returns_df[ticker] * weights[ticker]

print(f"\nPortfolio mean daily return: {portfolio_returns.mean()*100:.3f}%")
print(f"Portfolio daily volatility: {portfolio_returns.std()*100:.3f}%")

# Step 3: Find 5 worst days
print("\n" + "=" * 80)
print("5 WORST DAYS FOR YOUR PORTFOLIO")
print("=" * 80)

worst_days = portfolio_returns.nsmallest(5)

for date, ret in worst_days.items():
    # Calculate dollar loss
    dollar_loss = total_value * ret
    print(f"\n{date.date()} ({date.strftime('%A')})")
    print(f"  Portfolio loss: {ret*100:.2f}%")
    print(f"  Dollar loss: ${dollar_loss:,.2f}")
    print(f"  What happened to each stock:")
    for ticker in returns_df.columns:
        stock_ret = returns_df.loc[date, ticker]
        print(f"    {ticker}: {stock_ret*100:>+7.2f}%")

# Step 4: Find worst 1-month period (21 trading days)
print("\n" + "=" * 80)
print("WORST 1-MONTH PERIOD (21 Trading Days)")
print("=" * 80)

# Calculate rolling 21-day returns
rolling_21d = portfolio_returns.rolling(window=21).sum()

# Find the worst
worst_idx = rolling_21d.idxmin()
worst_21d_return = rolling_21d.min()

# Find start date (21 days before worst_idx)
worst_idx_loc = portfolio_returns.index.get_loc(worst_idx)
start_idx = max(0, worst_idx_loc - 20)
start_date = portfolio_returns.index[start_idx]

print(f"\nWorst 21-day period: {start_date.date()} to {worst_idx.date()}")
print(f"Cumulative return: {worst_21d_return*100:.2f}%")
print(f"Dollar loss: ${total_value * worst_21d_return:,.2f}")

# Show the daily returns during that period
print(f"\nDaily breakdown:")
period_returns = portfolio_returns.loc[start_date:worst_idx]
for date, ret in period_returns.items():
    print(f"  {date.date()}: {ret*100:>+6.2f}%")

# Step 5: Crisis correlations (using SPY's worst 10% days)
print("\n" + "=" * 80)
print("CRISIS CORRELATIONS (During Market's Worst 10% of Days)")
print("=" * 80)

# Align SPY returns with our stock returns
spy_aligned = spy_returns.reindex(returns_df.index).dropna()

# Find SPY's worst 10% of days
spy_10th_percentile = spy_aligned.quantile(0.10)
crisis_days = spy_aligned[spy_aligned <= spy_10th_percentile].index

print(f"\nSPY 10th percentile return: {spy_10th_percentile*100:.2f}%")
print(f"Number of crisis days: {len(crisis_days)} out of {len(returns_df)} days")
print(f"Crisis days are when SPY dropped more than {spy_10th_percentile*100:.2f}%")

# Calculate correlations on normal days vs crisis days
normal_days = returns_df.index.difference(crisis_days)
normal_corr = returns_df.loc[normal_days].corr()
crisis_corr = returns_df.loc[crisis_days].corr()

# Show comparison for key pairs
print("\n" + "=" * 80)
print("CORRELATION COMPARISON: Normal Days vs Crisis Days")
print("=" * 80)
print("\nFormat: Stock1 <-> Stock2: Normal | Crisis | Difference")
print("-" * 80)

# Calculate average correlations
normal_avg = normal_corr.values[np.triu_indices_from(normal_corr.values, k=1)].mean()
crisis_avg = crisis_corr.values[np.triu_indices_from(crisis_corr.values, k=1)].mean()

print(f"\nAVERAGE CORRELATION ACROSS ALL PAIRS:")
print(f"  Normal days:  {normal_avg:.3f}")
print(f"  Crisis days:  {crisis_avg:.3f}")
print(f"  Difference:   {crisis_avg - normal_avg:+.3f}")

# Show top 10 pairs with biggest correlation increase during crisis
print("\n" + "=" * 80)
print("TOP 10 PAIRS: Biggest Correlation Increase During Crisis")
print("=" * 80)

correlation_changes = []
for i in range(len(normal_corr.columns)):
    for j in range(i+1, len(normal_corr.columns)):
        stock1 = normal_corr.columns[i]
        stock2 = normal_corr.columns[j]
        normal_val = normal_corr.iloc[i, j]
        crisis_val = crisis_corr.iloc[i, j]
        change = crisis_val - normal_val
        correlation_changes.append({
            'pair': f"{stock1} <-> {stock2}",
            'normal': normal_val,
            'crisis': crisis_val,
            'change': change
        })

# Sort by biggest increase
correlation_changes.sort(key=lambda x: x['change'], reverse=True)

for item in correlation_changes[:10]:
    print(f"{item['pair']:20s}: {item['normal']:>6.3f} | {item['crisis']:>6.3f} | {item['change']:>+6.3f}")

# Step 6: Plain English Summary
print("\n" + "=" * 80)
print("PLAIN ENGLISH SUMMARY")
print("=" * 80)

# Calculate insights
avg_increase = crisis_avg - normal_avg
pct_increase = ((crisis_avg / normal_avg) - 1) * 100 if normal_avg != 0 else 0

print("\nDo your stocks move more together when the market crashes?")

if avg_increase > 0.15:
    answer = "YES - SIGNIFICANTLY"
    explanation = f"Your stocks' average correlation jumps from {normal_avg:.2f} on normal days to {crisis_avg:.2f} during market crashes ({pct_increase:+.1f}% increase). This means your diversification weakens exactly when you need it most."
elif avg_increase > 0.05:
    answer = "YES - MODERATELY"
    explanation = f"Your stocks' correlation increases from {normal_avg:.2f} to {crisis_avg:.2f} during crashes ({pct_increase:+.1f}% increase). You lose some diversification benefit during bad times."
elif avg_increase > -0.05:
    answer = "ROUGHLY THE SAME"
    explanation = f"Your stocks' correlation is similar on normal days ({normal_avg:.2f}) and crisis days ({crisis_avg:.2f}). Your diversification holds up reasonably well during crashes."
else:
    answer = "NO - THEY ACTUALLY SPREAD OUT"
    explanation = f"Interestingly, your stocks' correlation DECREASES from {normal_avg:.2f} to {crisis_avg:.2f} during crashes. This is unusual and means your diversification actually improves during bad times."

print(f"\n{answer}")
print(f"\n{explanation}")

# Risk assessment
worst_day_loss_pct = worst_days.iloc[0] * 100
print(f"\nWorst single day: {worst_day_loss_pct:.2f}% loss (${total_value * worst_days.iloc[0]:,.2f})")
print(f"Worst month: {worst_21d_return*100:.2f}% loss (${total_value * worst_21d_return:,.2f})")

if worst_day_loss_pct < -5:
    print(f"\n⚠ WARNING: Your worst day was a {abs(worst_day_loss_pct):.1f}% loss. This is substantial.")
if worst_21d_return < -0.15:
    print(f"⚠ WARNING: Your worst month was a {abs(worst_21d_return*100):.1f}% loss. Prepare for volatility.")

print("\n" + "=" * 80)
