import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import numpy as np

symbol = "INFY.NS"
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

# Calculate the number of trading days within the date range
num_trading_days = len(df)

# Determine the window size based on the number of trading days
window = int(num_trading_days * 0.05)  # Set the window to 5% of the number of trading days

# Plot the candlestick chart
fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'])])

# Function to calculate the ascending channel lines
def calculate_ascending_channel_lines(data, window):
    highs = data['high'].rolling(window=window, min_periods=1).max()
    lows = data['low'].rolling(window=window, min_periods=1).min()
    return highs, lows

# Add ascending channel lines to the plot
highs, lows = calculate_ascending_channel_lines(df, window)

# Get the indices of the swing highs and swing lows
swing_high_indices = highs.dropna().index
swing_low_indices = lows.dropna().index

# Calculate the slope and intercept for the upper and lower channel lines
slmax, intercmax = np.polyfit(swing_high_indices, highs.dropna(), 1)
slmin, intercmin = np.polyfit(swing_low_indices, lows.dropna(), 1)

# Plot the channel lines
fig.add_trace(go.Scatter(x=df.index, y=slmin*df.index + intercmin, mode='lines', line=dict(color='red'), name='Lower Channel Line'))
fig.add_trace(go.Scatter(x=df.index, y=slmax*df.index + intercmax, mode='lines', line=dict(color='blue'), name='Upper Channel Line'))

fig.show()