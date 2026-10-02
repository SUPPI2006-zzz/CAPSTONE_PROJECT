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