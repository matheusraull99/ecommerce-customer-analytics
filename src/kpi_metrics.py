"""
Business KPIs Module
--------------------
Calculates key e-commerce performance metrics:
  - Revenue, Orders, AOV (Average Order Value)
  - Customer Lifetime Value (CLV)
  - Repeat Purchase Rate
  - Customer Acquisition Trend
  - Category and Channel Performance
"""

import pandas as pd
import numpy as np


def revenue_summary(transactions: pd.DataFrame) -> dict:
    """High-level revenue and order metrics."""
    df = transactions.copy()
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])

    metrics = {
        'total_revenue': round(df['revenue'].sum(), 2),
        'total_orders': int(df['transaction_id'].nunique()),
        'unique_customers': int(df['customer_id'].nunique()),
        'avg_order_value': round(df['revenue'].mean(), 2),
        'avg_revenue_per_customer': round(df.groupby('customer_id')['revenue'].sum().mean(), 2),
        'date_range': f"{df['transaction_date'].min().date()} to {df['transaction_date'].max().date()}"
    }
    return metrics


def monthly_revenue_trend(transactions: pd.DataFrame) -> pd.DataFrame:
    """Aggregate revenue, orders, and customers by month."""
    df = transactions.copy()
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df['month'] = df['transaction_date'].dt.to_period('M').dt.to_timestamp()

    monthly = df.groupby('month').agg(
        revenue=('revenue', 'sum'),
        orders=('transaction_id', 'nunique'),
        customers=('customer_id', 'nunique')
    ).reset_index()

    monthly['avg_order_value'] = (monthly['revenue'] / monthly['orders']).round(2)
    monthly['revenue_growth_%'] = (monthly['revenue'].pct_change() * 100).round(2)

    return monthly


def category_performance(transactions: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Revenue and margin breakdown by product category."""
    df = transactions.merge(products, on='product_id', suffixes=('', '_prod'))
    df['cost_total'] = df['cost'] * df['quantity']
    df['gross_margin'] = df['revenue'] - df['cost_total']

    category = df.groupby('category').agg(
        revenue=('revenue', 'sum'),
        units_sold=('quantity', 'sum'),
        orders=('transaction_id', 'nunique'),
        gross_margin=('gross_margin', 'sum')
    ).round(2)

    category['margin_%'] = (category['gross_margin'] / category['revenue'] * 100).round(2)
    category['revenue_share_%'] = (category['revenue'] / category['revenue'].sum() * 100).round(2)

    return category.sort_values('revenue', ascending=False)


def channel_performance(transactions: pd.DataFrame) -> pd.DataFrame:
    """Performance by sales channel (Web, Mobile App, In-Store)."""
    channel = transactions.groupby('channel').agg(
        revenue=('revenue', 'sum'),
        orders=('transaction_id', 'nunique'),
        avg_order_value=('revenue', 'mean'),
        unique_customers=('customer_id', 'nunique')
    ).round(2)

    channel['revenue_share_%'] = (channel['revenue'] / channel['revenue'].sum() * 100).round(2)
    return channel.sort_values('revenue', ascending=False)


def repeat_purchase_rate(transactions: pd.DataFrame) -> dict:
    """Share of customers with more than one purchase."""
    purchase_counts = transactions.groupby('customer_id')['transaction_id'].nunique()
    repeat = (purchase_counts > 1).sum()
    total = len(purchase_counts)

    return {
        'total_customers': int(total),
        'repeat_customers': int(repeat),
        'one_time_customers': int(total - repeat),
        'repeat_purchase_rate_%': round(repeat / total * 100, 2)
    }


def customer_lifetime_value(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Approximate CLV using historical data:
      CLV = Average Order Value × Purchase Frequency × Customer Lifespan (years)
    """
    df = transactions.copy()
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])

    customer_data = df.groupby('customer_id').agg(
        total_revenue=('revenue', 'sum'),
        order_count=('transaction_id', 'nunique'),
        first_purchase=('transaction_date', 'min'),
        last_purchase=('transaction_date', 'max')
    ).reset_index()

    customer_data['avg_order_value'] = customer_data['total_revenue'] / customer_data['order_count']
    customer_data['lifespan_days'] = (customer_data['last_purchase'] - customer_data['first_purchase']).dt.days
    customer_data['lifespan_days'] = customer_data['lifespan_days'].clip(lower=1)
    customer_data['purchase_frequency_per_year'] = customer_data['order_count'] / (customer_data['lifespan_days'] / 365)
    customer_data['historical_clv'] = customer_data['total_revenue']

    return customer_data


def top_products(transactions: pd.DataFrame, products: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N products by revenue."""
    df = transactions.merge(products, on='product_id', suffixes=('', '_prod'))
    top = df.groupby(['product_id', 'product_name', 'category']).agg(
        revenue=('revenue', 'sum'),
        units_sold=('quantity', 'sum'),
        orders=('transaction_id', 'nunique')
    ).round(2).sort_values('revenue', ascending=False).head(n)
    return top.reset_index()


if __name__ == '__main__':
    transactions = pd.read_csv('/home/claude/ecommerce-customer-analytics/data/transactions.csv')
    products = pd.read_csv('/home/claude/ecommerce-customer-analytics/data/products.csv')

    print('=' * 60)
    print('REVENUE SUMMARY')
    print('=' * 60)
    for k, v in revenue_summary(transactions).items():
        print(f'  {k}: {v}')

    print('\n' + '=' * 60)
    print('REPEAT PURCHASE RATE')
    print('=' * 60)
    for k, v in repeat_purchase_rate(transactions).items():
        print(f'  {k}: {v}')

    print('\n' + '=' * 60)
    print('CATEGORY PERFORMANCE')
    print('=' * 60)
    print(category_performance(transactions, products).to_string())

    print('\n' + '=' * 60)
    print('CHANNEL PERFORMANCE')
    print('=' * 60)
    print(channel_performance(transactions).to_string())
