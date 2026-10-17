---
title: "Construí un dashboard de sismos con Python, Streamlit, Plotly y USGS"
published: false
description: "Del catálogo GeoJSON a un dashboard interactivo con énfasis en Perú y Sudamérica."
tags: python, streamlit, datavisualization, opensource
---

Quería explorar la actividad sísmica mundial y acercar el análisis a Perú y Sudamérica. Construí Global Earthquake Monitoring Dashboard: una aplicación que consulta datos reales de USGS, permite elegir fechas y magnitudes y presenta mapa, indicadores y gráficos.

Este proyecto es una herramienta de exploración. No predice sismos ni emite alertas.

El código está disponible en [GitHub](https://github.com/Cristhian465/global-earthquake-monitoring-dashboard). En la verificación local pasaron 18 pruebas y Ruff no encontró errores.

## De la pregunta a la arquitectura

La pregunta fue: ¿qué sismos registra USGS para una región y periodo determinados? Separé el proyecto en dos partes: `earthquake/data.py` valida consultas y transforma GeoJSON en una tabla; `app.py` controla los filtros, la caché y las visualizaciones.

El recorrido de los datos es:

```text
Formulario → Query validada → USGS → normalización → caché → mapa/KPIs/gráficos/CSV
```

## Consultar datos reales

Uso el [catálogo USGS](https://earthquake.usgs.gov/fdsnws/event/1/) con `format=geojson` y `eventtype=earthquake`. La consulta incluye fechas UTC y magnitudes. Para Perú y Sudamérica agrego límites geográficos rectangulares, explicados en la interfaz: incluyen zonas vecinas y mar, por lo que no equivalen a fronteras políticas.

USGS recomienda sus feeds para visualizaciones en tiempo real. Elegí el catálogo porque este proyecto necesita consultar periodos personalizados. La aplicación no mantiene una conexión de streaming.

## Una fecha final también debe incluir la tarde

Un detalle fácil de pasar por alto es que una fecha como `2024-01-02` suele representar la medianoche. Transformo el día final en `23:59:59.999999 UTC`, para incluir el día completo. También muestro cuándo se recuperaron los datos: la fecha del sismo y la de consulta son conceptos distintos.

## Visualizar sin confundir

El mapa utiliza Plotly y OpenStreetMap. El tamaño ayuda a comparar magnitudes y el color representa profundidad. No interpreto el tamaño como energía ni el color como riesgo.

Los indicadores muestran cantidad, magnitud máxima, cantidad con magnitud al menos 5 y profundidad mediana. Los gráficos complementan el mapa: conteo diario, distribución de magnitudes y relación entre profundidad y magnitud. Los días sin eventos se conservan en la serie diaria.

## Diseñar para los fallos

La API puede tardar o no responder. Añadí timeout, reintentos limitados y mensajes visibles. La caché de Streamlit conserva las consultas exitosas durante diez minutos; un botón permite renovarlas.

Otro límite es el máximo de 20 000 eventos por consulta. Si se alcanza, pido reducir el periodo o aumentar la magnitud mínima. Mostrar un resultado parcial como si fuera completo distorsionaría los indicadores.

La normalización conserva magnitudes ausentes, descarta registros imposibles de ubicar y elimina IDs duplicados. La exportación CSV neutraliza textos que una hoja de cálculo podría interpretar como fórmulas.

## Verificar antes de publicar

Las pruebas cubren fechas, regiones, valores nulos, duplicados, timeouts, errores HTTP, respuestas vacías y límites. También pruebo la interfaz con Streamlit AppTest usando datos controlados. GitHub Actions está configurado para ejecutar Ruff y pytest en Python 3.11 y 3.12.

## Ejecutarlo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Para Community Cloud, el punto de entrada es `app.py` y no hacen falta claves de API. La [guía oficial](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app) explica cómo conectar el repositorio.

## Lo que sigue

Me gustaría incorporar límites administrativos para comparaciones por país y consultas divididas para periodos más amplios. También sería útil comparar catálogos y documentar sus diferencias de cobertura.

Antes de publicar este borrador: insertar la URL de la aplicación solo si fue desplegada y capturas obtenidas con un periodo explícito. Anotar resultados de pruebas y ejecución CI únicamente después de verificarlos.
