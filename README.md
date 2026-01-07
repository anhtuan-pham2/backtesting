# Cryptocurrency Trading Backtesting System

A Python-based backtesting system that simulates cryptocurrency trading with perfect knowledge of future prices. This project analyzes whether it's possible to turn $10,000 into $1,000,000 through optimal trading strategies across multiple cryptocurrency pairs.

## Project Overview

This project implements a backtesting engine that:
- Downloads historical Binance futures klines data (1-minute intervals)
- Simulates trading with perfect knowledge of all future prices
- Supports both Long and Short positions
- Allows multiple simultaneous positions across different assets
- Calculates maximum possible profit per day
- Analyzes compounding returns over multiple days

## Features

- **Multi-Asset Trading**: Supports BTCUSDT, ETHUSDT, and BNBUSDT
- **Long/Short Positions**: Can profit from both rising and falling prices
- **Perfect Knowledge Strategy**: Uses future price information to make optimal decisions
- **Daily Analysis**: Calculates maximum profit achievable per day
- **Compounding Analysis**: Tracks cumulative returns over multiple days
- **Comprehensive Reporting**: Generates detailed CSV reports of all trades and daily summaries

## Project Structure

```
.
├── pull_data.py          # Downloads Binance klines data
├── load_data.py          # Loads and processes CSV data
├── backtesting.py        # Main backtesting engine
├── check_30day.py        # 30-day compounding analysis
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── .gitignore           # Git ignore rules
├── binance_december_data/  # Downloaded data (gitignored - run pull_data.py)
│   ├── BTCUSDT/
│   ├── ETHUSDT/
│   └── BNBUSDT/
└── result/              # Generated result files (gitignored - created by backtesting.py)
    ├── all_trades_per_day.csv
    └── daily_results_summary.csv
```

**Note:** Folders marked as "gitignored" are not included in the repository. You need to:
- Run `pull_data.py` to create `binance_december_data/`
- Run `backtesting.py` to create `result/`

## Algorithm Description

### Trading Strategy

The backtesting algorithm uses a **greedy optimization approach** with perfect knowledge of all future prices:

1. **Position Management**:
   - Tracks open positions for each ticker separately
   - Can have multiple positions open simultaneously across different assets
   - Closes positions when optimal (price peaks for LONG, price bottoms for SHORT)

2. **Entry Strategy**:
   - At each minute, evaluates all tickers for the best opportunity
   - Compares potential LONG returns (buy low, sell high) vs SHORT returns (sell high, buy low)
   - Opens the position with the highest expected return
   - Uses all available balance for the best opportunity

3. **Exit Strategy**:
   - Closes LONG positions when current price equals or exceeds maximum future price
   - Closes SHORT positions when current price equals or falls below minimum future price
   - Early exit if target balance ($1M) is reached

4. **Perfect Knowledge Utilization**:
   - For each ticker at each time point, looks ahead to find:
     - Maximum future price (for LONG exit timing)
     - Minimum future price (for SHORT exit timing)
   - Compares opportunities across all tickers to select the best trade

### Time Complexity Analysis

The backtesting algorithm has the following time complexity:

**For a single day:**
- **Time Complexity**: O(N² × M) in worst case, O(N × M) in average case
  - N = Total number of price events across all tickers in a day (~1,440 minutes × 3 tickers = 4,320 events)
  - M = Number of tickers (3: BTCUSDT, ETHUSDT, BNBUSDT)
  
  **Worst Case Analysis:**
  - For each of N events: O(N)
    - Check M tickers for opportunities: O(M)
    - For each ticker, scan remaining future prices: O(N) in worst case
    - Compare opportunities: O(M)
  - Total: O(N × M × N) = **O(N² × M)**

- **Space Complexity**: O(N × M)
  - Stores all price events: O(N)
  - Stores ticker event sequences: O(N)
  - Stores open positions per ticker: O(M × P) where P is max concurrent positions
  - Stores all trades: O(T) where T is total trades executed

**Detailed Breakdown:**
1. **Data Loading**: O(N × M) - Load and sort all price events
2. **Event Processing**: O(N² × M) worst case
   - For each of N events:
     - Check M tickers for opportunities: O(M)
     - For each ticker, find current index: O(N) using linear search
     - Scan future prices to find min/max: O(remaining_events) ≤ O(N)
     - Compare opportunities: O(M)
3. **Position Management**: O(P) per event where P is number of open positions

**Overall**: For 31 days of data:
- **Theoretical Worst Case**: O(31 × N² × M) ≈ O(31 × 4,320² × 3) ≈ **O(1.8 billion operations**
- **Average Case**: Much better due to optimizations and early exits

**Optimizations Applied:**
- Early termination when target balance is reached
- Only evaluates opportunities when balance > 0
- Caches ticker event sequences to avoid repeated filtering
- Stops scanning future prices once min/max is found
- Position closing logic reduces future scanning

**Practical Runtime**: 
- Single day: ~1-5 seconds (actual: ~2-3 seconds)
- Full 31 days: ~60-150 seconds (actual: ~60-90 seconds on modern hardware)

## Installation

1. **Clone or download this repository:**
```bash
git clone <repository-url>
cd Interview
```

2. **Create a virtual environment (recommended):**
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
# or
source .venv/bin/activate    # Linux/Mac
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

**Note:** The repository does not include the data files or results. You need to download the data using the provided script (see Usage section below).

## Usage

### Step 1: Download Data

**Important:** The `binance_december_data/` folder is not included in the repository (see `.gitignore`). You must download the data first.

Download historical Binance futures data for December 2025:

```bash
python pull_data.py
```

This will:
- Download 1-minute klines data for BTCUSDT, ETHUSDT, and BNBUSDT
- Save data into the `binance_december_data/` directory
- Show a progress bar during download
- Extract CSV files from downloaded ZIP archives

**Expected download time:** ~5-10 minutes depending on internet speed (93 files total: 31 days × 3 tickers)

### Step 2: Run Backtesting

Run the backtesting engine to calculate maximum profits per day:

```bash
python backtesting.py
```

This will:
- Process each day in December 2025
- Calculate maximum profit with perfect knowledge
- Generate CSV files in the `result/` directory (created automatically):
  - `all_trades_per_day.csv`: Detailed log of all trades
  - `daily_results_summary.csv`: Daily summary statistics

**Note:** The `result/` folder is gitignored and will be created automatically when you run the script.

### Step 3: Analyze Compounding (Optional)

Analyze whether compounding profits over 30 days can reach $1M:

```bash
python check_30day.py
```

This script reads from `result/daily_results_summary.csv` and calculates cumulative returns.

## Output Files

### `result/all_trades_per_day.csv`

Contains all trades executed during backtesting with columns:
- `ticker`: Trading symbol (BTCUSDT, ETHUSDT, BNBUSDT)
- `date`: Trading date
- `time`: Timestamp of the trade
- `minute`: Minute index in the day
- `action`: Trade action (OPEN_LONG, CLOSE_LONG, OPEN_SHORT, CLOSE_SHORT)
- `entry_price`: Entry price for the position
- `exit_price`: Exit price (None for open actions)
- `quantity`: Quantity traded
- `profit_loss`: Profit or loss from the trade
- `balance_after`: Account balance after the trade

### `result/daily_results_summary.csv`

Daily summary statistics with columns:
- `date`: Trading date
- `initial_balance`: Starting balance for the day ($10,000)
- `final_balance`: Ending balance after all trades
- `profit_loss`: Net profit/loss for the day
- `profit_pct`: Percentage return for the day
- `total_trades`: Number of trades executed
- `achieved_1m_target`: Boolean indicating if $1M target was reached
- `tickers_traded`: Number of different tickers traded

## Results Summary

Based on December 2025 data:

- **Single Day Performance**: 
  - Maximum profit: ~$1,695 per day
  - Average profit: ~$898 per day
  - **$1M target not achievable in a single day**

- **30-Day Compounding**:
  - Final balance after 31 days: ~$141,147
  - Average daily return: ~8.98%
  - **$1M target not achievable in 30 days**
  - Would need approximately 23 more days at average return rate

## Key Findings

1. **Single Day Limitation**: The maximum daily price movements in the data don't allow for the 100x growth needed to reach $1M from $10K in a single day.

2. **Compounding Potential**: While daily returns average ~9%, compounding over 30 days only reaches ~$141K, far short of the $1M target.

3. **Optimal Strategy**: The algorithm successfully identifies the best trades using perfect knowledge, but market volatility constraints limit achievable returns.

## Dependencies

- `pandas >= 2.0.0`: Data manipulation and CSV handling
- `requests >= 2.32.0`: HTTP requests for data download
- `tqdm >= 4.66.0`: Progress bars for downloads

## Data and Results

- **Data Files**: The `binance_december_data/` folder is gitignored. Download data using `pull_data.py` after cloning the repository.
- **Result Files**: The `result/` folder is gitignored. Results are generated when you run `backtesting.py`.
- **Why gitignored?**: These folders contain large files (data) or generated content (results) that should not be committed to version control.

## Notes

- This is a theoretical backtesting system assuming perfect knowledge of future prices
- Real-world trading would not have access to future price information
- No trading fees are included in the simulation
- Results are based on historical data and may not reflect future performance
- The algorithm assumes unlimited liquidity and perfect execution
- Data must be downloaded before running backtesting (see Usage section)

## License

This project is for educational and interview purposes.
