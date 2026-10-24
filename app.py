"""
app.py - Andhra Pradesh Assembly Constituencies Caste Demographics Dashboard
Built with Streamlit, Folium, and Plotly.
"""

import json
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

import utils

# ==========================================
# 1. PAGE SETUP & STYLING
# ==========================================
st.set_page_config(
    page_title="AP Assembly Constituencies - Caste Demographics",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished aesthetic and responsive card styling
st.markdown("""
<style>
    /* Metric Card Styling */
    .metric-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #e5e7eb;
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 2px;
    }
    .metric-sub {
        font-size: 0.82rem;
        color: #10b981;
        font-weight: 500;
    }
    .badge-res {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .badge-none { background-color: #E0E7FF; color: #3730A3; }
    .badge-sc { background-color: #FEE2E2; color: #991B1B; }
    .badge-st { background-color: #FCE7F3; color: #9D174D; }

    /* Map container styling */
    .map-container {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. DATA CACHING & INITIALIZATION
# ==========================================
@st.cache_data
def get_geojson_data():
    """Loads and caches the Andhra Pradesh constituencies GeoJSON map."""
    return utils.load_geojson()

@st.cache_data
def get_dataset(uploaded_file_bytes=None, file_name=None):
    """Loads and caches demographic data from default files or uploaded file."""
    if uploaded_file_bytes is not None and file_name:
        import io
        buf = io.BytesIO(uploaded_file_bytes)
        buf.name = file_name
        return utils.load_data(buf)
    return utils.load_data()


# ==========================================
# 3. SIDEBAR CONTROLS & DATA UPLOAD
# ==========================================
st.sidebar.title("🏛️ AP Demographics")
st.sidebar.caption("Andhra Pradesh Assembly Constituency Analytics")
st.sidebar.markdown("---")

# File Uploader Section
st.sidebar.subheader("📁 Data Source")
uploaded_file = st.sidebar.file_uploader(
    "Upload Excel (.xlsx) or CSV",
    type=["xlsx", "xls", "csv"],
    help="Upload your own caste data spreadsheet. Columns needed: Constituency_Name, Caste_Name, Voter_Count (Optional: Caste_Category, District, AC_No)"
)

# Load the dataset
try:
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        df = get_dataset(file_bytes, uploaded_file.name)
        st.sidebar.success(f"Loaded: {uploaded_file.name}")
    else:
        df = get_dataset()
        if df is not None:
            st.sidebar.info("Using default Andhra Pradesh demographic dataset (175 ACs)")
        else:
            st.sidebar.warning("Default dataset not found. Please upload an Excel/CSV file.")
except Exception as e:
    st.sidebar.error(f"Error loading file: {e}")
    df = None

# Load the GeoJSON boundaries
geojson_data = get_geojson_data()

if df is None:
    st.error("Please provide a valid dataset to view the dashboard.")
    st.stop()

# Build a lookup list of all unique constituencies
all_constituencies = sorted(df["Constituency_Name"].dropna().unique().tolist())
districts = sorted(df["District"].dropna().unique().tolist()) if "District" in df.columns else []

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Filter & Select")

# District Filter dropdown
selected_district = st.sidebar.selectbox(
    "Filter by District:",
    options=["All Districts"] + districts,
    index=0
)

# Filter constituencies list based on district
if selected_district != "All Districts":
    filtered_acs = sorted(df[df["District"] == selected_district]["Constituency_Name"].dropna().unique().tolist())
else:
    filtered_acs = all_constituencies

# Initialize session state for selected constituency
if "selected_ac" not in st.session_state:
    # Default to Kuppam or first in list
    st.session_state["selected_ac"] = "Kuppam" if "Kuppam" in all_constituencies else all_constituencies[0]

# Ensure current selection is valid
if st.session_state["selected_ac"] not in filtered_acs:
    st.session_state["selected_ac"] = filtered_acs[0] if filtered_acs else all_constituencies[0]

# Callback when user changes constituency from dropdown
def on_dropdown_change():
    st.session_state["selected_ac"] = st.session_state["ac_selector_key"]

selected_ac_dropdown = st.sidebar.selectbox(
    "Select Constituency:",
    options=filtered_acs,
    index=filtered_acs.index(st.session_state["selected_ac"]),
    key="ac_selector_key",
    on_change=on_dropdown_change
)

# Quick reset button
if st.sidebar.button("🔄 Reset Map View"):
    st.session_state["map_center"] = [15.9129, 79.7400]
    st.session_state["map_zoom"] = 7
    st.rerun()


# ==========================================
# 4. MAIN DASHBOARD TABS
# ==========================================
tab_map, tab_state, tab_guide = st.tabs([
    "🗺️ Interactive Map & Profile",
    "📊 State-Wide Analytics",
    "🚀 Deployment & Beginner Guide"
])

# ----------------------------------------------------
# TAB 1: INTERACTIVE MAP & CONSTITUENCY PROFILE
# ----------------------------------------------------
with tab_map:
    current_ac = st.session_state["selected_ac"]
    summary = utils.get_constituency_summary(df, current_ac)

    # Top title bar with constituency badges
    res_badge_class = "badge-none"
    if summary and summary.get("reservation") == "SC":
        res_badge_class = "badge-sc"
    elif summary and summary.get("reservation") == "ST":
        res_badge_class = "badge-st"

    ac_no_str = f"AC #{summary['ac_no']} • " if summary and summary.get("ac_no") else ""
    dist_str = f"District: {summary['district']}" if summary else ""
    res_str = f"Reservation: {summary['reservation']}" if summary and summary.get("reservation") != "None" else "General Category"

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 2px solid #f3f4f6; padding-bottom: 8px;">
        <div>
            <h1 style="margin: 0; font-size: 1.9rem; color: #1e3a8a;">{current_ac} Constituency</h1>
            <p style="margin: 2px 0 0 0; color: #4b5563; font-size: 0.95rem;">{ac_no_str}{dist_str}</p>
        </div>
        <div>
            <span class="badge-res {res_badge_class}">{res_str}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4 Quick KPI Summary Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        v_count = f"{summary['total_voters']:,}" if summary else "0"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">👥 Total Caste Voters</div>
            <div class="metric-value">{v_count}</div>
            <div class="metric-sub">Across registered communities</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        dom_caste = summary["dominant_caste"] if summary else "N/A"
        dom_pct = f"{summary['dominant_pct']}%" if summary else "0%"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🏆 Largest Community</div>
            <div class="metric-value">{dom_caste}</div>
            <div class="metric-sub">{dom_pct} of total constituency</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        dom_cat = summary["dominant_category"] if summary else "N/A"
        cat_pct = f"{summary['dominant_category_pct']}%" if summary else "0%"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🏷️ Dominant Category</div>
            <div class="metric-value">{dom_cat}</div>
            <div class="metric-sub">{cat_pct} category share</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        c_count = summary["caste_count"] if summary else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📊 Caste Groups</div>
            <div class="metric-value">{c_count}</div>
            <div class="metric-sub">Distinct communities recorded</div>
        </div>
        """, unsafe_allow_html=True)

    # Split View: Left Map, Right Charts
    map_col, chart_col = st.columns([1.1, 0.9], gap="medium")

    with map_col:
        st.subheader("🗺️ Andhra Pradesh Assembly Map")
        st.caption("Click any constituency polygon on the map to inspect its data.")

        # Build Folium Map
        # AP approximate centroid: 15.9129° N, 79.7400° E
        m = folium.Map(
            location=[15.9129, 79.7400],
            zoom_start=7,
            tiles="CartoDB positron",
            control_scale=True
        )

        if geojson_data:
            # Quick lookup for total voters per constituency to show on hover
            totals_dict = df.groupby(df["Constituency_Name"].str.lower())["Voter_Count"].sum().to_dict()

            def style_function(feature):
                props = feature.get("properties", {})
                f_name = str(props.get("display_name") or props.get("ac_name", "")).strip().lower()
                is_selected = (f_name == current_ac.lower())

                if is_selected:
                    return {
                        "fillColor": "#F59E0B",   # Vibrant Amber for selected
                        "color": "#B45309",       # Dark amber border
                        "weight": 3.5,
                        "fillOpacity": 0.85
                    }
                else:
                    return {
                        "fillColor": "#60A5FA",   # Soft blue
                        "color": "#1E40AF",       # Slate blue border
                        "weight": 0.8,
                        "fillOpacity": 0.4
                    }

            def highlight_function(feature):
                return {
                    "fillColor": "#34D399",       # Greenish on hover
                    "color": "#065F46",
                    "weight": 2.5,
                    "fillOpacity": 0.7
                }

            # Prepare GeoJSON layer with tooltip
            geojson_layer = folium.GeoJson(
                geojson_data,
                name="Andhra Pradesh Assembly Constituencies",
                style_function=style_function,
                highlight_function=highlight_function,
                tooltip=folium.GeoJsonTooltip(
                    fields=["ac_no", "display_name", "district_name", "reservation"],
                    aliases=["AC #:", "Constituency:", "District:", "Reservation:"],
                    localize=True,
                    sticky=False,
                    labels=True,
                    style="""
                        background-color: #1F2937;
                        color: #F9FAFB;
                        font-family: sans-serif;
                        font-size: 12px;
                        padding: 6px 10px;
                        border-radius: 6px;
                        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
                    """
                )
            )
            geojson_layer.add_to(m)

        # Render Map with click listener
        map_output = st_folium(
            m,
            width="100%",
            height=540,
            returned_objects=["last_active_drawing"],
            key="ap_choropleth_map"
        )

        # Handle map polygon click
        if map_output and map_output.get("last_active_drawing"):
            clicked_props = map_output["last_active_drawing"].get("properties", {})
            clicked_name = clicked_props.get("display_name") or clicked_props.get("ac_name")
            clicked_ac_no = clicked_props.get("ac_no")

            # Try matching by name or by AC number
            match = None
            if clicked_name:
                match = next((ac for ac in all_constituencies if ac.lower() == clicked_name.lower().strip()), None)
            if not match and clicked_ac_no is not None and "AC_No" in df.columns:
                ac_match_rows = df[df["AC_No"] == int(clicked_ac_no)]
                if not ac_match_rows.empty:
                    match = ac_match_rows.iloc[0]["Constituency_Name"]

            if match and match != st.session_state["selected_ac"]:
                st.session_state["selected_ac"] = match
                st.rerun()

    # Right Column: Visualizations for the selected AC
    with chart_col:
        st.subheader("📊 Caste Composition")

        if summary and not summary["category_df"].empty:
            # 1. Donut Chart: Category Share
            fig_donut = px.pie(
                summary["category_df"],
                names="Caste_Category",
                values="Voter_Count",
                hole=0.45,
                color="Caste_Category",
                color_discrete_map=utils.CATEGORY_COLORS,
                title=f"Category Breakdown ({current_ac})"
            )
            fig_donut.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>Voters: %{value:,}<br>Share: %{percent}<extra></extra>"
            )
            fig_donut.update_layout(
                margin=dict(l=10, r=10, t=35, b=10),
                height=260,
                showlegend=False
            )
            st.plotly_chart(fig_donut, use_container_width=True)

            # 2. Bar Chart: Top 7 Castes
            top_castes = summary["top_castes_df"].head(7).sort_values(by="Voter_Count", ascending=True)
            fig_bar = px.bar(
                top_castes,
                x="Voter_Count",
                y="Caste_Name",
                orientation="h",
                color="Caste_Category",
                color_discrete_map=utils.CATEGORY_COLORS,
                title=f"Top Communities by Voter Count",
                text="Voter_Count"
            )
            fig_bar.update_traces(
                texttemplate='%{text:,}',
                textposition='inside',
                insidetextanchor='middle',
                hovertemplate="<b>%{y}</b><br>Category: %{customdata[0]}<br>Voters: %{x:,}<extra></extra>",
                customdata=top_castes[["Caste_Category"]]
            )
            fig_bar.update_layout(
                margin=dict(l=10, r=10, t=35, b=10),
                height=280,
                xaxis_title="Voters",
                yaxis_title="",
                showlegend=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No caste records available for this constituency.")

    # Bottom Section: Detailed Caste Data Table & Export
    st.markdown("---")
    st.subheader(f"📋 Detailed Community Data: {current_ac}")

    if summary and not summary["full_df"].empty:
        table_df = summary["full_df"][["Caste_Name", "Caste_Category", "Voter_Count", "Share_Pct"]].copy()
        table_df.columns = ["Community / Caste", "Social Category", "Voter Count", "Share (% of AC)"]

        # Search bar for filtering castes within constituency
        search_query = st.text_input("🔍 Search caste inside this constituency:", placeholder="Type caste name (e.g., Kapu, Yadava, Reddy)...")
        if search_query:
            table_df = table_df[table_df["Community / Caste"].str.contains(search_query, case=False, na=False)]

        st.dataframe(
            table_df.style.format({
                "Voter Count": "{:,}",
                "Share (% of AC)": "{:.2f}%"
            }),
            use_container_width=True,
            height=250
        )

        # Download CSV button
        csv_data = table_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📥 Download {current_ac} Data (CSV)",
            data=csv_data,
            file_name=f"{current_ac}_caste_demographics.csv",
            mime="text/csv"
        )


# ----------------------------------------------------
# TAB 2: STATE-WIDE ANALYTICS & COMPARISON
# ----------------------------------------------------
with tab_state:
    st.header("📊 State-Wide Demographic Overview")
    st.caption("Aggregated numbers across all 175 Andhra Pradesh Assembly Constituencies")

    state_metrics = utils.get_state_metrics(df)

    scol1, scol2, scol3, scol4 = st.columns(4)
    with scol1:
        st.metric("Total Voters Mapped", f"{state_metrics['total_voters']:,}")
    with scol2:
        st.metric("Assembly Constituencies", f"{state_metrics['total_constituencies']}")
    with scol3:
        st.metric("Distinct Castes Recorded", f"{state_metrics['total_castes']}")
    with scol4:
        st.metric("Avg Voters / Constituency", f"{state_metrics['avg_voters_per_ac']:,}")

    st.markdown("---")
    sc1, sc2 = st.columns(2)

    with sc1:
        st.subheader("🥧 State-Wide Social Category Share")
        fig_state_cat = px.pie(
            state_metrics["category_breakdown"],
            names="Caste_Category",
            values="Voter_Count",
            color="Caste_Category",
            color_discrete_map=utils.CATEGORY_COLORS,
            hole=0.4
        )
        fig_state_cat.update_traces(textposition='inside', textinfo='percent+label')
        fig_state_cat.update_layout(height=360)
        st.plotly_chart(fig_state_cat, use_container_width=True)

    with sc2:
        st.subheader("🏆 Top 10 Largest Communities Across AP")
        top_s_castes = state_metrics["top_state_castes"].sort_values(by="Voter_Count", ascending=True)
        fig_state_bar = px.bar(
            top_s_castes,
            x="Voter_Count",
            y="Caste_Name",
            orientation="h",
            color="Voter_Count",
            color_continuous_scale="Blues",
            text="Voter_Count"
        )
        fig_state_bar.update_traces(texttemplate='%{text:,}', textposition='inside')
        fig_state_bar.update_layout(height=360, yaxis_title="", xaxis_title="Total Voters across AP", coloraxis_showscale=False)
        st.plotly_chart(fig_state_bar, use_container_width=True)


# ----------------------------------------------------
# TAB 3: DEPLOYMENT & BEGINNER GUIDE
# ----------------------------------------------------
with tab_guide:
    st.header("🚀 Beginner Guide & Free Deployment Walkthrough")
    st.markdown("""
    Welcome! If you are new to data dashboards and GIS maps, this guide explains **how every piece works** and **how you can deploy it to the web for free in 5 minutes**.
    """)

    with st.expander("🧩 1. How This Project Works (Mental Model)", expanded=True):
        st.markdown("""
        This dashboard connects three core pieces:
        1. **Spatial Boundary Data (`ap_constituencies.geojson`)**:
           - A standard geographic file containing polygon coordinates that draw the boundaries of all **175 Assembly Constituencies** of Andhra Pradesh.
        2. **Tabular Demographic Data (Excel/CSV)**:
           - Contains the rows of demographic information: `Constituency_Name`, `Caste_Category`, `Caste_Name`, and `Voter_Count`.
        3. **The Common Join Key**:
           - Both files share the same constituency name (`Constituency_Name`). When you click a boundary on the map, the dashboard filters your Excel spreadsheet for that constituency and immediately calculates the charts and totals!
        """)

    with st.expander("📁 2. How to Use Your Own Excel File"):
        st.markdown("""
        To display your exact dataset:
        1. **Option A (Live in the Browser)**: Simply drag and drop your `.xlsx` or `.csv` file into the sidebar uploader under **"📁 Data Source"**.
        2. **Option B (Permanent Default)**: Replace the file inside `data/caste_voters_ap.xlsx` with your own file.
        
        **Recommended Column Names for your Excel spreadsheet:**
        - `Constituency_Name` (e.g. `Kuppam`, `Mangalagiri`, `Pulivendla`)
        - `Caste_Category` (e.g. `OC`, `BC-A`, `BC-B`, `SC`, `ST`)
        - `Caste_Name` (e.g. `Kapu`, `Reddy`, `Kamma`, `Yadava`, `Madiga`)
        - `Voter_Count` (e.g. `32450`)
        - `District` *(Optional)*
        - `AC_No` *(Optional, 1 to 175)*
        
        *(Note: The app's smart column mapper automatically recognizes common variations like `AC Name`, `Community`, `Category`, `Total Voters`, etc.)*
        """)

    with st.expander("💻 3. How to Run Locally on Your Computer"):
        st.markdown("""
        1. Open your terminal or PowerShell in this project folder:
           ```bash
           cd C:\\Users\\Dell\\.gemini\\antigravity\\scratch\\ap-constituency-dashboard
           ```
        2. Run Streamlit:
           ```bash
           streamlit run app.py
           ```
        3. Your default web browser will automatically open `http://localhost:8501`!
        """)

    with st.expander("🌐 4. How to Deploy Online for Free (Streamlit Community Cloud)"):
        st.markdown("""
        You can share this dashboard with anyone using **Streamlit Community Cloud** (100% free hosting):

        ### Step 1: Push Your Code to GitHub
        1. Create a free account on [GitHub.com](https://github.com) if you don't already have one.
        2. Create a new repository named `ap-constituency-dashboard` (leave it public).
        3. In your terminal inside the project directory, run:
           ```bash
           git init
           git add .
           git commit -m "Initial commit of AP Constituency Dashboard"
           git branch -M main
           git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/ap-constituency-dashboard.git
           git push -u origin main
           ```

        ### Step 2: Deploy on Streamlit Cloud
        1. Go to [share.streamlit.io](https://share.streamlit.io) and click **Sign in with GitHub**.
        2. Click **New app**.
        3. Select your repository: `<YOUR_GITHUB_USERNAME>/ap-constituency-dashboard`.
        4. Main file path: `app.py`.
        5. Click **Deploy!** 🚀
        6. In ~1-2 minutes, Streamlit will give you a live shareable URL (like `https://ap-constituency-dashboard.streamlit.app`) that anyone can access from their computer or smartphone!
        """)
