# Cryptocurrency Trading Backtesting

A backtesting system that simulates crypto trading with **perfect knowledge** of future prices. Tests whether $10K can become $1M through optimal trading.

## Quick Start

**Using Cursor IDE** (recommended):
```
Open project in Cursor → Chat → Say "setup the project"
```

**Manual setup**:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python pull_data.py      # Download data (~5 min)
python backtesting.py    # Run backtest
```

## Results

| Metric | Value |
|--------|-------|
| Average daily profit | ~$898 (+9%) |
| Best single day | ~$1,695 (+17%) |
| 31-day compounded | ~$141K |
| **$1M target reached?** | **No** |

**Key finding**: Even with perfect knowledge of all future prices, market volatility limits daily returns to ~5-17%. The $1M target requires ~54 more days of compounding.

## Algorithm

The backtesting uses a **greedy optimization** strategy with perfect future knowledge:

1. **Data preparation**: Loads 1-minute Binance futures data for BTC, ETH, and BNB. Precomputes suffix arrays storing the maximum and minimum future prices from each time point.

2. **Opportunity detection**: At each minute, evaluates all tickers to find the best long (buy low, sell at future max) or short (sell high, buy at future min) opportunity based on expected return.

3. **Position management**: Opens the highest-return position using full available balance. Closes positions when the current price equals the optimal exit point (peak for longs, bottom for shorts).

4. **Trade execution**: Processes ~4,320 price events per day (1,440 minutes × 3 tickers), generating trade logs and daily summaries.

## Files

| File | Purpose |
|------|---------|
| `pull_data.py` | Downloads Binance klines data |
| `backtesting.py` | Main backtesting engine |
| `check_30day.py` | Analyzes compounding returns |
| `result/*.csv` | Generated trade logs and summaries |

## Output

After running `backtesting.py`:
- `result/all_trades_per_day.csv` - All executed trades
- `result/daily_results_summary.csv` - Daily P&L summary

Run `python check_30day.py` to see compounding analysis.

## Notes

- Uses perfect future knowledge (not realistic trading)
- No fees, unlimited liquidity assumed
- Educational/interview project
