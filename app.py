from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from flask_frozen import Freezer
import sys
import os

app = Flask(__name__)
df_nifty100 = pd.read_csv('nifty100list.csv')
df_index = pd.read_csv('niftyindex.csv')

def custom_strftime(date_object):
    suffix = 'th' if 11 <= date_object.day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(date_object.day % 10, 'th')
    return date_object.strftime(f"%d{suffix} %b, %y")

today_date = custom_strftime(datetime.now())

def calculate_percentage_difference(current_price, reference_price):
    return ((current_price - reference_price) / reference_price) * 100

def fetch_ticker_data(ticker):
    try:
        ticker_yahoo = yf.Ticker(ticker)
        data = ticker_yahoo.history(period='5y')
        last_quote = data['Close'].iloc[-1]
        ma_200 = data['Close'].rolling(window=200).mean().iloc[-1]
        avg_percentage = calculate_percentage_difference(last_quote, ma_200)

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

        return [
            f"{int(last_quote):,}",
            f"{avg_percentage:.2f}",
            f"{high_1y_diff:.2f}",
            f"{high_2y_diff:.2f}",
            f"{high_5y_diff:.2f}",
            f"{low_1y_diff:.2f}",
            f"{low_2y_diff:.2f}",
            f"{low_5y_diff:.2f}"
        ]

    except Exception as e:
        return [None, None, None, None, None, None, None, None]

def read_csv_and_preprocess(filename):
    data = pd.read_csv(filename)
    data['Symbol'] = data['Symbol'] + ".NS"
    return data

def get_data_for_endpoints(data):
    data_list = []
    stocks_not_fetched = []

    # Add ^NSEI index data
    nsei_data = fetch_ticker_data("^NSEI")
    if all(data_point is not None for data_point in nsei_data):
        data_list.append([
            "^Nifty 50",
            "^Index",
            "^NSEI",
            *nsei_data
        ])
    else:
        stocks_not_fetched.append("^NSEI")

    # Add individual stock data
    for index, row in data.iterrows():
        ticker = row['Symbol']
        ticker_data = fetch_ticker_data(ticker)

        if all(data_point is not None for data_point in ticker_data):
            data_list.append([
                row['Company Name'],
                row['Industry'],
                row['Symbol'],
                *ticker_data
            ])
        else:
            stocks_not_fetched.append(row['Symbol'])

    return pd.DataFrame(data_list, columns=['Name', 'Industry', 'Symbol', 'Current Price', '200 DMA Avg', '1Y High % Diff', '2Y High % Diff', '5Y High % Diff', '1Y Low % Diff', '2Y Low % Diff', '5Y Low % Diff']), stocks_not_fetched

def get_financial_data(symbol):
    try:
        stock_info = yf.Ticker(symbol)
        eps = stock_info.info.get('trailingEps', 'N/A')
        pe_ratio = stock_info.info.get('trailingPE', 'N/A')
        book_value = stock_info.info.get('bookValue', 'N/A')  # Add this line for Book Value
        revenue = stock_info.info.get('totalRevenue', 'N/A')
        analyst_recommendation_mean = stock_info.info.get('recommendationMean', 'N/A')
        analyst_recommendation_key = stock_info.info.get('recommendationKey', 'N/A')
        return eps, pe_ratio, revenue, analyst_recommendation_mean, analyst_recommendation_key, book_value
    except Exception as e:
        print(f"Failed to fetch financial data for {symbol}: {e}")
        return 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'


def process_data_and_plot_chart(symbol, info_text_enabled=True):
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=5 * 365)).strftime("%Y-%m-%d")
    data = yf.download(symbol, start=start_date, end=end_date)
    data.reset_index(inplace=True)

    # Create DataFrame
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

    # Calculate channel lines outside the function
    highs, lows = df['high'].rolling(window=int(len(df) * 0.05), min_periods=1).max(), df['low'].rolling(
        window=int(len(df) * 0.05), min_periods=1).min()
    swing_high_indices, swing_low_indices = highs.dropna().index, lows.dropna().index
    support, resistance = np.polyfit(swing_low_indices, lows.dropna(), 1), np.polyfit(swing_high_indices,
                                                                                    highs.dropna(), 1)

    if info_text_enabled:
        fig, axs = plt.subplots(2, 1, figsize=(10, 9), gridspec_kw={'height_ratios': [3, 1]})
        ax_price, ax_pe_ratio = axs
    else:
        fig, ax_price = plt.subplots(figsize=(10, 6))

    ax_price.plot(df['time'], df['open'], linestyle='-', color='#663300')
    ax_price.plot(df['time'], df['close'], linestyle='-', color='#663300')
    ax_price.vlines(df['time'], df['low'], df['high'], color='#663300', linewidth=.1)
    ax_price.legend()

    # Plot support and resistance lines
    num_future_days = 120
    last_date = pd.to_datetime(df['time'].iloc[-1])
    future_dates = [last_date + timedelta(days=i) for i in range(1, num_future_days + 1)]
    support_line_future = support[0] * np.arange(len(df), len(df) + num_future_days) + support[1]
    resistance_line_future = resistance[0] * np.arange(len(df), len(df) + num_future_days) + resistance[1]

    ax_price.plot(future_dates, support_line_future, linestyle='--', color='green')
    ax_price.plot(future_dates, resistance_line_future, linestyle='--', color='orange')
    ax_price.plot(df['time'], support[0] * np.arange(len(df)) + support[1], linestyle='-', color='green')
    ax_price.plot(df['time'], resistance[0] * np.arange(len(df)) + resistance[1], linestyle='-', color='orange')

    if info_text_enabled:
        current_price = df['close'].iloc[-1]
        eps, pe_ratio, revenue, analyst_recommendation_mean, analyst_recommendation_key, book_value = get_financial_data(symbol)

        # Convert revenue to crores
        revenue_in_crores = revenue / 1e7

        info_text = f'Current Value: {current_price:.2f}\n' \
            f'P/E Ratio: {pe_ratio}\n' \
            f'Book Value: {book_value}\n' \
            f'EPS: {eps}\n' \
            f'Advice|Mean: {analyst_recommendation_key}|{analyst_recommendation_mean}'

        bbox_props = dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="#ffe6e6", alpha=0.7)
        ax_price.text(0.02, 0.98, info_text, transform=ax_price.transAxes, fontsize=10, verticalalignment='top', bbox=bbox_props,
                fontfamily='sans-serif', color='#002699')

    # Set labels and title
    ax_price.set_xlabel("Date")
    ax_price.set_ylabel("Price")
    # ax_price.set_title(symbol)
    ax_price.legend()

    try:
        if info_text_enabled:
            eps = yf.Ticker(symbol).info['trailingEps'] 
            pe_ratio = df['close'] / eps  
            ax_pe_ratio.plot(df['time'], pe_ratio, linestyle='-', color='#d45087') 
            ax_pe_ratio.set_ylabel("PE Ratio") 
    except:
        print(f"PE chart not generated for {symbol}")

    image_path = os.path.join('static', 'images', f'{symbol}.png')
    plt.savefig(image_path)
    plt.close()

def generate_graph(symbol):
    try:
        if symbol != '^NSEI':
            process_data_and_plot_chart(symbol)
        else:
            # Symbol is ^NSEI, do not call get_financial_data and do not generate info_text
            process_data_and_plot_chart(symbol, info_text_enabled=False)
    except Exception as e:
        print(f"Failed download for {symbol}: {e}")
        df_nifty100 = df_nifty100[df_nifty100['Symbol'] != symbol]

def generate_index_graph(symbol):
    try:
        process_data_and_plot_chart(symbol, info_text_enabled=False)
    except Exception as e:
        print(f"Failed download for {symbol}: {e}")
        df_index = df_index[df_index['Symbol'] != symbol]

def generate_all_graphs():
    for idx, row in df_nifty100.iterrows():
        symbol = row['Symbol']
        generate_graph(symbol)
    for idx, row in df_index.iterrows():
        symbol = row['Symbol']
        generate_index_graph(symbol)

def before_run():
    generate_all_graphs()

before_run()

nifty50_data = read_csv_and_preprocess("nifty50list.csv")
nifty50_df, nifty50_stocks_not_fetched = get_data_for_endpoints(nifty50_data)

niftynext50_data = read_csv_and_preprocess("niftynext50list.csv")
niftynext50_df, niftynext50_stocks_not_fetched = get_data_for_endpoints(niftynext50_data)

nifty100_data = read_csv_and_preprocess("niftymidcap100list.csv")
nifty100_df, nifty100_stocks_not_fetched = get_data_for_endpoints(nifty100_data)

@app.route('/')
def display_table():
    table_data = nifty50_df.values.tolist()

    return render_template('nifty50.html', table_data=table_data, today_date=today_date)

@app.route('/niftynext50')
def display_niftynext50_table():
    table_data = niftynext50_df.values.tolist()

    return render_template('niftynext50.html', table_data=table_data, today_date=today_date)

@app.route('/midcap100')
def display_nifty100_table():
    table_data = nifty100_df.values.tolist()

    return render_template('midcap100.html', table_data=table_data, today_date=today_date)

@app.route('/chart')
def display_candlestick_chart():
    symbols_data = []
    for idx, row in df_nifty100.iterrows():
        symbol_data = {
            'symbol': row['Symbol'],
            'name': row['Name'],
            'industry': row['Industry']
        }
        symbols_data.append(symbol_data)

    return render_template('chart.html', symbols_data=symbols_data, today_date=today_date)

@app.route('/chartindex')
def display_index_chart():
    index_data = []
    for idx, row in df_index.iterrows():
        symbol_data = {
            'symbol': row['Symbol'],
            'name': row['Name'],
            'industry': row['Industry']
        }
        index_data.append(symbol_data)

    return render_template('chartindex.html', symbols_data=index_data, today_date=today_date)


if __name__ == '__main__':
    freezer = Freezer(app)

    if len(sys.argv) > 1 and sys.argv[1] == 'freeze':
        freezer.freeze()
    else:
        app.run(debug=True)
