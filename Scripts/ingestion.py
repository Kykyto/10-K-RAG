from edgar import set_identity, Company

# Replace with your actual email to comply with EDGAR's requirements
set_identity("kylian.tarde@efrei.net")

def get_10ks(tickers):
    ten_ks = {}
    for ticker in tickers:
        company = Company(ticker)
        filings = company.get_filings(form="10-K")
        for filing in filings:
            if filing.form == "10-K":
                ten_ks[ticker] = filing.text()
                break
    return ten_ks   