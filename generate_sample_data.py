"""
generate_sample_data.py
Creates realistic sample dataset for all 175 Andhra Pradesh Assembly Constituencies
with Caste Names, Caste Categories, and Voter Counts.
"""

import json
import random
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
GEOJSON_PATH = DATA_DIR / "ap_constituencies.geojson"
EXCEL_OUTPUT = DATA_DIR / "caste_voters_ap.xlsx"
CSV_OUTPUT = DATA_DIR / "caste_voters_ap.csv"

# Representative communities in Andhra Pradesh grouped by category
CASTE_CATALOG = {
    "OC": [
        "Reddy", "Kamma", "Kapu", "Arya Vysya", "Brahmin",
        "Kshatriya", "Velama", "Other OC"
    ],
    "BC-A": [
        "Nayee Brahmin (Mangali)", "Rajaka (Chakali)", "Vaddera",
        "Kummari (Potters)", "Besta / Gangaputra", "Medari"
    ],
    "BC-B": [
        "Kuruba / Kuruma", "Padmashali (Weavers)", "Gowda / Settibalija",
        "Dudekula", "Viswabrahmin"
    ],
    "BC-C": [
        "SC Converts to Christianity"
    ],
    "BC-D": [
        "Yadava / Gollalu", "Turpu Kapu", "Koppula Velama",
        "Mudiraj / Mutrasi", "Bhatraju"
    ],
    "BC-E": [
        "Muslim (Shaik / Syed / Pathan)", "Muslim (Others)"
    ],
    "SC": [
        "Madiga", "Mala", "Relli", "Adi Andhra"
    ],
    "ST": [
        "Sugali / Lambada", "Yanadi", "Yerukula", "Chenchu", "Konda Dora"
    ],
}

def load_constituencies_from_geojson(geojson_path):
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    seen = {}
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        ac_no = props.get("ac_no")
        if ac_no is None:
            continue
        ac_no = int(ac_no)
        if ac_no not in seen:
            display_name = props.get("display_name") or props.get("ac_name", f"AC_{ac_no}").strip()
            seen[ac_no] = {
                "ac_no": ac_no,
                "ac_name": display_name,
                "original_name": props.get("ac_name", "").strip(),
                "district_name": props.get("district_name", "Unknown").strip(),
                "reservation": props.get("reservation", "None").strip(),
                "loksabha_name": props.get("loksabha_constituency_name", "").strip()
            }
    # Return sorted by ac_no
    return [seen[k] for k in sorted(seen.keys())]

def generate_caste_data():
    random.seed(42)  # For reproducible realistic data
    constituencies = load_constituencies_from_geojson(GEOJSON_PATH)
    print(f"Loaded {len(constituencies)} constituencies from GeoJSON.")

    rows = []

    for ac in constituencies:
        ac_no = ac["ac_no"]
        ac_name = ac["ac_name"]
        district = ac["district_name"]
        reservation = ac["reservation"]

        # Approximate total registered voters in an AC between 190,000 and 260,000
        total_voters = random.randint(190000, 260000)

        # Regional weighting to make data look authentic
        is_rayalaseema = district in ["Ananthapuramu", "Kurnool", "YSR Kadapa", "Annamayya", "Chittoor", "Tirupati", "Nandyal", "Sri Sathya Sai"]
        is_godavari = district in ["East Godavari", "West Godavari", "Kakinada", "Konaseema", "Eluru"]
        is_krishna_guntur = district in ["Krishna", "NTR", "Guntur", "Palnadu", "Bapatla"]
        is_north_coastal = district in ["Srikakulam", "Vizianagaram", "Visakhapatnam", "Parvathipuram Manyam", "Anakapalli", "Alluri Sitharama Raju"]

        weights = {}
        for cat, castes in CASTE_CATALOG.items():
            for caste in castes:
                base = random.uniform(1.0, 5.0)

                # Regional modifiers
                if is_rayalaseema:
                    if caste in ["Reddy", "Kuruba / Kuruma", "Muslim (Shaik / Syed / Pathan)", "Valmiki / Boya"]:
                        base *= random.uniform(3.5, 6.0)
                elif is_godavari:
                    if caste in ["Kapu", "Gowda / Settibalija", "Kshatriya"]:
                        base *= random.uniform(3.5, 6.0)
                elif is_krishna_guntur:
                    if caste in ["Kamma", "Kapu", "Reddy", "Arya Vysya"]:
                        base *= random.uniform(3.0, 5.5)
                elif is_north_coastal:
                    if caste in ["Turpu Kapu", "Yadava / Gollalu", "Koppula Velama", "Konda Dora"]:
                        base *= random.uniform(3.5, 6.0)

                # Reservation adjustments
                if reservation == "SC" and cat == "SC":
                    base *= 3.0
                elif reservation == "ST" and cat == "ST":
                    base *= 5.0

                weights[(cat, caste)] = base

        # Normalize weights so sum equals total_voters
        sum_weights = sum(weights.values())
        allocated_voters = 0
        cat_castes = list(weights.keys())

        for (cat, caste) in cat_castes:
            w = weights[(cat, caste)]
            voter_cnt = int((w / sum_weights) * total_voters)
            voter_cnt = max(voter_cnt, random.randint(250, 900))  # At least some presence
            allocated_voters += voter_cnt

            rows.append({
                "AC_No": ac_no,
                "Constituency_Name": ac_name,
                "District": district,
                "Reservation": reservation,
                "Caste_Category": cat,
                "Caste_Name": caste,
                "Voter_Count": voter_cnt
            })

    df = pd.DataFrame(rows)
    print(f"Generated {len(df)} rows across {len(constituencies)} constituencies.")

    # Save to CSV and Excel
    df.to_csv(CSV_OUTPUT, index=False)
    print(f"Saved CSV to: {CSV_OUTPUT}")

    try:
        df.to_excel(EXCEL_OUTPUT, index=False, engine="openpyxl")
        print(f"Saved Excel to: {EXCEL_OUTPUT}")
    except Exception as e:
        print(f"Error saving Excel (check openpyxl): {e}")

if __name__ == "__main__":
    generate_caste_data()
