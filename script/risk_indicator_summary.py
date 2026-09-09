import os
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# 1. Define project directory and output paths
project_dir = Path("/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026")
base_dir = project_dir / "data"
output_dir = project_dir / "Output" / "acct_profiling"
os.makedirs(output_dir, exist_ok=True)

# 2. Define input file paths
file_user = base_dir / "merged_user_info.xlsx"
input_file_lag = (
    project_dir / "Output" / "order_volume_breakdown" / "order_lag_split_by_user.xlsx"
)

# 3. Read input datasets
df_user = pd.read_excel(file_user)
df_lag_summary = pd.read_excel(input_file_lag, sheet_name="Summary_Overview")

total_accounts = len(df_user)

# 4. Compute derived risk boolean flags cleanly and dynamically
if "missing_email" not in df_user.columns:
    df_user["missing_email"] = df_user["email"].isna() | (
        df_user["email"].astype(str).str.strip() == ""
    )

# Clean dynamic check for incomplete profile name
if "user_name" in df_user.columns:
    df_user["incomplete_profile_name"] = df_user["user_name"].isna() | (
        df_user["user_name"].astype(str).str.strip() == ""
    )
elif "incomplete_profile_name" not in df_user.columns:
    full_name = (
        df_user["first_name"].fillna("").astype(str)
        + df_user["last_name"].fillna("").astype(str)
    ).str.strip()
    df_user["incomplete_profile_name"] = full_name == ""

if "is_web_device" not in df_user.columns:
    df_user["is_web_device"] = df_user["device_type"].astype(str).str.upper() == "WEB"

if "zero_completion" not in df_user.columns:
    df_user["zero_completion"] = df_user["total_complete_cnt"] == 0

if "shared_device_id" not in df_user.columns:
    shared_ids = df_user["device_identifier"].value_counts()
    shared_ids = shared_ids[shared_ids > 1].index
    df_user["shared_device_id"] = df_user["device_identifier"].isin(shared_ids)

# 5. Calculate High-Frequency Account Prevalence dynamically (<30s lag)
user_lag = df_lag_summary[
    ~df_lag_summary["user_id"].isin(["Total", "Percentage %"])
].copy()
hf_accounts_cnt = (user_lag["0s - <30s"] > 0).sum()
hf_prevalence = (hf_accounts_cnt / total_accounts) * 100

# 6. Build dynamic risk indicators dictionary (Fully automated calculation)
risk_indicators = {
    "Missing Email": (df_user["missing_email"].sum() / total_accounts) * 100,
    "Account Age < 90 Days": (
        (df_user["account_age(days)"] < 90).sum() / total_accounts
    )
    * 100,
    "Incomplete Profile Name": (
        df_user["incomplete_profile_name"].sum() / total_accounts
    )
    * 100,
    "High-Frequency Orders (<30s Lag)": hf_prevalence,
    "WEB Access Channel": (df_user["is_web_device"].sum() / total_accounts) * 100,
    "Zero Order Completion": (df_user["zero_completion"].sum() / total_accounts)
    * 100,
    "Shared Device ID": (
        df_user["shared_device_id"].sum() / total_accounts
    )
    * 100,
}

# 7. Convert to DataFrame and sort for horizontal bar plotting
risk_df = pd.DataFrame(
    list(risk_indicators.items()), columns=["Indicator", "Prevalence (%)"]
).sort_values("Prevalence (%)", ascending=True)

# 8. Generate Horizontal Bar Chart
fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
bars = ax.barh(
    risk_df["Indicator"],
    risk_df["Prevalence (%)"],
    color="#d62728",
    edgecolor="black",
    height=0.6,
)

ax.set_title(
    "Comprehensive Risk Indicator Breakdown for Strategy & Deployment",
    fontsize=12,
    fontweight="bold",
    pad=15,
    loc="center",
)
ax.set_xlabel(
    "Percentage (%) Across Accounts",
    fontsize=11,
    fontweight="bold",
)
ax.set_xlim(0, 118)

# Add percentage data labels dynamically
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

# 9. Save Chart Image
output_path = output_dir / "summary_risk_indicator_breakdown.png"
plt.savefig(output_path, bbox_inches="tight")
plt.close()

print(f"Chart generated successfully at:\n'{output_path}'")