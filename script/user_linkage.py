import os
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# 1. Define paths using Path objects
project_dir = Path("/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026")

base_dir = project_dir / "data"
output_dir = project_dir / "Output" / "user_linkage_info"
os.makedirs(output_dir, exist_ok=True)

file_linkage = base_dir / "result_20260903_110042 (linkage info).xlsx"
file_user = base_dir / "result_20260903_142231 (user extra info).xlsx"

# 2. Load data - PRESERVE ALL ID COLUMNS AS STRINGS
df_linkage = pd.read_excel(
    file_linkage, dtype={"target_user_id": str, "linked_entity_id": str}
)
df_user = pd.read_excel(file_user, dtype={"user_id": str})

# Ensure string formatting without trailing floating decimals
df_user["user_id"] = (
    df_user["user_id"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
)
if "target_user_id" in df_linkage.columns:
    df_linkage["target_user_id"] = (
        df_linkage["target_user_id"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )

all_users_df = pd.DataFrame({"user_id": df_user["user_id"]})

# 3. Extract metrics per user
u2u_d2 = (
    df_linkage[
        (df_linkage["linked_entity_type"] == "User")
        & (df_linkage["linkage_depth"] == 2)
    ]
    .groupby("target_user_id")
    .size()
)
u2u_d4 = (
    df_linkage[
        (df_linkage["linked_entity_type"] == "User")
        & (df_linkage["linkage_depth"] == 4)
    ]
    .groupby("target_user_id")
    .size()
)

u2d_d2 = (
    df_linkage[
        (df_linkage["linked_entity_type"] == "Driver")
        & (df_linkage["linkage_depth"] == 2)
    ]
    .groupby("target_user_id")
    .size()
)
u2d_d4 = (
    df_linkage[
        (df_linkage["linked_entity_type"] == "Driver")
        & (df_linkage["linkage_depth"] == 4)
    ]
    .groupby("target_user_id")
    .size()
)

summary = all_users_df.copy()
summary["u2u_direct"] = summary["user_id"].map(u2u_d2).fillna(0).astype(int)
summary["u2u_indirect"] = summary["user_id"].map(u2u_d4).fillna(0).astype(int)
summary["u2u_total"] = summary["u2u_direct"] + summary["u2u_indirect"]

summary["u2d_direct"] = summary["user_id"].map(u2d_d2).fillna(0).astype(int)
summary["u2d_indirect"] = summary["user_id"].map(u2d_d4).fillna(0).astype(int)
summary["u2d_total"] = summary["u2d_direct"] + summary["u2d_indirect"]

summary["total_linkages"] = summary["u2u_total"] + summary["u2d_total"]
summary["user_id_str"] = summary["user_id"].astype(str)

summary = summary.sort_values(
    by=["total_linkages", "u2u_total", "u2d_total"],
    ascending=[False, False, False],
).reset_index(drop=True)

# 4. Chart 1: Beautified Main Bar Chart
fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
colors = ["#1f77b4" if x > 0 else "#e0e0e0" for x in summary["total_linkages"]]
bars = ax.barh(
    summary["user_id_str"],
    summary["total_linkages"],
    color=colors,
    edgecolor="#333333",
    linewidth=0.8,
    height=0.65,
)
ax.set_title(
    "Overall Linked Entities Count per User ID",
    fontsize=14,
    fontweight="bold",
    pad=15,
    loc="center",
)
ax.set_xlabel("Total Linked Entities (Drivers + Users)", fontsize=11, labelpad=10)
ax.set_ylabel("User ID", fontsize=11, labelpad=10)
ax.invert_yaxis()
ax.grid(axis="x", linestyle="--", alpha=0.5)

for bar, val in zip(bars, summary["total_linkages"]):
    if val > 0:
        ax.text(
            val + 0.25,
            bar.get_y() + bar.get_height() / 2,
            f"{val} links",
            ha="left",
            va="center",
            fontweight="bold",
            color="#1f77b4",
            fontsize=10,
        )
    else:
        ax.text(
            0.2,
            bar.get_y() + bar.get_height() / 2,
            "0 (No Linkage)",
            ha="left",
            va="center",
            color="#777777",
            fontsize=9,
            fontstyle="italic",
        )

ax.set_xlim(0, max(summary["total_linkages"].max() * 1.25, 16))
plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "beautified_main_linkage.png"), bbox_inches="tight"
)
plt.close()

# 5. Chart 2: User to User Linkages
fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
ax.barh(
    summary["user_id_str"],
    summary["u2u_direct"],
    label="Direct Linkage (Depth 2)",
    color="#2ca02c",
    edgecolor="#333333",
    linewidth=0.8,
    height=0.65,
)
ax.barh(
    summary["user_id_str"],
    summary["u2u_indirect"],
    left=summary["u2u_direct"],
    label="Indirect Linkage (Depth 4)",
    color="#a6d854",
    edgecolor="#333333",
    linewidth=0.8,
    height=0.65,
)
ax.set_title(
    "User-to-User Linkages (Direct Depth 2 vs Indirect Depth 4)",
    fontsize=14,
    fontweight="bold",
    pad=15,
    loc="center",
)
ax.set_xlabel("Number of Linked User Entities", fontsize=11, labelpad=10)
ax.set_ylabel("User ID", fontsize=11, labelpad=10)
ax.invert_yaxis()
ax.grid(axis="x", linestyle="--", alpha=0.5)
ax.legend(loc="lower right", frameon=True, facecolor="white", framealpha=0.9)

for i, row in summary.iterrows():
    tot = row["u2u_total"]
    if tot > 0:
        ax.text(
            tot + 0.25,
            i,
            f'Total: {tot} (Dir: {row["u2u_direct"]}, Ind: {row["u2u_indirect"]})',
            ha="left",
            va="center",
            fontweight="bold",
            color="#1b7837",
            fontsize=9.5,
        )
    else:
        ax.text(0.2, i, "0", ha="left", va="center", color="#888888", fontsize=9)

ax.set_xlim(0, max(summary["u2u_total"].max() * 1.25, 18))
plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "u2u_linkage_chart.png"), bbox_inches="tight"
)
plt.close()

# 6. Chart 3: User to Driver Linkages (Dynamic Labels)
fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
ax.barh(
    summary["user_id_str"],
    summary["u2d_direct"],
    label="Direct Linkage (Depth 2)",
    color="#d95f02",
    edgecolor="#333333",
    linewidth=0.8,
    height=0.65,
)
ax.barh(
    summary["user_id_str"],
    summary["u2d_indirect"],
    left=summary["u2d_direct"],
    label="Indirect Linkage (Depth 4)",
    color="#fc8d62",
    edgecolor="#333333",
    linewidth=0.8,
    height=0.65,
)
ax.set_title(
    "User-to-Driver Linkages (Direct Depth 2 vs Indirect Depth 4)",
    fontsize=14,
    fontweight="bold",
    pad=15,
    loc="center",
)
ax.set_xlabel("Number of Linked Driver Entities", fontsize=11, labelpad=10)
ax.set_ylabel("User ID", fontsize=11, labelpad=10)
ax.invert_yaxis()
ax.grid(axis="x", linestyle="--", alpha=0.5)
ax.legend(loc="lower right", frameon=True, facecolor="white", framealpha=0.9)

for i, row in summary.iterrows():
    tot = row["u2d_total"]
    if tot > 0:
        ax.text(
            tot + 0.25,
            i,
            f'Total: {tot} Drivers ({row["u2d_direct"]} Direct, {row["u2d_indirect"]} Indirect)',
            ha="left",
            va="center",
            fontweight="bold",
            color="#b30000",
            fontsize=9.5,
        )
    else:
        ax.text(
            0.2,
            i,
            "0 Drivers",
            ha="left",
            va="center",
            color="#888888",
            fontsize=9,
        )

ax.set_xlim(0, max(summary["u2d_total"].max() * 1.35, 12))
plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "u2d_linkage_chart.png"), bbox_inches="tight"
)
plt.close()

# 7. Chart 4: Combined Total Linkage
fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
ax.barh(
    summary["user_id_str"],
    summary["u2u_total"],
    label="User-to-User Links",
    color="#3182bd",
    edgecolor="#333333",
    linewidth=0.8,
    height=0.65,
)
ax.barh(
    summary["user_id_str"],
    summary["u2d_total"],
    left=summary["u2u_total"],
    label="User-to-Driver Links",
    color="#e6550d",
    edgecolor="#333333",
    linewidth=0.8,
    height=0.65,
)
ax.set_title(
    "Combined Total Linkage Breakdown (User vs Driver Connections)",
    fontsize=14,
    fontweight="bold",
    pad=15,
    loc="center",
)
ax.set_xlabel("Total Linked Entities", fontsize=11, labelpad=10)
ax.set_ylabel("User ID", fontsize=11, labelpad=10)
ax.invert_yaxis()
ax.grid(axis="x", linestyle="--", alpha=0.5)
ax.legend(loc="lower right", frameon=True, facecolor="white", framealpha=0.9)

for i, row in summary.iterrows():
    tot = row["total_linkages"]
    if tot > 0:
        ax.text(
            tot + 0.25,
            i,
            f'{tot} Total ({row["u2u_total"]} Users + {row["u2d_total"]} Drivers)',
            ha="left",
            va="center",
            fontweight="bold",
            color="#2b5c8f",
            fontsize=9.5,
        )
    else:
        ax.text(0.2, i, "0", ha="left", va="center", color="#888888", fontsize=9)

ax.set_xlim(0, max(summary["total_linkages"].max() * 1.25, 18))
plt.tight_layout()
plt.savefig(
    os.path.join(output_dir, "combined_total_linkage_chart.png"),
    bbox_inches="tight",
)
plt.close()

# 8. Save Excel summary into user_linkage_info directory (Preserving IDs)
excel_out = os.path.join(output_dir, "user_linkage_detailed_breakdown.xlsx")
summary.drop(columns=["user_id_str"]).to_excel(excel_out, index=False)

print(f"All linkage files exported successfully into folder: '{output_dir}'")
