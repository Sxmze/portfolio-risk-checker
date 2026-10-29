import yfinance as yf
import pandas as pd
import numpy as np
import json

# Load portfolio
with open('portfolio.json', 'r') as f:
    portfolio = json.load(f)

print("=" * 70)
print("DETAILED PORTFOLIO CORRELATION & VOLATILITY ANALYSIS")
print("=" * 70)

# Step 1: Download all price data
print("\nStep 1: Downloading price data for all stocks...")
all_prices = {}
all_returns = {}

for ticker in portfolio.keys():
    print(f"  Fetching {ticker}...")
    stock = yf.Ticker(ticker)
    prices = stock.history(period="1y")['Close']
    if len(prices) > 1:
        all_prices[ticker] = prices
        all_returns[ticker] = prices.pct_change().dropna()

# Create DataFrame with all returns aligned by date
returns_df = pd.DataFrame(all_returns)

# Step 2: Show correlation matrix
print("\n" + "=" * 70)
print("CORRELATION MATRIX (how stocks move together)")
print("=" * 70)
print("1.0 = perfect correlation (move exactly together)")
print("0.0 = no correlation (move independently)")
print("-1.0 = perfect negative correlation (move opposite)")
print()

correlation_matrix = returns_df.corr()
print(correlation_matrix.round(3))

# Highlight strong correlations
print("\n--- Strong Correlations (>0.7) ---")
for i in range(len(correlation_matrix.columns)):
    for j in range(i+1, len(correlation_matrix.columns)):
        corr = correlation_matrix.iloc[i, j]
        if corr > 0.7:
            print(f"{correlation_matrix.columns[i]} <-> {correlation_matrix.columns[j]}: {corr:.3f}")

print("\n--- Weak Correlations (<0.3) ---")
for i in range(len(correlation_matrix.columns)):
    for j in range(i+1, len(correlation_matrix.columns)):
        corr = correlation_matrix.iloc[i, j]
        if corr < 0.3:
            print(f"{correlation_matrix.columns[i]} <-> {correlation_matrix.columns[j]}: {corr:.3f}")

# Step 3: Calculate current portfolio value and weights
print("\n" + "=" * 70)
print("PORTFOLIO WEIGHTS CALCULATION")
print("=" * 70)

stock_values = {}
for ticker in portfolio.keys():
    if ticker in all_prices:
        current_price = all_prices[ticker].iloc[-1]
        shares = portfolio[ticker]
        value = current_price * shares
        stock_values[ticker] = value
        print(f"{ticker}: {shares} shares × ${current_price:.2f} = ${value:,.2f}")

total_value = sum(stock_values.values())
print(f"\nTotal Portfolio Value: ${total_value:,.2f}")

print("\n--- Portfolio Weights (% of total) ---")
weights = {}
weights_array = []
for ticker in returns_df.columns:
    if ticker in stock_values:
        weight = stock_values[ticker] / total_value
        weights[ticker] = weight
        weights_array.append(weight)
        print(f"{ticker}: {weight*100:.2f}%")

weights_array = np.array(weights_array)

# Step 4: Calculate individual stock volatilities
print("\n" + "=" * 70)
print("INDIVIDUAL STOCK VOLATILITIES")
print("=" * 70)
print("(These are the diagonal elements if we only looked at individual variance)")
print()

individual_vols = {}
for ticker in returns_df.columns:
    daily_vol = returns_df[ticker].std()
    annual_vol = daily_vol * np.sqrt(252)
    individual_vols[ticker] = annual_vol
    print(f"{ticker}: {annual_vol*100:.2f}% annual volatility")

# Step 5: Calculate covariance matrix
print("\n" + "=" * 70)
print("COVARIANCE MATRIX (daily)")
print("=" * 70)
print("This measures how stock returns vary together")
print("Diagonal = variance of each stock")
print("Off-diagonal = covariance between pairs")
print()

cov_matrix = returns_df.cov()
print(cov_matrix.round(6))

# Step 6: Calculate portfolio variance step by step
print("\n" + "=" * 70)
print("PORTFOLIO VOLATILITY CALCULATION (STEP BY STEP)")
print("=" * 70)

print("\nFormula: Portfolio Variance = w^T × Σ × w")
print("  where w = weights vector")
print("        Σ = covariance matrix")
print()

print("Step 6a: Weights vector (as column)")
print(weights_array)
print()

print("Step 6b: Calculate (Σ × w) - multiply covariance matrix by weights")
cov_times_w = cov_matrix.values @ weights_array
print(cov_times_w)
print()

print("Step 6c: Calculate w^T × (Σ × w) - final portfolio variance")
portfolio_variance_daily = weights_array @ cov_times_w
print(f"Daily Portfolio Variance = {portfolio_variance_daily:.8f}")
print()

print("Step 6d: Portfolio standard deviation (daily)")
portfolio_std_daily = np.sqrt(portfolio_variance_daily)
print(f"Daily Portfolio Std Dev = {portfolio_std_daily:.6f} = {portfolio_std_daily*100:.4f}%")
print()

print("Step 6e: Annualize (multiply by sqrt(252 trading days))")
portfolio_volatility_annual = portfolio_std_daily * np.sqrt(252)
print(f"Annual Portfolio Volatility = {portfolio_std_daily:.6f} × {np.sqrt(252):.4f}")
print(f"                            = {portfolio_volatility_annual:.6f}")
print(f"                            = {portfolio_volatility_annual*100:.2f}%")

# Step 7: Compare to naive weighted average
print("\n" + "=" * 70)
print("COMPARISON: Naive vs Actual Portfolio Risk")
print("=" * 70)

naive_volatility = sum(weights[ticker] * individual_vols[ticker] for ticker in returns_df.columns)
print(f"\nNaive (weighted average): {naive_volatility*100:.2f}%")
print("  This assumes all stocks move independently (correlation = 0)")
print()
print(f"Actual portfolio volatility: {portfolio_volatility_annual*100:.2f}%")
print("  This accounts for how stocks move together")
print()

if portfolio_volatility_annual > naive_volatility:
    print(f"Difference: +{(portfolio_volatility_annual - naive_volatility)*100:.2f}%")
    print("Your stocks are positively correlated, increasing overall risk!")
else:
    print(f"Difference: {(portfolio_volatility_annual - naive_volatility)*100:.2f}%")
    print("Your stocks have some diversification benefit!")

# Step 8: Verification using pandas built-in
print("\n" + "=" * 70)
print("VERIFICATION CHECK")
print("=" * 70)

# Calculate portfolio returns
portfolio_returns = (returns_df * weights_array).sum(axis=1)
verification_vol = portfolio_returns.std() * np.sqrt(252)

print(f"\nMethod 1 (matrix algebra): {portfolio_volatility_annual*100:.2f}%")
print(f"Method 2 (weighted returns): {verification_vol*100:.2f}%")
print(f"Difference: {abs(portfolio_volatility_annual - verification_vol)*100:.4f}%")

if abs(portfolio_volatility_annual - verification_vol) < 0.0001:
    print("\n✓ MATH VERIFIED - Both methods match!")
else:
    print("\n⚠ WARNING - Methods don't match. Check calculation.")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Your portfolio volatility is {portfolio_volatility_annual*100:.2f}% annually")
print(f"Average correlation between stocks: {correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean():.3f}")
print(f"Diversification benefit: {(naive_volatility - portfolio_volatility_annual)*100:.2f}% reduction")
