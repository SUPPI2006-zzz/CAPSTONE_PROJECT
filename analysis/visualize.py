import pandas as pd
import matplotlib.pyplot as plt
import os

os.makedirs('visualizations', exist_ok=True)

customers = pd.read_csv('data/customers.csv')
products  = pd.read_csv('data/products.csv')
orders    = pd.read_csv('data/orders.csv')

orders['payment_method'] = orders['payment_method'].str.strip().str.upper()

natural_key = ['customer_id', 'product_id', 'order_date', 'quantity',
               'discount_pct', 'payment_method', 'rating', 'returned']
orders = orders[~orders.duplicated(subset=natural_key, keep='first')].copy()

orders['discount_pct'] = orders['discount_pct'].fillna(0)
orders['rating'] = orders['rating'].fillna(orders['rating'].median())

merged = (orders
          .merge(products,  on='product_id',  how='left')
          .merge(customers, on='customer_id', how='left'))

merged['order_value'] = (merged['quantity'] * merged['price']
                         * (1 - merged['discount_pct'] / 100))

q1 = merged['quantity'].quantile(0.25)
q3 = merged['quantity'].quantile(0.75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr
merged['is_outlier'] = (merged['quantity'] < lower) | (merged['quantity'] > upper)

print("Cleaned rows:", len(merged))
print("Cleaned total order_value: Rs", round(merged['order_value'].sum(), 2))
print("Outliers flagged:", merged['is_outlier'].sum())

rr = merged.groupby('payment_method')['returned'].mean() * 100
rr = rr.round(1).sort_values(ascending=False)
print("\nReturn rate by payment method:")
print(rr)

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(rr.index, rr.values, color=['#C0392B', '#E67E22', '#27AE60'])
for bar, val in zip(bars, rr.values):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 0.5,
            f"{val}%", ha='center', fontsize=11, fontweight='bold')
ax.set_title("COD Returns at 44.4% - 3x Card", fontsize=13, fontweight='bold')
ax.set_xlabel("Payment method")
ax.set_ylabel("Return rate (%)")
ax.set_ylim(0, max(rr.values) * 1.2)
plt.tight_layout()
plt.savefig('visualizations/return_rate_by_payment.png', dpi=120)
plt.close()
print("\nSaved visualizations/return_rate_by_payment.png")

merged['order_date'] = pd.to_datetime(merged['order_date'])
merged['month'] = merged['order_date'].dt.to_period('M').astype(str)

monthly_without = (merged.loc[~merged['is_outlier']]
                   .groupby('month')['order_value'].sum().round(2))
print("\nOutlier-corrected monthly revenue:")
print(monthly_without)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(monthly_without.index, monthly_without.values,
        marker='o', linewidth=2, color='#16A085')
for x, y in zip(monthly_without.index, monthly_without.values):
    ax.annotate(f"{y:,.0f}", (x, y), textcoords="offset points",
                xytext=(0, 8), ha='center', fontsize=9)
ax.set_title("Monthly Revenue (Outlier-Corrected) - Peak: March 2026",
             fontsize=13, fontweight='bold')
ax.set_xlabel("Month")
ax.set_ylabel("Revenue (INR)")
plt.tight_layout()
plt.savefig('visualizations/monthly_revenue_trend.png', dpi=120)
plt.close()
print("Saved visualizations/monthly_revenue_trend.png")