import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from urllib.parse import urlparse

st.set_page_config(
    page_title="Dashboard Equipo de Basketball",
    layout="wide",
    initial_sidebar_state="expanded",
)

MAXI_LABELS = ["<30", "30+", "35+", "40+", "45+", "50+"]

DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1_6o2Cs8Ipkz5q31VLbmW-Ry17mVt3YR2G9e09uxfex0/edit?usp=sharing"

st.title("Dashboard del Equipo de Basketball")
st.caption("Dashboard dinámico conectado a Google Sheets.")


def extract_sheet_id(sheet_url: str) -> str:
    parts = urlparse(sheet_url).path.split("/")
    if "d" in parts:
        idx = parts.index("d")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    raise ValueError("No se pudo extraer el Sheet ID desde la URL.")


@st.cache_data(ttl=300)
def load_google_sheet(sheet_url: str) -> pd.DataFrame:
    sheet_id = extract_sheet_id(sheet_url)
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    return pd.read_csv(csv_url)


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    normalized = {str(col).strip().lower(): col for col in df.columns}
    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]
    for col in df.columns:
        col_low = str(col).strip().lower()
        for candidate in candidates:
            if candidate.lower() in col_low:
                return col
    return None


def to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def maxi_category(age: float) -> str | None:
    if pd.isna(age):
        return None
    age = float(age)
    if age < 30:
        return "<30"
    if age < 35:
        return "30+"
    if age < 40:
        return "35+"
    if age < 45:
        return "40+"
    if age < 50:
        return "45+"
    return "50+"


def classify_bmi(bmi: float) -> str | None:
    if pd.isna(bmi):
        return None
    if bmi < 18.5:
        return "Bajo peso"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Sobrepeso"
    return "Obesidad"


def parse_scale_value(value):
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    direct = pd.to_numeric(text.replace(",", "."), errors="coerce")
    if not pd.isna(direct):
        return float(direct)

    mapping = {
        "muy mala": 1,
        "mala": 2,
        "regular": 3,
        "buena": 4,
        "muy buena": 5,
        "muy bajo": 1,
        "bajo": 2,
        "medio": 3,
        "alta": 4,
        "alto": 4,
        "muy alto": 5,
        "muy poca": 1,
        "poca": 2,
        "normal": 3,
        "excelente": 5,
        "nada clara": 1,
        "poco clara": 2,
        "clara": 4,
        "muy clara": 5,
    }
    return mapping.get(text.lower(), np.nan)


def prepare_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    colmap = {
        "nombre": find_column(df, ["Nombre Completo", "Nombre"]),
        "edad": find_column(df, ["Edad"]),
        "altura": find_column(df, ["Altura (cm)", "Altura"]),
        "peso": find_column(df, ["Peso (kg)", "Peso"]),
        "anios": find_column(df, ["Años jugando basketball", "Años jugando"]),
        "pos_principal": find_column(df, ["Posición principal"]),
        "pos_secundaria": find_column(df, ["Posición secundaria"]),
        "condicion": find_column(df, ["Condición física general"]),
        "velocidad": find_column(df, ["Velocidad"]),
        "resistencia": find_column(df, ["Resistencia"]),
        "fuerza": find_column(df, ["Fuerza"]),
        "manejo": find_column(df, ["Manejo de balón"]),
        "tiro_media": find_column(df, ["Tiro de media distancia"]),
        "tiro_3": find_column(df, ["Tiro de 3 puntos"]),
        "def_ind": find_column(df, ["Defensa individual"]),
        "def_equipo": find_column(df, ["Defensa en equipo"]),
        "rebotes": find_column(df, ["Rebotes"]),
        "claridad": find_column(df, ["Claridad de tu rol en el equipo"]),
        "aporte": find_column(df, ["Importancia de tu aporte al equipo"]),
        "comunicacion": find_column(df, ["Comunicación en el equipo"]),
        "confianza": find_column(df, ["Confianza entre jugadores"]),
        "liderazgo": find_column(df, ["Liderazgo del equipo"]),
    }

    work = df.copy()

    numeric_keys = [
        "edad",
        "altura",
        "peso",
        "anios",
        "velocidad",
        "resistencia",
        "fuerza",
        "manejo",
        "tiro_media",
        "tiro_3",
        "def_ind",
        "def_equipo",
        "rebotes",
    ]

    for key in numeric_keys:
        if colmap[key]:
            work[colmap[key]] = to_numeric(work[colmap[key]])

    score_keys = ["condicion", "claridad", "aporte", "comunicacion", "confianza", "liderazgo"]
    for key in score_keys:
        if colmap[key]:
            work[f"__score_{key}"] = work[colmap[key]].apply(parse_scale_value)

    if colmap["altura"] and colmap["peso"]:
        work["IMC"] = work[colmap["peso"]] / ((work[colmap["altura"]] / 100) ** 2)
        work["Clasificación IMC"] = work["IMC"].apply(classify_bmi)
    else:
        work["IMC"] = np.nan
        work["Clasificación IMC"] = None

    if colmap["edad"]:
        work["Categoría Maxi"] = work[colmap["edad"]].apply(maxi_category)
    else:
        work["Categoría Maxi"] = None

    performance_cols = [
        colmap["velocidad"],
        colmap["resistencia"],
        colmap["fuerza"],
        colmap["manejo"],
        colmap["tiro_media"],
        colmap["tiro_3"],
        colmap["def_ind"],
        colmap["def_equipo"],
        colmap["rebotes"],
    ]
    performance_cols = [c for c in performance_cols if c]
    work["Score Deportivo"] = work[performance_cols].mean(axis=1) if performance_cols else np.nan

    climate_cols = [
        f"__score_{k}"
        for k in ["comunicacion", "confianza", "liderazgo"]
        if f"__score_{k}" in work.columns
    ]
    work["Score Clima Equipo"] = work[climate_cols].mean(axis=1) if climate_cols else np.nan

    return work, colmap


def central_stats(series: pd.Series) -> dict:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return {
            "Media": np.nan,
            "Mediana": np.nan,
            "Desv. estándar": np.nan,
            "Mínimo": np.nan,
            "Máximo": np.nan,
        }
    return {
        "Media": clean.mean(),
        "Mediana": clean.median(),
        "Desv. estándar": clean.std(ddof=1) if len(clean) > 1 else 0.0,
        "Mínimo": clean.min(),
        "Máximo": clean.max(),
    }


sheet_url = st.sidebar.text_input("Google Sheets URL", value=DEFAULT_SHEET_URL)

try:
    df_raw = load_google_sheet(sheet_url)
except Exception as e:
    st.error(f"No pude leer la hoja pública: {e}")
    st.stop()

df, colmap = prepare_data(df_raw)

st.sidebar.markdown("### Filtros")
filtered = df.copy()

available_categories = [c for c in MAXI_LABELS if c in filtered["Categoría Maxi"].dropna().unique()]
selected_categories = st.sidebar.multiselect(
    "Categoría Maxi",
    available_categories,
    default=available_categories
)
if selected_categories:
    filtered = filtered[filtered["Categoría Maxi"].isin(selected_categories)]

if colmap["pos_principal"]:
    positions = sorted(
        [p for p in filtered[colmap["pos_principal"]].dropna().astype(str).unique() if p.strip()]
    )
    selected_positions = st.sidebar.multiselect(
        "Posición principal",
        positions,
        default=positions
    )
    if selected_positions:
        filtered = filtered[filtered[colmap["pos_principal"]].astype(str).isin(selected_positions)]

if colmap["edad"] and filtered[colmap["edad"]].notna().any():
    min_age = int(np.nanmin(filtered[colmap["edad"]]))
    max_age = int(np.nanmax(filtered[colmap["edad"]]))
    age_range = st.sidebar.slider("Rango de edad", min_age, max_age, (min_age, max_age))
    filtered = filtered[filtered[colmap["edad"]].between(age_range[0], age_range[1], inclusive="both")]

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Resumen",
    "Maxi Basket",
    "IMC",
    "Rendimiento",
    "Datos",
])

with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jugadores", int(len(filtered)))

    if colmap["edad"]:
        c2.metric("Edad promedio", f"{filtered[colmap['edad']].mean():.1f}")

    if colmap["altura"]:
        c3.metric("Altura promedio", f"{filtered[colmap['altura']].mean():.1f} cm")

    if colmap["peso"]:
        c4.metric("Peso promedio", f"{filtered[colmap['peso']].mean():.1f} kg")

    c5, c6, c7 = st.columns(3)

    if "IMC" in filtered.columns and filtered["IMC"].notna().any():
        c5.metric("IMC promedio", f"{filtered['IMC'].mean():.1f}")

    if "Score Deportivo" in filtered.columns and filtered["Score Deportivo"].notna().any():
        c6.metric("Score deportivo", f"{filtered['Score Deportivo'].mean():.2f}")

    if "Score Clima Equipo" in filtered.columns and filtered["Score Clima Equipo"].notna().any():
        c7.metric("Clima equipo", f"{filtered['Score Clima Equipo'].mean():.2f}")

    stat_targets = []
    mapping = [
        ("Edad", colmap["edad"]),
        ("Altura (cm)", colmap["altura"]),
        ("Peso (kg)", colmap["peso"]),
        ("Años jugando", colmap["anios"]),
    ]

    for label, col in mapping:
        if col:
            d = central_stats(filtered[col])
            d["Variable"] = label
            stat_targets.append(d)

    if "IMC" in filtered.columns:
        d = central_stats(filtered["IMC"])
        d["Variable"] = "IMC"
        stat_targets.append(d)

    if "Score Deportivo" in filtered.columns:
        d = central_stats(filtered["Score Deportivo"])
        d["Variable"] = "Score Deportivo"
        stat_targets.append(d)

    if stat_targets:
        stats_df = pd.DataFrame(stat_targets)[
            ["Variable", "Media", "Mediana", "Desv. estándar", "Mínimo", "Máximo"]
        ]
        st.dataframe(stats_df.round(2), use_container_width=True, hide_index=True)

with tab2:
    maxi_counts = (
        filtered["Categoría Maxi"]
        .value_counts(dropna=True)
        .reindex(MAXI_LABELS)
        .fillna(0)
        .reset_index()
    )
    maxi_counts.columns = ["Categoría Maxi", "Cantidad"]

    fig = px.bar(
        maxi_counts[maxi_counts["Cantidad"] > 0],
        x="Categoría Maxi",
        y="Cantidad",
        text_auto=True,
        title="Jugadores por categoría Maxi Basket",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    bmi_counts = (
        filtered["Clasificación IMC"]
        .value_counts(dropna=True)
        .rename_axis("Clasificación IMC")
        .reset_index(name="Cantidad")
    )

    if not bmi_counts.empty:
        fig = px.pie(
            bmi_counts,
            names="Clasificación IMC",
            values="Cantidad",
            hole=0.45,
            title="Distribución IMC",
        )
        st.plotly_chart(fig, use_container_width=True)

    if colmap["altura"] and colmap["peso"]:
        scatter = px.scatter(
            filtered,
            x=colmap["altura"],
            y=colmap["peso"],
            color="Clasificación IMC",
            hover_name=colmap["nombre"] if colmap["nombre"] else None,
            labels={
                colmap["altura"]: "Altura (cm)",
                colmap["peso"]: "Peso (kg)",
            },
            title="Altura vs Peso",
        )
        st.plotly_chart(scatter, use_container_width=True)

with tab4:
    performance_map = {
        "Velocidad": colmap["velocidad"],
        "Resistencia": colmap["resistencia"],
        "Fuerza": colmap["fuerza"],
        "Manejo de balón": colmap["manejo"],
        "Tiro media distancia": colmap["tiro_media"],
        "Tiro de 3": colmap["tiro_3"],
        "Defensa individual": colmap["def_ind"],
        "Defensa en equipo": colmap["def_equipo"],
        "Rebotes": colmap["rebotes"],
    }

    perf_pairs = [(k, v) for k, v in performance_map.items() if v]
    if perf_pairs:
        perf_df = pd.DataFrame({
            "Métrica": [k for k, _ in perf_pairs],
            "Promedio": [filtered[v].mean() for _, v in perf_pairs],
        }).sort_values("Promedio", ascending=False)

        fig = px.bar(
            perf_df,
            x="Métrica",
            y="Promedio",
            text_auto=".2f",
            title="Promedio por habilidad",
        )
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    show_cols = [
        c for c in [
            colmap["nombre"],
            colmap["edad"],
            colmap["altura"],
            colmap["peso"],
            colmap["anios"],
            colmap["pos_principal"],
            "Categoría Maxi",
            "IMC",
            "Clasificación IMC",
            "Score Deportivo",
            "Score Clima Equipo",
        ]
        if c and c in filtered.columns
    ]

    st.dataframe(filtered[show_cols].round(2), use_container_width=True, hide_index=True)
