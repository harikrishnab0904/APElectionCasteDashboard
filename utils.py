"""
utils.py
Helper functions for loading GeoJSON map boundaries, standardizing Excel/CSV data,
and computing caste voter statistics for Andhra Pradesh assembly constituencies.
"""

import json
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
GEOJSON_PATH = DATA_DIR / "ap_constituencies.geojson"
DEFAULT_EXCEL_PATH = DATA_DIR / "caste_voters_ap.xlsx"
DEFAULT_CSV_PATH = DATA_DIR / "caste_voters_ap.csv"

# Color palette for social categories
CATEGORY_COLORS = {
    "OC": "#3B82F6",       # Blue
    "BC-A": "#10B981",     # Emerald
    "BC-B": "#059669",     # Dark green
    "BC-C": "#14B8A6",     # Teal
    "BC-D": "#F59E0B",     # Amber
    "BC-E": "#8B5CF6",     # Purple
    "SC": "#EF4444",       # Red
    "ST": "#EC4899",       # Pink
    "Minorities": "#6366F1",# Indigo
    "Others": "#9CA3AF"    # Gray
}

def load_geojson(path=GEOJSON_PATH):
    """Loads GeoJSON boundary file and returns the JSON data."""
    if not Path(path).exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_column_names(df):
    """
    Intelligently maps various column names to standard keys:
    Constituency_Name, AC_No, District, Caste_Category, Caste_Name, Voter_Count.
    """
    col_mapping = {}
    for col in df.columns:
        c_clean = str(col).strip().lower().replace(" ", "_").replace("-", "_")
        
        # Match Constituency Name
        if c_clean in ["constituency_name", "constituency", "ac_name", "assembly", "assembly_constituency"]:
            col_mapping[col] = "Constituency_Name"
        # Match AC Number
        elif c_clean in ["ac_no", "ac_num", "ac_number", "constituency_no", "s_no", "ac"]:
            col_mapping[col] = "AC_No"
        # Match District
        elif c_clean in ["district", "district_name", "dt_name", "dist"]:
            col_mapping[col] = "District"
        # Match Caste Category
        elif c_clean in ["caste_category", "category", "social_category", "group", "caste_group"]:
            col_mapping[col] = "Caste_Category"
        # Match Caste Name
        elif c_clean in ["caste_name", "caste", "community", "sub_caste", "subcaste"]:
            col_mapping[col] = "Caste_Name"
        # Match Voter Count
        elif c_clean in ["voter_count", "voters", "voter", "count", "total_voters", "votes", "population"]:
            col_mapping[col] = "Voter_Count"
        # Match Reservation
        elif c_clean in ["reservation", "res_status", "category_seat"]:
            col_mapping[col] = "Reservation"

    df = df.rename(columns=col_mapping)
    return df

def load_data(source=None):
    """
    Loads dataset from an uploaded file object or default data files.
    Returns cleaned pandas DataFrame.
    """
    df = None
    if source is not None:
        filename = getattr(source, "name", "").lower()
        if filename.endswith(".csv"):
            df = pd.read_csv(source)
        else:
            # Excel file (.xlsx / .xls)
            df = pd.read_excel(source)
    else:
        # Load default dataset
        if DEFAULT_EXCEL_PATH.exists():
            try:
                df = pd.read_excel(DEFAULT_EXCEL_PATH)
            except Exception:
                pass
        if df is None and DEFAULT_CSV_PATH.exists():
            df = pd.read_csv(DEFAULT_CSV_PATH)

    if df is None:
        return None

    # Clean & normalize columns
    df = normalize_column_names(df)

    # Ensure required columns
    required = ["Constituency_Name", "Caste_Name", "Voter_Count"]
    for req in required:
        if req not in df.columns:
            raise ValueError(f"Missing required column: '{req}'. Detected columns: {list(df.columns)}")

    # Fill defaults for optional columns if absent
    if "Caste_Category" not in df.columns:
        df["Caste_Category"] = "Others"
    if "District" not in df.columns:
        df["District"] = "N/A"
    if "Reservation" not in df.columns:
        df["Reservation"] = "General"

    # Data type cleanup
    df["Constituency_Name"] = df["Constituency_Name"].astype(str).str.strip()
    df["Caste_Name"] = df["Caste_Name"].astype(str).str.strip()
    df["Caste_Category"] = df["Caste_Category"].astype(str).str.strip()
    df["District"] = df["District"].astype(str).str.strip()
    df["Voter_Count"] = pd.to_numeric(df["Voter_Count"], errors="coerce").fillna(0).astype(int)

    return df

def get_constituency_summary(df, constituency_name):
    """
    Computes summary metrics, category totals, and top castes for a selected constituency.
    Supports smart matching even with parenthetical district names.
    """
    c_name_str = str(constituency_name).strip().lower()
    sub = df[df["Constituency_Name"].str.lower() == c_name_str].copy()

    # Fallback smart match for names like 'Prathipadu (Guntur)'
    if sub.empty and "(" in c_name_str and ")" in c_name_str:
        base_name = c_name_str.split("(")[0].strip()
        qualifier = c_name_str.split("(")[1].split(")")[0].strip()
        # Try matching base name and district
        sub = df[
            (df["Constituency_Name"].str.lower() == base_name) &
            (df["District"].str.lower().str.contains(qualifier, na=False))
        ].copy()
        if sub.empty:
            sub = df[df["Constituency_Name"].str.lower() == base_name].copy()

    if sub.empty:
        return None

    total_voters = sub["Voter_Count"].sum()
    district = sub["District"].iloc[0] if "District" in sub.columns else "N/A"
    reservation = sub["Reservation"].iloc[0] if "Reservation" in sub.columns else "None"
    ac_no = sub["AC_No"].iloc[0] if "AC_No" in sub.columns else None

    # Calculate percentage for each caste
    sub["Share_Pct"] = (sub["Voter_Count"] / total_voters * 100).round(2) if total_voters > 0 else 0
    sub_sorted = sub.sort_values(by="Voter_Count", ascending=False)

    dominant_caste = sub_sorted.iloc[0]["Caste_Name"] if not sub_sorted.empty else "N/A"
    dominant_count = sub_sorted.iloc[0]["Voter_Count"] if not sub_sorted.empty else 0
    dominant_pct = sub_sorted.iloc[0]["Share_Pct"] if not sub_sorted.empty else 0.0

    # Category breakdown
    cat_df = (
        sub.groupby("Caste_Category", as_index=False)["Voter_Count"]
        .sum()
        .sort_values(by="Voter_Count", ascending=False)
    )
    cat_df["Share_Pct"] = (cat_df["Voter_Count"] / total_voters * 100).round(2) if total_voters > 0 else 0

    dominant_category = cat_df.iloc[0]["Caste_Category"] if not cat_df.empty else "N/A"
    dominant_category_pct = cat_df.iloc[0]["Share_Pct"] if not cat_df.empty else 0.0

    return {
        "ac_name": constituency_name,
        "ac_no": ac_no,
        "district": district,
        "reservation": reservation,
        "total_voters": total_voters,
        "caste_count": len(sub),
        "dominant_caste": dominant_caste,
        "dominant_count": dominant_count,
        "dominant_pct": dominant_pct,
        "dominant_category": dominant_category,
        "dominant_category_pct": dominant_category_pct,
        "category_df": cat_df,
        "top_castes_df": sub_sorted.head(10),
        "full_df": sub_sorted
    }

def get_state_metrics(df):
    """Calculates overall metrics across all constituencies."""
    total_voters = df["Voter_Count"].sum()
    total_constituencies = df["Constituency_Name"].nunique()
    total_castes = df["Caste_Name"].nunique()
    avg_voters_per_ac = int(total_voters / total_constituencies) if total_constituencies > 0 else 0

    top_state_castes = (
        df.groupby("Caste_Name", as_index=False)["Voter_Count"]
        .sum()
        .sort_values(by="Voter_Count", ascending=False)
        .head(10)
    )
    top_state_castes["Share_Pct"] = (top_state_castes["Voter_Count"] / total_voters * 100).round(2)

    cat_state = (
        df.groupby("Caste_Category", as_index=False)["Voter_Count"]
        .sum()
        .sort_values(by="Voter_Count", ascending=False)
    )
    cat_state["Share_Pct"] = (cat_state["Voter_Count"] / total_voters * 100).round(2)

    return {
        "total_voters": total_voters,
        "total_constituencies": total_constituencies,
        "total_castes": total_castes,
        "avg_voters_per_ac": avg_voters_per_ac,
        "top_state_castes": top_state_castes,
        "category_breakdown": cat_state
    }
