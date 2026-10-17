"""Global Earthquake Monitoring Dashboard — Streamlit entry point."""
from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.express as px
import streamlit as st

from earthquake.data import DataError, Query, REGIONS, export_csv, fetch

st.set_page_config(page_title="Earthquake Monitor", page_icon="🌎", layout="wide")
st.title("🌎 Global Earthquake Monitoring Dashboard")
st.caption("Explora la actividad sísmica del mundo · Fuente: USGS · Perú y Sudamérica")
st.info("Datos observacionales sujetos a revisión. Esta aplicación no predice sismos ni emite alertas de emergencia.")


@st.cache_data(ttl=600, max_entries=32, show_spinner=False)
def load_data(query):
    frame, skipped = fetch(query)
    return frame, skipped, datetime.now(timezone.utc)


now = datetime.now(timezone.utc).date()
with st.sidebar:
    st.header("Explorar catálogo")
    with st.form("filters"):
        region = st.selectbox("Región", list(REGIONS))
        start = st.date_input("Desde (UTC)", now - timedelta(days=7), max_value=now)
        end = st.date_input("Hasta (UTC, día completo)", now, max_value=now)
        magnitudes = st.slider("Magnitud", -2.0, 10.0, (2.5, 10.0), 0.1)
        st.form_submit_button("Consultar USGS", type="primary")
    st.caption("Perú y entorno y Sudamérica son rectángulos geográficos; incluyen océano y zonas vecinas.")
    if st.button("Actualizar consulta (vaciar caché)"):
        load_data.clear()
    st.caption("Caché: 10 minutos. Sin claves de API.")

query = Query(start, end, *magnitudes, region)
try:
    query.params()
    with st.spinner("Consultando catálogo USGS…"):
        frame, skipped, fetched_at = load_data(query)
except (DataError, ValueError) as exc:
    st.error(str(exc))
    st.stop()

st.caption(f"Consulta: {region} · {start} a {end} UTC · M {magnitudes[0]}–{magnitudes[1]} · "
           f"Recuperado: {fetched_at:%Y-%m-%d %H:%M:%S} UTC")
if skipped:
    st.warning(f"Se omitieron {skipped} registros sin coordenadas, fecha o identificador válidos.")
if frame.empty:
    st.warning("No hay eventos para estos filtros. Amplía el periodo o reduce la magnitud mínima.")
    st.stop()

cols = st.columns(4)
cols[0].metric("Sismos registrados", f"{len(frame):,}")
maximum = frame.magnitude.max()
cols[1].metric("Magnitud máxima", f"{maximum:.1f}" if maximum == maximum else "Sin datos")
cols[2].metric("Magnitud ≥ 5", int(frame.magnitude.ge(5).sum()))
depth = frame.depth_km.median()
cols[3].metric("Profundidad mediana", f"{depth:.1f} km" if depth == depth else "Sin datos")

map_data = frame.assign(marker_size=frame.magnitude.fillna(0).clip(lower=0) + 2,
                        time_label=frame.time_utc.dt.strftime("%Y-%m-%d %H:%M UTC"))
center = {"lat": -10, "lon": -76} if region == "Perú y entorno" else {"lat": -20, "lon": -60}
fig = px.scatter_map(map_data, lat="latitude", lon="longitude", size="marker_size",
                     color="depth_km", color_continuous_scale="Turbo", size_max=22,
                     hover_name="place", hover_data={"magnitude": True, "depth_km": ":.1f",
                     "time_label": True, "marker_size": False},
                     zoom=0.6 if region == "Mundo" else (3.5 if region == "Perú y entorno" else 1.8),
                     center={"lat": 0, "lon": 0} if region == "Mundo" else center,
                     map_style="open-street-map", height=540,
                     labels={"depth_km": "Profundidad (km)", "magnitude": "Magnitud", "time_label": "Fecha"})
fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig, width="stretch")
st.caption("Tamaño: magnitud relativa (no energía). Color: profundidad. Mapa: © OpenStreetMap contributors.")
left, right = st.columns(2)
daily = frame.set_index("time_utc").resample("D").size().rename("Sismos")
# Include zero-event days at either edge of the selected period.
daily = daily.reindex(pd.date_range(start, end, tz="UTC"), fill_value=0)
left.plotly_chart(px.bar(x=daily.index, y=daily.values, labels={"x": "Día UTC", "y": "Sismos"},
                        title="Actividad diaria"), width="stretch")
right.plotly_chart(px.histogram(frame, x="magnitude", nbins=25, title="Distribución de magnitudes",
                               labels={"magnitude": "Magnitud"}), width="stretch")
st.plotly_chart(px.scatter(frame, x="depth_km", y="magnitude", hover_name="place",
                           title="Magnitud y profundidad", labels={"depth_km": "Profundidad (km)",
                           "magnitude": "Magnitud"}), width="stretch")
st.subheader("Los 10 eventos de mayor magnitud")
st.dataframe(frame.nlargest(10, "magnitude"), hide_index=True, width="stretch")
st.subheader("Catálogo consultado")
st.download_button("Descargar CSV", export_csv(frame), "usgs_earthquakes.csv", "text/csv")
st.dataframe(frame, hide_index=True, width="stretch")
st.caption("Las magnitudes pueden tener diferentes tipos de medición. La cobertura de eventos pequeños varía por región.")
st.markdown("[Catálogo y documentación USGS](https://earthquake.usgs.gov/fdsnws/event/1/)")
