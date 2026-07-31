import csv
import os
from datetime import datetime, timedelta

import pandas as pd


def load_env(path=".env"):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


load_env()

# ------------------------------------------------------------------------
# THE MAIN SWITCH: this decides which data source and which env vars matter
#   ASSET_TYPE = equity   -> pulls from Yahoo Finance (yfinance)
#   ASSET_TYPE = futures  -> pulls from NSE historical F&O data (nsepython)
#   ASSET_TYPE = options  -> pulls from NSE historical F&O data (nsepython)
# ------------------------------------------------------------------------
ASSET_TYPE = os.getenv("ASSET_TYPE", "equity").strip().lower()
SYMBOL = os.getenv("SYMBOL", "TCS").strip().upper()

# --- Used only when ASSET_TYPE=equity ---
TIMEFRAME = os.getenv("TIMEFRAME", "1d").strip().lower()
PERIOD = os.getenv("PERIOD", "5y").strip().lower()

# --- Used only when ASSET_TYPE=futures or options ---
# Dates in DD-MM-YYYY format, e.g. 01-01-2021
FROM_DATE = os.getenv("FROM_DATE", "")
TO_DATE = os.getenv("TO_DATE", "")
# Expiry in DD-MMM-YYYY format, e.g. 25-Jul-2024 (must be an actual NSE expiry date)
EXPIRY = os.getenv("EXPIRY", "")
# --- Used only when ASSET_TYPE=options ---
STRIKE = os.getenv("STRIKE", "")          # e.g. 3800
OPTION_TYPE = os.getenv("OPTION_TYPE", "").strip().upper()  # CE or PE


# ==========================================================================
# EQUITY (Yahoo Finance) — unchanged from before
# ==========================================================================

MAX_LOOKBACK_DAYS = {
    "1m": 7, "2m": 60, "5m": 60, "15m": 60, "30m": 60,
    "1h": 730, "4h": 730, "1d": None,
}
YF_INTERVAL = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "60m", "4h": "60m", "1d": "1d",
}


def parse_period_to_days(period: str) -> int:
    period = period.strip().lower()
    if period == "max":
        return 20 * 365
    if period.endswith("mo"):
        return int(period[:-2]) * 30
    if period.endswith("y"):
        return int(period[:-1]) * 365
    if period.endswith("d"):
        return int(period[:-1])
    return int(period)


def fetch_equity(symbol: str, timeframe: str, period: str):
    import yfinance as yf

    if timeframe not in YF_INTERVAL:
        raise ValueError(f"Unknown TIMEFRAME '{timeframe}'. Use one of: {', '.join(YF_INTERVAL)}")

    requested_days = parse_period_to_days(period)
    max_days = MAX_LOOKBACK_DAYS[timeframe]

    if max_days is not None and requested_days > max_days:
        print(
            f"NOTE: Yahoo Finance only allows the last {max_days} days of '{timeframe}' data "
            f"(you asked for ~{requested_days} days). Fetching the maximum available instead."
        )
        effective_days = max_days
    else:
        effective_days = requested_days

    end = datetime.now()
    start = end - timedelta(days=effective_days)

    ticker = f"{symbol}.NS"
    yf_interval = YF_INTERVAL[timeframe]
    df = yf.download(ticker, start=start, end=end, interval=yf_interval, progress=False)

    if df.empty:
        raise RuntimeError(f"No data returned for {ticker} at interval={yf_interval}.")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if timeframe == "4h":
        df = df.resample("4h").agg({
            "Open": "first", "High": "max", "Low": "min",
            "Close": "last", "Volume": "sum",
        }).dropna(subset=["Open"])

    return df


def write_equity_csv(df, symbol: str, timeframe: str):
    filename = f"{symbol}_{timeframe}.csv"
    include_time = timeframe != "1d"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp" if include_time else "date", "open", "high", "low", "close", "volume"])
        count = 0
        for ts, row in df.iterrows():
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if include_time else ts.strftime("%Y-%m-%d")
            writer.writerow([
                ts_str,
                round(float(row["Open"]), 2), round(float(row["High"]), 2),
                round(float(row["Low"]), 2), round(float(row["Close"]), 2),
                int(row["Volume"]),
            ])
            count += 1
    print(f"Wrote {count} rows to {filename}")


# ==========================================================================
# FUTURES / OPTIONS (NSE historical F&O data via nsepython)
# Daily granularity only — NSE does not publish free intraday F&O history.
# ==========================================================================

def fetch_derivative(symbol: str, asset_type: str):
    from nsepython import derivative_history

    missing = []
    if not FROM_DATE:
        missing.append("FROM_DATE")
    if not TO_DATE:
        missing.append("TO_DATE")
    if not EXPIRY:
        missing.append("EXPIRY")
    if asset_type == "options":
        if not STRIKE:
            missing.append("STRIKE")
        if OPTION_TYPE not in ("CE", "PE"):
            missing.append("OPTION_TYPE (must be CE or PE)")
    if missing:
        raise ValueError(
            f"Missing required env vars for ASSET_TYPE={asset_type}: {', '.join(missing)}\n"
            "Required format examples:\n"
            "  FROM_DATE=01-01-2024   (DD-MM-YYYY)\n"
            "  TO_DATE=31-01-2024     (DD-MM-YYYY)\n"
            "  EXPIRY=25-Jan-2024     (DD-MMM-YYYY, must be a real NSE expiry)\n"
            + ("  STRIKE=3800\n  OPTION_TYPE=CE   (or PE)\n" if asset_type == "options" else "")
        )

    instrument_type = "options" if asset_type == "options" else "futures"
    kwargs = dict(
        symbol=symbol,
        start_date=FROM_DATE,
        end_date=TO_DATE,
        instrumentType=instrument_type,
        expiry_date=EXPIRY,
    )
    if asset_type == "options":
        kwargs["strikePrice"] = STRIKE
        kwargs["optionType"] = OPTION_TYPE

    df = derivative_history(**kwargs)
    if df is None or df.empty:
        raise RuntimeError(
            "No data returned. Double-check SYMBOL, EXPIRY (must be an exact NSE expiry date), "
            "STRIKE and OPTION_TYPE, and that FROM_DATE/TO_DATE fall within that contract's life."
        )
    return df


def write_derivative_csv(df, symbol: str, asset_type: str):
    suffix = "options" if asset_type == "options" else "futures"
    strike_part = f"_{STRIKE}{OPTION_TYPE}" if asset_type == "options" else ""
    filename = f"{symbol}_{suffix}{strike_part}.csv"

    cols = {
        "FH_TIMESTAMP": "date",
        "FH_OPENING_PRICE": "open",
        "FH_TRADE_HIGH_PRICE": "high",
        "FH_TRADE_LOW_PRICE": "low",
        "FH_CLOSING_PRICE": "close",
        "FH_SETTLE_PRICE": "settle_price",
        "FH_TOT_TRADED_QTY": "volume",
        "FH_OPEN_INT": "open_interest",
        "FH_CHANGE_IN_OI": "change_in_oi",
    }
    available = [c for c in cols if c in df.columns]
    out = df[available].rename(columns=cols)
    out.to_csv(filename, index=False)
    print(f"Wrote {len(out)} rows to {filename}")


# ==========================================================================
def main():
    if ASSET_TYPE == "equity":
        print(f"Fetching EQUITY {TIMEFRAME} data for {SYMBOL} (period={PERIOD}) ...")
        try:
            df = fetch_equity(SYMBOL, TIMEFRAME, PERIOD)
        except Exception as e:
            print(f"Failed: {e}")
            return
        write_equity_csv(df, SYMBOL, TIMEFRAME)

    elif ASSET_TYPE in ("futures", "options"):
        print(f"Fetching {ASSET_TYPE.upper()} data for {SYMBOL} ...")
        try:
            df = fetch_derivative(SYMBOL, ASSET_TYPE)
        except Exception as e:
            print(f"Failed: {e}")
            return
        write_derivative_csv(df, SYMBOL, ASSET_TYPE)

    else:
        print(f"Unknown ASSET_TYPE '{ASSET_TYPE}'. Use one of: equity, futures, options")


if __name__ == "__main__":
    main()