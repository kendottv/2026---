"""
Prepare aggregated data for the interactive Plotly dashboard.
- Loads raw Taipei + New Taipei real price registration data
- Extracts year from 交易年月 (ROC calendar)
- Computes yearly median unit price + transaction count per district
- Labels pre-fixed Egg Yolk districts (from egg_yolk_definition.json)
- Outputs two clean CSVs for the dashboard:
  1. district_yearly_stats.csv : full district x year granularity
  2. egg_protein_yearly.csv    : the original aggregate view (2015-2025)
"""

import pandas as pd
import json
from pathlib import Path

# ============== CONFIG ==============
RAW_TAIPEI = "taipei_housing_cleaned_final.csv"
RAW_NEWTAIPEI = "new_taipei_housing_cleaned_final.csv"
EGG_DEF_JSON = "egg_yolk_definition.json"
OUT_DIR = Path(".")

# Known good Chinese district names (from egg_yolk_definition.json)
EGG_YOLK_DISTRICTS = [
    "大安區", "中正區", "松山區", "中山區", "信義區",
    "南港區", "大同區", "士林區", "內湖區"
]

# Column indices in the raw CSVs (0-based, after inspection)
COL_PRICE = 1      # 單價 (元/坪)
COL_DISTRICT = 2   # 行政區 / 鄉鎮市區
COL_YEARMONTH = 3  # 交易年月 (e.g. 1041005 = 2015-10-05)

START_YEAR = 2015
END_YEAR = 2025
# ====================================


def parse_roc_year(ym: int) -> int:
    """Convert ROC year-month integer like 1041005 to Western year 2015."""
    if pd.isna(ym):
        return None
    try:
        s = str(int(ym))
        roc_year = int(s[:3])   # 104
        western_year = roc_year + 1911
        return western_year
    except Exception:
        return None


def load_and_aggregate(path: str, is_new_taipei: bool = False) -> pd.DataFrame:
    """Load one raw file and return district-year aggregates."""
    print(f"Loading {path} ...")
    # Read without relying on header names (encoding issues)
    df = pd.read_csv(path, encoding="utf-8-sig", header=None, low_memory=False)

    # Select only the columns we need
    df = df[[COL_PRICE, COL_DISTRICT, COL_YEARMONTH]].copy()
    df.columns = ["單價", "行政區", "交易年月"]

    # Clean
    df["單價"] = pd.to_numeric(df["單價"], errors="coerce")
    df["行政區"] = df["行政區"].astype(str).str.strip()
    df["年份"] = df["交易年月"].apply(parse_roc_year)

    # Filter
    df = df[(df["年份"] >= START_YEAR) & (df["年份"] <= END_YEAR)]
    df = df[df["單價"].notna() & (df["單價"] > 0)]
    df = df[df["行政區"].notna() & (df["行政區"] != "") & (df["行政區"] != "nan")]

    print(f"  After filter {START_YEAR}-{END_YEAR}: {len(df):,} transactions")

    # Aggregate per district-year
    agg = (
        df.groupby(["行政區", "年份"])
        .agg(
            單價中位數=("單價", "median"),
            交易筆數=("單價", "count"),
        )
        .reset_index()
    )
    agg["來源"] = "新北市" if is_new_taipei else "台北市"
    return agg


def main():
    # 1. Load egg yolk definition (for reference)
    with open(EGG_DEF_JSON, encoding="utf-8") as f:
        egg_def = json.load(f)
    print("Egg yolk definition loaded:", egg_def["方法"])

    # 2. Process both cities
    tpe = load_and_aggregate(RAW_TAIPEI, is_new_taipei=False)
    nt = load_and_aggregate(RAW_NEWTAIPEI, is_new_taipei=True)

    district_yearly = pd.concat([tpe, nt], ignore_index=True)

    # 3. Add pre-fixed egg yolk label (only the 9 Taipei districts)
    district_yearly["蛋黃區"] = district_yearly["行政區"].isin(EGG_YOLK_DISTRICTS)

    # 4. Create the classic Egg-vs-Protein aggregate (for main lines)
    egg_protein = (
        district_yearly.groupby(["年份", "蛋黃區"])
        .agg(
            單價中位數=("單價中位數", "median"),   # median of medians is acceptable for overview
            交易筆數=("交易筆數", "sum"),
        )
        .reset_index()
    )
    egg_protein["類型"] = egg_protein["蛋黃區"].map({True: "蛋黃區", False: "蛋白區"})

    # 5. Save outputs
    out1 = OUT_DIR / "district_yearly_stats.csv"
    out2 = OUT_DIR / "egg_protein_yearly.csv"

    district_yearly.to_csv(out1, index=False, encoding="utf-8-sig")
    egg_protein.to_csv(out2, index=False, encoding="utf-8-sig")

    print("\n=== Outputs created ===")
    print(f"{out1} : {len(district_yearly):,} rows (行政區 × 年份)")
    print(f"  Unique districts: {district_yearly['行政區'].nunique()}")
    print(f"  Years: {sorted(district_yearly['年份'].unique())}")

    print(f"\n{out2} : {len(egg_protein):,} rows (蛋黃 vs 蛋白)")
    print(egg_protein.head(8).to_string(index=False))

    # Quick sanity: show egg yolk districts present
    egg_districts_in_data = (
        district_yearly[district_yearly["蛋黃區"]]["行政區"].unique()
    )
    print(f"\nEgg yolk districts found in data: {list(egg_districts_in_data)}")


if __name__ == "__main__":
    main()
