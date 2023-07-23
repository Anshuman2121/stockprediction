from flask import Flask, render_template, request, make_response
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
from flask_frozen import Freezer 
import sys

app = Flask(__name__)

def calculate_percentage_difference(current_price, reference_price):
    return ((current_price - reference_price) / reference_price) * 100

tickers = [
    'LT.NS', 'ONGC.NS', 'NTPC.NS', 'SBIN.NS', 'TATAMOTORS.NS', 'KOTAKBANK.NS', 'HEROMOTOCO.NS',
    'DIVISLAB.NS', 'BPCL.NS', 'ICICIBANK.NS', 'ITC.NS', 'BHARTIARTL.NS', 'APOLLOHOSP.NS',
    'ADANIENT.NS', 'MARUTI.NS', 'CIPLA.NS', 'EICHERMOT.NS', 'BAJFINANCE.NS', 'POWERGRID.NS',
    'BAJAJ-AUTO.NS', 'NESTLEIND.NS', 'TATASTEEL.NS', 'COALINDIA.NS', 'ASIANPAINT.NS',
    'SUNPHARMA.NS', 'BAJAJFINSV.NS', 'TITAN.NS', 'ADANIPORTS.NS', 'BRITANNIA.NS', 'AXISBANK.NS',
    'HDFCBANK.NS', 'UPL.NS', 'GRASIM.NS', 'LT.NS', 'DRREDDY.NS', 'INDUSINDBK.NS', 'ULTRACEMCO.NS',
    'JSWSTEEL.NS', 'SBILIFE.NS', 'M&M.NS', 'HINDALCO.NS', 'HDFCLIFE.NS', 'TECHM.NS', 'TATACONSUM.NS',
    'RELIANCE.NS', 'TCS.NS', 'WIPRO.NS', 'HCLTECH.NS', 'HINDUNILVR.NS', 'INFY.NS'
]

data_list = []
stocks_not_fetched = []

for ticker in tickers:
    try:
        ticker_yahoo = yf.Ticker(ticker)
        data = ticker_yahoo.history(period='5y')
        last_quote = data['Close'].iloc[-1]
        high_1y = data['High'].rolling(window='365D').max().iloc[-1]
        high_2y = data['High'].rolling(window='730D').max().iloc[-1]
        high_5y = data['High'].max()
        low_1y = data['Low'].rolling(window='365D').min().iloc[-1]
        low_2y = data['Low'].rolling(window='730D').min().iloc[-1]
        low_5y = data['Low'].min()

        high_1y_diff = calculate_percentage_difference(last_quote, high_1y)
        high_2y_diff = calculate_percentage_difference(last_quote, high_2y)
        high_5y_diff = calculate_percentage_difference(last_quote, high_5y)
        low_1y_diff = calculate_percentage_difference(last_quote, low_1y)
        low_2y_diff = calculate_percentage_difference(last_quote, low_2y)
        low_5y_diff = calculate_percentage_difference(last_quote, low_5y)

        short_name = ticker_yahoo.info['shortName']  # Fetch the short name (company name)
        data_list.append([
            short_name,
            f"{int(last_quote):,}",
            f"{high_1y_diff:.2f}",
            f"{high_2y_diff:.2f}",
            f"{high_5y_diff:.2f}",
            f"{low_1y_diff:.2f}",
            f"{low_2y_diff:.2f}",
            f"{low_5y_diff:.2f}"
        ])

    except Exception as e:
        stocks_not_fetched.append(ticker + ": " + str(e))

df = pd.DataFrame(data_list, columns=['Name', 'Current Price', '1Y High % Diff', '2Y High % Diff',
                                      '5Y High % Diff', '1Y Low % Diff', '2Y Low % Diff', '5Y Low % Diff'])

if stocks_not_fetched:
    print("\nStocks Not Fetched:")
    for stock in stocks_not_fetched:
        print(stock)

@app.route('/')
def display_table():
    # Sort the DataFrame based on the selected column (if provided in the query string)
    column = request.args.get('sort', default='Name', type=str)
    df_sorted = df.sort_values(by=column)

    # Convert the sorted DataFrame to a list of lists for passing to the template
    table_data = df_sorted.values.tolist()

    return render_template('table_template.html', table_data=table_data)

@app.route('/chart')
def display_candlestick_chart():
    symbol = "^NSEI"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=5*365)).strftime("%Y-%m-%d")
    data = yf.download(symbol, start=start_date, end=end_date)
    data.reset_index(inplace=True)
    df = pd.DataFrame({
        'time': data['Date'],
        'open': data['Open'],
        'high': data['High'],
        'low': data['Low'],
        'close': data['Close'],
        'volume': data['Volume']
    })
    df = df[df['volume'] != 0]
    df.reset_index(drop=True, inplace=True)

    num_trading_days = len(df)
    window = int(num_trading_days * 0.05)

    fig = go.Figure(data=[go.Candlestick(x=df['time'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'])])

    def calculate_ascending_channel_lines(data, window):
        highs = data['high'].rolling(window=window, min_periods=1).max()
        lows = data['low'].rolling(window=window, min_periods=1).min()
        return highs, lows

    highs, lows = calculate_ascending_channel_lines(df, window)
    swing_high_indices = highs.dropna().index
    swing_low_indices = lows.dropna().index
    slmax, intercmax = np.polyfit(swing_high_indices, highs.dropna(), 1)
    slmin, intercmin = np.polyfit(swing_low_indices, lows.dropna(), 1)

    num_future_days = 120
    last_date = pd.to_datetime(df['time'].iloc[-1])
    future_dates = [last_date + timedelta(days=i) for i in range(1, num_future_days+1)]
    upper_channel_line_future = slmax * np.arange(num_trading_days, num_trading_days + num_future_days) + intercmax
    lower_channel_line_future = slmin * np.arange(num_trading_days, num_trading_days + num_future_days) + intercmin

    fig.add_trace(go.Scatter(x=future_dates, y=lower_channel_line_future, mode='lines', line=dict(color='red', dash='dash'), name='Lower Channel Line (Future)'))
    fig.add_trace(go.Scatter(x=future_dates, y=upper_channel_line_future, mode='lines', line=dict(color='blue', dash='dash'), name='Upper Channel Line (Future)'))
    fig.add_trace(go.Scatter(x=df['time'], y=slmin*np.arange(num_trading_days) + intercmin, mode='lines', line=dict(color='red'), name='Lower Channel Line'))
    fig.add_trace(go.Scatter(x=df['time'], y=slmax*np.arange(num_trading_days) + intercmax, mode='lines', line=dict(color='blue'), name='Upper Channel Line'))

    fig.update_layout(
        # title="Candlestick Chart for ^NSEI",
        xaxis_title="Date",
        yaxis_title="Price",
        margin=dict(l=50, r=50, t=50, b=50),  # Adjust margins for better visualization
        autosize=True, 
        # height=800, 
    )

    chart_div = fig.to_html(full_html=False, include_plotlyjs='cdn')
    response = app.make_response(render_template('candlestick_chart_template.html', chart_div=chart_div))
    response.headers['Content-Type'] = 'text/html; charset=utf-8'

    return response

if __name__ == '__main__':
    freezer = Freezer(app)

    if len(sys.argv) > 1 and sys.argv[1] == 'freeze':
        freezer.freeze()
    else:
        app.run(debug=True)

# if __name__ == '__main__':
#     app.run(debug=True)