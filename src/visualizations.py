"""
Visualization Script
--------------------
Generates publication-quality charts from the analytics modules and saves
them to the images/ directory for use in reports and the README.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rfm_analysis import run_rfm_analysis
from cohort_analysis import build_cohort_table
from kpi_metrics import (monthly_revenue_trend, category_performance,
                         channel_performance, customer_lifetime_value)

# Style
sns.set_style('whitegrid')
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['axes.titleweight'] = 'bold'

PALETTE = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B', '#6A994E', '#BC4749']
IMG_DIR = '/home/claude/ecommerce-customer-analytics/images'


def plot_monthly_revenue(transactions: pd.DataFrame):
    monthly = monthly_revenue_trend(transactions)

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    axes[0].plot(monthly['month'], monthly['revenue'] / 1000, marker='o', color=PALETTE[0], linewidth=2)
    axes[0].fill_between(monthly['month'], monthly['revenue'] / 1000, alpha=0.2, color=PALETTE[0])
    axes[0].set_title('Monthly Revenue Trend')
    axes[0].set_ylabel('Revenue (USD, thousands)')
    axes[0].set_xlabel('')

    axes[1].bar(monthly['month'], monthly['orders'], color=PALETTE[1], width=20, alpha=0.8)
    axes[1].set_title('Monthly Order Volume')
    axes[1].set_ylabel('Number of Orders')
    axes[1].set_xlabel('Month')

    plt.tight_layout()
    plt.savefig(f'{IMG_DIR}/monthly_revenue_trend.png')
    plt.close()
    print('Saved: monthly_revenue_trend.png')


def plot_category_performance(transactions: pd.DataFrame, products: pd.DataFrame):
    cat = category_performance(transactions, products).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    axes[0].barh(cat['category'], cat['revenue'] / 1000, color=PALETTE[:len(cat)])
    axes[0].set_title('Revenue by Category')
    axes[0].set_xlabel('Revenue (USD, thousands)')
    axes[0].invert_yaxis()

    axes[1].barh(cat['category'], cat['margin_%'], color=PALETTE[:len(cat)])
    axes[1].set_title('Gross Margin by Category (%)')
    axes[1].set_xlabel('Margin (%)')
    axes[1].invert_yaxis()

    plt.tight_layout()
    plt.savefig(f'{IMG_DIR}/category_performance.png')
    plt.close()
    print('Saved: category_performance.png')


def plot_rfm_segments(transactions: pd.DataFrame):
    rfm, summary = run_rfm_analysis(transactions)
    summary = summary.reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    axes[0].barh(summary['segment'], summary['customers'], color=PALETTE[:len(summary)])
    axes[0].set_title('Customer Count by RFM Segment')
    axes[0].set_xlabel('Number of Customers')
    axes[0].invert_yaxis()

    axes[1].barh(summary['segment'], summary['total_revenue'] / 1000, color=PALETTE[:len(summary)])
    axes[1].set_title('Revenue by RFM Segment')
    axes[1].set_xlabel('Revenue (USD, thousands)')
    axes[1].invert_yaxis()

    plt.tight_layout()
    plt.savefig(f'{IMG_DIR}/rfm_segments.png')
    plt.close()
    print('Saved: rfm_segments.png')


def plot_cohort_heatmap(transactions: pd.DataFrame):
    _, retention = build_cohort_table(transactions)
    retention_pct = (retention.iloc[:, :12] * 100).round(1)
    retention_pct.index = retention_pct.index.strftime('%Y-%m')

    fig, ax = plt.subplots(figsize=(13, 9))
    sns.heatmap(retention_pct, annot=True, fmt='.1f', cmap='YlGnBu',
                cbar_kws={'label': 'Retention Rate (%)'}, ax=ax,
                linewidths=0.5, linecolor='white')
    ax.set_title('Customer Cohort Retention (% of cohort active in each month)')
    ax.set_xlabel('Months Since First Purchase')
    ax.set_ylabel('Cohort (First Purchase Month)')

    plt.tight_layout()
    plt.savefig(f'{IMG_DIR}/cohort_retention_heatmap.png')
    plt.close()
    print('Saved: cohort_retention_heatmap.png')


def plot_channel_performance(transactions: pd.DataFrame):
    channel = channel_performance(transactions).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    axes[0].pie(channel['revenue'], labels=channel['channel'],
                autopct='%1.1f%%', colors=PALETTE[:len(channel)], startangle=90,
                wedgeprops={'edgecolor': 'white', 'linewidth': 2})
    axes[0].set_title('Revenue Share by Channel')

    axes[1].bar(channel['channel'], channel['avg_order_value'], color=PALETTE[:len(channel)])
    axes[1].set_title('Average Order Value by Channel')
    axes[1].set_ylabel('AOV (USD)')
    for i, v in enumerate(channel['avg_order_value']):
        axes[1].text(i, v + 5, f'${v:.2f}', ha='center', fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'{IMG_DIR}/channel_performance.png')
    plt.close()
    print('Saved: channel_performance.png')


def plot_clv_distribution(transactions: pd.DataFrame):
    clv = customer_lifetime_value(transactions)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].hist(clv['historical_clv'], bins=50, color=PALETTE[0], edgecolor='white')
    axes[0].axvline(clv['historical_clv'].median(), color=PALETTE[3], linestyle='--',
                    linewidth=2, label=f"Median: ${clv['historical_clv'].median():.0f}")
    axes[0].axvline(clv['historical_clv'].mean(), color=PALETTE[2], linestyle='--',
                    linewidth=2, label=f"Mean: ${clv['historical_clv'].mean():.0f}")
    axes[0].set_title('Customer Lifetime Value Distribution')
    axes[0].set_xlabel('Lifetime Revenue (USD)')
    axes[0].set_ylabel('Number of Customers')
    axes[0].legend()

    # Top 20% vs rest
    threshold = clv['historical_clv'].quantile(0.80)
    top_20_revenue = clv[clv['historical_clv'] >= threshold]['historical_clv'].sum()
    rest_revenue = clv[clv['historical_clv'] < threshold]['historical_clv'].sum()

    labels = ['Top 20% Customers', 'Bottom 80% Customers']
    sizes = [top_20_revenue, rest_revenue]
    axes[1].pie(sizes, labels=labels, autopct='%1.1f%%', colors=[PALETTE[0], PALETTE[4]],
                startangle=90, wedgeprops={'edgecolor': 'white', 'linewidth': 2})
    axes[1].set_title('Pareto: Revenue Concentration')

    plt.tight_layout()
    plt.savefig(f'{IMG_DIR}/clv_distribution.png')
    plt.close()
    print('Saved: clv_distribution.png')


def main():
    print('Loading data...')
    transactions = pd.read_csv('/home/claude/ecommerce-customer-analytics/data/transactions.csv')
    products = pd.read_csv('/home/claude/ecommerce-customer-analytics/data/products.csv')

    print('\nGenerating visualizations...')
    plot_monthly_revenue(transactions)
    plot_category_performance(transactions, products)
    plot_rfm_segments(transactions)
    plot_cohort_heatmap(transactions)
    plot_channel_performance(transactions)
    plot_clv_distribution(transactions)

    print('\nAll visualizations saved to /images/')


if __name__ == '__main__':
    main()
