import os
import re
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# 1. Define file paths and output folder
base_dir = "/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026/data"
input_file = os.path.join(base_dir, "order_lag_splitting.xlsx")
output_dir = os.path.join(base_dir, "location_and_risk_analysis")
os.makedirs(output_dir, exist_ok=True)

# 2. Load dataset
df = pd.read_excel(input_file)


# 3. Smart clean function to strip concatenated duplicated text suffixes
def smart_clean_address(addr):
    if pd.isna(addr) or not str(addr).strip():
        return "Unknown"
    addr_str = str(addr).strip()
    matches = list(
        re.finditer(r"(,\s*(?:Việt Nam|Vietnam))", addr_str, re.IGNORECASE)
    )
    if matches:
        cleaned = addr_str[: matches[-1].end()]
    else:
        m = list(
            re.finditer(r"((?:Việt Nam|Vietnam))", addr_str, re.IGNORECASE)
        )
        if m:
            cleaned = addr_str[: m[-1].end()]
        else:
            cleaned = addr_str
    return cleaned.strip()


df["clean_start_address"] = df["start_address"].apply(smart_clean_address)
df["clean_end_address"] = df["end_address"].apply(smart_clean_address)

# 4. Extract Frequency Rankings
start_addr_counts = (
    df["clean_start_address"]
    .value_counts()
    .reset_index(name="order_count")
    .rename(columns={"index": "start_address"})
)
end_addr_counts = (
    df["clean_end_address"]
    .value_counts()
    .reset_index(name="order_count")
    .rename(columns={"index": "end_address"})
)

# 5. Province Extraction Regex Rules
PROVINCE_KEYWORDS = [
    (
        "Hồ Chí Minh",
        [
            r"Hồ Chí Minh",
            r"Thành phố Hồ Chí Minh",
            r"TP\.?HCM",
            r"Sài Gòn",
            r"HCM",
            r"Quận \d+",
            r"Bình Tân",
            r"Bình Thạnh",
            r"Gò Vấp",
            r"Phú Nhuận",
            r"Tân Bình",
            r"Tân Phú",
            r"Thủ Đức",
            r"Bình Chánh",
            r"Cần Giờ",
            r"Củ Chi",
            r"Hóc Môn",
            r"Nhà Bè",
        ],
    ),
    ("Tây Ninh", [r"Tây Ninh", r"Tay Ninh"]),
    (
        "Long An",
        [
            r"Long An",
            r"Bến Lức",
            r"Cần Đước",
            r"Cần Giuộc",
            r"Tân An",
            r"Mỹ Yên",
        ],
    ),
    (
        "Bình Dương",
        [
            r"Bình Dương",
            r"Binh Duong",
            r"Dĩ An",
            r"Thuận An",
            r"Thủ Dầu Một",
            r"Tân Uyên",
            r"Bến Cát",
        ],
    ),
    (
        "Đồng Nai",
        [r"Đồng Nai", r"Dong Nai", r"Biên Hòa", r"Long Thành", r"Nhơn Trạch"],
    ),
    ("Tiền Giang", [r"Tiền Giang", r"Tien Giang", r"Mỹ Tho"]),
    ("Bà Rịa - Vũng Tàu", [r"Bà Rịa", r"Vũng Tàu"]),
    ("Đồng Tháp", [r"Đồng Tháp"]),
    ("Vĩnh Long", [r"Vĩnh Long"]),
    ("Cần Thơ", [r"Cần Thơ"]),
]


def extract_province(addr):
    if pd.isna(addr) or not str(addr).strip():
        return "Unknown"
    addr_str = str(addr)
    for prov_name, patterns in PROVINCE_KEYWORDS:
        for pat in patterns:
            if re.search(pat, addr_str, re.IGNORECASE):
                return prov_name
    return "Other"


df["start_province"] = df["start_address"].apply(extract_province)
df["end_province"] = df["end_address"].apply(extract_province)
df["route"] = df["start_province"] + " ➔ " + df["end_province"]

# Lat/Long Geo-Clustering (~100m Precision)
df["start_lat_long_cluster"] = (
    df["start_latitude"].round(3).astype(str)
    + ", "
    + df["start_longitude"].round(3).astype(str)
)
df["end_lat_long_cluster"] = (
    df["end_latitude"].round(3).astype(str)
    + ", "
    + df["end_longitude"].round(3).astype(str)
)

# Summaries
route_summary = (
    df.groupby("route")
    .size()
    .reset_index(name="order_count")
    .sort_values("order_count", ascending=False)
)
start_hotspots = (
    df.groupby(["start_province", "start_lat_long_cluster"])
    .size()
    .reset_index(name="order_count")
    .sort_values("order_count", ascending=False)
)
risk_vehicle_summary = pd.crosstab(
    df["vehicle_type"].fillna("NULL"), df["order_status"]
)

# ------------------------------------------------------------
# 6. Plotting Charts
# ------------------------------------------------------------
sns.set_theme(style="whitegrid")


def truncate_addr(text, max_len=55):
    text_str = str(text)
    return text_str[:max_len] + "..." if len(text_str) > max_len else text_str


# Plot A: Top 10 Start Addresses Bar Chart
start_top10 = start_addr_counts.head(10).copy()
start_top10["short_address"] = start_top10["clean_start_address"].apply(
    truncate_addr
)

plt.figure(figsize=(11, 6), dpi=300)
bars1 = plt.barh(
    start_top10["short_address"],
    start_top10["order_count"],
    color="#1f77b4",
    edgecolor="black",
)
plt.gca().invert_yaxis()
plt.title(
    "Top 10 Most Frequent Start (Pickup) Addresses",
    fontsize=13,
    fontweight="bold",
    pad=15,
)
plt.xlabel("Order Count", fontsize=11)
plt.ylabel("Pickup Address", fontsize=11)

for bar in bars1:
    w = bar.get_width()
    plt.text(
        w + 0.8,
        bar.get_y() + bar.get_height() / 2,
        f"{w}",
        ha="left",
        va="center",
        fontweight="bold",
        color="#1f77b4",
    )

plt.xlim(0, max(start_top10["order_count"]) * 1.15)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "top_start_addresses.png"))
plt.close()

# Plot B: Top 10 End Addresses Bar Chart
end_top10 = end_addr_counts.head(10).copy()
end_top10["short_address"] = end_top10["clean_end_address"].apply(
    truncate_addr
)

plt.figure(figsize=(11, 6), dpi=300)
bars2 = plt.barh(
    end_top10["short_address"],
    end_top10["order_count"],
    color="#ff7f0e",
    edgecolor="black",
)
plt.gca().invert_yaxis()
plt.title(
    "Top 10 Most Frequent End (Dropoff) Addresses",
    fontsize=13,
    fontweight="bold",
    pad=15,
)
plt.xlabel("Order Count", fontsize=11)
plt.ylabel("Dropoff Address", fontsize=11)

for bar in bars2:
    w = bar.get_width()
    plt.text(
        w + 0.4,
        bar.get_y() + bar.get_height() / 2,
        f"{w}",
        ha="left",
        va="center",
        fontweight="bold",
        color="#d95f02",
    )

plt.xlim(0, max(end_top10["order_count"]) * 1.15)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "top_end_addresses.png"))
plt.close()

# Plot C: Top Inter-Province Routes
plt.figure(figsize=(10, 5), dpi=300)
top_routes = route_summary.head(8)
bars3 = plt.barh(
    top_routes["route"],
    top_routes["order_count"],
    color="#2ca02c",
    edgecolor="black",
)
plt.gca().invert_yaxis()
plt.title(
    "Top Inter-Province Order Routes (Start ➔ End)",
    fontsize=13,
    fontweight="bold",
    pad=12,
)
plt.xlabel("Order Volume", fontsize=11)
plt.ylabel("Route", fontsize=11)

for bar in bars3:
    w = bar.get_width()
    plt.text(
        w + 15,
        bar.get_y() + bar.get_height() / 2,
        f"{w:,}",
        ha="left",
        va="center",
        fontweight="bold",
    )

plt.xlim(0, max(top_routes["order_count"]) * 1.15)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "top_order_routes.png"))
plt.close()

# ------------------------------------------------------------
# 7. Export Excel File
# ------------------------------------------------------------
excel_out = os.path.join(output_dir, "location_risk_breakdown.xlsx")
with pd.ExcelWriter(excel_out, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Parsed_Data", index=False)
    start_addr_counts.to_excel(
        writer, sheet_name="Top_Start_Addresses", index=False
    )
    end_addr_counts.to_excel(
        writer, sheet_name="Top_End_Addresses", index=False
    )
    route_summary.to_excel(writer, sheet_name="Route_Summary", index=False)
    start_hotspots.to_excel(
        writer, sheet_name="Start_Geo_Hotspots", index=False
    )
    risk_vehicle_summary.to_excel(
        writer, sheet_name="Vehicle_Status_CrossTab"
    )

print(
    f"Analysis completed! All files and plots saved to '{output_dir}'."
)