"""Module for loading Binance klines data from CSV files."""
from pathlib import Path

import pandas as pd


def load_data(data_dir="binance_december_data"):
    """
    Load Binance klines data from CSV files into a dictionary structure.
    
    Args:
        data_dir: Path to the directory containing the downloaded data
        
    Returns:
        Dictionary with ticker symbols as keys and pandas DataFrames as values.
        Each DataFrame contains all daily data concatenated with columns:
        open_time, open, high, low, close, volume, etc.
        
    Example usage:
        all_data = load_data()
        prices = all_data['BTCUSDT']['close'].values
    """
    data_dir = Path(data_dir)
    
    if not data_dir.exists():
        raise ValueError(f"Data directory {data_dir} does not exist")
    
    all_data = {}
    
    # Iterate through each symbol directory
    for symbol_dir in data_dir.iterdir():
        if not symbol_dir.is_dir():
            continue
            
        symbol = symbol_dir.name
        csv_files = sorted(symbol_dir.glob("*.csv"))
        
        if not csv_files:
            print(f"Warning: No CSV files found for {symbol}")
            continue
        
        # Read and concatenate all CSV files for this symbol
        dfs = []
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                # Convert open_time to datetime if needed
                if 'open_time' in df.columns:
                    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
                dfs.append(df)
            except Exception as e:
                print(f"Error reading {csv_file}: {e}")
                continue
        
        if dfs:
            # Concatenate all dataframes and sort by open_time
            combined_df = pd.concat(dfs, ignore_index=True)
            combined_df = combined_df.sort_values('open_time').reset_index(drop=True)
            all_data[symbol] = combined_df
            print(f"Loaded {len(combined_df)} rows for {symbol}")
        else:
            print(f"Warning: No valid data loaded for {symbol}")
    
    return all_data
