import io
import pandas as pd
import streamlit as st

# pydeck je volitelné (kvůli mapě s barvami); když by chyběl, použijeme st.map
try:
    import pydeck as pdk
except Exception:
    pdk = None

# ---------------------------
# ZÁKLADNÍ NASTAVENÍ A DATA
# ---------------------------
st.set_page_config(page_title="PID Stops", layout="wide")

@st.cache_data(ttl=600)
def load_data(path: str = "data/clean/stops_clean.xlsx") -> pd.DataFrame:
    df_ = pd.read_excel(path)
    # sjednocení názvů souřadnic
    if {"avgLat", "avgLon"}.issubset(df_.columns):
        df_ = df_.rename(columns={"avgLat": "lat", "avgLon": "lon"})
    df_["lat"] = pd.to_numeric(df_.get("lat"), errors="coerce")
    df_["lon"] = pd.to_numeric(df_.get("lon"), errors="coerce")

    # základní textové sloupce (kvůli filtrům a contains)
    for c in ["stop_name", "fullName", "municipality", "district_code", "mainTrafficType"]:
        if c in df_.columns:
            df_[c] = df_[c].astype(str)

    return df_.dropna(subset=["lat", "lon"]).copy()

df = load_data()

# ---------------------------
# QUERY PARAMS (sdílení odkazu)
# ---------------------------
def _get_qp(key: str) -> str:
    try:
        val = st.query_params.get(key, "")
    except Exception:
        val = st.experimental_get_query_params().get(key, "")
    if isinstance(val, list):
        val = val[0] if val else ""
    return val or ""

def _set_qp(params: dict):
    try:
        st.query_params.update(params)
    except Exception:
        st.experimental_set_query_params(**params)

# ---------------------------
# SIDEBAR FILTRY
# ---------------------------
st.sidebar.header("Filtry")

types_all = sorted(df["mainTrafficType"].dropna().unique()) if "mainTrafficType" in df.columns else []
districts_all = sorted(df["district_code"].dropna().unique()) if "district_code" in df.columns else []

# výchozí hodnoty z URL
types_param = [t for t in _get_qp("types").split(",") if t] or types_all
dists_param = [d for d in _get_qp("districts").split(",") if d]
q_param = _get_qp("q")

sel_types = st.sidebar.multiselect("Druh dopravy", types_all, default=types_param)
sel_dist  = st.sidebar.multiselect("Okres (district_code)", districts_all, default=dists_param)
q = st.sidebar.text_input("Hledat název", q_param)

if st.sidebar.button("Reset filtrů"):
    sel_types, sel_dist, q = types_all, [], ""
    _set_qp({"types": "", "districts": "", "q": ""})

# ---------------------------
# APLIKACE FILTRŮ
# ---------------------------
f = df.copy()
if sel_types and "mainTrafficType" in f.columns:
    f = f[f["mainTrafficType"].isin(sel_types)]
if sel_dist and "district_code" in f.columns:
    f = f[f["district_code"].isin(sel_dist)]
if q:
    name_cols = [c for c in ["stop_name", "fullName"] if c in f.columns]
    if name_cols:
        mask = f[name_cols].apply(lambda s: s.str.contains(q, case=False, na=False)).any(axis=1)
        f = f[mask]

# URL pro sdílení stejného filtru
_set_qp({"types": ",".join(sel_types), "districts": ",".join(sel_dist), "q": q})

# ---------------------------
# HLAVIČKA + METRIKY
# ---------------------------
st.metric("Počet zastávek", len(f))
if "mainTrafficType" in f.columns and len(f):
    st.caption(", ".join(f["mainTrafficType"].value_counts().head(5).index))

# ---------------------------
# MAPA
# ---------------------------
if len(f) == 0:
    st.warning("Žádná data pro zvolený filtr.")
else:
    lat_c = float(f["lat"].median())
    lon_c = float(f["lon"].median())

    if pdk is not None:
        # barvy pro typy dopravy
        color_map = {
            "bus": [255, 76, 64],
            "train": [66, 135, 245],
            "tram": [255, 180, 0],
            "trolleybus": [132, 92, 255],
            "metroa": [0, 200, 120],
            "metrob": [0, 160, 130],
            "metroc": [0, 120, 140],
            "ferry": [0, 180, 220],
        }

        f_vis = f.copy()
        if "mainTrafficType" not in f_vis.columns:
            f_vis["mainTrafficType"] = "unknown"

        mt = f_vis["mainTrafficType"].astype(str).str.lower()
        # bezpečné mapování barev (po řádcích) s defaultem
        f_vis["__color"] = mt.apply(lambda t: color_map.get(t, [200, 200, 200]))

        layers = [
            pdk.Layer(
                "HexagonLayer",
                data=f_vis[["lon", "lat"]],
                get_position="[lon, lat]",
                radius=300,
                elevation_scale=20,
                elevation_range=[0, 1000],
                extruded=True,
                opacity=0.18,
            ),
            pdk.Layer(
                "ScatterplotLayer",
                data=f_vis[["stop_name", "lon", "lat", "__color"]],
                get_position="[lon, lat]",
                get_fill_color="__color",
                get_radius=60,
                pickable=True,
            ),
        ]

        st.pydeck_chart(
            pdk.Deck(
                map_style=None,  # bez tokenu
                initial_view_state=pdk.ViewState(latitude=lat_c, longitude=lon_c, zoom=8),
                layers=layers,
                tooltip={"text": "{stop_name}"},
            )
        )
    else:
        # fallback na st.map
        map_df = f.rename(columns={"lat": "latitude", "lon": "longitude"})[["latitude", "longitude"]]
        st.map(map_df, size=3)

# ---------------------------
# TABULKA + EXPORT
# ---------------------------
cols_to_show = [c for c in ["stop_name", "municipality", "district_code", "mainTrafficType", "lat", "lon"] if c in f.columns]
st.dataframe(f[cols_to_show].reset_index(drop=True), use_container_width=True)

# CSV
st.download_button(
    "Stáhnout filtr jako CSV",
    f.to_csv(index=False).encode("utf-8"),
    "pid_stops_filtered.csv",
    "text/csv",
)

# XLSX
buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="openpyxl") as writer:
    f.to_excel(writer, index=False, sheet_name="stops")
st.download_button(
    "Stáhnout filtr jako XLSX",
    data=buf.getvalue(),
    file_name="pid_stops_filtered.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.caption("Tip: Váš aktuální výběr se ukládá do URL. Stačí zkopírovat odkaz a klient uvidí stejný filtr.")
