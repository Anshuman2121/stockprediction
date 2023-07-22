const express = require('express');
const yahooFinance = require('yahoo-finance2').default;
const path = require('path');

const app = express();
const port = 3000;

// Helper function to calculate percentage difference
function calculatePercentageDifference(currentPrice, referencePrice) {
    return ((currentPrice - referencePrice) / referencePrice) * 100;
}

// Helper function to format date
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Fetch stock data for a given ticker
async function fetchStockData(ticker) {
    try {
        const today = new Date();
        const fiveYearsAgo = new Date(today.getFullYear() - 5, today.getMonth(), today.getDate());

        const queryOptions = {
            period1: formatDate(fiveYearsAgo),
            interval: '1wk'
        };

        const tickerData = await yahooFinance.historical(ticker, queryOptions);

        if (!tickerData || tickerData.length === 0) {
            throw new Error('Historical data not available.');
        }

        const lastDataPoint = tickerData[tickerData.length - 1];
        const lastQuote = lastDataPoint.close;
        const high1Y = Math.max(...tickerData.map(dataPoint => dataPoint.high));
        const high2Y = Math.max(...tickerData.slice(-2 * 52).map(dataPoint => dataPoint.high)); // 2 years (assuming 52 weeks per year)
        const high5Y = Math.max(...tickerData.slice(-5 * 52).map(dataPoint => dataPoint.high)); // 5 years (assuming 52 weeks per year)
        const low1Y = Math.min(...tickerData.map(dataPoint => dataPoint.low));
        const low2Y = Math.min(...tickerData.slice(-2 * 52).map(dataPoint => dataPoint.low)); // 2 years (assuming 52 weeks per year)
        const low5Y = Math.min(...tickerData.slice(-5 * 52).map(dataPoint => dataPoint.low)); // 5 years (assuming 52 weeks per year)

        const high1YDiff = calculatePercentageDifference(lastQuote, high1Y);
        const high2YDiff = calculatePercentageDifference(lastQuote, high2Y);
        const high5YDiff = calculatePercentageDifference(lastQuote, high5Y);
        const low1YDiff = calculatePercentageDifference(lastQuote, low1Y);
        const low2YDiff = calculatePercentageDifference(lastQuote, low2Y);
        const low5YDiff = calculatePercentageDifference(lastQuote, low5Y);

        return [
            ticker,
            lastQuote.toFixed(2),
            high1YDiff.toFixed(2),
            high2YDiff.toFixed(2),
            high5YDiff.toFixed(2),
            low1YDiff.toFixed(2),
            low2YDiff.toFixed(2),
            low5YDiff.toFixed(2)
        ];

    } catch (error) {
        return `${ticker}: ${error.message}`;
    }
}

app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');

app.get('/', async (req, res) => {
    const tickers = [
        'LT.NS', 'ONGC.NS', 'NTPC.NS', 'SBIN.NS', 'TATAMOTORS.NS', 'KOTAKBANK.NS', 'HEROMOTOCO.NS',
    'DIVISLAB.NS', 'BPCL.NS', 'ICICIBANK.NS', 'ITC.NS', 'BHARTIARTL.NS', 'APOLLOHOSP.NS',
    'ADANIENT.NS', 'MARUTI.NS', 'CIPLA.NS', 'EICHERMOT.NS', 'BAJFINANCE.NS', 'POWERGRID.NS',
    'BAJAJ-AUTO.NS', 'NESTLEIND.NS', 'TATASTEEL.NS', 'COALINDIA.NS', 'ASIANPAINT.NS',
    'SUNPHARMA.NS', 'BAJAJFINSV.NS', 'TITAN.NS', 'ADANIPORTS.NS', 'BRITANNIA.NS', 'AXISBANK.NS',
    'HDFCBANK.NS', 'UPL.NS', 'GRASIM.NS', 'LT.NS', 'DRREDDY.NS', 'INDUSINDBK.NS', 'ULTRACEMCO.NS',
    'JSWSTEEL.NS', 'SBILIFE.NS', 'M&M.NS', 'HINDALCO.NS', 'HDFCLIFE.NS', 'TECHM.NS', 'TATACONSUM.NS',
    'RELIANCE.NS', 'TCS.NS', 'WIPRO.NS', 'HCLTECH.NS', 'HINDUNILVR.NS', 'INFY.NS'
    ];

    const dataPromises = tickers.map(ticker => fetchStockData(ticker));
    const stockData = await Promise.all(dataPromises);

    const tableData = stockData.filter(data => Array.isArray(data));

    res.render('stock_data', { tableData });
});

app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
