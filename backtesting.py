"""Backtesting module for cryptocurrency trading with perfect knowledge."""
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from load_data import load_data


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


def load_day_data(data_dir, trading_date):
    """
    Load data for a specific day across all tickers.
    
    Args:
        data_dir: Path to data directory
        trading_date: Date object for the trading day
        
    Returns:
        Dictionary with ticker as key and DataFrame as value for that day
    """
    data_dir = Path(data_dir)
    day_data = {}
    
    for symbol_dir in data_dir.iterdir():
        if not symbol_dir.is_dir():
            continue
        
        symbol = symbol_dir.name
        filename = f"{symbol}-1m-{trading_date}.csv"
        csv_file = symbol_dir / filename
        
        if csv_file.exists():
            try:
                df = pd.read_csv(csv_file)
                if 'open_time' in df.columns:
                    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
                day_data[symbol] = df
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
    
    return day_data


def max_profit_per_day(day_data, initial_balance=10000, target=1000000):
    """
    Calculate maximum profit for a single day with Long/Short positions.
    Uses perfect knowledge to find optimal trades across all assets.
    
    Strategy: With perfect knowledge of all future prices:
    1. Find all profitable opportunities across all assets
    2. Execute trades optimally, allowing multiple simultaneous positions
    3. Close positions at optimal exit points
    
    Args:
        day_data: Dictionary of {ticker: DataFrame} for the day
        initial_balance: Starting balance
        target: Target balance to achieve
        
    Returns:
        tuple: (final_balance, all_trades, achieved_target)
    """
    balance = initial_balance
    trades = []
    
    # Track open positions: {ticker: [(entry_price, quantity, type, entry_time, entry_minute), ...]}
    positions = {ticker: [] for ticker in day_data.keys()}
    
    # Get all price points across all tickers, sorted by time
    all_events = []
    for ticker, df in day_data.items():
        for idx, row in df.iterrows():
            all_events.append({
                'ticker': ticker,
                'idx': idx,
                'time': row['open_time'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close']
            })
    
    # Sort by time
    all_events.sort(key=lambda x: x['time'])
    
    # Build price sequences for each ticker
    ticker_events = {}
    for ticker in day_data.keys():
        ticker_events[ticker] = [e for e in all_events if e['ticker'] == ticker]
    
    # Process each minute across all tickers
    for i, event in enumerate(all_events):
        ticker = event['ticker']
        current_price = event['close']
        current_time = event['time']
        
        # Close existing positions for this ticker if optimal
        positions_to_close = []
        for pos_idx, (entry_price, quantity, pos_type, _, _) in enumerate(
            positions[ticker]
        ):
            should_close = False
            profit = 0
            
            # Find best future price for this ticker to decide if we should close now
            ticker_future = ticker_events[ticker]
            current_ticker_idx = next(
                (j for j, e in enumerate(ticker_future)
                 if e['time'] == current_time),
                None
            )
            
            if current_ticker_idx is not None and current_ticker_idx < len(ticker_future) - 1:
                # Check if there's a better exit point in the future
                future_prices = [e['close'] for e in ticker_future[current_ticker_idx + 1:]]
                
                if pos_type == 'LONG':
                    max_future_price = (
                        max(future_prices) if future_prices else current_price
                    )
                    # Close if current price is the peak or if we've reached target
                    if (current_price >= max_future_price or
                            balance + quantity * current_price >= target):
                        profit = quantity * (current_price - entry_price)
                        should_close = True
                elif pos_type == 'SHORT':
                    min_future_price = (
                        min(future_prices) if future_prices else current_price
                    )
                    # Close if current price is the bottom or if we've reached target
                    short_profit = quantity * (entry_price - current_price)
                    if (current_price <= min_future_price or
                            balance + quantity * entry_price + short_profit >= target):
                        profit = short_profit
                        should_close = True
            else:
                # Last price point, close position
                if pos_type == 'LONG':
                    profit = quantity * (current_price - entry_price)
                else:
                    profit = quantity * (entry_price - current_price)
                should_close = True
            
            if should_close:
                if pos_type == 'LONG':
                    balance += quantity * current_price
                else:  # SHORT
                    balance += quantity * entry_price + profit
                
                trades.append({
                    'ticker': ticker,
                    'time': current_time,
                    'minute': i,
                    'action': f'CLOSE_{pos_type}',
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'quantity': quantity,
                    'profit_loss': profit,
                    'balance_after': balance
                })
                positions_to_close.append(pos_idx)
        
        # Remove closed positions
        for pos_idx in sorted(positions_to_close, reverse=True):
            positions[ticker].pop(pos_idx)
        
        # Check if we've reached target
        if balance >= target:
            # Close all remaining positions
            for ticker_pos in positions.values():
                for entry_price, quantity, pos_type, _, _ in ticker_pos:
                    if pos_type == 'LONG':
                        balance += quantity * current_price
                    elif pos_type == 'SHORT':
                        profit = quantity * (entry_price - current_price)
                        balance += quantity * entry_price + profit
            break
        
        # Find best opportunity across ALL tickers at this moment
        # With perfect knowledge, find the best trade from current time to end of day
        if balance > 0:
            best_opportunity = None
            best_return = 0
            
            # Check all tickers for best opportunity from current time onwards
            for check_ticker in day_data.keys():
                ticker_future = ticker_events[check_ticker]
                current_ticker_idx = next(
                    (j for j, e in enumerate(ticker_future)
                     if e['time'] == current_time),
                    None
                )
                
                if (current_ticker_idx is not None and
                        current_ticker_idx < len(ticker_future) - 1):
                    # Get the current price for THIS ticker at this time
                    ticker_price = ticker_future[current_ticker_idx]['close']
                    future_events = ticker_future[current_ticker_idx + 1:]
                    future_prices = [e['close'] for e in future_events]
                    
                    if not future_prices:
                        continue
                    
                    # Find best LONG opportunity: buy now, sell at max future price
                    max_future_price = max(future_prices)
                    if max_future_price > ticker_price:
                        long_return = ((max_future_price - ticker_price) /
                                       ticker_price)
                        if long_return > best_return:
                            best_return = long_return
                            best_opportunity = {
                                'ticker': check_ticker,
                                'price': ticker_price,
                                'type': 'LONG',
                                'exit_price': max_future_price,
                                'return': long_return,
                                'time': current_time
                            }
                    
                    # Find best SHORT opportunity: short now, cover at min price
                    min_future_price = min(future_prices)
                    if min_future_price < ticker_price:
                        short_return = ((ticker_price - min_future_price) /
                                        ticker_price)
                        if short_return > best_return:
                            best_return = short_return
                            best_opportunity = {
                                'ticker': check_ticker,
                                'price': ticker_price,
                                'type': 'SHORT',
                                'exit_price': min_future_price,
                                'return': short_return,
                                'time': current_time
                            }
            
            # Execute best opportunity if found
            # Allow opening new positions even if we have existing ones
            if best_opportunity and best_return > 0:
                opp_ticker = best_opportunity['ticker']
                opp_price = best_opportunity['price']
                opp_type = best_opportunity['type']
                
                quantity = balance / opp_price
                
                if opp_type == 'LONG':
                    cost = quantity * opp_price
                    positions[opp_ticker].append(
                        (opp_price, quantity, 'LONG', current_time, i)
                    )
                    trades.append({
                        'ticker': opp_ticker,
                        'time': current_time,
                        'minute': i,
                        'action': 'OPEN_LONG',
                        'entry_price': opp_price,
                        'exit_price': None,
                        'quantity': quantity,
                        'profit_loss': 0,
                        'balance_after': balance - cost
                    })
                    balance -= cost
                else:  # SHORT
                    margin = quantity * opp_price
                    positions[opp_ticker].append(
                        (opp_price, quantity, 'SHORT', current_time, i)
                    )
                    trades.append({
                        'ticker': opp_ticker,
                        'time': current_time,
                        'minute': i,
                        'action': 'OPEN_SHORT',
                        'entry_price': opp_price,
                        'exit_price': None,
                        'quantity': quantity,
                        'profit_loss': 0,
                        'balance_after': balance - margin
                    })
                    balance -= margin
    
    # Close all remaining positions at the end
    if all_events:
        last_event = all_events[-1]
        final_price = last_event['close']
        final_time = last_event['time']
        
        for ticker, ticker_positions in positions.items():
            for entry_price, quantity, pos_type, _, _ in ticker_positions:
                if pos_type == 'LONG':
                    profit = quantity * (final_price - entry_price)
                    balance += quantity * final_price
                    trades.append({
                        'ticker': ticker,
                        'time': final_time,
                        'minute': len(all_events) - 1,
                        'action': 'CLOSE_LONG',
                        'entry_price': entry_price,
                        'exit_price': final_price,
                        'quantity': quantity,
                        'profit_loss': profit,
                        'balance_after': balance
                    })
                elif pos_type == 'SHORT':
                    profit = quantity * (entry_price - final_price)
                    balance += quantity * entry_price + profit
                    trades.append({
                        'ticker': ticker,
                        'time': final_time,
                        'minute': len(all_events) - 1,
                        'action': 'CLOSE_SHORT',
                        'entry_price': entry_price,
                        'exit_price': final_price,
                        'quantity': quantity,
                        'profit_loss': profit,
                        'balance_after': balance
                    })
    
    achieved_target = balance >= target
    return balance, trades, achieved_target


def main():
    """Main function to run per-day backtesting and generate CSV files."""
    data_dir = "binance_december_data"
    initial_balance = 10000
    target_balance = 1000000
    start_date = date(2025, 12, 1)
    end_date = date(2025, 12, 31)
    
    # Storage for results
    all_trades = []
    daily_summaries = []
    
    print("Running per-day backtesting...")
    print("=" * 80)
    
    for trading_date in daterange(start_date, end_date):
        print(f"\nProcessing {trading_date}...")
        
        # Load day data
        day_data = load_day_data(data_dir, trading_date)
        
        if not day_data:
            print(f"  No data available for {trading_date}")
            continue
        
        # Calculate max profit for the day
        final_balance, trades, achieved_target = max_profit_per_day(
            day_data, initial_balance, target_balance
        )
        
        profit = final_balance - initial_balance
        profit_pct = (profit / initial_balance) * 100
        
        # Add date to trades
        for trade in trades:
            trade['date'] = trading_date
        
        all_trades.extend(trades)
        
        # Daily summary
        daily_summaries.append({
            'date': trading_date,
            'initial_balance': initial_balance,
            'final_balance': final_balance,
            'profit_loss': profit,
            'profit_pct': profit_pct,
            'total_trades': len(trades),
            'achieved_1m_target': achieved_target,
            'tickers_traded': len(set(trade['ticker'] for trade in trades))
        })
        
        print(f"  Final balance: ${final_balance:,.2f}")
        print(f"  Profit: ${profit:,.2f} ({profit_pct:+.2f}%)")
        print(f"  Total trades: {len(trades)}")
        print(f"  Achieved $1M target: {'YES' if achieved_target else 'NO'}")
    
    # Generate CSV files
    print("\n" + "=" * 80)
    print("Generating CSV files...")
    
    # Create result directory
    result_dir = Path("result")
    result_dir.mkdir(exist_ok=True)
    
    # All trades CSV
    if all_trades:
        trades_df = pd.DataFrame(all_trades)
        trades_df = trades_df.sort_values(['date', 'minute'])
        trades_csv = result_dir / 'all_trades_per_day.csv'
        trades_df.to_csv(trades_csv, index=False)
        print(f"  Created: {trades_csv} ({len(trades_df)} trades)")
    
    # Daily summary CSV
    if daily_summaries:
        summary_df = pd.DataFrame(daily_summaries)
        summary_csv = result_dir / 'daily_results_summary.csv'
        summary_df.to_csv(summary_csv, index=False)
        print(f"  Created: {summary_csv} ({len(summary_df)} days)")
        
        # Print summary statistics
        print("\n" + "=" * 80)
        print("SUMMARY STATISTICS:")
        achieved_count = summary_df['achieved_1m_target'].sum()
        max_profit = summary_df['profit_loss'].max()
        avg_profit = summary_df['profit_loss'].mean()
        print(f"  Days that achieved $1M target: {achieved_count}")
        print(f"  Maximum profit in a day: ${max_profit:,.2f}")
        print(f"  Average profit per day: ${avg_profit:,.2f}")
        print(f"  Total trades across all days: {len(all_trades)}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
