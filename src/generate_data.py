"""
Synthetic E-commerce Dataset Generator
---------------------------------------
Generates a realistic e-commerce transactions dataset for analytics purposes.
The dataset includes customers, products, and transactions with realistic
patterns including seasonality, customer churn, and product popularity.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

# Configuration
N_CUSTOMERS = 5000
N_PRODUCTS = 200
N_TRANSACTIONS = 50000
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)

# ---------- Customers ----------
countries = ['USA', 'UK', 'Germany', 'France', 'Brazil', 'Canada', 'Australia', 'Japan']
country_weights = [0.35, 0.15, 0.12, 0.10, 0.10, 0.08, 0.06, 0.04]

customer_segments = ['New', 'Regular', 'VIP', 'At-Risk']
segment_weights = [0.40, 0.35, 0.10, 0.15]

customers = pd.DataFrame({
    'customer_id': [f'CUST_{i:05d}' for i in range(1, N_CUSTOMERS + 1)],
    'signup_date': [START_DATE + timedelta(days=int(np.random.uniform(0, 730))) for _ in range(N_CUSTOMERS)],
    'country': np.random.choice(countries, N_CUSTOMERS, p=country_weights),
    'age': np.clip(np.random.normal(38, 12, N_CUSTOMERS).astype(int), 18, 80),
    'gender': np.random.choice(['M', 'F', 'Other'], N_CUSTOMERS, p=[0.48, 0.49, 0.03]),
    'segment': np.random.choice(customer_segments, N_CUSTOMERS, p=segment_weights)
})

# ---------- Products ----------
categories = ['Electronics', 'Clothing', 'Home & Kitchen', 'Books', 'Beauty', 'Sports', 'Toys']
category_weights = [0.20, 0.25, 0.18, 0.10, 0.12, 0.08, 0.07]

price_ranges = {
    'Electronics': (50, 1500),
    'Clothing': (15, 200),
    'Home & Kitchen': (10, 500),
    'Books': (8, 50),
    'Beauty': (5, 150),
    'Sports': (20, 400),
    'Toys': (10, 200),
}

products_data = []
for i in range(1, N_PRODUCTS + 1):
    category = np.random.choice(categories, p=category_weights)
    low, high = price_ranges[category]
    products_data.append({
        'product_id': f'PROD_{i:04d}',
        'product_name': f'{category} Item {i}',
        'category': category,
        'unit_price': round(np.random.uniform(low, high), 2),
        'cost': None  # filled below
    })

products = pd.DataFrame(products_data)
# Cost is 40-70% of price (margin)
products['cost'] = (products['unit_price'] * np.random.uniform(0.40, 0.70, N_PRODUCTS)).round(2)

# ---------- Transactions ----------
# Higher purchase activity for VIP, lower for At-Risk
segment_activity = {'New': 0.5, 'Regular': 1.0, 'VIP': 3.0, 'At-Risk': 0.3}

transactions = []
transaction_id = 1

# Build a weighted customer pool based on segment activity
weights = customers['segment'].map(segment_activity).values
weights = weights / weights.sum()

for _ in range(N_TRANSACTIONS):
    customer = customers.sample(1, weights=weights).iloc[0]
    product = products.sample(1).iloc[0]

    # Transaction must be after customer signup
    days_after_signup = np.random.exponential(scale=180)
    transaction_date = customer['signup_date'] + timedelta(days=int(days_after_signup))
    if transaction_date > END_DATE:
        transaction_date = END_DATE - timedelta(days=int(np.random.uniform(0, 365)))

    # Seasonality: boost Nov-Dec by 30%
    quantity = max(1, int(np.random.poisson(1.5)))
    if transaction_date.month in [11, 12]:
        quantity = int(quantity * np.random.uniform(1.0, 1.5)) or 1

    discount = round(np.random.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20], p=[0.55, 0.10, 0.05, 0.10, 0.10, 0.05, 0.05]), 2)

    unit_price = product['unit_price']
    revenue = round(unit_price * quantity * (1 - discount), 2)

    transactions.append({
        'transaction_id': f'TXN_{transaction_id:07d}',
        'customer_id': customer['customer_id'],
        'product_id': product['product_id'],
        'transaction_date': transaction_date.date(),
        'quantity': quantity,
        'unit_price': unit_price,
        'discount': discount,
        'revenue': revenue,
        'payment_method': np.random.choice(['Credit Card', 'Debit Card', 'PayPal', 'Bank Transfer'],
                                           p=[0.55, 0.20, 0.20, 0.05]),
        'channel': np.random.choice(['Web', 'Mobile App', 'In-Store'], p=[0.50, 0.40, 0.10])
    })
    transaction_id += 1

transactions_df = pd.DataFrame(transactions)
transactions_df = transactions_df.sort_values('transaction_date').reset_index(drop=True)

# ---------- Save ----------
customers.to_csv('/home/claude/ecommerce-customer-analytics/data/customers.csv', index=False)
products.to_csv('/home/claude/ecommerce-customer-analytics/data/products.csv', index=False)
transactions_df.to_csv('/home/claude/ecommerce-customer-analytics/data/transactions.csv', index=False)

print(f'Generated {len(customers)} customers')
print(f'Generated {len(products)} products')
print(f'Generated {len(transactions_df)} transactions')
print(f'Date range: {transactions_df["transaction_date"].min()} to {transactions_df["transaction_date"].max()}')
print(f'Total revenue: ${transactions_df["revenue"].sum():,.2f}')
