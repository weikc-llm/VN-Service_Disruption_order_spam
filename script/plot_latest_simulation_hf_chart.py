import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

# 1. Define directory path (all inputs and outputs in Compiled_Output)
compiled_output_dir = Path(
    "/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026/data"
)
os.makedirs(compiled_output_dir, exist_ok=True)

# 2. Input and Output File Paths
input_file = compiled_output_dir / "Simulation_User_Summary.xlsx"
output_chart = compiled_output_dir / "latest_simulation_hf_user_share.png"

# 3. Read exact target sheets
df_july = pd.read_excel(input_file, sheet_name="user-summary(July2026)")
df_aug = pd.read_excel(input_file, sheet_name="user-summary(Aug2026)")


# Helper function to convert percentage values cleanly to floats
def clean_hf_percentage(df):
    pct_col = "0s - <30s (>50%)"
    
    # Safely convert strings with '%' or floats into numeric floats
    df["hf_pct"] = pd.to_numeric(
        df[pct_col].astype(str).str.replace("%", "", regex=False).str.strip(),
        errors="coerce"
    )
    
    # If values were decimals (e.g., 0.5174 instead of 51.74), convert to percentage
    if df["hf_pct"].max() <= 1.0:
        df["hf_pct"] = df["hf_pct"] * 100

    df["user_id_str"] = df["user_id"].astype(str)
    return df.sort_values(by="hf_pct", ascending=True).reset_index(drop=True)


# 4. Clean and process July & August data
df_july_sorted = clean_hf_percentage(df_july)
df_aug_sorted = clean_hf_percentage(df_aug)

# 5. Create side-by-side comparison visualization
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 10), dpi=300)

# Left Panel: July 2026
bars1 = ax1.barh(
    df_july_sorted["user_id_str"],
    df_july_sorted["hf_pct"],
    color="#d62728",
    edgecolor="black",
    linewidth=0.6,
    height=0.65,
)
ax1.set_title(
    "July 2026: Accounts with >50% High-Frequency Orders (<30s Lag)",
    fontsize=11,
    fontweight="bold",
    pad=12,
)
ax1.set_xlabel("High-Frequency Order Share (%)", fontsize=10, fontweight="bold")
ax1.set_ylabel("User ID", fontsize=10, fontweight="bold")
ax1.set_xlim(0, 115)
ax1.axvline(
    x=50, color="black", linestyle="--", linewidth=1, label="50% Threshold"
)
ax1.grid(axis="x", linestyle="--", alpha=0.5)
ax1.legend(loc="lower right")

for bar, (i, row) in zip(bars1, df_july_sorted.iterrows()):
    val_pct = row["hf_pct"]
    hf_cnt = int(row["0s - <30s"])
    tot_cnt = int(row["Total"])
    ax1.text(
        val_pct + 1.2,
        bar.get_y() + bar.get_height() / 2,
        f"{val_pct:.1f}% ({hf_cnt}/{tot_cnt})",
        ha="left",
        va="center",
        fontweight="bold",
        fontsize=8,
        color="#b30000",
    )

# Right Panel: August 2026
bars2 = ax2.barh(
    df_aug_sorted["user_id_str"],
    df_aug_sorted["hf_pct"],
    color="#1f77b4",
    edgecolor="black",
    linewidth=0.6,
    height=0.65,
)
ax2.set_title(
    "August 2026: Accounts with >50% High-Frequency Orders (<30s Lag)",
    fontsize=11,
    fontweight="bold",
    pad=12,
)
ax2.set_xlabel("High-Frequency Order Share (%)", fontsize=10, fontweight="bold")
ax2.set_ylabel("User ID", fontsize=10, fontweight="bold")
ax2.set_xlim(0, 115)
ax2.axvline(
    x=50, color="black", linestyle="--", linewidth=1, label="50% Threshold"
)
ax2.grid(axis="x", linestyle="--", alpha=0.5)
ax2.legend(loc="lower right")

for bar, (i, row) in zip(bars2, df_aug_sorted.iterrows()):
    val_pct = row["hf_pct"]
    hf_cnt = int(row["0s - <30s"])
    tot_cnt = int(row["Total"])
    ax2.text(
        val_pct + 1.2,
        bar.get_y() + bar.get_height() / 2,
        f"{val_pct:.1f}% ({hf_cnt}/{tot_cnt})",
        ha="left",
        va="center",
        fontweight="bold",
        fontsize=8,
        color="#004080",
    )

plt.suptitle(
    "User-Level High-Frequency Order Share (>50% Threshold) — July vs. August 2026",
    fontsize=13,
    fontweight="bold",
    y=0.98,
)
plt.tight_layout()

# 6. Save image into Compiled_Output directory
plt.savefig(output_chart, bbox_inches="tight")
plt.close()

print(f"[SUCCESS] Chart saved to: '{output_chart}'")