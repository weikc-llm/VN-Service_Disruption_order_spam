import os
import pandas as pd

# 1. Define File Directory Path & Excel File Names
data_dir = "/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026/data"

july_file_path = os.path.join(data_dir, "result_20260921_192957(VN-July-simulation_latest).xlsx")
aug_file_path = os.path.join(data_dir, "result_20260921_164639(VN-Aug-simulation_latest).xlsx")

output_file_path = os.path.join(data_dir, "VN_High_Frequency_User_Summary_July_Aug_2026.xlsx")


def summarize_excel_simulation(file_path, sheet_name="Results export"):
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return pd.DataFrame()

    print(f"Processing input file: {os.path.basename(file_path)}...")
    df = pd.read_excel(file_path, sheet_name=sheet_name)

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
    pivot_df = (
        df.groupby(["user_id", "frequency_tier"])["order_display_id"]
        .nunique()
        .unstack(fill_value=0)
    )

    # Ensure all tiers exist in dataframe
    for tier in tier_order:
        if tier not in pivot_df.columns:
            pivot_df[tier] = 0

    pivot_df = pivot_df[tier_order]

    # Calculate Total Orders and High-Frequency Share (>50%)
    pivot_df["Total"] = pivot_df[tier_order].sum(axis=1)
    pivot_df["0s - <30s (>50%)"] = (
        pivot_df["0s - <30s"] / pivot_df["Total"]
    ).round(4)

    # Extract user-level metrics from detailed simulation output
    user_metrics = df.groupby("user_id").agg(
        rolling_flag_count=("rolling_flag_count", "first"),
        total_create_cnt=("total_create_cnt", "first"),
        total_complete_cnt=("total_complete_cnt", "first"),
        total_cancelled_cnt=("total_cancelled_cnt", "first"),
        completion_rate=("completion_rate", "first"),
        cancellation_rate=("cancellation_rate", "first"),
    )

    # Combine Summary
    summary_df = pivot_df.merge(
        user_metrics, left_index=True, right_index=True
    ).reset_index()

    # Format percentage fields as strings for clean Excel viewing
    summary_df["0s - <30s (>50%)_Formatted"] = (
        summary_df["0s - <30s (>50%)"] * 100
    ).round(2).astype(str) + "%"
    summary_df["completion_rate_Formatted"] = (
        summary_df["completion_rate"] * 100
    ).round(2).astype(str) + "%"
    summary_df["cancellation_rate_Formatted"] = (
        summary_df["cancellation_rate"] * 100
    ).round(2).astype(str) + "%"

    # Reorder and rename columns to match spreadsheet layout
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

    return summary_df[list(final_cols.keys())].rename(columns=final_cols)


# 2. Process July and August Simulation Files
july_summary = summarize_excel_simulation(july_file_path)
aug_summary = summarize_excel_simulation(aug_file_path)

# 3. Save Summary to Excel with Specific Sheet Names
with pd.ExcelWriter(output_file_path, engine="openpyxl") as writer:
    if not july_summary.empty:
        july_summary.to_excel(
            writer, sheet_name="account to check (July)", index=False
        )
    if not aug_summary.empty:
        aug_summary.to_excel(
            writer, sheet_name="account to check (Aug)", index=False
        )

print(
    f"\n[SUCCESS] Summary Excel successfully exported to: {output_file_path}"
)