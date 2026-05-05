"""
RFM Analysis Module
-------------------
Performs Recency, Frequency, and Monetary (RFM) analysis to segment customers
based on their purchasing behavior.

RFM is a proven marketing technique for identifying high-value customer groups,
predicting churn risk, and tailoring campaigns to each segment.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple


def calculate_rfm(transactions: pd.DataFrame, snapshot_date: datetime = None) -> pd.DataFrame:
    """
    Compute RFM metrics for each customer.

    Parameters
    ----------
    transactions : pd.DataFrame
        Must contain columns: customer_id, transaction_date, transaction_id, revenue
    snapshot_date : datetime, optional
        Reference date for recency calculation. Defaults to max transaction date + 1 day.

    Returns
    -------
    pd.DataFrame
        Customer-level dataframe with recency, frequency, and monetary columns.
    """
    df = transactions.copy()
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])

    if snapshot_date is None:
        snapshot_date = df['transaction_date'].max() + pd.Timedelta(days=1)

    rfm = df.groupby('customer_id').agg(
        recency=('transaction_date', lambda x: (snapshot_date - x.max()).days),
        frequency=('transaction_id', 'count'),
        monetary=('revenue', 'sum')
    ).reset_index()

    return rfm


def assign_rfm_scores(rfm: pd.DataFrame, n_quantiles: int = 5) -> pd.DataFrame:
    """
    Assign 1–5 scores for each RFM dimension using quantiles.

    Lower recency is better → higher score.
    Higher frequency and monetary are better → higher score.
    """
    rfm = rfm.copy()

    # Recency: lower = better, so reverse the labels
    rfm['R_score'] = pd.qcut(rfm['recency'], q=n_quantiles,
                              labels=range(n_quantiles, 0, -1), duplicates='drop').astype(int)

    # Frequency: handle ties with rank to avoid duplicate bin edges
    rfm['F_score'] = pd.qcut(rfm['frequency'].rank(method='first'), q=n_quantiles,
                              labels=range(1, n_quantiles + 1)).astype(int)

    # Monetary
    rfm['M_score'] = pd.qcut(rfm['monetary'], q=n_quantiles,
                              labels=range(1, n_quantiles + 1), duplicates='drop').astype(int)

    rfm['RFM_score'] = rfm['R_score'].astype(str) + rfm['F_score'].astype(str) + rfm['M_score'].astype(str)
    rfm['RFM_total'] = rfm['R_score'] + rfm['F_score'] + rfm['M_score']

    return rfm


def segment_customers(rfm: pd.DataFrame) -> pd.DataFrame:
    """
    Map RFM scores to actionable customer segments.

    Segments
    --------
    Champions       : Best customers, recent and frequent buyers with high spend.
    Loyal Customers : Buy regularly and respond well to promotions.
    Potential Loyalists: Recent customers with average frequency.
    New Customers   : Recent buyers with low frequency.
    At Risk         : Used to purchase often but haven't returned recently.
    Cannot Lose Them: Past high-value customers who have stopped buying.
    Hibernating     : Last purchase long ago, low frequency.
    Lost            : Lowest scores across all dimensions.
    """
    def _assign(row):
        r, f, m = row['R_score'], row['F_score'], row['M_score']

        if r >= 4 and f >= 4 and m >= 4:
            return 'Champions'
        if r >= 3 and f >= 4:
            return 'Loyal Customers'
        if r >= 4 and f <= 2:
            return 'New Customers'
        if r >= 3 and f >= 2 and m >= 2:
            return 'Potential Loyalists'
        if r <= 2 and f >= 3 and m >= 3:
            return 'At Risk'
        if r <= 2 and f >= 4 and m >= 4:
            return 'Cannot Lose Them'
        if r <= 2 and f <= 2:
            return 'Hibernating'
        return 'Lost'

    rfm = rfm.copy()
    rfm['segment'] = rfm.apply(_assign, axis=1)
    return rfm


def run_rfm_analysis(transactions: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Full RFM pipeline: calculate, score, and segment.

    Returns
    -------
    rfm : pd.DataFrame
        Customer-level RFM data with segment assignment.
    summary : pd.DataFrame
        Segment-level summary with counts, average revenue, and revenue share.
    """
    rfm = calculate_rfm(transactions)
    rfm = assign_rfm_scores(rfm)
    rfm = segment_customers(rfm)

    summary = rfm.groupby('segment').agg(
        customers=('customer_id', 'count'),
        avg_recency=('recency', 'mean'),
        avg_frequency=('frequency', 'mean'),
        avg_monetary=('monetary', 'mean'),
        total_revenue=('monetary', 'sum')
    ).round(2).sort_values('total_revenue', ascending=False)

    summary['revenue_share_%'] = (summary['total_revenue'] / summary['total_revenue'].sum() * 100).round(2)
    summary['customer_share_%'] = (summary['customers'] / summary['customers'].sum() * 100).round(2)

    return rfm, summary


if __name__ == '__main__':
    transactions = pd.read_csv('/home/claude/ecommerce-customer-analytics/data/transactions.csv')
    rfm, summary = run_rfm_analysis(transactions)

    print('=' * 70)
    print('RFM SEGMENT SUMMARY')
    print('=' * 70)
    print(summary.to_string())
    print(f'\nTotal customers analyzed: {len(rfm):,}')
    print(f'Total revenue: ${rfm["monetary"].sum():,.2f}')
