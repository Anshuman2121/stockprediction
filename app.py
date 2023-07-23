from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
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

# if __name__ == '__main__':
#     app.run(debug=True)

if __name__ == '__main__':
    freezer = Freezer(app)  # Create a Freezer object

    # If you want to freeze your application, run this command:
    # python app.py freeze

    # If you want to run the development server, use this command:
    # python app.py runserver

    # The following block should be used only when freezing the application
    if len(sys.argv) > 1 and sys.argv[1] == 'freeze':
        freezer.freeze()  # Freeze the application into static files
    else:
        app.run(debug=True)
