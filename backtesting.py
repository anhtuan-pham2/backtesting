"""
Optimal Backtesting using Dynamic Programming

This module finds the globally optimal sequence of trades for cryptocurrency
trading with perfect knowledge of future prices.

Time Complexity: O(N² × M) where N = minutes per day, M = number of tickers
Space Complexity: O(N² × M) for storing all possible trades
"""
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


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


def find_all_trades(day_data):
    """
    Find all possible profitable trades across all tickers.
    
    Time Complexity: O(N² × M) where N = minutes, M = tickers
    
    Returns:
        trades: List of all possible profitable trades
        all_events: Sorted list of all price events
    """
    all_events = []
    for ticker, df in day_data.items():
        for idx, row in df.iterrows():
            all_events.append({
                'ticker': ticker,
                'idx': idx,
                'time': row['open_time'],
                'close': row['close']
            })
    
    all_events.sort(key=lambda x: x['time'])
    
    ticker_events = {ticker: [] for ticker in day_data.keys()}
    for global_idx, event in enumerate(all_events):
        ticker_events[event['ticker']].append((global_idx, event))
    
    trades = []
    
    for ticker, events in ticker_events.items():
        n = len(events)
        for i in range(n):
            entry_global_idx, entry_event = events[i]
            entry_price = entry_event['close']
            
            for j in range(i + 1, n):
                exit_global_idx, exit_event = events[j]
                exit_price = exit_event['close']
                
                if exit_price > entry_price:
                    return_pct = (exit_price - entry_price) / entry_price
                    trades.append({
                        'entry_idx': entry_global_idx,
                        'exit_idx': exit_global_idx,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'ticker': ticker,
                        'type': 'LONG',
                        'return': return_pct,
                        'entry_time': entry_event['time'],
                        'exit_time': exit_event['time']
                    })
                
                if exit_price < entry_price:
                    return_pct = (entry_price - exit_price) / entry_price
                    trades.append({
                        'entry_idx': entry_global_idx,
                        'exit_idx': exit_global_idx,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'ticker': ticker,
                        'type': 'SHORT',
                        'return': return_pct,
                        'entry_time': entry_event['time'],
                        'exit_time': exit_event['time']
                    })
    
    return trades, all_events


def dp_optimal_trades(day_data, initial_balance=10000, target=1000000):
    """
    Use Dynamic Programming to find optimal sequence of non-overlapping trades.
    
    Algorithm:
        dp[i] = maximum balance multiplier achievable starting from time index i
        
        For each time point i (from end to start):
            Option 1: Skip this time point -> dp[i] = dp[i+1]
            Option 2: Take a trade starting at i -> dp[i] = (1 + return) * dp[exit_idx]
        
        Choose the option with maximum multiplier.
    
    Time Complexity: O(T) where T = total number of trades (≤ N² × M)
    Space Complexity: O(N + T)
    
    Returns:
        final_balance: Maximum achievable balance
        optimal_trades: List of trades in the optimal sequence
        achieved_target: Whether $1M target was reached
    """
    trades, all_events = find_all_trades(day_data)
    n = len(all_events)
    
    if n == 0:
        return initial_balance, [], False
    
    trades_by_entry = {i: [] for i in range(n)}
    for trade in trades:
        trades_by_entry[trade['entry_idx']].append(trade)
    
    dp = [(1.0, None)] * (n + 1)
    
    for i in range(n - 1, -1, -1):
        best_mult = dp[i + 1][0]
        best_trade = None
        
        for trade in trades_by_entry[i]:
            exit_idx = trade['exit_idx']
            trade_mult = 1 + trade['return']
            future_mult = dp[exit_idx][0] if exit_idx < n else 1.0
            total_mult = trade_mult * future_mult
            
            if total_mult > best_mult:
                best_mult = total_mult
                best_trade = trade
        
        dp[i] = (best_mult, best_trade)
    
    optimal_trades = []
    i = 0
    while i < n:
        _, trade = dp[i]
        if trade is not None:
            optimal_trades.append(trade)
            i = trade['exit_idx']
        else:
            i += 1
    
    final_balance = initial_balance * dp[0][0]
    achieved_target = final_balance >= target
    
    return final_balance, optimal_trades, achieved_target


def format_trade_sequence(trades, initial_balance):
    """Format trades into a readable sequence with running balance."""
    formatted = []
    balance = initial_balance
    
    for i, trade in enumerate(trades):
        quantity = balance / trade['entry_price']
        
        if trade['type'] == 'LONG':
            profit = quantity * (trade['exit_price'] - trade['entry_price'])
        else:
            profit = quantity * (trade['entry_price'] - trade['exit_price'])
        
        balance = balance * (1 + trade['return'])
        
        formatted.append({
            'trade_num': i + 1,
            'ticker': trade['ticker'],
            'type': trade['type'],
            'entry_time': trade['entry_time'],
            'exit_time': trade['exit_time'],
            'entry_price': trade['entry_price'],
            'exit_price': trade['exit_price'],
            'quantity': quantity,
            'profit': profit,
            'balance_after': balance
        })
    
    return formatted


def save_trade_sequence(trades, trading_date, result_dir):
    """Save trade sequence to CSV file."""
    if not trades:
        return None
    
    sequences_dir = result_dir / 'trade_sequences'
    sequences_dir.mkdir(exist_ok=True)
    
    df = pd.DataFrame(trades)
    filename = sequences_dir / f'{trading_date}_trades.csv'
    df.to_csv(filename, index=False)
    
    return filename


def print_day_results(trading_date, final_balance, initial_balance, trades, achieved_target):
    """Print formatted results for a single day."""
    profit = final_balance - initial_balance
    profit_pct = (profit / initial_balance) * 100
    
    print("=" * 80)
    print(f"Day: {trading_date}")
    print("=" * 80)
    print(f"$1M Target Achievable: {'YES' if achieved_target else 'NO'}")
    print(f"Maximum Profit: ${final_balance:,.2f} ({profit_pct:+.2f}%)")
    print(f"Total Trades: {len(trades)}")
    
    if trades and len(trades) <= 20:
        print("\nTrade Sequence (showing all):")
        for t in trades:
            print(f"  #{t['trade_num']:4d}  {t['type']:5s}  {t['ticker']:8s}  "
                  f"${t['entry_price']:,.2f} → ${t['exit_price']:,.2f}  "
                  f"+${t['profit']:,.2f}  Balance: ${t['balance_after']:,.2f}")
    elif trades:
        print(f"\nTrade Sequence (showing first 10 of {len(trades)}):")
        for t in trades[:10]:
            print(f"  #{t['trade_num']:4d}  {t['type']:5s}  {t['ticker']:8s}  "
                  f"${t['entry_price']:,.2f} → ${t['exit_price']:,.2f}  "
                  f"+${t['profit']:,.2f}  Balance: ${t['balance_after']:,.2f}")
        print(f"  ... and {len(trades) - 10} more trades")
    
    print()


def main():
    """Main function to run DP-optimal backtesting."""
    data_dir = "binance_december_data"
    initial_balance = 10000
    target_balance = 1000000
    start_date = date(2025, 12, 1)
    end_date = date(2025, 12, 31)
    
    result_dir = Path("result")
    result_dir.mkdir(exist_ok=True)
    
    daily_summaries = []
    days_achieved_target = []
    
    print("\n" + "=" * 80)
    print("CRYPTOCURRENCY BACKTESTING - DYNAMIC PROGRAMMING OPTIMAL SOLUTION")
    print("=" * 80)
    print(f"Initial Balance: ${initial_balance:,}")
    print(f"Target: ${target_balance:,}")
    print(f"Period: {start_date} to {end_date}")
    print("=" * 80 + "\n")
    
    for trading_date in daterange(start_date, end_date):
        day_data = load_day_data(data_dir, trading_date)
        
        if not day_data:
            print(f"No data available for {trading_date}")
            continue
        
        final_balance, optimal_trades, achieved_target = dp_optimal_trades(
            day_data, initial_balance, target_balance
        )
        
        formatted_trades = format_trade_sequence(optimal_trades, initial_balance)
        
        save_trade_sequence(formatted_trades, trading_date, result_dir)
        
        print_day_results(trading_date, final_balance, initial_balance, 
                         formatted_trades, achieved_target)
        
        profit = final_balance - initial_balance
        profit_pct = (profit / initial_balance) * 100
        
        daily_summaries.append({
            'date': trading_date,
            'initial_balance': initial_balance,
            'final_balance': final_balance,
            'profit_loss': profit,
            'profit_pct': profit_pct,
            'total_trades': len(optimal_trades),
            'achieved_1m_target': achieved_target
        })
        
        if achieved_target:
            days_achieved_target.append(trading_date)
    
    if daily_summaries:
        summary_df = pd.DataFrame(daily_summaries)
        summary_csv = result_dir / 'daily_results_summary.csv'
        summary_df.to_csv(summary_csv, index=False)
    
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    if days_achieved_target:
        print(f"\n$1M TARGET ACHIEVED ON {len(days_achieved_target)} DAY(S):")
        for d in days_achieved_target:
            print(f"  - {d}")
    else:
        print("\n$1M TARGET: NOT ACHIEVABLE in any single day")
    
    if daily_summaries:
        max_profit = max(s['profit_loss'] for s in daily_summaries)
        max_profit_day = [s['date'] for s in daily_summaries if s['profit_loss'] == max_profit][0]
        avg_profit = sum(s['profit_loss'] for s in daily_summaries) / len(daily_summaries)
        
        print(f"\nMaximum single-day profit: ${max_profit:,.2f} on {max_profit_day}")
        print(f"Average daily profit: ${avg_profit:,.2f}")
        print(f"Total days analyzed: {len(daily_summaries)}")
    
    print(f"\nResults saved to: {result_dir}/")
    print(f"  - daily_results_summary.csv")
    print(f"  - trade_sequences/*.csv")
    print("\nDone!")


if __name__ == "__main__":
    main()
