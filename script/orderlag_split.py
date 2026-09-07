import os
import matplotlib.pyplot as plt
import pandas as pd

# 1. Define file paths and create output directory
input_file = (
    "/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026/data/order_lag_splitting.xlsx"
)
output_dir = (
    "/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026/order_volume_breakdown"
)
os.makedirs(output_dir, exist_ok=True)

output_excel = os.path.join(output_dir, "order_lag_split_by_user.xlsx")

# 2. Load dataset
df = pd.read_excel(input_file)
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

# ------------------------------------------------------------
# 6. Generate & Save Charts into 'order_volume_breakdown'
# ------------------------------------------------------------

# Chart A: Hourly Breakdown Chart
hourly_counts = df["order_hour"].value_counts().sort_index()
plt.figure(figsize=(10, 5), dpi=300)
plt.bar(
    hourly_counts.index, hourly_counts.values, color="#1f77b4", edgecolor="black"
)
plt.xlabel("Hour of Day (24-Hour Format)", fontsize=12)
plt.ylabel("Order Volume", fontsize=12)
plt.title(
    "Hourly Order Volume Breakdown (00:00 - 23:00)",
    fontsize=14,
    fontweight="bold",
)
plt.xticks(range(0, 24))
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "hourly_order_volume.png"))
plt.close()

# Chart B: Monthly Breakdown Chart
month_counts = df["order_month"].value_counts().sort_index()
plt.figure(figsize=(7, 4.5), dpi=300)
bars_m = plt.bar(
    month_counts.index,
    month_counts.values,
    color="#1f77b4",
    edgecolor="black",
    width=0.4,
)
plt.xlabel("Month", fontsize=11)
plt.ylabel("Order Volume", fontsize=11)
plt.title("Monthly Order Volume Breakdown", fontsize=13, fontweight="bold")
plt.grid(axis="y", linestyle="--", alpha=0.7)
for bar in bars_m:
    yval = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2.0,
        yval + 15,
        f"{yval:,}",
        ha="center",
        va="bottom",
        fontweight="bold",
    )
plt.ylim(0, max(month_counts.values) * 1.15)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "monthly_order_volume.png"))
plt.close()

# Chart C: Daily Breakdown Chart
date_counts = df["order_date"].value_counts().sort_index()
plt.figure(figsize=(12, 5), dpi=300)
bars_d = plt.bar(
    date_counts.index,
    date_counts.values,
    color="#2ca02c",
    edgecolor="black",
    width=0.6,
)
plt.xlabel("Date (YYYY-MM-DD)", fontsize=11)
plt.ylabel("Order Volume", fontsize=11)
plt.title("Daily Order Volume Breakdown", fontsize=13, fontweight="bold")
plt.xticks(rotation=45, ha="right", fontsize=9)
plt.grid(axis="y", linestyle="--", alpha=0.7)
for bar in bars_d:
    yval = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2.0,
        yval + 2,
        f"{yval}",
        ha="center",
        va="bottom",
        fontsize=8,
    )
plt.ylim(0, max(date_counts.values) * 1.15)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "daily_order_volume.png"))
plt.close()

# ------------------------------------------------------------
# 7. Write Summary Tables & Individual Sheets into Excel
# ------------------------------------------------------------
with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
    # Sheet 1: Summary Overview (Lag Tiers)
    summary_df = (
        pd.crosstab(
            df["user_id"], df["frequency_tier"], margins=True, margins_name="Total"
        )
        .reset_index()
    )
    summary_df.to_excel(writer, sheet_name="Summary_Overview", index=False)

    # Sheet 2: Monthly Breakdown (Total)
    monthly_df = (
        df.groupby("order_month").size().reset_index(name="order_volume")
    )
    monthly_df.to_excel(writer, sheet_name="Monthly_Breakdown", index=False)

    # Sheet 3: Daily Breakdown (Total)
    daily_df = df.groupby("order_date").size().reset_index(name="order_volume")
    daily_df.to_excel(writer, sheet_name="Daily_Breakdown", index=False)

    # Sheet 4: Hourly Breakdown (Total)
    hourly_df = (
        df.groupby(["order_hour", "time_window"])
        .size()
        .reset_index(name="order_volume")
    )
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
    user_monthly.to_excel(writer, sheet_name="User_Monthly_Breakdown", index=False)

    # Sheet 6: User x Daily Matrix
    user_daily = (
        pd.crosstab(
            df["user_id"], df["order_date"], margins=True, margins_name="Total"
        )
        .reset_index()
    )
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
    user_hourly.to_excel(writer, sheet_name="User_Hourly_Breakdown", index=False)

    # Individual User Sheets
    for user_id, group in df.groupby("user_id"):
        sheet_title = f"User_{user_id}"
        group.to_excel(writer, sheet_name=sheet_title, index=False)

print(
    f"Successfully processed! All outputs saved in folder: '{output_dir}'"
)