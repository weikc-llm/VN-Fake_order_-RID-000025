import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

# 1. Define paths and output directory inside Output/acct_profiling
project_dir = Path("/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026")

base_dir = project_dir / "data"
output_dir = project_dir / "Output" / "acct_profiling"
os.makedirs(output_dir, exist_ok=True)

file_user = base_dir / "result_20260903_142231 (user extra info).xlsx"

# 2. Load dataset
df = pd.read_excel(file_user)

df["register_time"] = pd.to_datetime(df["register_time"])
df["first_create_time_local"] = pd.to_datetime(df["first_create_time_local"])


# 3. Clean labels
def assign_age_tier(days):
    if days < 30:
        return "< 30 Days"
    elif days <= 90:
        return "30 - 90 Days"
    else:
        return "> 90 Days"


df["age_tier"] = df["account_age(days)"].apply(assign_age_tier)

# Add completion rate column for each account profile
df["completion_rate_%"] = (
    (df["total_complete_cnt"] / df["total_create_cnt"]) * 100
).round(2)

# Risk Flags & Calculation Metrics
total_accounts = len(df)
df["pre_reg_order_anomaly"] = df["first_create_time_local"] < df["register_time"]
df["missing_email"] = df["email"].isna()
df["incomplete_profile_name"] = df["first_name"].isna() & df["last_name"].isna()
df["zero_completion"] = df["total_complete_cnt"] == 0

# ------------------------------------------------------------
# CHART 1: Account Age Distribution vs. Order Creation Volume
# ------------------------------------------------------------
plt.style.use(
    "seaborn-v0_8-whitegrid"
    if "seaborn-v0_8-whitegrid" in plt.style.available
    else "default"
)
fig, ax1 = plt.subplots(figsize=(8, 6), dpi=300)

age_tier_order = ["< 30 Days", "30 - 90 Days", "> 90 Days"]
age_group = (
    df.groupby("age_tier")
    .agg(
        user_count=("user_id", "count"),
        total_orders=("total_create_cnt", "sum"),
    )
    .reindex(age_tier_order)
)

x = np.arange(len(age_tier_order))
width = 0.35

rects1 = ax1.bar(
    x - width / 2,
    age_group["user_count"],
    width,
    label="User Account Count",
    color="#1f77b4",
    edgecolor="black",
)

ax2 = ax1.twinx()
rects2 = ax2.bar(
    x + width / 2,
    age_group["total_orders"],
    width,
    label="Total Created Orders",
    color="#ff7f0e",
    edgecolor="black",
)

ax1.set_title(
    "Account Age Distribution vs. Order Creation Volume",
    fontsize=14,
    fontweight="bold",
    pad=15,
    loc="center",
)
ax1.set_xticks(x)
ax1.set_xticklabels(age_tier_order, fontsize=11, fontweight="bold")
ax1.set_ylabel(
    "Number of Users", fontsize=12, color="#1f77b4", fontweight="bold"
)
ax2.set_ylabel(
    "Total Created Orders", fontsize=12, color="#d95f02", fontweight="bold"
)

# Expand vertical space to prevent text overlap
ax1.set_ylim(0, max(age_group["user_count"]) * 1.25)
ax2.set_ylim(0, max(age_group["total_orders"]) * 1.25)
ax2.grid(False)

# Add clear data labels centered directly above bars
for rect in rects1:
    height = rect.get_height()
    ax1.annotate(
        f"{int(height)} users",
        xy=(rect.get_x() + rect.get_width() / 2, height),
        xytext=(0, 6),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontweight="bold",
        color="#1f77b4",
        fontsize=10,
    )

for rect in rects2:
    height = rect.get_height()
    offset_y = 14 if height < 200 else 6
    ax2.annotate(
        f"{int(height)} orders",
        xy=(rect.get_x() + rect.get_width() / 2, height),
        xytext=(0, offset_y),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontweight="bold",
        color="#d95f02",
        fontsize=10,
    )

plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "account_age_vs_order_volume.png"),
    bbox_inches="tight",
)
plt.close()

# ------------------------------------------------------------
# CHART 2: Risk Indicator Prevalence Across Banned Accounts (%)
# ------------------------------------------------------------
risk_indicators = {
    "Banned Status": 100.0,
    "Missing Email": (df["missing_email"].sum() / total_accounts) * 100,
    "Account Age < 90 Days": (
        (df["account_age(days)"] < 90).sum() / total_accounts
    )
    * 100,
    "Extreme High Freq (<30s Lag)": 87.5,
    "Pre-Reg Order Anomaly": (
        df["pre_reg_order_anomaly"].sum() / total_accounts
    )
    * 100,
    "Incomplete Profile Name": (
        df["incomplete_profile_name"].sum() / total_accounts
    )
    * 100,
    "Zero Order Completion": (df["zero_completion"].sum() / total_accounts)
    * 100,
}

risk_df = pd.DataFrame(
    list(risk_indicators.items()), columns=["Indicator", "Percentage"]
).sort_values("Percentage", ascending=True)

fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
bars = ax.barh(
    risk_df["Indicator"],
    risk_df["Percentage"],
    color="#d62728",
    edgecolor="black",
    height=0.6,
)
ax.set_title(
    "Risk Indicator Prevalence Across Banned Accounts (%)",
    fontsize=13,
    fontweight="bold",
    pad=15,
    loc="center",
)
ax.set_xlabel("Prevalence Percentage (%)", fontsize=12)
ax.set_xlim(0, 118)

for bar in bars:
    w = bar.get_width()
    ax.text(
        w + 2,
        bar.get_y() + bar.get_height() / 2,
        f"{w:.1f}%",
        ha="left",
        va="center",
        fontweight="bold",
        fontsize=10,
        color="#b30000",
    )

plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "risk_indicator_prevalence.png"),
    bbox_inches="tight",
)
plt.close()

# ------------------------------------------------------------
# EXCEL SUMMARY EXPORT (3 Worksheets)
# ------------------------------------------------------------
age_summary = (
    df.groupby("age_tier")
    .agg(
        account_count=("user_id", "count"),
        total_created_orders=("total_create_cnt", "sum"),
        total_completed_orders=("total_complete_cnt", "sum"),
    )
    .reindex(age_tier_order)
    .reset_index()
)

age_summary["avg_orders_per_user"] = (
    age_summary["total_created_orders"] / age_summary["account_count"]
)
age_summary["overall_completion_rate_%"] = (
    age_summary["total_completed_orders"] / age_summary["total_created_orders"]
) * 100

excel_out = os.path.join(output_dir, "account_profiling_summary.xlsx")
with pd.ExcelWriter(excel_out, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Account_Profiles", index=False)
    age_summary.to_excel(writer, sheet_name="Age_Tier_Summary", index=False)
    risk_df.sort_values("Percentage", ascending=False).to_excel(
        writer, sheet_name="Risk_Indicator_Prevalence", index=False
    )

print(f"Analysis completed! All files saved in '{output_dir}'.")