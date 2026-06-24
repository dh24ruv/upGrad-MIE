import yfinance as yf
from datetime import datetime, timedelta

def get_stock_data(ticker: str) -> dict | None:
    """
    Fetch real-time stock data + last-24h intraday history for the chart.
    Returns None if ticker is invalid or not listed.
    """
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info

        # Verify it's a real ticker
        if not info.get("regularMarketPrice") and not info.get("currentPrice"):
            return None

        price      = info.get("currentPrice") or info.get("regularMarketPrice")
        prev       = info.get("previousClose")
        change     = round(price - prev, 2) if price and prev else None
        change_pct = round((change / prev) * 100, 2) if change and prev else None
        mktcap     = info.get("marketCap")
        high_52w   = info.get("fiftyTwoWeekHigh")
        low_52w    = info.get("fiftyTwoWeekLow")
        currency   = info.get("currency", "INR")
        name       = info.get("longName") or info.get("shortName", ticker)

        # Last 24h intraday history (5-min candles) for the chart.
        # period="1d" sometimes only returns the most recent session if markets
        # are closed, so we pull 2 days of 5m bars and trim to the last 24h —
        # this keeps the chart populated outside trading hours too.
        prices_24h = []
        times_24h  = []
        try:
            hist = stock.history(period="2d", interval="5m")
            if not hist.empty:
                cutoff = hist.index.max() - timedelta(hours=24)
                hist = hist[hist.index >= cutoff]
                prices_24h = [round(p, 2) for p in hist["Close"].tolist()]
                times_24h  = [t.strftime("%H:%M") for t in hist.index.tolist()]
        except Exception as e:
            print(f"Intraday history error for {ticker}: {e}")

        # Fallback: if intraday is empty (e.g. delisted intraday feed, weekend
        # with no 5m data), fall back to daily closes over the last 5 sessions
        # so the chart isn't blank.
        if not prices_24h:
            try:
                hist = stock.history(period="5d", interval="1d")
                if not hist.empty:
                    prices_24h = [round(p, 2) for p in hist["Close"].tolist()]
                    times_24h  = [d.strftime("%d %b") for d in hist.index.tolist()]
            except Exception as e:
                print(f"Daily fallback history error for {ticker}: {e}")

        # Convert market cap to ₹ Cr
        mktcap_cr = None
        if mktcap:
            if currency == "INR":
                mktcap_cr = round(mktcap / 1e7, 1)
            else:
                mktcap_cr = round((mktcap * 83.5) / 1e7, 1)

        return {
            "ticker":      ticker,
            "name":        name,
            "price":       price,
            "currency":    currency,
            "change":      change,
            "change_pct":  change_pct,
            "mktcap_cr":   mktcap_cr,
            "high_52w":    high_52w,
            "low_52w":     low_52w,
            "prices_24h":  prices_24h,
            "times_24h":   times_24h,
            "as_of":       datetime.now().strftime("%d %b %Y, %H:%M IST")
        }

    except Exception as e:
        print(f"Stock data error for {ticker}: {e}")
        return None


def format_price(price, currency="INR"):
    """Format price with currency symbol."""
    if price is None:
        return "—"
    if currency == "INR":
        return f"₹{price:,.2f}"
    return f"${price:,.2f}"


def format_mktcap(cr):
    """Format market cap in Cr with L suffix for lakh crore."""
    if cr is None:
        return "—"
    if cr >= 100000:
        return f"₹{cr/100000:.2f}L Cr"
    return f"₹{cr:,.0f} Cr"


if __name__ == "__main__":
    ticker = input("Enter ticker (e.g. NAUKRI.NS): ")
    data = get_stock_data(ticker)
    if data:
        print(f"\n{data['name']} ({data['ticker']})")
        print(f"Price:     {format_price(data['price'])}")
        print(f"Change:    {data['change']} ({data['change_pct']}%)")
        print(f"Mkt Cap:   {format_mktcap(data['mktcap_cr'])}")
        print(f"52W High:  {format_price(data['high_52w'])}")
        print(f"52W Low:   {format_price(data['low_52w'])}")
        print(f"24h pts:   {len(data['prices_24h'])} data points")
    else:
        print("No data found — not listed or invalid ticker.")