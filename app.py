
import io
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Dashboard Equipo de Basketball",
    layout="wide",
    initial_sidebar_state="expanded",
)

MAXI_LABELS = ["<30", "30+", "35+", "40+", "45+", "50+"]

st.title("Dashboard del Equipo de Basketball")
st.caption("Sube el Excel de respuestas y explora métricas, categorías Maxi Basket, IMC y rendimiento general.")


@st.cache_data
def load_dataframe(file_bytes: bytes, filename: str) -> pd.DataFrame:
    if filename.lower().endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))
    else:
        df = pd.read_excel(io.BytesIO(file_bytes))
    return df


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
    if series is None:
        return series
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
        "muy mala": 1, "mala": 2, "regular": 3, "buena": 4, "muy buena": 5,
        "muy bajo": 1, "bajo": 2, "medio": 3, "alta": 4, "alto": 4, "muy alto": 5,
        "muy poca": 1, "poca": 2, "normal": 3, "buena": 4, "excelente": 5,
        "nada clara": 1, "poco clara": 2, "regular": 3, "clara": 4, "muy clara": 5,
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
        "comodidad": find_column(df, ["¿Te sientes cómodo en tu posición actual?"]),
        "claridad": find_column(df, ["Claridad de tu rol en el equipo"]),
        "aporte": find_column(df, ["Importancia de tu aporte al equipo"]),
        "pos_gustaria": find_column(df, ["¿En qué posición te gustaría jugar?"]),
        "comunicacion": find_column(df, ["Comunicación en el equipo"]),
        "confianza": find_column(df, ["Confianza entre jugadores"]),
        "liderazgo": find_column(df, ["Liderazgo del equipo"]),
        "fortaleza": find_column(df, ["¿Cuál es la mayor fortaleza del equipo?"]),
        "debilidad": find_column(df, ["¿Cuál es la mayor debilidad del equipo?"]),
        "mejora_entrenamiento": find_column(df, ["¿Qué mejorarías del entrenamiento?"]),
        "mejora_equipo": find_column(df, ["¿Qué mejorarías del juego en equipo?"]),
    }

    work = df.copy()

    for key in ["edad", "altura", "peso", "anios", "velocidad", "resistencia", "fuerza",
                "manejo", "tiro_media", "tiro_3", "def_ind", "def_equipo", "rebotes"]:
        if colmap[key]:
            work[colmap[key]] = to_numeric(work[colmap[key]])

    for key in ["condicion", "claridad", "aporte", "comunicacion", "confianza", "liderazgo"]:
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
        colmap["velocidad"], colmap["resistencia"], colmap["fuerza"], colmap["manejo"],
        colmap["tiro_media"], colmap["tiro_3"], colmap["def_ind"], colmap["def_equipo"],
        colmap["rebotes"]
    ]
    performance_cols = [c for c in performance_cols if c]
    if performance_cols:
        work["Score Deportivo"] = work[performance_cols].mean(axis=1)
    else:
        work["Score Deportivo"] = np.nan

    climate_cols = [f"__score_{k}" for k in ["comunicacion", "confianza", "liderazgo"] if f"__score_{k}" in work.columns]
    if climate_cols:
        work["Score Clima Equipo"] = work[climate_cols].mean(axis=1)
    else:
        work["Score Clima Equipo"] = np.nan

    return work, colmap


def central_stats(series: pd.Series) -> dict:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return {"Media": np.nan, "Mediana": np.nan, "Desv. estándar": np.nan, "Mínimo": np.nan, "Máximo": np.nan}
    return {
        "Media": clean.mean(),
        "Mediana": clean.median(),
        "Desv. estándar": clean.std(ddof=1) if len(clean) > 1 else 0.0,
        "Mínimo": clean.min(),
        "Máximo": clean.max(),
    }


uploaded = st.sidebar.file_uploader(
    "Sube el archivo Excel o CSV",
    type=["xlsx", "xls", "csv"],
)

default_path = Path("/mnt/data/Encuesta de Evaluación del Equipo de Basketball (Responses).xlsx")
use_default = False
if uploaded is None and default_path.exists():
    use_default = st.sidebar.checkbox("Usar archivo cargado previamente", value=True)

if uploaded is None and not use_default:
    st.info("Sube el archivo para generar el dashboard.")
    st.stop()

if uploaded is not None:
    raw_bytes = uploaded.getvalue()
    filename = uploaded.name
else:
    raw_bytes = default_path.read_bytes()
    filename = default_path.name

df_raw = load_dataframe(raw_bytes, filename)
df, colmap = prepare_data(df_raw)

st.sidebar.markdown("### Filtros")
filtered = df.copy()

if "Categoría Maxi" in filtered.columns:
    available_categories = [c for c in MAXI_LABELS if c in filtered["Categoría Maxi"].dropna().unique()]
    selected_categories = st.sidebar.multiselect("Categoría Maxi", available_categories, default=available_categories)
    if selected_categories:
        filtered = filtered[filtered["Categoría Maxi"].isin(selected_categories)]

if colmap["pos_principal"]:
    positions = sorted([p for p in filtered[colmap["pos_principal"]].dropna().astype(str).unique() if p.strip()])
    selected_positions = st.sidebar.multiselect("Posición principal", positions, default=positions)
    if selected_positions:
        filtered = filtered[filtered[colmap["pos_principal"]].astype(str).isin(selected_positions)]

if colmap["edad"]:
    min_age = int(np.nanmin(filtered[colmap["edad"]])) if filtered[colmap["edad"]].notna().any() else 0
    max_age = int(np.nanmax(filtered[colmap["edad"]])) if filtered[colmap["edad"]].notna().any() else 100
    age_range = st.sidebar.slider("Rango de edad", min_age, max_age, (min_age, max_age))
    filtered = filtered[filtered[colmap["edad"]].between(age_range[0], age_range[1], inclusive="both")]

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Resumen", "Maxi Basket", "IMC", "Rendimiento", "Datos"
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
    if "IMC" in filtered.columns:
        c5.metric("IMC promedio", f"{filtered['IMC'].mean():.1f}")
    if "Score Deportivo" in filtered.columns:
        c6.metric("Score deportivo", f"{filtered['Score Deportivo'].mean():.2f}")
    if "Score Clima Equipo" in filtered.columns and filtered["Score Clima Equipo"].notna().any():
        c7.metric("Clima equipo", f"{filtered['Score Clima Equipo'].mean():.2f}")

    st.subheader("Medidas de tendencia central y dispersión")
    stat_targets = []
    for label, key in [
        ("Edad", "edad"), ("Altura (cm)", "altura"), ("Peso (kg)", "peso"),
        ("Años jugando", "anios"), ("IMC", None), ("Score Deportivo", None)
    ]:
        if key is None:
            series = filtered[label] if label in filtered.columns else None
        else:
            series = filtered[colmap[key]] if colmap[key] else None
        if series is not None:
            stats = central_stats(series)
            stats["Variable"] = label
            stat_targets.append(stats)

    if stat_targets:
        stats_df = pd.DataFrame(stat_targets)[["Variable", "Media", "Mediana", "Desv. estándar", "Mínimo", "Máximo"]]
        st.dataframe(stats_df.round(2), use_container_width=True, hide_index=True)

    if colmap["pos_principal"] and "Score Deportivo" in filtered.columns:
        pos_perf = (
            filtered.dropna(subset=[colmap["pos_principal"]])
            .groupby(colmap["pos_principal"], as_index=False)["Score Deportivo"]
            .mean()
            .sort_values("Score Deportivo", ascending=False)
        )
        fig = px.bar(
            pos_perf,
            x=colmap["pos_principal"],
            y="Score Deportivo",
            title="Score deportivo promedio por posición principal",
            text_auto=".2f",
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Jugadores por categoría Maxi Basket")
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
        title="Distribución por categoría de edad",
    )
    st.plotly_chart(fig, use_container_width=True)

    if colmap["edad"]:
        hist = px.histogram(
            filtered,
            x=colmap["edad"],
            nbins=min(12, max(5, len(filtered))),
            title="Distribución de edades",
        )
        st.plotly_chart(hist, use_container_width=True)

with tab3:
    st.subheader("Estado nutricional según IMC")
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
            title="Altura vs peso",
            labels={colmap["altura"]: "Altura (cm)", colmap["peso"]: "Peso (kg)"},
        )
        st.plotly_chart(scatter, use_container_width=True)

    if "IMC" in filtered.columns:
        bmi_table = filtered[[c for c in [colmap["nombre"], colmap["edad"], "IMC", "Clasificación IMC"] if c]].copy()
        if "IMC" in bmi_table.columns:
            bmi_table["IMC"] = bmi_table["IMC"].round(1)
        st.dataframe(bmi_table, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Rendimiento")
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
        fig = px.bar(perf_df, x="Métrica", y="Promedio", text_auto=".2f", title="Promedio por habilidad")
        st.plotly_chart(fig, use_container_width=True)

    if colmap["anios"] and "Score Deportivo" in filtered.columns:
        fig = px.scatter(
            filtered,
            x=colmap["anios"],
            y="Score Deportivo",
            color=colmap["pos_principal"] if colmap["pos_principal"] else None,
            hover_name=colmap["nombre"] if colmap["nombre"] else None,
            title="Experiencia vs score deportivo",
            labels={colmap["anios"]: "Años jugando"},
        )
        st.plotly_chart(fig, use_container_width=True)

    climate_display = []
    for label, key in [("Comunicación", "comunicacion"), ("Confianza", "confianza"), ("Liderazgo", "liderazgo")]:
        score_col = f"__score_{key}"
        source_col = colmap[key]
        if score_col in filtered.columns and filtered[score_col].notna().any():
            climate_display.append({"Métrica": label, "Promedio": filtered[score_col].mean()})
        elif source_col and pd.api.types.is_numeric_dtype(filtered[source_col]):
            climate_display.append({"Métrica": label, "Promedio": filtered[source_col].mean()})
    if climate_display:
        climate_df = pd.DataFrame(climate_display)
        fig = px.bar(climate_df, x="Métrica", y="Promedio", text_auto=".2f", title="Clima del equipo")
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("Datos procesados")
    export_cols = []
    preferred = [
        colmap["nombre"], colmap["edad"], colmap["altura"], colmap["peso"], colmap["anios"],
        colmap["pos_principal"], colmap["pos_secundaria"], "Categoría Maxi", "IMC",
        "Clasificación IMC", "Score Deportivo", "Score Clima Equipo"
    ]
    export_cols = [c for c in preferred if c and c in filtered.columns]
    st.dataframe(filtered[export_cols].round(2), use_container_width=True, hide_index=True)

    csv = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Descargar datos procesados en CSV",
        data=csv,
        file_name="basket_dashboard_datos_procesados.csv",
        mime="text/csv",
    )
