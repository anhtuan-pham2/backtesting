# Cryptocurrency Trading Backtesting

A backtesting system that finds the **optimal sequence of trades** using Dynamic Programming, given perfect knowledge of future prices. Tests whether $10K can become $1M in a 24-hour period.

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

| Metric                  | Value            |
| ----------------------- | ---------------- |
| Average daily profit    | ~$14,329 (+143%) |
| Best single day         | ~$36,673 (+267%) |
| **$1M target reached?** | **No**           |

**Key finding**: Even with perfect knowledge and optimal trade sequencing, the maximum achievable in a single day is ~$36K. The $1M target is not achievable within any 24-hour window in December 2025.

## Algorithm

### Dynamic Programming Approach

The algorithm finds the **globally optimal sequence of non-overlapping trades**.

**Key insight**: A greedy approach (picking the best trade at each moment) is suboptimal. Multiple smaller trades with compounding can outperform fewer larger trades.

#### How It Works

1. **Find all possible trades**: For each ticker, enumerate all profitable (entry, exit) pairs

   - LONG: Buy at time i, sell at time j where price[j] > price[i]
   - SHORT: Sell at time i, buy at time j where price[j] < price[i]

2. **Dynamic Programming**:

   ```
   dp[i] = maximum balance multiplier achievable from time i to end of day

   For each time i (backwards from end):
     Option 1: Skip → dp[i] = dp[i+1]
     Option 2: Take trade → dp[i] = (1 + return) × dp[exit_time]

   Answer: initial_balance × dp[0]
   ```

3. **Reconstruct optimal sequence**: Backtrack through DP to get the actual trades

### Time Complexity

| Phase             | Complexity    | Description                          |
| ----------------- | ------------- | ------------------------------------ |
| Find all trades   | O(N² × M)     | N = minutes (~1440), M = tickers (3) |
| Build trade index | O(T)          | T = total trades                     |
| DP computation    | O(N + T)      | One pass through time points         |
| **Overall**       | **O(N² × M)** | ~6.2M operations per day             |

### Space Complexity

| Component   | Complexity    |
| ----------- | ------------- |
| All trades  | O(N² × M)     |
| DP array    | O(N)          |
| **Overall** | **O(N² × M)** |

## Output

After running `backtesting.py`:

```
result/
├── daily_results_summary.csv    # Summary for all days
└── trade_sequences/
    ├── 2025-12-01_trades.csv    # Detailed trades for each day
    ├── 2025-12-02_trades.csv
    └── ...
```

### Console Output Format

```
================================================================================
Day: 2025-12-01
================================================================================
$1M Target Achievable: NO
Maximum Profit: $36,673.01 (+266.73%)
Total Trades: 1,227

Trade Sequence (showing first 10 of 1,227):
  #   1  SHORT  ETHUSDT   $2,996.46 → $2,991.66  +$16.02  Balance: $10,016.02
  #   2  SHORT  BTCUSDT   $90,264.80 → $90,159.20  +$11.72  Balance: $10,027.74
  ...
```

## Files

| File              | Purpose                       |
| ----------------- | ----------------------------- |
| `backtesting.py`  | Main DP backtesting engine    |
| `pull_data.py`    | Downloads Binance klines data |
| `check_30day.py`  | Analyzes compounding returns  |
| `assumptions.txt` | Documents assumptions made    |

## Comparison: Greedy vs DP

| Approach | Avg Daily Profit    | Strategy                          |
| -------- | ------------------- | --------------------------------- |
| Greedy   | $898 (+9%)          | Best single trade at each moment  |
| **DP**   | **$14,329 (+143%)** | Optimal sequence with compounding |

The DP solution achieves **16x better returns** by finding many smaller trades that compound.

## Notes

- Uses perfect future knowledge (not realistic trading)
- No fees, unlimited liquidity assumed
- Sequential trades only (one position at a time)
- Each day starts fresh with $10,000
- See `assumptions.txt` for full list of assumptions
