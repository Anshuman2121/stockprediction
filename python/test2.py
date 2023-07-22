import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

symbol = "AAPL"
start_date = "2018-05-05"
end_date = "2023-05-16"
data = yf.download(symbol, start=start_date, end=end_date)

# Reset the index to turn the date into a column
data.reset_index(inplace=True)

# Create a new DataFrame with the correct column names and data types
df = pd.DataFrame({
    'time': data['Date'],
    'open': data['Open'],
    'high': data['High'],
    'low': data['Low'],
    'close': data['Close'],
    'volume': data['Volume']
})

# Check if NA values are in data
df = df[df['volume'] != 0]
df.reset_index(drop=True, inplace=True)
df.isna().sum()
df.head(10)

# Plot the candlestick chart
fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'])])

fig.show()
