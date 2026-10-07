import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================================================================
# 1. FILE PATH CONFIGURATION (WSL Linux Format)
# ==============================================================================
# Input Excel File
input_path = "/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026/data/september strat simulation/latest(for stakeholder)/result_20261006_095054(July to Sept VN latest simulation).xlsx"

# Output Directory & Target File Name
output_dir = "/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026/data/september strat simulation/latest(for stakeholder)/output"
output_file = os.path.join(output_dir, "flagged_account_age_distribution.png")

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# ==============================================================================
# 2. DATA PROCESSING
# ==============================================================================
# Read 'reporting' sheet
df = pd.read_excel(input_path, sheet_name='reporting')

# Clean relevant columns
user_df = df[['User ID', 'Account age (days)', 'Flag order count']].dropna(subset=['User ID']).copy()

# Categorize into 3 Account Age Tiers
bins = [-1, 29.99, 90, 100000]
labels = ['< 30 Days', '30 - 90 Days', '> 90 Days']
user_df['Age_Group'] = pd.cut(user_df['Account age (days)'], bins=bins, labels=labels)

# Aggregate User Counts and Total Flagged Orders
summary = user_df.groupby('Age_Group', observed=False).agg(
    user_count=('User ID', 'nunique'),
    total_flagged_orders=('Flag order count', 'sum')
).reset_index()

# ==============================================================================
# 3. CHART PLOTTING
# ==============================================================================
sns.set_theme(style="whitegrid")
fig, ax1 = plt.subplots(figsize=(10, 7))

x = np.arange(len(summary['Age_Group']))
width = 0.38  # Bar width

blue_color = '#1f77b4'
orange_color = '#ff7f0e'

ax2 = ax1.twinx()  # Secondary Y-axis for orders

# Plot adjacent bars
rects1 = ax1.bar(x - width/2, summary['user_count'], width, 
                 color=blue_color, edgecolor='black', linewidth=1.2)
rects2 = ax2.bar(x + width/2, summary['total_flagged_orders'], width, 
                 color=orange_color, edgecolor='black', linewidth=1.2)

# Set Title & Axis Labels
ax1.set_title('Age distribution vs Order Creation Volume', fontsize=18, fontweight='bold', pad=25, color='#222222')
ax1.set_xlabel('Flagged Account Age', fontsize=15, fontweight='bold', labelpad=15)
ax1.set_ylabel('Number of Users', fontsize=15, fontweight='bold', color=blue_color, labelpad=10)
ax2.set_ylabel('Total Flagged Orders', fontsize=15, fontweight='bold', color='#d35400', labelpad=10)

# Configure Ticks
ax1.set_xticks(x)
ax1.set_xticklabels(summary['Age_Group'], fontsize=13, fontweight='bold')
ax1.tick_params(axis='y', labelsize=12)
ax2.tick_params(axis='y', labelsize=12)

# Add Y-limits padding to keep data labels clean and below the border
ax1.set_ylim(0, max(summary['user_count']) * 1.30)
ax2.set_ylim(0, max(summary['total_flagged_orders']) * 1.30)
ax1.grid(True, linestyle='-', alpha=0.6, color='#cccccc')
ax2.grid(False)

# Data Labels: Number of Users (Blue Bars)
for rect in rects1:
    height = int(rect.get_height())
    ax1.annotate(f'{height:,} users',
                 xy=(rect.get_x() + rect.get_width() / 2, height),
                 xytext=(-4, 6), textcoords="offset points",
                 ha='center', va='bottom', fontsize=11, fontweight='bold', color=blue_color)

# Data Labels: Total Flagged Orders (Orange Bars)
for rect in rects2:
    height = int(rect.get_height())
    ax2.annotate(f'{height:,} orders',
                 xy=(rect.get_x() + rect.get_width() / 2, height),
                 xytext=(4, 6), textcoords="offset points",
                 ha='center', va='bottom', fontsize=11, fontweight='bold', color='#d35400')

plt.tight_layout()

# Save image to output directory
plt.savefig(output_file, dpi=300)
plt.close()

print(f"Graph successfully saved to: {output_file}")