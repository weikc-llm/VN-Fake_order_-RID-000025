import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

# 1. Define project directory and create output subdirectory
project_dir = Path("/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026")

base_dir = project_dir / "data"
output_dir = project_dir / "Output" / "order_volume_breakdown"
os.makedirs(output_dir, exist_ok=True)

input_file = base_dir / "order_lag_splitting.xlsx"
output_excel = output_dir / "order_lag_split_by_user.xlsx"

# 2. Load dataset - PRESERVE LONG IDs AS STRINGS
id_cols = ["order_display_id", "user_id", "driver_id"]
df = pd.read_excel(input_file, dtype={col: str for col in id_cols})

# Ensure all ID columns remain clean strings without floating-point decimals
for col in id_cols:
    if col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.strip()
        )

df["order_creation_local_time"] = pd.to_datetime(
    df["order_creation_local_time"]
)

# 3. Extract Time Formats (Month, Date, Hour & Time Window)
df["order_month"] = df["order_creation_local_time"].dt.strftime("%Y-%m")
df["order_date"] = df["order_creation_local_time"].dt.strftime("%Y-%m-%d")
df["order_hour"] = df["order_creation_local_time"].dt.hour
df["time_window"] = df["order_hour"].apply(
    lambda h: f"{h:02d}:00 - {h:02d}:59"
)

# 4. Sort chronologically by user and calculate lag
df = df.sort_values(
    by=["user_id", "order_creation_local_time"], ascending=[True, True]
)
df["lag_sec_from_prev"] = (
    df.groupby("user_id")["order_creation_local_time"].diff().dt.total_seconds()
)


# 5. Assign frequency tiers with custom categorical ordering
def assign_frequency_tier(sec):
    if pd.isna(sec):
        return "First Order"
    elif sec < 30:
        return "0s - <30s"
    elif sec < 60:
        return "30s - <1m"
    elif sec < 300:
        return "1m - <5m"
    elif sec < 1800:
        return "5m - <30m"
    else:
        return ">= 30m"


df["frequency_tier"] = df["lag_sec_from_prev"].apply(assign_frequency_tier)

tier_order = [
    "First Order",
    "0s - <30s",
    "30s - <1m",
    "1m - <5m",
    "5m - <30m",
    ">= 30m",
]
df["frequency_tier"] = pd.Categorical(
    df["frequency_tier"], categories=tier_order, ordered=True
)

total_volume = len(df)

# ------------------------------------------------------------
# 6. Generate & Save Charts (Horizontal Readable Text Labels)
# ------------------------------------------------------------

# Chart A: Hourly Breakdown Chart
hourly_counts = (
    df["order_hour"]
    .value_counts()
    .reindex(range(24), fill_value=0)
    .sort_index()
)
plt.figure(figsize=(14, 6), dpi=300)
bars_h = plt.bar(
    hourly_counts.index,
    hourly_counts.values,
    color="#1f77b4",
    edgecolor="black",
    width=0.7,
)

plt.xlabel("Hour of Day (24-Hour Format)", fontsize=12, fontweight="bold")
plt.ylabel("Order Volume", fontsize=12, fontweight="bold")
plt.title(
    "Hourly Order Volume Breakdown (00:00 - 23:00)",
    fontsize=14,
    fontweight="bold",
    pad=15,
    loc="center",
)
plt.xticks(range(0, 24), fontsize=10, fontweight="bold")
plt.grid(axis="y", linestyle="--", alpha=0.7)

for bar in bars_h:
    yval = bar.get_height()
    if yval > 0:
        pct = (yval / total_volume) * 100
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + 15,
            f"{yval:,}\n({pct:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
            color="#0d47a1" if pct >= 10 else "black",
            rotation=0,
        )

plt.ylim(0, max(hourly_counts.values) * 1.25)
plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "hourly_order_volume.png"), bbox_inches="tight"
)
plt.close()

# Chart B: Monthly Breakdown Chart
month_counts = df["order_month"].value_counts().sort_index()
plt.figure(figsize=(8, 5), dpi=300)
bars_m = plt.bar(
    month_counts.index,
    month_counts.values,
    color="#1f77b4",
    edgecolor="black",
    width=0.4,
)
plt.xlabel("Month", fontsize=11, fontweight="bold")
plt.ylabel("Order Volume", fontsize=11, fontweight="bold")
plt.title(
    "Monthly Order Volume Breakdown",
    fontsize=13,
    fontweight="bold",
    loc="center",
)
plt.grid(axis="y", linestyle="--", alpha=0.7)

for bar in bars_m:
    yval = bar.get_height()
    pct = (yval / total_volume) * 100
    plt.text(
        bar.get_x() + bar.get_width() / 2.0,
        yval + 15,
        f"{yval:,}\n({pct:.1f}%)",
        ha="center",
        va="bottom",
        fontsize=11,
        fontweight="bold",
        rotation=0,
    )

plt.ylim(0, max(month_counts.values) * 1.20)
plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "monthly_order_volume.png"), bbox_inches="tight"
)
plt.close()

# Chart C: Daily Breakdown Chart
date_counts = df["order_date"].value_counts().sort_index()
plt.figure(figsize=(14, 6), dpi=300)
bars_d = plt.bar(
    date_counts.index,
    date_counts.values,
    color="#2ca02c",
    edgecolor="black",
    width=0.6,
)
plt.xlabel("Date (YYYY-MM-DD)", fontsize=11, fontweight="bold")
plt.ylabel("Order Volume", fontsize=11, fontweight="bold")
plt.title(
    "Daily Order Volume Breakdown",
    fontsize=13,
    fontweight="bold",
    loc="center",
)
plt.xticks(rotation=45, ha="right", fontsize=9, fontweight="bold")
plt.grid(axis="y", linestyle="--", alpha=0.7)

for bar in bars_d:
    yval = bar.get_height()
    if yval > 0:
        pct = (yval / total_volume) * 100
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + 2,
            f"{yval}\n({pct:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=7.5,
            fontweight="bold",
            rotation=0,
        )

plt.ylim(0, max(date_counts.values) * 1.25)
plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "daily_order_volume.png"), bbox_inches="tight"
)
plt.close()

# ------------------------------------------------------------
# Chart D: High-Frequency Orders (<30s Lag) Count per User ID
# ------------------------------------------------------------
summary_raw = (
    pd.crosstab(df["user_id"], df["frequency_tier"], margins=True, margins_name="Total")
    .reset_index()
)

user_data = summary_raw[
    ~summary_raw["user_id"].isin(["Total", "Percentage %"])
].copy()

user_data_sorted = user_data.sort_values(
    by="0s - <30s", ascending=True
).reset_index(drop=True)

colors_hf = [
    "#d62728" if x > 0 else "#cccccc" for x in user_data_sorted["0s - <30s"]
]

fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
bars = ax.barh(
    user_data_sorted["user_id"],
    user_data_sorted["0s - <30s"],
    color=colors_hf,
    edgecolor="black",
    linewidth=0.7,
    height=0.65,
)

ax.set_title(
    "High-Frequency Orders (<30s Lag) Count per User ID",
    fontsize=13,
    fontweight="bold",
    pad=15,
    loc="center",
)
ax.set_xlabel(
    "High-Frequency Order Count (<30s Lag)",
    fontsize=11,
    fontweight="bold",
    labelpad=10,
)
ax.set_ylabel("User ID", fontsize=11, fontweight="bold", labelpad=10)
ax.grid(axis="x", linestyle="--", alpha=0.5)

for bar, (i, row) in zip(bars, user_data_sorted.iterrows()):
    val = int(row["0s - <30s"])
    tot = int(row["Total"])
    pct = (val / tot) * 100 if tot > 0 else 0
    if val > 0:
        ax.text(
            val + 1.5,
            bar.get_y() + bar.get_height() / 2,
            f"{val} out of {tot} orders ({pct:.1f}%)",
            ha="left",
            va="center",
            fontweight="bold",
            color="#b30000",
            fontsize=9.5,
        )
    else:
        ax.text(
            1,
            bar.get_y() + bar.get_height() / 2,
            f"0 out of {tot} orders (0.0%)",
            ha="left",
            va="center",
            color="#777777",
            fontsize=9,
            fontstyle="italic",
        )

ax.set_xlim(0, max(user_data_sorted["0s - <30s"]) * 1.40)
plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "high_frequency_orders_per_user.png"),
    bbox_inches="tight",
)
plt.close()

# ------------------------------------------------------------
# Chart E: 100% Normalized Order Volume Share per User ID
# ------------------------------------------------------------
pct_df = user_data.copy()
tier_cols_norm = [
    "First Order",
    "0s - <30s",
    "30s - <1m",
    "1m - <5m",
    "5m - <30m",
    ">= 30m",
]

for col in tier_cols_norm:
    pct_df[col] = (pct_df[col] / pct_df["Total"]) * 100

pct_df = pct_df.sort_values(by="0s - <30s", ascending=True).reset_index(
    drop=True
)

fig, ax = plt.subplots(figsize=(12, 8), dpi=300)

ordered_tiers = [
    "0s - <30s",
    "30s - <1m",
    "1m - <5m",
    "5m - <30m",
    ">= 30m",
    "First Order",
]
colors_norm = ["#d62728", "#ff7f0e", "#1f77b4", "#2ca02c", "#9467bd", "#8c564b"]

left = np.zeros(len(pct_df))

for col, color in zip(ordered_tiers, colors_norm):
    values = pct_df[col].values
    bars = ax.barh(
        pct_df["user_id"],
        values,
        left=left,
        label=col,
        color=color,
        edgecolor="black",
        linewidth=0.6,
        height=0.65,
    )

    for i, val in enumerate(values):
        if val >= 6.0:
            ax.text(
                left[i] + val / 2.0,
                i,
                f"{val:.1f}%",
                ha="center",
                va="center",
                color=(
                    "white"
                    if col in ["0s - <30s", "1m - <5m"]
                    else "black"
                ),
                fontsize=8.5,
                fontweight="bold",
            )

    left += values

ax.set_title(
    "100% Normalized Order Volume Share per User ID by Lag Frequency Tier",
    fontsize=13,
    fontweight="bold",
    pad=15,
    loc="center",
)
ax.set_xlabel(
    "Percentage of Total User Orders (%)",
    fontsize=11,
    fontweight="bold",
    labelpad=10,
)
ax.set_ylabel("User ID", fontsize=11, fontweight="bold", labelpad=10)
ax.set_xlim(0, 100)
ax.grid(axis="x", linestyle="--", alpha=0.5)
ax.legend(
    title="Frequency Tier",
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    frameon=True,
    facecolor="white",
)

# Right-margin text: "X out of Y orders (Z%)"
for i, row in pct_df.iterrows():
    hf_cnt = int(user_data.loc[user_data["user_id"] == row["user_id"], "0s - <30s"].values[0])
    tot_cnt = int(row["Total"])
    hf_pct = row["0s - <30s"]
    
    if hf_pct > 0:
        ax.text(
            101.5,
            i,
            f"{hf_cnt} out of {tot_cnt} orders ({hf_pct:.1f}%)",
            ha="left",
            va="center",
            color="#b30000" if hf_pct > 50 else "#333333",
            fontweight="bold" if hf_pct > 50 else "normal",
            fontsize=9,
        )
    else:
        ax.text(
            101.5,
            i,
            f"0 out of {tot_cnt} orders (0.0%)",
            ha="left",
            va="center",
            color="#777777",
            fontsize=9,
        )

ax.set_xlim(0, 140)
plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "normalized_100pct_stacked_bar.png"),
    bbox_inches="tight",
)
plt.close()

# ------------------------------------------------------------
# 7. Write Summary Tables with Percentage Rows into Excel
# ------------------------------------------------------------
with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:

    # Helper function to append percentage row to crosstab summaries
    def append_pct_row(summary_table, total_vol):
        summary_copy = summary_table.copy()
        pct_row = {"user_id": "Percentage %"}
        for col in summary_copy.columns:
            if col != "user_id":
                col_sum = summary_copy.loc[
                    summary_copy["user_id"] == "Total", col
                ].values
                if len(col_sum) > 0:
                    pct_row[col] = f"{(col_sum[0] / total_vol) * 100:.1f}%"
        return pd.concat(
            [summary_copy, pd.DataFrame([pct_row])], ignore_index=True
        )

    # Sheet 1: Summary Overview (Lag Tiers)
    summary_df = (
        pd.crosstab(
            df["user_id"], df["frequency_tier"], margins=True, margins_name="Total"
        )
        .reset_index()
    )
    summary_df = append_pct_row(summary_df, total_volume)
    summary_df.to_excel(writer, sheet_name="Summary_Overview", index=False)

    # Sheet 2: Monthly Breakdown (Total)
    monthly_df = (
        df.groupby("order_month").size().reset_index(name="order_volume")
    )
    monthly_df["percentage_%"] = (
        (monthly_df["order_volume"] / total_volume) * 100
    ).round(2).astype(str) + "%"
    monthly_df.to_excel(writer, sheet_name="Monthly_Breakdown", index=False)

    # Sheet 3: Daily Breakdown (Total)
    daily_df = df.groupby("order_date").size().reset_index(name="order_volume")
    daily_df["percentage_%"] = (
        (daily_df["order_volume"] / total_volume) * 100
    ).round(2).astype(str) + "%"
    daily_df.to_excel(writer, sheet_name="Daily_Breakdown", index=False)

    # Sheet 4: Hourly Breakdown (Total)
    hourly_df = (
        df.groupby(["order_hour", "time_window"])
        .size()
        .reset_index(name="order_volume")
    )
    hourly_df["percentage_%"] = (
        (hourly_df["order_volume"] / total_volume) * 100
    ).round(2).astype(str) + "%"
    hourly_df.to_excel(writer, sheet_name="Hourly_Breakdown", index=False)

    # Sheet 5: User x Monthly Matrix
    user_monthly = (
        pd.crosstab(
            df["user_id"],
            df["order_month"],
            margins=True,
            margins_name="Total",
        )
        .reset_index()
    )
    user_monthly = append_pct_row(user_monthly, total_volume)
    user_monthly.to_excel(writer, sheet_name="User_Monthly_Breakdown", index=False)

    # Sheet 6: User x Daily Matrix
    user_daily = (
        pd.crosstab(
            df["user_id"], df["order_date"], margins=True, margins_name="Total"
        )
        .reset_index()
    )
    user_daily = append_pct_row(user_daily, total_volume)
    user_daily.to_excel(writer, sheet_name="User_Daily_Breakdown", index=False)

    # Sheet 7: User x Hourly Matrix
    user_hourly = (
        pd.crosstab(
            df["user_id"],
            df["time_window"],
            margins=True,
            margins_name="Total",
        )
        .reset_index()
    )
    user_hourly = append_pct_row(user_hourly, total_volume)
    user_hourly.to_excel(writer, sheet_name="User_Hourly_Breakdown", index=False)

    # Individual User Sheets
    for user_id, group in df.groupby("user_id"):
        sheet_title = f"User_{user_id}"
        group.to_excel(writer, sheet_name=sheet_title, index=False)

print(
    f"Successfully processed! All outputs saved in folder: '{output_dir}'"
)