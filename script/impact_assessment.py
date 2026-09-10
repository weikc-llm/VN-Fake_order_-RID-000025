import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

# 1. Define project directory and input/output file paths
project_dir = Path("/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026")

base_dir = project_dir / "data"
output_dir = project_dir / "Output" / "high_frequency_simulation"
os.makedirs(output_dir, exist_ok=True)

input_file = base_dir / "simulation_high_frequency_tier.xlsx"
output_chart = output_dir / "july_aug_user_high_frequency_share.png"

# 2. Read exact target sheets
df_july = pd.read_excel(input_file, sheet_name="account to check (July)")
df_aug = pd.read_excel(input_file, sheet_name="account to check(Aug)")

# 3. Clean and process July data
df_july["user_id_str"] = df_july["user_id"].astype(str)
df_july["hf_pct"] = df_july["0s - <30s (>50%)"] * 100
df_july_sorted = df_july.sort_values(by="hf_pct", ascending=True).reset_index(
    drop=True
)

# 4. Clean and process August data
df_aug["user_id_str"] = df_aug["user_id"].astype(str)
df_aug["hf_pct"] = df_aug["0s - <30s (>50%)"] * 100
df_aug_sorted = df_aug.sort_values(by="hf_pct", ascending=True).reset_index(
    drop=True
)

# 5. Create side-by-side comparison visualization
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9), dpi=300)

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

# 6. Save image
plt.savefig(output_chart, bbox_inches="tight")
plt.close()

print(f"Chart successfully generated and saved to: '{output_chart}'")