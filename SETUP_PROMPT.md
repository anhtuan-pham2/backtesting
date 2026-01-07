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

STEP 1: Create Required Directories
- Create `binance_december_data/` folder if it doesn't exist
- Create `result/` folder if it doesn't exist
- Verify both folders are created

STEP 2: Set Up Python Virtual Environment
- Check if `.venv` folder exists
- If not, create a new virtual environment: `python -m venv .venv`
- Activate the virtual environment:
  - On Windows: `.venv\Scripts\Activate.ps1`
  - On Linux/Mac: `source .venv/bin/activate`
- Install all dependencies from `requirements.txt`: `pip install -r requirements.txt`
- Verify installation by checking if pandas, requests, and tqdm are installed

STEP 3: Download Market Data
- Run `python pull_data.py` to download Binance klines data
- This will download 93 files total (31 days × 3 tickers: BTCUSDT, ETHUSDT, BNBUSDT)
- The script will show a progress bar
- Wait for the download to complete (this may take 5-10 minutes)
- Verify data is downloaded by checking:
  - `binance_december_data/BTCUSDT/` contains 31 CSV files
  - `binance_december_data/ETHUSDT/` contains 31 CSV files
  - `binance_december_data/BNBUSDT/` contains 31 CSV files

STEP 4: Verify Complete Setup
- Confirm `binance_december_data/` folder exists with subdirectories
- Confirm `result/` folder exists
- Confirm `.venv/` folder exists
- Confirm all dependencies are installed

STEP 5: Final Confirmation
- Once all steps are complete, inform me:
  - "Setup complete! You can now run: python backtesting.py"
  - Provide a summary of what was created/downloaded

Please execute these steps sequentially and provide status updates after each step. If any step fails, stop and inform me of the error.
```

---

## What This Does

When you paste this prompt into Cursor, it will:
- ✅ Create all necessary folders
- ✅ Set up Python virtual environment
- ✅ Install all dependencies
- ✅ Download all required market data (93 files)
- ✅ Verify everything is set up correctly

After setup completes, you can immediately run:
```bash
python backtesting.py
```

No manual steps required!
