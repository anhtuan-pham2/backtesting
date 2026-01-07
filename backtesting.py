"""Backtesting module for cryptocurrency trading with perfect knowledge."""
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from load_data import load_data


def daterange(start_date, end_date):
    """Generate date range from start to end (inclusive)."""
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def load_day_data(data_dir, trading_date):
    """Load data for a specific day across all tickers."""
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


def precompute_suffix_arrays(ticker_events):
    """Precompute suffix max and min arrays for future price lookups."""
    n = len(ticker_events)
    if n == 0:
        return [], []
    
    suffix_max = [0.0] * n
    suffix_min = [float('inf')] * n
    
    suffix_max[n - 1] = 0.0
    suffix_min[n - 1] = float('inf')
    
    for i in range(n - 2, -1, -1):
        next_price = ticker_events[i + 1]['close']
        suffix_max[i] = max(next_price, suffix_max[i + 1])
        suffix_min[i] = min(next_price, suffix_min[i + 1])
    
    return suffix_max, suffix_min


def max_profit_per_day(day_data, initial_balance=10000, target=1000000):
    """
    Calculate maximum profit for a single day with Long/Short positions.
    Uses perfect knowledge to find optimal trades across all assets.
    """
    balance = initial_balance
    trades = []
    positions = {ticker: [] for ticker in day_data.keys()}
    
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
    
    all_events.sort(key=lambda x: x['time'])
    
    ticker_events = {}
    for ticker in day_data.keys():
        ticker_events[ticker] = [e for e in all_events if e['ticker'] == ticker]
    
    ticker_time_to_idx = {}
    for ticker, events in ticker_events.items():
        ticker_time_to_idx[ticker] = {e['time']: i for i, e in enumerate(events)}
    
    ticker_suffix_max = {}
    ticker_suffix_min = {}
    for ticker, events in ticker_events.items():
        suffix_max, suffix_min = precompute_suffix_arrays(events)
        ticker_suffix_max[ticker] = suffix_max
        ticker_suffix_min[ticker] = suffix_min
    
    for i, event in enumerate(all_events):
        ticker = event['ticker']
        current_price = event['close']
        current_time = event['time']
        
        positions_to_close = []
        for pos_idx, (entry_price, quantity, pos_type, _, _) in enumerate(
            positions[ticker]
        ):
            should_close = False
            profit = 0
            
            current_ticker_idx = ticker_time_to_idx[ticker].get(current_time)
            
            if current_ticker_idx is not None and current_ticker_idx < len(ticker_events[ticker]) - 1:
                max_future_price = ticker_suffix_max[ticker][current_ticker_idx]
                min_future_price = ticker_suffix_min[ticker][current_ticker_idx]
                
                if pos_type == 'LONG':
                    if (current_price >= max_future_price or
                            balance + quantity * current_price >= target):
                        profit = quantity * (current_price - entry_price)
                        should_close = True
                elif pos_type == 'SHORT':
                    short_profit = quantity * (entry_price - current_price)
                    if (current_price <= min_future_price or
                            balance + quantity * entry_price + short_profit >= target):
                        profit = short_profit
                        should_close = True
            else:
                if pos_type == 'LONG':
                    profit = quantity * (current_price - entry_price)
                else:
                    profit = quantity * (entry_price - current_price)
                should_close = True
            
            if should_close:
                if pos_type == 'LONG':
                    balance += quantity * current_price
                else:
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
        
        for pos_idx in sorted(positions_to_close, reverse=True):
            positions[ticker].pop(pos_idx)
        
        if balance >= target:
            for ticker_pos in positions.values():
                for entry_price, quantity, pos_type, _, _ in ticker_pos:
                    if pos_type == 'LONG':
                        balance += quantity * current_price
                    elif pos_type == 'SHORT':
                        profit = quantity * (entry_price - current_price)
                        balance += quantity * entry_price + profit
            break
        
        if balance > 0:
            best_opportunity = None
            best_return = 0
            
            for check_ticker in day_data.keys():
                current_ticker_idx = ticker_time_to_idx[check_ticker].get(current_time)
                
                if (current_ticker_idx is not None and
                        current_ticker_idx < len(ticker_events[check_ticker]) - 1):
                    ticker_price = ticker_events[check_ticker][current_ticker_idx]['close']
                    
                    max_future_price = ticker_suffix_max[check_ticker][current_ticker_idx]
                    min_future_price = ticker_suffix_min[check_ticker][current_ticker_idx]
                    
                    if max_future_price > ticker_price:
                        long_return = (max_future_price - ticker_price) / ticker_price
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
                    
                    if min_future_price < ticker_price:
                        short_return = (ticker_price - min_future_price) / ticker_price
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
                else:
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
    
    all_trades = []
    daily_summaries = []
    
    print("Running per-day backtesting...")
    print("=" * 80)
    
    for trading_date in daterange(start_date, end_date):
        print(f"\nProcessing {trading_date}...")
        
        day_data = load_day_data(data_dir, trading_date)
        
        if not day_data:
            print(f"  No data available for {trading_date}")
            continue
        
        final_balance, trades, achieved_target = max_profit_per_day(
            day_data, initial_balance, target_balance
        )
        
        profit = final_balance - initial_balance
        profit_pct = (profit / initial_balance) * 100
        
        for trade in trades:
            trade['date'] = trading_date
        
        all_trades.extend(trades)
        
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
    
    print("\n" + "=" * 80)
    print("Generating CSV files...")
    
    result_dir = Path("result")
    result_dir.mkdir(exist_ok=True)
    
    if all_trades:
        trades_df = pd.DataFrame(all_trades)
        trades_df = trades_df.sort_values(['date', 'minute'])
        trades_csv = result_dir / 'all_trades_per_day.csv'
        trades_df.to_csv(trades_csv, index=False)
        print(f"  Created: {trades_csv} ({len(trades_df)} trades)")
    
    if daily_summaries:
        summary_df = pd.DataFrame(daily_summaries)
        summary_csv = result_dir / 'daily_results_summary.csv'
        summary_df.to_csv(summary_csv, index=False)
        print(f"  Created: {summary_csv} ({len(summary_df)} days)")
        
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
