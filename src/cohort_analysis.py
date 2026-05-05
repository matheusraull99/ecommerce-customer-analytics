"""
Cohort Analysis Module
----------------------
Performs customer cohort retention analysis to measure how customers from
different acquisition periods retain over time.

Cohort analysis is essential for understanding customer lifecycle, evaluating
acquisition channel quality, and identifying retention drop-off points.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def _get_cohort_month(date: pd.Timestamp) -> pd.Timestamp:
    """Truncate a date to its month (e.g., 2024-03-15 -> 2024-03-01)."""
    return date.to_period('M').to_timestamp()


def build_cohort_table(transactions: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build a cohort retention table.

    Parameters
    ----------
    transactions : pd.DataFrame
        Must contain customer_id and transaction_date columns.

    Returns
    -------
    cohort_counts : pd.DataFrame
        Absolute customer counts per cohort and period.
    retention : pd.DataFrame
        Retention rates (0–1) per cohort and period.
    """
    df = transactions.copy()
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df['order_month'] = df['transaction_date'].apply(_get_cohort_month)

    # Cohort = first purchase month of each customer
    df['cohort_month'] = df.groupby('customer_id')['order_month'].transform('min')

    # Period number = months between first purchase and current order
    df['period_number'] = ((df['order_month'].dt.year - df['cohort_month'].dt.year) * 12 +
                           (df['order_month'].dt.month - df['cohort_month'].dt.month))

    cohort_data = df.groupby(['cohort_month', 'period_number'])['customer_id'].nunique().reset_index()
    cohort_counts = cohort_data.pivot(index='cohort_month', columns='period_number', values='customer_id')

    cohort_size = cohort_counts.iloc[:, 0]
    retention = cohort_counts.divide(cohort_size, axis=0)

    return cohort_counts, retention


def cohort_revenue_table(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Build a cohort table showing average revenue per customer over time.

    Returns
    -------
    pd.DataFrame
        Average revenue per customer per cohort and period.
    """
    df = transactions.copy()
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df['order_month'] = df['transaction_date'].apply(_get_cohort_month)
    df['cohort_month'] = df.groupby('customer_id')['order_month'].transform('min')
    df['period_number'] = ((df['order_month'].dt.year - df['cohort_month'].dt.year) * 12 +
                           (df['order_month'].dt.month - df['cohort_month'].dt.month))

    revenue = df.groupby(['cohort_month', 'period_number']).agg(
        revenue=('revenue', 'sum'),
        customers=('customer_id', 'nunique')
    ).reset_index()
    revenue['avg_revenue_per_customer'] = revenue['revenue'] / revenue['customers']

    return revenue.pivot(index='cohort_month', columns='period_number', values='avg_revenue_per_customer')


def retention_summary(retention: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize retention rates by period (averaged across all cohorts).
    """
    avg_retention = retention.mean(axis=0).reset_index()
    avg_retention.columns = ['period_number', 'avg_retention_rate']
    avg_retention['avg_retention_rate'] = (avg_retention['avg_retention_rate'] * 100).round(2)
    return avg_retention


if __name__ == '__main__':
    transactions = pd.read_csv('/home/claude/ecommerce-customer-analytics/data/transactions.csv')
    cohort_counts, retention = build_cohort_table(transactions)

    print('=' * 70)
    print('COHORT RETENTION RATES (first 12 months)')
    print('=' * 70)
    print((retention.iloc[:12, :12] * 100).round(1).to_string())

    print('\n')
    print('=' * 70)
    print('AVERAGE RETENTION ACROSS ALL COHORTS')
    print('=' * 70)
    summary = retention_summary(retention)
    print(summary.head(12).to_string(index=False))
