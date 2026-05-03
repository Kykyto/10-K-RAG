from edgar import set_identity, Company

set_identity("kylian.tarde@efrei.net")

TICKERS = ['AAPL', 'GOOG', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']

ten_ks = {}
for ticker in TICKERS:
    ten_k = Company(ticker).get_filings(form="10-K").latest()
    ten_ks[ticker] = ten_k.text()

