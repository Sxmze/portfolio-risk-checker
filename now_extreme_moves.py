import yfinance as yf
import pandas as pd

print("=" * 70)
print("NOW (ServiceNow) - Biggest One-Day Moves Analysis")
print("=" * 70)

# Download NOW data
now_stock = yf.Ticker("NOW")
data = now_stock.history(period="1y")

print(f"\nData Range: {data.index[0].date()} to {data.index[-1].date()}")
print(f"Total days: {len(data)}")
print(f"\nLast date in data: {data.index[-1]}")
print(f"Last closing price: ${data['Close'].iloc[-1]:.2f}")

# Calculate daily returns
data['Return'] = data['Close'].pct_change()

print("\n" + "=" * 70)
print("10 BIGGEST ONE-DAY DROPS")
print("=" * 70)

biggest_drops = data.nsmallest(10, 'Return')[['Close', 'Return']].sort_values('Return')

for date, row in biggest_drops.iterrows():
    print(f"{date.date()} ({date.strftime('%A'):>9}): ${row['Close']:>7.2f}  |  {row['Return']*100:>6.2f}%")

print("\n" + "=" * 70)
print("10 BIGGEST ONE-DAY GAINS")
print("=" * 70)

biggest_gains = data.nlargest(10, 'Return')[['Close', 'Return']].sort_values('Return', ascending=False)

for date, row in biggest_gains.iterrows():
    print(f"{date.date()} ({date.strftime('%A'):>9}): ${row['Close']:>7.2f}  |  +{row['Return']*100:>5.2f}%")

print("\n" + "=" * 70)
print("10 BIGGEST ABSOLUTE MOVES (Both Directions)")
print("=" * 70)

data['Abs_Return'] = data['Return'].abs()
biggest_absolute = data.nlargest(10, 'Abs_Return')[['Close', 'Return', 'Abs_Return']].sort_values('Abs_Return', ascending=False)

for date, row in biggest_absolute.iterrows():
    sign = "+" if row['Return'] > 0 else ""
    print(f"{date.date()} ({date.strftime('%A'):>9}): ${row['Close']:>7.2f}  |  {sign}{row['Return']*100:>6.2f}%  |  abs: {row['Abs_Return']*100:.2f}%")

# Show context around the biggest drop
print("\n" + "=" * 70)
print("CONTEXT: Week Around Biggest Drop (April 23, 2026: -17.75%)")
print("=" * 70)

april_drop_date = pd.Timestamp('2026-04-23')
if april_drop_date in data.index:
    # Get 5 days before and after
    drop_idx = data.index.get_loc(april_drop_date)
    context_start = max(0, drop_idx - 5)
    context_end = min(len(data), drop_idx + 6)

    context = data.iloc[context_start:context_end][['Close', 'Return']]

    for date, row in context.iterrows():
        is_drop_day = date == april_drop_date
        marker = " <<< BIGGEST DROP" if is_drop_day else ""
        sign = "+" if row['Return'] > 0 else ""
        ret_str = f"{sign}{row['Return']*100:>6.2f}%" if pd.notna(row['Return']) else "   N/A  "
        print(f"{date.date()} ({date.strftime('%A'):>9}): ${row['Close']:>7.2f}  |  {ret_str}{marker}")

# Statistics
print("\n" + "=" * 70)
print("VOLATILITY STATISTICS")
print("=" * 70)

returns_clean = data['Return'].dropna()
print(f"Mean daily return: {returns_clean.mean()*100:>6.2f}%")
print(f"Median daily return: {returns_clean.median()*100:>6.2f}%")
print(f"Std dev (daily): {returns_clean.std()*100:>6.2f}%")
print(f"Std dev (annual): {returns_clean.std()*100*15.8745:>6.2f}%")
print(f"\nDays with >10% move: {(data['Abs_Return'] > 0.10).sum()}")
print(f"Days with >5% move: {(data['Abs_Return'] > 0.05).sum()}")
print(f"Days with >3% move: {(data['Abs_Return'] > 0.03).sum()}")
