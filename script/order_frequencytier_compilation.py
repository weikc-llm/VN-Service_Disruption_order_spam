# import os
# import glob
# import pandas as pd
# import numpy as np

# # 1. Define File Directory Path & Filter ONLY Parquet Datasets
# data_dir = "/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026/data/VN_order(July-Aug)/Compiled_Output/"

# # Find only parquet files for July and August
# file_paths = glob.glob(os.path.join(data_dir, "*Jul*.parquet")) + glob.glob(os.path.join(data_dir, "*Aug*.parquet"))

# print(f"Loading Parquet Files: {[os.path.basename(p) for p in file_paths]}")

# # Load ONLY necessary columns to optimize memory usage (prevents script getting killed)
# REQUIRED_COLS = ['user_id', 'order_display_id', 'order_creation_local_time']

# data_frames = []
# for file_path in file_paths:
#     data_frames.append(pd.read_parquet(file_path, columns=REQUIRED_COLS))

# df = pd.concat(data_frames, ignore_index=True)
# print(f"Total Combined Rows Loaded: {len(df):,}")

# # 2. Chronological Sorting & Inter-Order Lag Calculation
# df['order_creation_local_time'] = pd.to_datetime(df['order_creation_local_time'])
# df = df.sort_values(by=['user_id', 'order_creation_local_time']).reset_index(drop=True)

# df['prev_order_creation_time'] = df.groupby('user_id')['order_creation_local_time'].shift(1)
# df['time_diff_seconds'] = (df['order_creation_local_time'] - df['prev_order_creation_time']).dt.total_seconds()

# # Fast Vectorized Frequency Tier Assignment (much faster & lower memory than df.apply)
# conditions = [
#     df['prev_order_creation_time'].isna(),
#     (df['time_diff_seconds'] >= 0) & (df['time_diff_seconds'] < 30),
#     (df['time_diff_seconds'] >= 30) & (df['time_diff_seconds'] < 60),
#     (df['time_diff_seconds'] >= 60) & (df['time_diff_seconds'] < 300),
#     (df['time_diff_seconds'] >= 300) & (df['time_diff_seconds'] < 1800),
#     df['time_diff_seconds'] >= 1800
# ]

# choices = ['First Order', '0s - <30s', '30s - <1m', '1m - <5m', '5m - <30m', '>= 30m']

# df['frequency_tier'] = np.select(conditions, choices, default='Unknown')

# # 3. Pivot Frequency Tiers by user_id
# tier_order = ['First Order', '0s - <30s', '30s - <1m', '1m - <5m', '5m - <30m', '>= 30m']

# pivot_df = (
#     df.groupby(['user_id', 'frequency_tier'])['order_display_id']
#     .nunique()
#     .unstack(fill_value=0)
#     .reindex(columns=tier_order, fill_value=0)
#     .reset_index()
# )

# # 4. Calculate Total Orders and High-Frequency Share (>50%)
# pivot_df['Total'] = pivot_df[tier_order].sum(axis=1)
# pivot_df['0s - <30s (>50%)'] = (pivot_df['0s - <30s'] / pivot_df['Total']).round(4)

# # 5. Filter User Pool for 0s - <30s Share > 50%
# user_pool_df = pivot_df[pivot_df['0s - <30s (>50%)'] > 0.50].copy()

# # Format percentage column as text (e.g., 51.74%) for clean CSV/Excel display
# user_pool_df['0s - <30s (>50%)_Formatted'] = (user_pool_df['0s - <30s (>50%)'] * 100).round(2).astype(str) + '%'

# # Drop unformatted helper column & rename for final output
# output_df = user_pool_df.drop(columns=['0s - <30s (>50%)']).rename(
#     columns={'0s - <30s (>50%)_Formatted': '0s - <30s (>50%)'}
# )

# # 6. Save to CSV
# output_path = os.path.join(data_dir, "user_pool_hf_share.csv")
# output_df.to_csv(output_path, index=False)

# print(f"\n[SUCCESS] Exported {len(output_df)} users to: {output_path}")
# print(output_df.head(10))




import os
import glob
import pandas as pd
import numpy as np

# 1. Define File Directory & Read Parquet Files
data_dir = "/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026/data/VN_order(July-Aug)/Compiled_Output/"

file_paths = glob.glob(os.path.join(data_dir, "*Jul*.parquet")) + glob.glob(os.path.join(data_dir, "*Aug*.parquet"))
print(f"Loading Parquet files: {[os.path.basename(f) for f in file_paths]}")

df = pd.concat([pd.read_parquet(f) for f in file_paths], ignore_index=True)

# Ensure ID columns remain exact strings
str_cols = ['order_display_id', 'user_id', 'driver_id', 'user_name', 'order_remark', 'start_address', 'end_address']
for col in str_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()

# 2. Chronological Sorting & Timestamp Processing
df['order_creation_local_time'] = pd.to_datetime(df['order_creation_local_time'])
df = df.sort_values(by=['user_id', 'order_creation_local_time']).reset_index(drop=True)

df['order_timestamp_sec'] = (df['order_creation_local_time'].astype('int64') // 10**9)

# 3. Inter-Order Time Difference (Seconds)
df['prev_order_creation_time'] = df.groupby('user_id')['order_creation_local_time'].shift(1)
df['time_diff_seconds'] = (df['order_creation_local_time'] - df['prev_order_creation_time']).dt.total_seconds()

# Assign Frequency Tier (<30s focus)
conditions = [
    df['prev_order_creation_time'].isna(),
    (df['time_diff_seconds'] >= 0) & (df['time_diff_seconds'] < 30),
    (df['time_diff_seconds'] >= 30) & (df['time_diff_seconds'] < 60),
    (df['time_diff_seconds'] >= 60) & (df['time_diff_seconds'] < 300),
    (df['time_diff_seconds'] >= 300) & (df['time_diff_seconds'] < 1800),
    df['time_diff_seconds'] >= 1800
]
choices = ['First Order', '<30s', '30s - <1m', '1m - <5m', '5m - <30m', '>= 30m']
df['frequency_tier'] = np.select(conditions, choices, default='Unknown')

# Binary High-Frequency Flag (< 30 seconds)
df['is_high_frequency_order'] = np.where((df['time_diff_seconds'] >= 0) & (df['time_diff_seconds'] < 30), 1, 0)

# 4. 1-Hour Rolling Window Calculation (3600 Seconds)
df_indexed = df.set_index('order_creation_local_time')

# Rolling 1-Hour Total Orders per user
df['rolling_1h_total_orders'] = (
    df_indexed.groupby('user_id')['order_display_id']
    .rolling('1h', closed='both')
    .count()
    .values
)

# Rolling 1-Hour High-Frequency Orders (<30s lag) per user
df['rolling_1h_hf_orders'] = (
    df_indexed.groupby('user_id')['is_high_frequency_order']
    .rolling('1h', closed='both')
    .sum()
    .values
)

# 5. Flagging Event (> 5 HF orders in a 1-hour window)
# Assign 'is_flag_event' FIRST so it exists in df and df_indexed
df['is_flag_event'] = np.where(df['rolling_1h_hf_orders'] > 5, 1, 0)

# Re-index df after creating 'is_flag_event' to apply rolling window sum on it
df_indexed = df.set_index('order_creation_local_time')

# Rolling 1-Hour Flag Event Count
df['rolling_1h_flag_count'] = (
    df_indexed.groupby('user_id')['is_flag_event']
    .rolling('1h', closed='both')
    .sum()
    .values
)

# 6. Max Flag & Volume Metrics per User
user_max_metrics = df.groupby('user_id').agg(
    max_flag_count=('rolling_1h_flag_count', 'max'),
    max_1h_order_volume=('rolling_1h_total_orders', 'max'),
    total_user_orders=('order_display_id', 'nunique'),
    total_hf_orders=('is_high_frequency_order', 'sum')
).reset_index()

user_max_metrics['hf_volume_share'] = user_max_metrics['total_hf_orders'] / user_max_metrics['total_user_orders']

# Merge user-level metrics back into order-level dataframe
df = df.merge(
    user_max_metrics[['user_id', 'max_flag_count', 'max_1h_order_volume', 'hf_volume_share']], 
    on='user_id', 
    how='left'
)

# 7. Apply Enforcement Strategy Filters (>50% HF share & >3 Rolling Flags)
enforced_users = user_max_metrics[
    (user_max_metrics['hf_volume_share'] > 0.50) & 
    (user_max_metrics['max_flag_count'] > 3)
]['user_id'].tolist()

enforced_orders_df = df[df['user_id'].isin(enforced_users)].copy()

# 8. Export Detailed CSV Output
output_path = os.path.join(data_dir, "VN_HF_orders_evaluation_detail.csv")
enforced_orders_df.to_csv(output_path, index=False)

print(f"\n[SUCCESS] Exported {len(enforced_orders_df):,} orders across {len(enforced_users)} enforced users.")
print(f"Output File Location: {output_path}")