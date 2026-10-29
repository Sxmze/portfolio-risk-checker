"""
Stock Portfolio Risk Checker
A simple tool to analyze the risk level of your stock portfolio
"""

import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
import sys
from datetime import datetime, timedelta

# File where we save your portfolio
PORTFOLIO_FILE = "portfolio.json"
EXAMPLE_FILE = "portfolio.example.json"

# Demo mode: set to True to hide share counts and dollar values
DEMO_MODE = False

# Check for --demo flag
if "--demo" in sys.argv:
    DEMO_MODE = True
    print("Running in DEMO MODE (percentages only, no dollar values)")


def load_portfolio():
    """Load your saved portfolio from file, or use example if none exists"""
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, 'r') as f:
            return json.load(f)
    elif os.path.exists(EXAMPLE_FILE):
        print(f"No {PORTFOLIO_FILE} found. Loading example portfolio from {EXAMPLE_FILE}")
        print("(Add your own stocks to create your personal portfolio)\n")
        with open(EXAMPLE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_portfolio(portfolio):
    """Save your portfolio to a file so you don't lose it"""
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(portfolio, f, indent=2)
    print(f"✓ Portfolio saved to {PORTFOLIO_FILE}")


def add_stock(portfolio):
    """Add a new stock to your portfolio"""
    print("\n--- Add Stock ---")
    ticker = input("Enter stock ticker (e.g., AAPL, MSFT, GOOGL): ").upper().strip()

    if not ticker:
        print("No ticker entered.")
        return

    try:
        shares = float(input(f"How many shares of {ticker} do you own? "))
        if shares <= 0:
            print("Please enter a positive number of shares.")
            return
    except ValueError:
        print("Invalid number. Please enter a valid number of shares.")
        return

    portfolio[ticker] = shares
    save_portfolio(portfolio)
    print(f"✓ Added {shares} shares of {ticker}")


def view_portfolio(portfolio):
    """Show all stocks in your portfolio"""
    if not portfolio:
        print("\nYour portfolio is empty. Add some stocks first!")
        return

    print("\n--- Your Portfolio ---")
    for ticker, shares in portfolio.items():
        if DEMO_MODE:
            print(f"{ticker}: [HIDDEN] shares")
        else:
            print(f"{ticker}: {shares} shares")


def get_stock_data(ticker, period="1y"):
    """
    Download historical price data for a stock
    period="1y" means get the last year of data
    """
    try:
        stock = yf.Ticker(ticker)
        # Get historical prices (Close = closing price each day)
        data = stock.history(period=period)

        if data.empty:
            print(f"⚠ Warning: No data found for {ticker}")
            return None

        return data['Close']  # Return just the closing prices
    except Exception as e:
        print(f"⚠ Error downloading {ticker}: {e}")
        return None


def calculate_returns(prices):
    """
    Calculate daily returns (percentage change from day to day)
    Returns show how much the stock went up or down each day
    """
    # pct_change() calculates percentage change between each day
    # Example: if price goes from $100 to $102, return is 0.02 (2%)
    return prices.pct_change().dropna()


def calculate_volatility(returns):
    """
    Calculate volatility (risk measure)
    Volatility = standard deviation of returns
    Higher volatility = more risky (price jumps around more)
    We annualize it by multiplying by sqrt(252) because there are ~252 trading days per year
    """
    return returns.std() * np.sqrt(252)


def calculate_var(returns, confidence=0.95):
    """
    Calculate Value at Risk (VaR)
    VaR answers: "How much could I lose on a bad day?"
    confidence=0.95 means we're looking at the worst 5% of days
    """
    return np.percentile(returns, (1 - confidence) * 100)


def analyze_portfolio(portfolio):
    """Main analysis function - calculates risk for your entire portfolio"""
    if not portfolio:
        print("\nYour portfolio is empty. Add some stocks first!")
        return

    print("\n--- Analyzing Portfolio Risk ---")
    print("Downloading stock data... (this may take a moment)\n")

    # Step 1: Download price data for all stocks
    all_prices = {}
    all_returns = {}

    for ticker in portfolio.keys():
        print(f"Fetching {ticker}...")
        prices = get_stock_data(ticker)

        if prices is not None and len(prices) > 1:
            all_prices[ticker] = prices
            all_returns[ticker] = calculate_returns(prices)

    if not all_prices:
        print("\n⚠ Could not fetch data for any stocks. Please check your tickers.")
        return

    # Show data freshness
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

    # Step 2: Calculate current portfolio value
    print("\n--- Current Portfolio Value ---")
    total_value = 0
    stock_values = {}

    for ticker, shares in portfolio.items():
        if ticker in all_prices:
            current_price = all_prices[ticker].iloc[-1]  # Most recent price
            value = current_price * shares
            stock_values[ticker] = value
            total_value += value

            if DEMO_MODE:
                # Show percentages only in demo mode
                pct = (value / total_value * 100) if total_value > 0 else 0
                print(f"{ticker}: [HIDDEN] shares × $[HIDDEN] = [will show as %]")
            else:
                print(f"{ticker}: {shares} shares × ${current_price:.2f} = ${value:.2f}")

    if DEMO_MODE:
        # Recalculate and show percentages after total is known
        print("\nPortfolio weights:")
        for ticker, value in stock_values.items():
            pct = (value / total_value) * 100
            print(f"  {ticker}: {pct:.1f}%")
        print(f"\nTotal Portfolio Value: $[HIDDEN]")
    else:
        print(f"\nTotal Portfolio Value: ${total_value:.2f}")

    # Step 3: Calculate individual stock risk
    print("\n--- Individual Stock Risk ---")
    print("(Volatility shows how much the stock price bounces around)")
    print("(Lower = more stable, Higher = more risky)\n")

    for ticker in portfolio.keys():
        if ticker in all_returns:
            volatility = calculate_volatility(all_returns[ticker])
            var_95 = calculate_var(all_returns[ticker])

            # Classify risk level
            if volatility < 0.20:
                risk_level = "LOW"
            elif volatility < 0.40:
                risk_level = "MEDIUM"
            else:
                risk_level = "HIGH"

            print(f"{ticker}:")
            print(f"  Volatility: {volatility*100:.1f}% (annual) - {risk_level} RISK")
            print(f"  Bad Day Loss: {var_95*100:.1f}% (worst 5% of days)")
            print()

    # Step 4: Calculate portfolio-level risk
    print("--- Overall Portfolio Risk ---")

    # Create a DataFrame with all returns aligned by date
    returns_df = pd.DataFrame(all_returns)

    # Calculate portfolio weights (what % of your money is in each stock)
    weights = {}
    for ticker in returns_df.columns:
        if ticker in stock_values:
            weights[ticker] = stock_values[ticker] / total_value

    # Calculate weighted average return for each day
    portfolio_returns = pd.Series(0, index=returns_df.index)
    for ticker in returns_df.columns:
        if ticker in weights:
            portfolio_returns += returns_df[ticker] * weights[ticker]

    # Calculate portfolio volatility
    portfolio_volatility = calculate_volatility(portfolio_returns)
    portfolio_var = calculate_var(portfolio_returns)

    # Classify overall portfolio risk
    if portfolio_volatility < 0.15:
        overall_risk = "LOW"
    elif portfolio_volatility < 0.25:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "HIGH"

    print(f"Portfolio Volatility: {portfolio_volatility*100:.1f}% (annual)")
    print(f"Overall Risk Level: {overall_risk}")
    print(f"\nOn a bad day (worst 5%), your portfolio could drop by: {portfolio_var*100:.1f}%")

    if DEMO_MODE:
        print(f"That would be a loss of approximately: $[HIDDEN]")
    else:
        print(f"That would be a loss of approximately: ${total_value * portfolio_var:.2f}")

    # Diversification insight
    print("\n--- Diversification Check ---")
    num_stocks = len(portfolio)
    if num_stocks == 1:
        print("⚠ You only have 1 stock - consider diversifying to reduce risk!")
    elif num_stocks < 5:
        print(f"You have {num_stocks} stocks - adding more could help reduce risk.")
    else:
        print(f"✓ You have {num_stocks} stocks - good diversification!")


def remove_stock(portfolio):
    """Remove a stock from your portfolio"""
    if not portfolio:
        print("\nYour portfolio is empty.")
        return

    print("\n--- Remove Stock ---")
    view_portfolio(portfolio)
    ticker = input("\nEnter ticker to remove: ").upper().strip()

    if ticker in portfolio:
        del portfolio[ticker]
        save_portfolio(portfolio)
        print(f"✓ Removed {ticker} from portfolio")
    else:
        print(f"{ticker} not found in portfolio.")


def main():
    """Main program loop - shows menu and handles user choices"""
    portfolio = load_portfolio()

    print("=" * 50)
    print("  STOCK PORTFOLIO RISK CHECKER")
    print("=" * 50)

    while True:
        print("\n--- Menu ---")
        print("1. Add stock")
        print("2. View portfolio")
        print("3. Analyze risk")
        print("4. Remove stock")
        print("5. Exit")

        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == "1":
            add_stock(portfolio)
        elif choice == "2":
            view_portfolio(portfolio)
        elif choice == "3":
            analyze_portfolio(portfolio)
        elif choice == "4":
            remove_stock(portfolio)
        elif choice == "5":
            print("\nGoodbye! Your portfolio has been saved.")
            break
        else:
            print("Invalid choice. Please enter 1-5.")


if __name__ == "__main__":
    main()
