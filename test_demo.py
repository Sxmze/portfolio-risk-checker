"""
Quick demo of the portfolio risk checker in demo mode
"""
import sys
sys.argv.append('--demo')

# Import and run the load function
from portfolio_risk import load_portfolio, DEMO_MODE

print("=" * 70)
print("DEMO MODE TEST")
print("=" * 70)

portfolio = load_portfolio()

print(f"\nDemo mode enabled: {DEMO_MODE}")
print(f"\nLoaded portfolio with {len(portfolio)} stocks:")

for ticker, shares in portfolio.items():
    if DEMO_MODE:
        print(f"  {ticker}: [HIDDEN] shares")
    else:
        print(f"  {ticker}: {shares} shares")

print("\nIn demo mode:")
print("  ✓ Share counts are hidden")
print("  ✓ Dollar values are hidden")
print("  ✓ Only percentages are shown in analysis")
print("\nTo run the full program in demo mode:")
print("  python portfolio_risk.py --demo")
