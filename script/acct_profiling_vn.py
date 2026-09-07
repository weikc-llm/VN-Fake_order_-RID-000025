import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 1. Define paths and output directory
base_dir = "/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026/data"
file_user = os.path.join(
    base_dir, "result_20260903_142231 (user extra info).xlsx"
)

output_dir = os.path.join(base_dir, "account_profiling")
os.makedirs(output_dir, exist_ok=True)

# 2. Load dataset
df = pd.read_excel(file_user)

df["register_time"] = pd.to_datetime(df["register_time"])
df["first_create_time_local"] = pd.to_datetime(df["first_create_time_local"])


# 3. Clean labels without (New), (Recent), (Legacy)
def assign_age_tier(days):
    if days < 30:
        return "< 30 Days"
    elif days <= 90:
        return "30 - 90 Days"
    else:
        return "> 90 Days"


df["age_tier"] = df["account_age(days)"].apply(assign_age_tier)

# Risk Flags
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
ax1.set_ylim(0, max(age_group["user_count"]) * 1.22)
ax2.set_ylim(0, max(age_group["total_orders"]) * 1.22)
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
    ax2.annotate(
        f"{int(height)} orders",
        xy=(rect.get_x() + rect.get_width() / 2, height),
        xytext=(0, 6),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontweight="bold",
        color="#d95f02",
        fontsize=10,
    )

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "account_age_vs_order_volume.png"))
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
    fontsize=14,
    fontweight="bold",
    pad=15,
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
plt.savefig(os.path.join(output_dir, "risk_indicator_prevalence.png"))
plt.close()

print(f"Charts saved in '{output_dir}'")