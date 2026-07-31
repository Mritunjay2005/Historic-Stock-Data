# NSE Historical Data Fetcher

A lightweight Python script to pull historical **equity**, **futures**, and **options** data for NSE-listed stocks — fully configurable through a single `.env` file, no code changes required.

- 📈 **Equity** — daily to 1-minute candles via [Yahoo Finance](https://finance.yahoo.com/) (free, no API key)
- 📊 **Futures & Options** — historical F&O data straight from NSE (free, end-of-day)
- ⚙️ Switch between asset types, timeframes, and date ranges purely through `.env`

---

## Features

- One script, one config file — no code editing needed for day-to-day use
- Auto-caps intraday requests to whatever Yahoo actually allows for that timeframe (with a clear warning instead of a silent failure)
- Builds 4-hour candles from 1-hour data since Yahoo has no native 4h interval
- Clean CSV output, one row per candle/contract-day
- Clear, actionable error messages when a config value is missing or wrong

---

## Requirements

- Python 3.9+
- Packages: `yfinance`, `pandas`, `nsepython`

```bash
pip install yfinance pandas nsepython
```

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up your config
cp .env.example .env
# edit .env with your symbol, asset type, timeframe/period, etc.

# 4. Run
python main.py
```

Output is written as a CSV file in the project directory, e.g. `TCS_1d.csv`, `TCS_futures.csv`, or `TCS_options_3800CE.csv`.

---

## Configuration (`.env`)

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

### Equity timeframe limits (Yahoo Finance)

| Timeframe | Max free lookback |
|---|---|
| 1m | 7 days |
| 5m / 15m / 30m | 60 days |
| 1h | ~730 days (2 years) |
| 4h | ~730 days (derived from 1h candles) |
| 1d | unlimited |

If `PERIOD` exceeds what a timeframe allows, the script automatically fetches the maximum available instead of failing.

**Note:** Futures and options data is end-of-day only — there is no free source for intraday F&O history.

Full details, example configs, and troubleshooting: see [`SETUP_GUIDE.md`](./SETUP_GUIDE.md).

---

## Example `.env` Configs

**5 years of daily equity data:**
```dotenv
ASSET_TYPE=equity
SYMBOL=TCS
TIMEFRAME=1d
PERIOD=5y
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

Don't know a valid expiry for a symbol? Run:
```bash
python -c "from nsepython import expiry_history; print(expiry_history('TCS'))"
```

---

## Project Structure

```
.
├── main.py           # main script
├── .env.example       # config template — copy to .env
├── SETUP_GUIDE.md      # detailed variable reference & walkthrough
└── README.md
```

---

## Disclaimer

This tool is for educational and informational purposes only. It is not financial advice. Data is sourced from Yahoo Finance and NSE's public archives via unofficial community libraries (`yfinance`, `nsepython`) and may occasionally be delayed, incomplete, or interrupted if those upstream sources change. Always verify data independently before making trading or investment decisions.

## License

MIT
