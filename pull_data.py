"""Module for downloading Binance futures klines data."""
import io
import os
import zipfile
from datetime import date, timedelta

import requests
from tqdm import tqdm

BASE_URL = "https://data.binance.vision/data/futures/um/daily/klines"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
INTERVAL = "1m"
START_DATE = date(2025, 12, 1)
END_DATE = date(2025, 12, 31)
OUTPUT_DIR = "binance_december_data"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def daterange(start_date, end_date):
    """Generate date range from start to end (inclusive).
    
    Args:
        start_date: Starting date
        end_date: Ending date
        
    Yields:
        Date objects from start_date to end_date (inclusive)
    """
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def download_day(symbol, trading_date):
    """Download klines data for a specific symbol and day.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        trading_date: Date object for the trading day
        
    Returns:
        bool: True if download successful, False otherwise
    """
    filename = f"{symbol}-{INTERVAL}-{trading_date}.zip"
    url = f"{BASE_URL}/{symbol}/{INTERVAL}/{filename}"
    symbol_dir = os.path.join(OUTPUT_DIR, symbol)
    os.makedirs(symbol_dir, exist_ok=True)

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zip_file:
            zip_file.extractall(symbol_dir)

        return True

    except requests.HTTPError:
        print(f"Missing: {filename}")
    except Exception as e:
        print(f"Error downloading {filename}: {e}")

    return False


def main():
    """Main function to download all klines data."""
    total_days = (END_DATE - START_DATE).days + 1
    total_tasks = total_days * len(SYMBOLS)

    with tqdm(total=total_tasks, desc="Downloading data") as pbar:
        for symbol in SYMBOLS:
            for trading_date in daterange(START_DATE, END_DATE):
                download_day(symbol, trading_date)
                pbar.update(1)


if __name__ == "__main__":
    main()
