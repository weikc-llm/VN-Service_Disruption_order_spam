import os
import glob
import pandas as pd

# 1. Define File Directory Path & Output Name
data_dir = "/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026/data"
output_file_path = os.path.join(
    data_dir, "VN_High_Frequency_User_Summary_July_Aug_2026(rollcnt).xlsx"
)


def find_latest_file(pattern):
    """Finds the newest file matching the pattern in data_dir."""
    matches = glob.glob(os.path.join(data_dir, pattern))
    if matches:
        return max(matches, key=os.path.getmtime)
    return None


def summarize_excel_simulation(file_path):
    if not file_path or not os.path.exists(file_path):
        print(f"[SKIP] Target file not found: {file_path}")
        return pd.DataFrame()

    print(f"Processing input file: {os.path.basename(file_path)}...")

    # Load Excel sheet safely (tries 'Results export', then falls back to first sheet)
    try:
        df = pd.read_excel(file_path, sheet_name="Results export")
    except Exception:
        try:
            df = pd.read_excel(file_path, sheet_name=0)
        except Exception as e:
            print(f"[ERROR] Could not read {os.path.basename(file_path)}: {e}")
            return pd.DataFrame()

    # Required Frequency Tiers in Exact Order
    tier_order = [
        "First Order",
        "0s - <30s",
        "30s - <1m",
        "1m - <5m",
        "5m - <30m",
        ">= 30m",
    ]

    # Pivot frequency tier counts per user
    if "frequency_tier" in df.columns and "order_display_id" in df.columns:
        pivot_df = (
            df.groupby(["user_id", "frequency_tier"])["order_display_id"]
            .nunique()
            .unstack(fill_value=0)
        )
    else:
        pivot_df = pd.DataFrame(index=df["user_id"].unique())

    # Ensure all tiers exist in dataframe
    for tier in tier_order:
        if tier not in pivot_df.columns:
            pivot_df[tier] = 0

    pivot_df = pivot_df[tier_order]

    # Calculate Total Orders and High-Frequency Share (>50%)
    pivot_df["Total"] = pivot_df[tier_order].sum(axis=1)
    pivot_df["0s - <30s (>50%)"] = (
        pivot_df["0s - <30s"] / pivot_df["Total"].replace(0, pd.NA)
    ).round(4)

    # DYNAMIC COLUMN MATCHING: Find exact flag column name present in df
    flag_col = None
    possible_flag_cols = [
        "rolling_flag_count",
        "rolling_1h_flag_count",
        "max_flag_count",
        "max_rolling_flag_count",
        "rolling_1h_flags",
        "rolling_flag_cnt",
    ]
    for col in possible_flag_cols:
        if col in df.columns:
            flag_col = col
            break

    # Build aggregation mapping dynamically ONLY for columns that actually exist
    agg_dict = {}
    if flag_col:
        agg_dict[flag_col] = "max"  # Uses MAX to get peak flag count instead of FIRST (0)

    for col in [
        "total_create_cnt",
        "total_complete_cnt",
        "total_cancelled_cnt",
        "completion_rate",
        "cancellation_rate",
    ]:
        if col in df.columns:
            agg_dict[col] = "first"

    # Extract user-level metrics safely
    if agg_dict:
        user_metrics = df.groupby("user_id").agg(agg_dict)
        if flag_col and flag_col != "rolling_flag_count":
            user_metrics = user_metrics.rename(columns={flag_col: "rolling_flag_count"})
    else:
        user_metrics = pd.DataFrame(index=df["user_id"].unique())

    # Combine Summary
    summary_df = pivot_df.merge(
        user_metrics, left_index=True, right_index=True, how="left"
    ).reset_index()

    # Format percentage fields as strings
    summary_df["0s - <30s (>50%)_Formatted"] = (
        (summary_df["0s - <30s (>50%)"].fillna(0) * 100).round(2).astype(str) + "%"
    )

    if "completion_rate" in summary_df.columns:
        summary_df["completion_rate_Formatted"] = (
            (summary_df["completion_rate"].fillna(0) * 100).round(2).astype(str) + "%"
        )
    else:
        summary_df["completion_rate_Formatted"] = "0.0%"

    if "cancellation_rate" in summary_df.columns:
        summary_df["cancellation_rate_Formatted"] = (
            (summary_df["cancellation_rate"].fillna(0) * 100).round(2).astype(str) + "%"
        )
    else:
        summary_df["cancellation_rate_Formatted"] = "0.0%"

    final_cols = {
        "user_id": "user_id",
        "First Order": "First Order",
        "0s - <30s": "0s - <30s",
        "30s - <1m": "30s - <1m",
        "1m - <5m": "1m - <5m",
        "5m - <30m": "5m - <30m",
        ">= 30m": ">= 30m",
        "Total": "Total",
        "0s - <30s (>50%)_Formatted": "0s - <30s (>50%)",
        "rolling_flag_count": "Rolling 1h Flags",
        "total_create_cnt": "Lifetime Create Cnt",
        "total_complete_cnt": "Lifetime Complete Cnt",
        "total_cancelled_cnt": "Lifetime Cancel Cnt",
        "completion_rate_Formatted": "Completion Rate",
        "cancellation_rate_Formatted": "Cancellation Rate",
    }

    existing_cols = [c for c in final_cols.keys() if c in summary_df.columns]
    return summary_df[existing_cols].rename(columns=final_cols)


# 2. Automatically Find Most Recent Simulation Files for July & August
july_file_path = find_latest_file("*July*simulation*")
aug_file_path = find_latest_file("*Aug*simulation*")

# 3. Process Available Simulation Files
july_summary = summarize_excel_simulation(july_file_path)
aug_summary = summarize_excel_simulation(aug_file_path)

# 4. Save Summary to Excel safely
if not july_summary.empty or not aug_summary.empty:
    with pd.ExcelWriter(output_file_path, engine="openpyxl") as writer:
        if not july_summary.empty:
            july_summary.to_excel(
                writer, sheet_name="account to check (July)", index=False
            )
        if not aug_summary.empty:
            aug_summary.to_excel(
                writer, sheet_name="account to check (Aug)", index=False
            )

    print(f"\n[SUCCESS] Summary Excel exported to: {output_file_path}")
else:
    print(
        f"\n[ERROR] No simulation files found in '{data_dir}'. "
        "Please confirm your input filenames."
    )