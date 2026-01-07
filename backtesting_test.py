"""
Test module for backtesting validation using VectorBT.

This module imports the core DP algorithm from backtesting.py and validates
the results independently using VectorBT's portfolio simulation.

Usage:
    python -m unittest backtesting_test -v
    python backtesting_test.py
"""
import unittest
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import vectorbt as vbt

from backtesting import (
    daterange,
    load_day_data,
    dp_optimal_trades,
    find_all_trades,
)


class TestVectorBTValidation(unittest.TestCase):
    """Validate DP algorithm results against VectorBT portfolio simulation."""
    
    DATA_DIR = "binance_december_data"
    INITIAL_BALANCE = 10000
    TARGET_BALANCE = 1000000
    TOLERANCE = 0.01  # Allow $0.01 difference for floating point
    
    @classmethod
    def setUpClass(cls):
        """Print VectorBT version once before all tests."""
        print(f"\nUsing VectorBT v{vbt.__version__} for validation")
    
    def build_price_dataframe(self, day_data):
        """Build a combined price DataFrame from day_data."""
        price_dfs = []
        for ticker, df in day_data.items():
            df_copy = df.copy()
            if 'open_time' in df_copy.columns:
                df_copy = df_copy.set_index('open_time')
            df_copy = df_copy[['close']].rename(columns={'close': ticker})
            price_dfs.append(df_copy)
        
        price_df = pd.concat(price_dfs, axis=1)
        price_df = price_df.sort_index().ffill()
        return price_df
    
    def simulate_trades_vectorbt(self, trades, initial_balance, day_data):
        """
        Simulate trades using VectorBT's Portfolio simulation.
        
        Uses VectorBT's Portfolio.from_signals() to independently simulate
        the trade sequence and calculate P&L.
        """
        if not trades:
            return initial_balance
        
        price_df = self.build_price_dataframe(day_data)
        balance = initial_balance
        
        for trade in trades:
            ticker = trade['ticker']
            entry_price = trade['entry_price']
            exit_price = trade['exit_price']
            entry_time = trade['entry_time']
            exit_time = trade['exit_time']
            trade_type = trade['type']
            
            if ticker not in price_df.columns:
                continue
            
            # Create a mini price series for this trade
            trade_prices = pd.Series(
                [entry_price, exit_price],
                index=[entry_time, exit_time],
                name=ticker
            )
            
            if trade_type == 'LONG':
                entries = pd.Series([True, False], index=[entry_time, exit_time])
                exits = pd.Series([False, True], index=[entry_time, exit_time])
                
                pf = vbt.Portfolio.from_signals(
                    close=trade_prices,
                    entries=entries,
                    exits=exits,
                    init_cash=balance,
                    fees=0,
                    slippage=0,
                    freq='1min'
                )
            else:
                entries = pd.Series([True, False], index=[entry_time, exit_time])
                exits = pd.Series([False, True], index=[entry_time, exit_time])
                
                pf = vbt.Portfolio.from_signals(
                    close=trade_prices,
                    short_entries=entries,
                    short_exits=exits,
                    init_cash=balance,
                    fees=0,
                    slippage=0,
                    freq='1min'
                )
            
            balance = pf.final_value()
        
        return balance
    
    def run_day_test(self, trading_date):
        """Run validation for a single day and return results."""
        day_data = load_day_data(self.DATA_DIR, trading_date)
        
        if not day_data:
            self.skipTest(f"No data available for {trading_date}")
        
        # Run DP algorithm
        dp_balance, optimal_trades, achieved_target = dp_optimal_trades(
            day_data, self.INITIAL_BALANCE, self.TARGET_BALANCE
        )
        
        # Validate with VectorBT
        vbt_balance = self.simulate_trades_vectorbt(
            optimal_trades, self.INITIAL_BALANCE, day_data
        )
        
        return dp_balance, vbt_balance, len(optimal_trades)


def generate_day_tests():
    """Generate test methods for each day in December 2025."""
    start_date = date(2025, 12, 1)
    end_date = date(2025, 12, 31)
    
    for single_date in daterange(start_date, end_date):
        def make_test(d):
            def test_method(self):
                dp_balance, vbt_balance, num_trades = self.run_day_test(d)
                
                self.assertAlmostEqual(
                    dp_balance,
                    vbt_balance,
                    delta=self.TOLERANCE,
                    msg=f"DP=${dp_balance:,.2f} vs VBT=${vbt_balance:,.2f} "
                        f"(diff=${abs(dp_balance - vbt_balance):.2f}, {num_trades} trades)"
                )
            return test_method
        
        test_name = f"test_day_{single_date.strftime('%Y_%m_%d')}"
        setattr(TestVectorBTValidation, test_name, make_test(single_date))


class TestDPAlgorithm(unittest.TestCase):
    """Unit tests for DP algorithm components."""
    
    def test_find_all_trades_long(self):
        """Test that find_all_trades correctly identifies long opportunities."""
        # Create mock data with clear long opportunity
        mock_df = pd.DataFrame({
            'open_time': pd.date_range('2025-12-01', periods=5, freq='1min'),
            'close': [100.0, 101.0, 102.0, 101.0, 100.0]
        })
        day_data = {'TESTUSDT': mock_df}
        
        trades, all_events = find_all_trades(day_data)
        
        # Should find at least one long trade (buy at 100, sell at 102)
        long_trades = [t for t in trades if t['type'] == 'LONG']
        self.assertGreater(len(long_trades), 0, "Should find long opportunities")
        
        # Best long trade should have ~2% return
        best_long = max(long_trades, key=lambda t: t['return'])
        self.assertGreater(best_long['return'], 0.01)
    
    def test_find_all_trades_short(self):
        """Test that find_all_trades correctly identifies short opportunities."""
        # Create mock data with clear short opportunity
        mock_df = pd.DataFrame({
            'open_time': pd.date_range('2025-12-01', periods=5, freq='1min'),
            'close': [102.0, 101.0, 100.0, 101.0, 102.0]
        })
        day_data = {'TESTUSDT': mock_df}
        
        trades, all_events = find_all_trades(day_data)
        
        # Should find at least one short trade (short at 102, cover at 100)
        short_trades = [t for t in trades if t['type'] == 'SHORT']
        self.assertGreater(len(short_trades), 0, "Should find short opportunities")
    
    def test_dp_optimal_trades_empty_data(self):
        """Test DP handles empty data gracefully."""
        day_data = {}
        balance, trades, achieved = dp_optimal_trades(day_data, 10000, 1000000)
        
        self.assertEqual(balance, 10000)
        self.assertEqual(len(trades), 0)
        self.assertFalse(achieved)
    
    def test_dp_optimal_trades_no_opportunity(self):
        """Test DP handles flat prices (no trading opportunity)."""
        mock_df = pd.DataFrame({
            'open_time': pd.date_range('2025-12-01', periods=5, freq='1min'),
            'close': [100.0, 100.0, 100.0, 100.0, 100.0]
        })
        day_data = {'TESTUSDT': mock_df}
        
        balance, trades, achieved = dp_optimal_trades(day_data, 10000, 1000000)
        
        self.assertEqual(balance, 10000)
        self.assertEqual(len(trades), 0)


class TestTradeSequencing(unittest.TestCase):
    """Tests for trade sequencing constraints."""
    
    DATA_DIR = "binance_december_data"
    
    def test_trades_are_sequential(self):
        """Verify that selected trades don't overlap in time."""
        day_data = load_day_data(self.DATA_DIR, date(2025, 12, 1))
        
        if not day_data:
            self.skipTest("No data available for 2025-12-01")
        
        _, trades, _ = dp_optimal_trades(day_data, 10000, 1000000)
        
        for i in range(len(trades) - 1):
            current_exit = trades[i]['exit_time']
            next_entry = trades[i + 1]['entry_time']
            
            self.assertLessEqual(
                current_exit,
                next_entry,
                f"Trade {i} exits at {current_exit} but trade {i+1} enters at {next_entry}"
            )
    
    def test_trades_compound_correctly(self):
        """Verify that balance compounds correctly through trades."""
        day_data = load_day_data(self.DATA_DIR, date(2025, 12, 1))
        
        if not day_data:
            self.skipTest("No data available for 2025-12-01")
        
        initial = 10000
        dp_balance, trades, _ = dp_optimal_trades(day_data, initial, 1000000)
        
        # Manually compound through trades
        manual_balance = initial
        for trade in trades:
            if trade['type'] == 'LONG':
                ret = (trade['exit_price'] - trade['entry_price']) / trade['entry_price']
            else:
                ret = (trade['entry_price'] - trade['exit_price']) / trade['entry_price']
            manual_balance *= (1 + ret)
        
        self.assertAlmostEqual(dp_balance, manual_balance, places=2)


# Generate test methods for each day
generate_day_tests()


if __name__ == "__main__":
    unittest.main(verbosity=2)
