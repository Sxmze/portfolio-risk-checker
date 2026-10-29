import yfinance as yf
import pandas as pd

# Download NOW data
print("Downloading ServiceNow (NOW) data...")
now_stock = yf.Ticker("NOW")
data = now_stock.history(period="1y")

if data.empty:
    print("No data found!")
else:
    # Calculate daily returns
    data['Return'] = data['Close'].pct_change()

    # Find biggest drops
    print("\n=== NOW's 10 Biggest One-Day Drops ===")
    biggest_drops = data.nsmallest(10, 'Return')[['Close', 'Return']]

    for date, row in biggest_drops.iterrows():
        print(f"{date.date()}: Price ${row['Close']:.2f}, Drop: {row['Return']*100:.2f}%")

    # Check for splits
    print("\n=== Stock Split Information ===")
    splits = now_stock.splits
    if len(splits) > 0:
        print("Splits found in data:")
        print(splits)
    else:
        print("No splits found in the data period")

    # Show recent prices
    print("\n=== Recent Prices (Last 5 Days) ===")
    recent = data[['Close']].tail()
    print(recent)

    # Check if data is adjusted
    print("\n=== Data Adjustment Status ===")
    print("yfinance automatically downloads adjusted close prices")
    print("(adjusted for splits and dividends)")
