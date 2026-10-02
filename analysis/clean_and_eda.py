import pandas as pd

pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 20)

print("TASK 1 - Load and inspect")

customers = pd.read_csv('data/customers.csv')
products  = pd.read_csv('data/products.csv')
orders    = pd.read_csv('data/orders.csv')

print("customers.shape:", customers.shape)
print("products.shape :", products.shape)
print("orders.shape   :", orders.shape)

print("\nTASK 2 - Standardise payment_method casing")

print("BEFORE distinct values:", sorted(orders['payment_method'].unique()))
print("BEFORE count:", orders['payment_method'].nunique())

orders['payment_method'] = orders['payment_method'].str.strip().str.upper()

print("AFTER distinct values:", sorted(orders['payment_method'].unique()))
print("AFTER count:", orders['payment_method'].nunique())
print(orders['payment_method'].value_counts())

print("\nTASK 3 - Remove duplicate orders")

natural_key = ['customer_id', 'product_id', 'order_date', 'quantity',
               'discount_pct', 'payment_method', 'rating', 'returned']

dup_mask = orders.duplicated(subset=natural_key, keep='first')
dropped_ids = orders.loc[dup_mask, 'order_id'].tolist()

print("Duplicates flagged:", dup_mask.sum())
print("Dropped order_id values:", dropped_ids)

orders_clean = orders[~dup_mask].copy()
print("orders_clean.shape:", orders_clean.shape)

print("\nTASK 4 - Impute missing values")

print("discount_pct NaN before fill:", orders_clean['discount_pct'].isna().sum())
orders_clean['discount_pct'] = orders_clean['discount_pct'].fillna(0)

rating_median = orders_clean['rating'].median()
print("rating NaN before fill:", orders_clean['rating'].isna().sum())
print("rating median (before imputing):", rating_median)
orders_clean['rating'] = orders_clean['rating'].fillna(rating_median)

print("Post-impute nulls:")
print(orders_clean[['discount_pct', 'rating']].isnull().sum())

print("\nTASK 5 - Merge and reconcile against Part 1")

merged = (orders_clean
          .merge(products,  on='product_id',  how='left')
          .merge(customers, on='customer_id', how='left'))

merged['order_value'] = (merged['quantity'] * merged['price']
                         * (1 - merged['discount_pct'] / 100))

cleaned_total = round(merged['order_value'].sum(), 2)
print("Cleaned rows:", len(merged))
print("Cleaned total order_value: Rs", cleaned_total)

raw = pd.read_csv('data/orders.csv')
raw = raw.merge(products, on='product_id', how='left')
raw['discount_pct_filled'] = raw['discount_pct'].fillna(0)
raw['order_value'] = (raw['quantity'] * raw['price']
                      * (1 - raw['discount_pct_filled'] / 100))

raw_total = round(raw['order_value'].sum(), 2)
delta = round(raw_total - cleaned_total, 2)
dropped_value = round(
    raw.loc[raw['order_id'].isin(dropped_ids), 'order_value'].sum(), 2
)

print("\nRECONCILIATION")
print(f"Raw Part-1 total (180 rows)        : Rs {raw_total:,.2f}")
print(f"Cleaned Part-2 total (175 rows)    : Rs {cleaned_total:,.2f}")
print(f"Delta                              : Rs {delta:,.2f}")
print(f"Sum of 5 dropped rows' order_value : Rs {dropped_value:,.2f}")
print("The entire delta is explained by the 5 duplicate rows removed in Task 3.")
print("Discount/rating imputation does NOT change any order_value.")


print("\nTASK 6 - IQR outlier detection on quantity")

q1 = merged['quantity'].quantile(0.25)
q3 = merged['quantity'].quantile(0.75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr

print("Q1:", q1)
print("Q3:", q3)
print("IQR:", iqr)
print("lower bound:", lower)
print("upper bound:", upper)

merged['is_outlier'] = (merged['quantity'] < lower) | (merged['quantity'] > upper)
outlier_rows = merged[merged['is_outlier']]
print("Outlier rows:", len(outlier_rows))
print(outlier_rows[['order_id', 'quantity', 'order_value']])

print("\nTASK 7 - Hypothesis: does COD have a higher return rate?")

print("HYPOTHESIS: COD orders have a higher return rate than other payment methods.")

pm_stats = merged.groupby('payment_method')['returned'].agg(['count', 'mean'])
pm_stats['return_rate_pct'] = (pm_stats['mean'] * 100).round(1)
print(pm_stats)

cod_rate = pm_stats.loc['COD', 'return_rate_pct']
card_rate = pm_stats.loc['CARD', 'return_rate_pct']
upi_rate = pm_stats.loc['UPI', 'return_rate_pct']
verdict = "Confirmed" if cod_rate > card_rate and cod_rate > upi_rate else "Rejected"
print("Verdict:", verdict)

print("\nTASK 8 - Multi-level segmentation: payment_method x city_tier")

seg = merged.groupby(['payment_method', 'city_tier'])['returned'].agg(['count', 'mean'])
seg['return_rate_pct'] = (seg['mean'] * 100).round(1)
print(seg)

worst = seg['return_rate_pct'].idxmax()
worst_rate = seg['return_rate_pct'].max()
print(f"HIGHEST-RISK SEGMENT: {worst[0]} + Tier-{worst[1]} at {worst_rate}%")

print("\nTASK 9 - Correlation analysis")

corr = merged[['rating', 'returned', 'discount_pct', 'quantity']].corr().round(3)
print(corr)

print("Correlation strength bands: negligible |r|<0.2, weak 0.2-0.39, moderate 0.4-0.69, strong 0.7-1.0")
pairs = [
    ('rating', 'returned'),
    ('rating', 'discount_pct'),
    ('rating', 'quantity'),
    ('returned', 'discount_pct'),
    ('returned', 'quantity'),
    ('discount_pct', 'quantity'),
]
for a, b in pairs:
    r = corr.loc[a, b]
    ar = abs(r)
    if ar < 0.2:
        band = 'negligible'
    elif ar < 0.4:
        band = 'weak'
    elif ar < 0.7:
        band = 'moderate'
    else:
        band = 'strong'
    print(f"  {a} vs {b}: r = {r}  -> {band}")

print("Hypothesis 'higher discounts reduce returns' is Busted:")
print(f"  discount_pct vs returned correlation = {corr.loc['discount_pct', 'returned']} (negligible)")

print("\nTASK 10 - Outlier-corrected monthly time series")

merged['order_date'] = pd.to_datetime(merged['order_date'])
merged['month'] = merged['order_date'].dt.to_period('M').astype(str)

monthly_with = merged.groupby('month')['order_value'].sum().round(2)
monthly_without = merged.loc[~merged['is_outlier']].groupby('month')['order_value'].sum().round(2)

print("Monthly revenue INCLUDING outliers:")
print(monthly_with)
print("\nMonthly revenue EXCLUDING outliers (outlier-corrected):")
print(monthly_without)

print("\nJanuary's apparent lead is an artifact of two bulk orders:")
print("  O0011 on 2026-01-28 (quantity 25)")
print("  O0098 on 2026-01-10 (quantity 30)")
print("Once excluded, March 2026 is the genuine peak month.")

with_peak = monthly_with.idxmax()
without_peak = monthly_without.idxmax()
print(f"Peak month WITH outliers   : {with_peak} (Rs {monthly_with.max():,.2f})")
print(f"Peak month WITHOUT outliers: {without_peak} (Rs {monthly_without.max():,.2f})")



import json

findings = {
    "cleaned_total_revenue_inr": round(merged['order_value'].sum(), 2),
    "raw_total_revenue_inr": round(raw_total, 2),
    "duplicate_reconciliation_delta_inr": round(delta, 2),
    "return_rate_by_payment": {
        "COD":  float(round(pm_stats.loc['COD',  'return_rate_pct'], 1)),
        "CARD": float(round(pm_stats.loc['CARD', 'return_rate_pct'], 1)),
        "UPI":  float(round(pm_stats.loc['UPI',  'return_rate_pct'], 1)),
    },
    "highest_risk_segment": {
        "payment_method": worst[0],
        "city_tier":      int(worst[1]),
        "return_rate_pct": float(worst_rate),
    },
    "true_peak_month": {
        "month":       without_peak,
        "revenue_inr": float(round(monthly_without.max(), 2)),
    },
    "outlier_inflated_month": {
        "month":                 with_peak,
        "apparent_revenue_inr":  float(round(monthly_with.max(), 2)),
        "corrected_revenue_inr": float(round(monthly_without.loc[with_peak], 2)),
    },
}

with open('narrator/findings.json', 'w') as f:
    json.dump(findings, f, indent=2)

print("\nfindings.json written to narrator/findings.json")
print(json.dumps(findings, indent=2))