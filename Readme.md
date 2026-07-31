# Historical Data Fetcher — Setup Guide

This script pulls historical market data for NSE-listed symbols:
- **Equity** data from Yahoo Finance (free, any timeframe)
- **Futures** and **Options** data from NSE's own historical records (free, daily only)

---

## Full Variable Reference

| Variable | Used for | Format | Example |
|---|---|---|---|
| `ASSET_TYPE` | all | `equity` / `futures` / `options` | `equity` |
| `SYMBOL` | all | plain NSE symbol, no suffix | `TCS` |
| `TIMEFRAME` | equity only | `1m`/`5m`/`15m`/`30m`/`1h`/`4h`/`1d` | `1d` |
| `PERIOD` | equity only | `Nd` / `Nmo` / `Ny` / `max` | `5y` |
| `FROM_DATE` | futures/options only | `DD-MM-YYYY` | `01-01-2024` |
| `TO_DATE` | futures/options only | `DD-MM-YYYY` | `31-01-2024` |
| `EXPIRY` | futures/options only | `DD-MMM-YYYY` | `25-Jan-2024` |
| `STRIKE` | options only | plain number | `3800` |
| `OPTION_TYPE` | options only | `CE` or `PE` | `CE` |

### Timeframe → Max Free Lookback (equity / Yahoo only)

| Timeframe | Max lookback |
|---|---|
| 1m | 7 days |
| 5m / 15m / 30m | 60 days |
| 1h | ~730 days (2 years) |
| 4h | ~730 days (built from 1h candles — Yahoo has no native 4h) |
| 1d | unlimited |

If `PERIOD` asks for more than a timeframe's real limit, the script won't error out — it prints a note and automatically fetches the maximum Yahoo allows for that timeframe instead.

**Important:** Futures and options data is **end-of-day (daily) only**. There is no free source anywhere for intraday (minute-level) F&O history.

---

## `.env` File Reference

Copy this into your `.env` file and edit the values:

```dotenv
# --------------------------------------------------------------------
# 1) ASSET_TYPE — THE MAIN SWITCH
#    Decides which data source is used and which other variables matter.
# --------------------------------------------------------------------
# Accepts:  equity | futures | options
#   equity  -> pulled from Yahoo Finance (free, no login, no cost)
#   futures -> pulled from NSE's own historical F&O data (free, daily only)
#   options -> pulled from NSE's own historical F&O data (free, daily only)
ASSET_TYPE=equity


# --------------------------------------------------------------------
# 2) SYMBOL — used by ALL asset types
# --------------------------------------------------------------------
# The plain NSE trading symbol, no exchange suffix, no spaces.
# Examples: TCS, RELIANCE, INFY, HDFCBANK
SYMBOL=TCS


# ======================================================================
# SECTION A — used ONLY when ASSET_TYPE=equity
# ======================================================================

# TIMEFRAME — candle size for equity data
# Accepts: 1m | 5m | 15m | 30m | 1h | 4h | 1d
TIMEFRAME=1d

# PERIOD — how far back to fetch, for equity data
# Accepts: 7d | 60d | 6mo | 1y | 2y | 5y | 10y | max  (or any Nd / Ny / Nmo)
#   d  = days     e.g. 7d, 60d, 730d
#   mo = months   e.g. 6mo, 18mo
#   y  = years    e.g. 1y, 2y, 5y, 10y
#   max = as much history as Yahoo has (since the stock's listing)
PERIOD=5y


# ======================================================================
# SECTION B — used ONLY when ASSET_TYPE=futures or ASSET_TYPE=options
# ======================================================================

# FROM_DATE / TO_DATE — date range to fetch
# Format: DD-MM-YYYY  (different from EXPIRY below!)
FROM_DATE=01-01-2024
TO_DATE=31-01-2024

# EXPIRY — the contract's expiry date
# Format: DD-MMM-YYYY (3-letter month, capitalized)
# MUST be an exact, real NSE expiry date for that symbol.
#
# Don't know the valid expiries? Run once in Python:
#   from nsepython import expiry_history
#   print(expiry_history("TCS"))
EXPIRY=25-Jan-2024

# STRIKE and OPTION_TYPE — used ONLY when ASSET_TYPE=options
# (futures don't have a strike or CE/PE, skip these for futures)
STRIKE=3800
OPTION_TYPE=CE
```

---

## Step-by-Step Setup and Launch

### 1. Install Python packages (one-time)
```bash
pip install yfinance pandas nsepython
```

### 2. Create your config file
```bash
cp .env.example .env
```
Then open `.env` in a text editor and edit the values per the reference above.

### 3. (Options/futures only) Find a valid expiry date first
`EXPIRY` must match an exact NSE expiry, so look it up before running:
```bash
python -c "from nsepython import expiry_history; print(expiry_history('TCS'))"
```
Copy one of the printed dates into `EXPIRY` in `.env`.

### 4. Run the script
```bash
python main.py
```

### 5. Check the output
Depending on `ASSET_TYPE`, you'll get one of:
- `SYMBOL_TIMEFRAME.csv` — equity, e.g. `TCS_1d.csv`
- `SYMBOL_futures.csv`
- `SYMBOL_options_STRIKE+TYPE.csv` — e.g. `TCS_options_3800CE.csv`

If it fails, the printed error tells you which env var is missing or wrong before it even tries to hit the network.

---

## Quick Examples

**5 years of daily equity data:**
```dotenv
ASSET_TYPE=equity
SYMBOL=TCS
TIMEFRAME=1d
PERIOD=5y
```

**2 years of hourly equity data (auto-capped from a bigger request):**
```dotenv
ASSET_TYPE=equity
SYMBOL=TCS
TIMEFRAME=1h
PERIOD=5y
```

**One month of futures data:**
```dotenv
ASSET_TYPE=futures
SYMBOL=TCS
FROM_DATE=01-01-2024
TO_DATE=31-01-2024
EXPIRY=25-Jan-2024
```

**One month of a specific call option:**
```dotenv
ASSET_TYPE=options
SYMBOL=TCS
FROM_DATE=01-01-2024
TO_DATE=31-01-2024
EXPIRY=25-Jan-2024
STRIKE=3800
OPTION_TYPE=CE
```