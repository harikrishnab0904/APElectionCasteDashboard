# 🏛️ Andhra Pradesh Assembly Constituencies - Caste Demographics Dashboard

An interactive spatial data dashboard built with **Streamlit**, **Folium (Leaflet)**, and **Plotly** to visualize community and caste voter demographics across all **175 Assembly Constituencies of Andhra Pradesh**.

---

## 🌟 Key Features

- **Interactive 175-Constituency Map**: Real-time Leaflet map of Andhra Pradesh with official boundaries.
  - Hover over any constituency to see AC number, constituency name, and district.
  - Click on any constituency polygon to automatically load its detailed caste profile!
- **Constituency Deep-Dive**:
  - 👥 **Total Voters** & community statistics.
  - 🏆 **Largest Community** and share percentage.
  - 🏷️ **Category Breakdown**: Donut chart visualizing OC, BC-A/B/C/D/E, SC, ST, and Minorities.
  - 📊 **Top 10 Communities**: Horizontal bar chart sorted by voter count.
  - 📋 **Searchable Data Table**: Search specific castes with one-click **CSV Export**.
- **State-Wide Overview**: Aggregated totals, category percentages, and top caste groups across all of AP.
- **Flexible Data Input**:
  - Out of the box, loads a sample dataset representing all 175 AP constituencies.
  - Easily upload your own **Excel (`.xlsx`, `.xls`)** or **CSV** file directly through the sidebar.
  - Intelligent column-name mapping: accommodates variations like `AC_Name`, `Constituency`, `Community`, `Voters`, etc.

---

## 📂 Project Directory Structure

```text
ap-constituency-dashboard/
├── .streamlit/
│   └── config.toml                # Custom Streamlit UI theme
├── data/
│   ├── ap_constituencies.geojson  # 175 AP Assembly boundaries (Official 2024 Gazette)
│   ├── caste_voters_ap.xlsx       # Excel dataset mapped to all 175 constituencies
│   └── caste_voters_ap.csv        # CSV backup of the dataset
├── app.py                         # Main Streamlit application
├── utils.py                       # Helper functions (GeoJSON loading, data cleanup, metrics)
├── generate_sample_data.py        # Script to generate realistic sample dataset
├── requirements.txt               # Python package dependencies
└── README.md                      # Comprehensive guide and documentation
```

---

## 🚀 How to Run Locally (On Your Computer)

### Step 1: Open PowerShell or Command Prompt
Navigate to your project folder:
```powershell
cd C:\Users\Dell\.gemini\antigravity\scratch\ap-constituency-dashboard
```

### Step 2: Install Required Libraries (one-time setup)
```bash
pip install -r requirements.txt
```

### Step 3: Launch the Dashboard
```bash
streamlit run app.py
```
Streamlit will start a local server and automatically open the dashboard in your web browser at:
`http://localhost:8501`

---

## 📊 How to Use Your Own Excel File

You can feed your own data in two easy ways:

### Method 1: Live Upload in the Browser
1. In the left sidebar of the running dashboard, find **📁 Data Source**.
2. Click **Browse files** and select your `.xlsx` or `.csv` file.
3. The dashboard will instantly update all maps, charts, and tables!

### Method 2: Replace the Default File
Simply place your Excel file in the `data/` folder and name it:
`caste_voters_ap.xlsx`

### Recommended Spreadsheet Columns:
| Column Header | Example Values | Description |
| :--- | :--- | :--- |
| `Constituency_Name` | `Kuppam`, `Mangalagiri`, `Pulivendla` | Name of the assembly constituency |
| `Caste_Category` | `OC`, `BC-A`, `BC-B`, `SC`, `ST`, `Minorities` | Social category group |
| `Caste_Name` | `Kapu`, `Reddy`, `Kamma`, `Yadava`, `Madiga` | Specific caste/community name |
| `Voter_Count` | `34500`, `12400` | Number of voters in that community |
| `District` *(Optional)* | `Chittoor`, `Guntur`, `Krishna` | District name |
| `AC_No` *(Optional)* | `1`, `175` | Official AC number (1 to 175) |

*(Note: The app's smart column matcher automatically handles lower/upper case, spaces, or aliases like `AC Name`, `Community`, `Category`, `Total Voters`, etc.)*

---

## 🌐 How to Deploy Online for Free (Streamlit Cloud)

You can share your live dashboard with anyone via a public URL using **Streamlit Community Cloud** (100% free hosting):

### 1. Push to GitHub
1. Make sure you have a free [GitHub](https://github.com) account.
2. Open PowerShell in this project folder and run:
   ```bash
   git init
   git add .
   git commit -m "Deploy AP Constituency Caste Dashboard"
   git branch -M main
   ```
3. Create a new repository on GitHub named `ap-constituency-dashboard`.
4. Link and push your code:
   ```bash
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/ap-constituency-dashboard.git
   git push -u origin main
   ```

### 2. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
2. Click **"New app"**.
3. Choose:
   - **Repository**: `<YOUR_GITHUB_USERNAME>/ap-constituency-dashboard`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. Click **"Deploy!"** 🚀
5. Within 1-2 minutes, you will receive a public link (e.g. `https://ap-caste-dashboard.streamlit.app`) that works on any laptop, tablet, or smartphone!

---

## 💡 How GIS & Spatial Dashboards Work (Concept Explained)

If you are new to building dashboards with maps:
1. **The Map Layer (`.geojson`)**: A GeoJSON file stores geographic coordinates (latitude and longitude pairs) that draw polygon outlines of each constituency. Each polygon also holds properties like `ac_name` and `ac_no`.
2. **The Data Layer (`.xlsx`)**: Your spreadsheet has demographic rows with voters for each caste.
3. **The Connection (Join)**: The Python code matches `feature.properties.ac_name` from the map with `row.Constituency_Name` from your spreadsheet. When you click a constituency on the map, Folium sends the clicked polygon's name to Streamlit, which triggers an instant filter and re-computes all charts in real time!
