"""Script to analyze 30-day compounding results."""
from pathlib import Path

import pandas as pd

INITIAL_BALANCE = 10000
TARGET_BALANCE = 1000000
RESULT_DIR = Path("result")
SUMMARY_CSV = RESULT_DIR / 'daily_results_summary.csv'


def main():
    """Main function to analyze compounding results."""
    df = pd.read_csv(SUMMARY_CSV)
    balance = INITIAL_BALANCE

    print("=" * 80)
    print("30-DAY COMPOUNDING ANALYSIS")
    print("=" * 80)
    print(f"\nStarting balance: ${balance:,.2f}")
    print(f"Target: ${TARGET_BALANCE:,.2f}")
    print("\nDay-by-day compounding progress:\n")

    for i, row in df.iterrows():
        daily_return = row['final_balance'] / row['initial_balance']
        balance = balance * daily_return
        pct = (daily_return - 1) * 100

        print(f"Day {i+1:2d} ({row['date']}): "
              f"${balance:,.2f} ({pct:+.2f}% daily return)")

        if balance >= TARGET_BALANCE:
            print(f"\n{'='*80}")
            print(f"*** REACHED $1M TARGET on Day {i+1}! ***")
            print(f"{'='*80}")
            break

    print(f"\n{'='*80}")
    print("FINAL RESULTS:")
    print(f"{'='*80}")
    print(f"Final balance after {len(df)} days: ${balance:,.2f}")
    print(f"Target: ${TARGET_BALANCE:,.2f}")
    print(f"Difference: ${TARGET_BALANCE - balance:,.2f}")
    print(f"Achieved $1M target: {'YES' if balance >= TARGET_BALANCE else 'NO'}")

    if balance < TARGET_BALANCE:
        # Calculate how many more days needed (using average daily return)
        avg_daily_return = (df['final_balance'] / df['initial_balance']).mean()
        days_needed = 0
        test_balance = balance
        while test_balance < TARGET_BALANCE and days_needed < 100:
            test_balance *= avg_daily_return
            days_needed += 1

        if days_needed < 100:
            avg_return_pct = (avg_daily_return - 1) * 100
            print(f"\nAt average daily return of {avg_return_pct:.2f}%, "
                  f"would need {days_needed} more days to reach $1M")


if __name__ == "__main__":
    main()
