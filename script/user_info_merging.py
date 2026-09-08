from pathlib import Path
import pandas as pd

# Define paths
project_dir = Path("/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026")
base_dir = project_dir / "data"
output_dir = project_dir / "Output" / "user_info_merging"

# Create output subdirectories automatically if they don't exist
output_dir.mkdir(parents=True, exist_ok=True)

# Define file locations inside data/
file1 = base_dir / "result_20260903_142231 (user extra info).xlsx"
file2 = base_dir / "result_20260904_101858 (user extra extra info).xlsx"

# 1. Read 'Results export' sheet from both files
df1 = pd.read_excel(file1, sheet_name="Results export")
df2 = pd.read_excel(file2, sheet_name="Results export")

# 2. Merge on user_id
merged_df = pd.merge(df1, df2, on="user_id", how="outer", suffixes=("", "_dup"))

# 3. Clean up duplicate columns
for col in merged_df.columns:
    if col.endswith("_dup"):
        base_col = col[:-4]
        merged_df[base_col] = merged_df[base_col].combine_first(merged_df[col])
        merged_df.drop(columns=[col], inplace=True)

# 4. Define target 37 columns
target_columns = [
    "user_id",
    "register_time",
    "is_corp",
    "industry_id",
    "license_no",
    "device_identifier",
    "device_type",
    "version",
    "revision",
    "receive_coupon_cnt",
    "use_coupon_cnt",
    "usable_coupon_cnt",
    "max_order_city_id",
    "first_login_device_type",
    "last_login_device_type",
    "first_login_city",
    "first_login_market",
    "intercity_recency",
    "last_login_city",
    "last_login_market",
    "ban_status",
    "phone_no",
    "email",
    "last_name",
    "first_name",
    "city_id",
    "city_name",
    "city_name_cn",
    "first_login_country",
    "first_login_country_name",
    "total_create_cnt",
    "total_complete_cnt",
    "days_since_register",
    "first_create_time_local",
    "first_completed_order_time_local",
    "last_create_time_local",
    "last_complete_time_local",
]

final_df = merged_df[target_columns]

# 5. Export to target directory
output_file = output_dir / "merged_user_info.xlsx"
final_df.to_excel(output_file, sheet_name="Results export", index=False)

print(f"Successfully saved merged file to: {output_file}")