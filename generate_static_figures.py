"""
Generate clean, presentation-ready static figures for the PPT/report.

Uses the same pre-fixed egg yolk definition and cleaned aggregate data.
Output: high-resolution PNGs in figures/ folder.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# ============== CONFIG ==============
EGG_PROTEIN_CSV = "egg_protein_yearly.csv"
OUTPUT_DIR = Path("figures")
OUTPUT_DIR.mkdir(exist_ok=True)

# Colors (consistent with interactive dashboard)
COLOR_EGG = "#C1121F"
COLOR_PROTEIN = "#1D3557"
COLOR_2022 = "#E76F51"
COLOR_ACCENT = "#2A9D8F"

# Font settings for Traditional Chinese on Windows
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Microsoft YaHei', 'PingFang TC', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300
# ====================================


def load_data():
    df = pd.read_csv(EGG_PROTEIN_CSV, encoding="utf-8-sig")
    # Rename to safe English columns to avoid any encoding issues
    df = df.rename(columns={
        "年份": "year",
        "蛋黃區": "is_egg",
        "單價中位數": "median_price",
        "交易筆數": "count"
    })
    egg = df[df["is_egg"] == True].sort_values("year")
    protein = df[df["is_egg"] == False].sort_values("year")
    return egg, protein, df


def add_source_note(fig, ax):
    """Add consistent source + definition note at bottom"""
    fig.text(
        0.5, 0.02,
        "資料來源：內政部實價登錄（台北市＋新北市 cleaned_final，2015-2025）\n"
        "蛋黃區定義：2015-2017基期單價中位數前25%（9區），預先固定，永不事後調整",
        ha="center", va="bottom",
        fontsize=8, color="#555555",
        linespacing=1.4
    )


def create_figure1_timeseries(egg, protein):
    """Main time series figure — most important for PPT"""
    fig, ax = plt.subplots(figsize=(11, 6))

    # Main lines
    ax.plot(egg["year"], egg["median_price"],
            color=COLOR_EGG, linewidth=3.5, marker="o", markersize=7,
            label="蛋黃區總體（預先固定9區）")
    ax.plot(protein["year"], protein["median_price"],
            color=COLOR_PROTEIN, linewidth=3.5, marker="s", markersize=7,
            label="蛋白區總體")

    # 2022 vertical line + annotation
    ax.axvline(x=2022, color=COLOR_2022, linestyle="--", linewidth=2, alpha=0.9)
    ax.text(2022.2, ax.get_ylim()[1] * 0.92, "2022 升息循環啟動",
            fontsize=10, color=COLOR_2022, fontweight="bold", rotation=0)

    # Styling
    ax.set_title("2015–2025 蛋黃區 vs 蛋白區 單價中位數變化", fontsize=16, fontweight="bold", pad=12)
    ax.set_xlabel("年份", fontsize=11)
    ax.set_ylabel("單價中位數（元/坪）", fontsize=11)
    ax.grid(True, alpha=0.3, linestyle="-")
    ax.legend(loc="upper left", frameon=True, fontsize=10)

    # Force reasonable y range (avoid truncation trap)
    y_min = min(protein["median_price"].min(), egg["median_price"].min()) * 0.92
    y_max = max(protein["median_price"].max(), egg["median_price"].max()) * 1.08
    ax.set_ylim(y_min, y_max)

    # Add small annotation box
    textstr = "蛋黃區（9區）：\n大安、中正、松山、中山、信義、\n南港、大同、士林、內湖"
    props = dict(boxstyle="round,pad=0.4", facecolor="#fff0f0", edgecolor=COLOR_EGG, alpha=0.95)
    ax.text(0.02, 0.97, textstr, transform=ax.transAxes, fontsize=8.5,
            verticalalignment="top", bbox=props, linespacing=1.35)

    add_source_note(fig, ax)
    plt.tight_layout(rect=[0, 0.08, 1, 0.98])

    filepath = OUTPUT_DIR / "fig1_timeseries.png"
    plt.savefig(filepath, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved: {filepath}")


def create_figure2_gap(egg, protein):
    """Price gap over time — supports the core story"""
    fig, ax = plt.subplots(figsize=(10, 5))

    gap = egg["median_price"].values - protein["median_price"].values
    years = egg["year"].values

    ax.plot(years, gap, color=COLOR_ACCENT, linewidth=3, marker="o", markersize=6)
    ax.fill_between(years, gap, alpha=0.15, color=COLOR_ACCENT)

    ax.axvline(x=2022, color=COLOR_2022, linestyle="--", linewidth=2)
    ax.text(2022.3, gap.max() * 0.88, "2022升息後差距擴大趨勢", fontsize=10, color=COLOR_2022)

    ax.axhline(y=0, color="gray", linewidth=1, linestyle="-")

    ax.set_title("蛋黃區相對蛋白區的單價差距變化（元/坪）", fontsize=15, fontweight="bold", pad=10)
    ax.set_xlabel("年份", fontsize=11)
    ax.set_ylabel("單價差距（元/坪）", fontsize=11)
    ax.grid(True, alpha=0.3)

    add_source_note(fig, ax)
    plt.tight_layout(rect=[0, 0.08, 1, 0.98])

    filepath = OUTPUT_DIR / "fig2_gap.png"
    plt.savefig(filepath, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved: {filepath}")


def create_figure3_before_after(egg, protein):
    """Simple before/after comparison for policy impact (good for PPT)"""
    fig, ax = plt.subplots(figsize=(8, 5.5))

    # Define periods (using year values directly)
    pre_years = (egg["year"] >= 2019) & (egg["year"] <= 2021)
    post_years = (egg["year"] >= 2023) & (egg["year"] <= 2025)

    egg_pre = egg.loc[pre_years, "median_price"].mean()
    egg_post = egg.loc[post_years, "median_price"].mean()

    # For protein, create masks based on year values (not reuse egg's boolean series)
    protein_pre_mask = (protein["year"] >= 2019) & (protein["year"] <= 2021)
    protein_post_mask = (protein["year"] >= 2023) & (protein["year"] <= 2025)
    protein_pre = protein.loc[protein_pre_mask, "median_price"].mean()
    protein_post = protein.loc[protein_post_mask, "median_price"].mean()

    # Better grouping for before/after comparison:
    # Group by time period (政策前 | 政策後) instead of by district type
    # This makes the temporal contrast much clearer
    x_positions = [0, 1, 3, 4]   # pre group at 0-1, post group at 3-4 (with gap in between)
    labels = ["蛋黃區\n(2019-2021)", "蛋白區\n(2019-2021)",
              "蛋黃區\n(2023-2025)", "蛋白區\n(2023-2025)"]
    values = [egg_pre, protein_pre, egg_post, protein_post]
    colors = [COLOR_EGG, COLOR_PROTEIN, COLOR_EGG, COLOR_PROTEIN]

    bars = ax.bar(x_positions, values, color=colors, edgecolor="black", linewidth=0.6, width=0.7)

    # Add value labels on bars
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.annotate(f"{val:,.0f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha="center", va="bottom", fontsize=10, fontweight="bold")

    # Add gap annotation - highlight the post-period gap on the right side
    # This clearly shows the enlarged gap after the policy (the "extra protruding part")
    gap_pre = egg_pre - protein_pre
    gap_post = egg_post - protein_post

    # Give space on the right for the gap indicator + group labels
    ax.set_xlim(-0.5, 5.2)

    # Add group labels for time periods (placed above the plot area)
    top_y = max(values) * 1.18
    ax.text(0.5, top_y, "政策前", ha='center', fontsize=11, fontweight='bold', color='#555')
    ax.text(3.5, top_y, "政策後", ha='center', fontsize=11, fontweight='bold', color='#555')

    # Vertical double arrow for the post gap (now at x=3 and x=4)
    right_x = 4.65
    ax.annotate('', xy=(right_x, protein_post), xytext=(right_x, egg_post),
                arrowprops=dict(arrowstyle='<->', color=COLOR_EGG, lw=2.2))
    ax.text(right_x + 0.12, (egg_post + protein_post) / 2,
            f'政策後差距\n+{gap_post - gap_pre:,.0f}',
            fontsize=9, color=COLOR_EGG, fontweight="bold", va='center')

    ax.set_title("政策前後（2019-2021 vs 2023-2025）單價中位數比較", fontsize=14, fontweight="bold", pad=10)
    ax.set_ylabel("平均單價中位數（元/坪）", fontsize=11)

    # Increase upper y-limit to make room for the "政策前 / 政策後" labels above the bars
    ax.set_ylim(0, max(values) * 1.28)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Legend - moved outside to the right to avoid overlapping top labels and right-side text
    egg_patch = mpatches.Patch(color=COLOR_EGG, label="蛋黃區")
    protein_patch = mpatches.Patch(color=COLOR_PROTEIN, label="蛋白區")
    ax.legend(handles=[egg_patch, protein_patch], 
              loc='upper left', 
              bbox_to_anchor=(1.02, 1.0))

    add_source_note(fig, ax)
    # Give more headroom at the top for the "政策前 / 政策後" labels
    plt.tight_layout(rect=[0, 0.08, 0.82, 0.93])

    filepath = OUTPUT_DIR / "fig3_before_after.png"
    plt.savefig(filepath, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved: {filepath}")


def main():
    print("Loading data...")
    egg, protein, _ = load_data()

    print("Generating static figures (300 dpi)...")
    create_figure1_timeseries(egg, protein)
    create_figure2_gap(egg, protein)
    create_figure3_before_after(egg, protein)

    print("\n全部靜態圖已產生完成！檔案位於 figures/ 資料夾")
    print("建議直接放入簡報：fig1_timeseries.png（最重要） + fig3_before_after.png")


if __name__ == "__main__":
    main()
