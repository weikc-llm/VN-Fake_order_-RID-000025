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

# File source using merged_user_info.xlsx
file_user = base_dir / "merged_user_info.xlsx"

# 2. Load merged dataset (preserving string IDs)
id_cols = ["user_id", "phone_no", "device_identifier", "city_id"]
df = pd.read_excel(file_user, dtype={col: str for col in id_cols})

# Clean string formatting for numerical string fields
for col in id_cols:
    if col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.strip()
        )

# 3. Timezone Adjustment & Datetime Parsing
# register_time is in MYT (UTC+8); subtract 1 hour to convert to Vietnam Time (UTC+7)
df["register_time_vn"] = pd.to_datetime(df["register_time"]) - pd.Timedelta(hours=1)
df["first_create_time_local_dt"] = pd.to_datetime(df["first_create_time_local"])


# 4. Clean age tier labels
def assign_age_tier(days):
    if days < 30:
        return "< 30 Days"
    elif days <= 90:
        return "30 - 90 Days"
    else:
        return "> 90 Days"


# 5. Engineered Metric Calculations
df["age_tier"] = df["account_age(days)"].apply(assign_age_tier)
df["completion_rate_%"] = (
    (df["total_complete_cnt"] / df["total_create_cnt"]) * 100
).round(2)

total_accounts = len(df)

# Anomaly flag comparing Vietnam Local Order Creation vs Adjusted Vietnam Registration Time
df["pre_reg_order_anomaly"] = df["first_create_time_local_dt"] < df["register_time_vn"]
df["missing_email"] = df["email"].isna()
df["incomplete_profile_name"] = df["first_name"].isna() & df["last_name"].isna()
df["zero_completion"] = df["total_complete_cnt"] == 0
df["is_web_device"] = df["device_type"] == "WEB"
df["is_corporate"] = df["is_corp"] == "Corp"
df["shared_device_id"] = (
    df["device_identifier"] == "05724e79-2bde-4cfc-a9af-c216ed36b2cf"
)
df["hcm_login_cantho_target"] = (df["first_login_city"] == "Ho Chi Minh City") & (
    df["max_order_city_id"] == "Can Tho"
)

plt.style.use(
    "seaborn-v0_8-whitegrid"
    if "seaborn-v0_8-whitegrid" in plt.style.available
    else "default"
)

# ------------------------------------------------------------
# CHART 1: Account Age Distribution vs. Order Creation Volume
# ------------------------------------------------------------
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
ax1.set_xlabel("Account Age", fontsize=12, fontweight="bold", labelpad=10)

ax1.set_ylabel(
    "Number of Users", fontsize=12, color="#1f77b4", fontweight="bold"
)
ax2.set_ylabel(
    "Total Created Orders", fontsize=12, color="#d95f02", fontweight="bold"
)

ax1.set_ylim(0, max(age_group["user_count"]) * 1.25)
ax2.set_ylim(0, max(age_group["total_orders"]) * 1.25)
ax2.grid(False)

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
# CHART 2: Account Profiling Indicator Breakdown (%)
# ------------------------------------------------------------
# Removed "Pre-Reg Order Anomaly" (evaluated to 0% after MYT-to-ICT timezone adjustment)
risk_indicators = {
    "Banned Status": 100.0,
    "Missing Email": (df["missing_email"].sum() / total_accounts) * 100,
    "Account Age < 90 Days": (
        (df["account_age(days)"] < 90).sum() / total_accounts
    )
    * 100,
    "Extreme High Freq (<30s Lag)": 87.5,
    "Incomplete Profile Name": (
        df["incomplete_profile_name"].sum() / total_accounts
    )
    * 100,
    "WEB Access Channel": (df["is_web_device"].sum() / total_accounts) * 100,
    "Zero Order Completion": (df["zero_completion"].sum() / total_accounts)
    * 100,
    "Shared Device ID": (
        df["shared_device_id"].sum() / total_accounts
    )
    * 100,
}

risk_df = pd.DataFrame(
    list(risk_indicators.items()), columns=["Indicator", "Percentage"]
).sort_values("Percentage", ascending=True)

fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
bars = ax.barh(
    risk_df["Indicator"],
    risk_df["Percentage"],
    color="#d62728",
    edgecolor="black",
    height=0.6,
)
ax.set_title(
    "Account Profiling Indicator Breakdown",
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
        fontsize=9.5,
        color="#b30000",
    )

plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "risk_indicator_prevalence.png"),
    bbox_inches="tight",
)
plt.close()

# ------------------------------------------------------------
# CHART 3A: Device Type Access Channel (WEB vs ANDROID)
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
dev_counts = df["device_type"].value_counts()
bars = ax.bar(
    dev_counts.index,
    dev_counts.values,
    color="#1f77b4",
    edgecolor="black",
    width=0.45,
)
ax.set_title(
    "Device Type Access Channel (WEB vs ANDROID)",
    fontweight="bold",
    fontsize=12,
    pad=15,
    loc="center",
)
ax.set_xlabel("Access Channel", fontweight="bold", fontsize=11, labelpad=10)
ax.set_ylabel("Number of Accounts", fontweight="bold", fontsize=11, labelpad=10)
ax.grid(axis="y", linestyle="--", alpha=0.5)

for bar in bars:
    yval = bar.get_height()
    pct = (yval / total_accounts) * 100
    ax.text(
        bar.get_x() + bar.get_width() / 2.0,
        yval + 0.3,
        f"{yval} ({pct:.1f}%)",
        ha="center",
        va="bottom",
        fontweight="bold",
        fontsize=10,
    )

ax.set_ylim(0, max(dev_counts.values) * 1.25)
plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "device_type_distribution.png"),
    bbox_inches="tight",
)
plt.close()

# ------------------------------------------------------------
# CHART 3B: Corporate Account Flag (Non-Corp vs Corp)
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
corp_counts = df["is_corp"].value_counts()
bars = ax.bar(
    corp_counts.index,
    corp_counts.values,
    color="#2ca02c",
    edgecolor="black",
    width=0.45,
)
ax.set_title(
    "Corporate Account Classification (Non-Corp vs Corp)",
    fontweight="bold",
    fontsize=12,
    pad=15,
    loc="center",
)
ax.set_xlabel("Corporate Flag Status", fontweight="bold", fontsize=11, labelpad=10)
ax.set_ylabel("Number of Accounts", fontweight="bold", fontsize=11, labelpad=10)
ax.grid(axis="y", linestyle="--", alpha=0.5)

for bar in bars:
    yval = bar.get_height()
    pct = (yval / total_accounts) * 100
    ax.text(
        bar.get_x() + bar.get_width() / 2.0,
        yval + 0.3,
        f"{yval} ({pct:.1f}%)",
        ha="center",
        va="bottom",
        fontweight="bold",
        fontsize=10,
    )

ax.set_ylim(0, max(corp_counts.values) * 1.25)
plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "corporate_account_status.png"),
    bbox_inches="tight",
)
plt.close()

# ------------------------------------------------------------
# CHART 3C: Multi-Account Device Identifier Sharing
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.5, 5), dpi=300)
shared_cnt = df["shared_device_id"].sum()
unique_cnt = total_accounts - shared_cnt

bars = ax.bar(
    ["Shared Device Identifier\n(05724e79-...)", "Unique Device Identifier"],
    [shared_cnt, unique_cnt],
    color="#17becf",
    edgecolor="black",
    width=0.45,
)
ax.set_title(
    "Multi-Account Device Identifier Sharing",
    fontweight="bold",
    fontsize=12,
    pad=15,
    loc="center",
)
ax.set_xlabel(
    "Device Identifier Category", fontweight="bold", fontsize=11, labelpad=10
)
ax.set_ylabel("Number of Accounts", fontweight="bold", fontsize=11, labelpad=10)
ax.grid(axis="y", linestyle="--", alpha=0.5)

for bar, v in zip(bars, [shared_cnt, unique_cnt]):
    pct = (v / total_accounts) * 100
    ax.text(
        bar.get_x() + bar.get_width() / 2.0,
        v + 0.3,
        f"{v} ({pct:.1f}%)",
        ha="center",
        va="bottom",
        fontweight="bold",
        fontsize=10,
    )

ax.set_ylim(0, max(unique_cnt, shared_cnt) * 1.25)
plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "device_fingerprint_sharing.png"),
    bbox_inches="tight",
)
plt.close()

# ------------------------------------------------------------
# CHART 3D: Total Completed Orders & Completion Rate Share (NO GRIDLINES)
# ------------------------------------------------------------
df_sorted = df.sort_values(by="total_complete_cnt", ascending=True).reset_index(
    drop=True
)

fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
colors_comp = [
    "#2ca02c" if x > 0 else "#cccccc" for x in df_sorted["total_complete_cnt"]
]

bars = ax.barh(
    df_sorted["user_id"],
    df_sorted["total_complete_cnt"],
    color=colors_comp,
    edgecolor="black",
    linewidth=0.7,
    height=0.65,
)

ax.set_title(
    "Total Completed Orders & Completion Rate Share per User ID",
    fontsize=13,
    fontweight="bold",
    pad=15,
    loc="center",
)
ax.set_xlabel(
    "Completed Order Count", fontsize=11, fontweight="bold", labelpad=10
)
ax.set_ylabel("User ID", fontsize=11, fontweight="bold", labelpad=10)
ax.grid(False)

for bar, (i, row) in zip(bars, df_sorted.iterrows()):
    comp = int(row["total_complete_cnt"])
    tot = int(row["total_create_cnt"])
    rate = row["completion_rate_%"]

    if comp > 0:
        ax.text(
            comp + 0.08,
            bar.get_y() + bar.get_height() / 2,
            f"{comp} out of {tot} orders ({rate:.2f}%)",
            ha="left",
            va="center",
            fontweight="bold",
            color="#1b7837",
            fontsize=9.5,
        )
    else:
        ax.text(
            0.08,
            bar.get_y() + bar.get_height() / 2,
            f"0 out of {tot} orders (0.00%)",
            ha="left",
            va="center",
            color="#666666",
            fontsize=9,
            fontstyle="italic",
        )

ax.set_xlim(
    0,
    max(df_sorted["total_complete_cnt"]) * 2.2
    if max(df_sorted["total_complete_cnt"]) > 0
    else 4,
)
plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "completed_orders_per_user.png"),
    bbox_inches="tight",
)
plt.close()

# ------------------------------------------------------------
# EXCEL SUMMARY EXPORT (Full 40 original + engineered metrics)
# ------------------------------------------------------------
export_df = df.drop(
    columns=["register_time_vn", "first_create_time_local_dt"]
)

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
    export_df.to_excel(writer, sheet_name="Account_Profiles", index=False)
    age_summary.to_excel(writer, sheet_name="Age_Tier_Summary", index=False)
    risk_df.sort_values("Percentage", ascending=False).to_excel(
        writer, sheet_name="Risk_Indicator_Prevalence", index=False
    )

print(
    f"Analysis completed! Clean indicator breakdown chart saved."
)