# Setup Prompt for Cursor AI

## How to Use

1. Open this file (`SETUP_PROMPT.md`) in Cursor
2. Copy the prompt below (everything between the triple backticks)
3. Paste it into Cursor's chat (Cmd/Ctrl + L)
4. Cursor will automatically set up the entire project

---

## The Prompt

Copy everything below this line:

```
I need to set up this cryptocurrency trading backtesting project. Please help me automate the complete setup process:

STEP 1: Set Up Python Virtual Environment
- Check if `.venv` folder exists
- If not, create a new virtual environment: `python -m venv .venv`
- Activate the virtual environment:
  - On Windows: `.venv\Scripts\Activate.ps1`
  - On Linux/Mac: `source .venv/bin/activate`
- Install all dependencies from `requirements.txt`: `pip install -r requirements.txt`
- Verify installation by checking if pandas, requests, and tqdm are installed

STEP 2: Download Market Data
- Run `python pull_data.py` to download Binance klines data
- This will download 93 files total (31 days × 3 tickers: BTCUSDT, ETHUSDT, BNBUSDT)
- The script will show a progress bar
- Wait for the download to complete (this may take 5-10 minutes)
- Verify data is downloaded by checking:
  - `binance_december_data/BTCUSDT/` contains 31 CSV files
  - `binance_december_data/ETHUSDT/` contains 31 CSV files
  - `binance_december_data/BNBUSDT/` contains 31 CSV files

STEP 3: Run Backtesting
- Run `python backtesting.py` to execute the backtesting engine
- This will process all 31 days of data and generate results
- The script will create the `result/` folder automatically
- Wait for completion (this may take 1-2 minutes)
- Verify that results were generated:
  - `result/all_trades_per_day.csv` exists
  - `result/daily_results_summary.csv` exists

STEP 4: Verify Complete Setup
- Confirm `binance_december_data/` folder was created with subdirectories (created automatically by pull_data.py)
- Confirm `result/` folder was created with CSV files (created automatically by backtesting.py)
- Confirm `.venv/` folder exists
- Confirm all dependencies are installed

STEP 5: Final Confirmation
- Once all steps are complete, inform me:
  - "Setup complete! Project is ready to use."
  - Provide a summary of what was created/downloaded:
    - Number of data files downloaded
    - Backtesting results generated
    - Location of result files

Please execute these steps sequentially and provide status updates after each step. If any step fails, stop and inform me of the error.
```

---

## What This Does

When you paste this prompt into Cursor, it will:
- ✅ Set up Python virtual environment
- ✅ Install all dependencies
- ✅ Download all required market data (93 files) - folders created automatically
- ✅ Run backtesting to generate results - result folder created automatically
- ✅ Verify everything is set up correctly

Note: Folders (`binance_december_data/` and `result/`) are created automatically by the scripts, so no manual folder creation is needed.

After setup completes, the project is fully ready:
- Data is downloaded
- Backtesting has been run
- Results are available in `result/` folder
- You can run `python check_30day.py` to analyze compounding returns

No manual steps required!
