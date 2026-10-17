# 🌎 Global Earthquake Monitoring Dashboard

Dashboard en español para explorar sismos reales del catálogo USGS con Python, Streamlit y Plotly. Enfoque mundial, Perú y Sudamérica. No requiere API key.

## Funciones

- Mapa mundial interactivo con zoom, tamaño por magnitud y color por profundidad.
- Fechas UTC inclusivas, rango de magnitud y región; formulario para evitar consultas por cada cambio.
- KPIs: número de eventos, magnitud máxima, eventos M ≥ 5 y profundidad mediana.
- Actividad diaria (incluye días sin eventos), histograma, relación magnitud/profundidad, top 10 y tabla completa.
- Exportación CSV UTF-8 con BOM y neutralización de fórmulas en campos de texto.
- Caché de 10 minutos, botón de actualización, timeout y reintentos limitados para errores transitorios.
- Estados explícitos de error y consulta vacía; validación y deduplicación de registros.
- Pruebas offline de datos y de interfaz Streamlit; CI en Python 3.11 y 3.12.

## Ejecutar localmente

Requisito: Python 3.11 o 3.12 y conexión a Internet.

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Abre la dirección local que muestre Streamlit. Selecciona una región, fechas y magnitudes en la barra lateral y pulsa **Consultar USGS**. La consulta inicial cubre los últimos siete días más el día actual en UTC. **Actualizar consulta** borra la caché de esta aplicación y vuelve a consultar.

## Pruebas y calidad

```bash
python -m pip install -r requirements-dev.txt
ruff check .
pytest -q
```

Las pruebas usan respuestas controladas; no dependen de que USGS esté disponible. Las pruebas de interfaz verifican indicadores, tablas y estados vacíos/de error. CI ejecuta ambos comandos en cada push y pull request. Una prueba local no equivale a una ejecución de GitHub Actions.

## Desplegar en Streamlit Community Cloud

1. Publica este directorio como raíz de `global-earthquake-monitoring-dashboard` en tu cuenta GitHub.
2. Inicia sesión en [Streamlit Community Cloud](https://share.streamlit.io/) y elige **Create app**.
3. Selecciona el repositorio, rama `main` y archivo `app.py`.
4. En las opciones avanzadas selecciona Python 3.12. No hacen falta secretos.
5. Despliega y revisa los registros; prueba Mundo, Perú y entorno, CSV y filtros.
6. Copia la URL real que genere la plataforma al README y al artículo, después de verificarla.

El repositorio contiene `requirements.txt` y `.streamlit/config.toml`; Community Cloud instala las dependencias. No se afirma que exista un despliegue hasta verificarlo. Consulta la [guía oficial de despliegue](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app).

## Datos y decisiones

Fuente: [USGS Earthquake Catalog API](https://earthquake.usgs.gov/fdsnws/event/1/), endpoint `query`, formato GeoJSON y `eventtype=earthquake`. Se usa el catálogo para permitir fechas y regiones personalizadas; USGS recomienda sus feeds GeoJSON para visualizaciones en tiempo real cuando sea posible.

Todas las fechas son UTC. El día final incluye hasta 23:59:59.999999 UTC. La fecha de recuperación se muestra separada de las fechas de origen de los sismos. No hay actualización automática ni streaming: la caché vence al volver a ejecutar la consulta y puede forzarse con el botón.

| Región | Latitud | Longitud |
|---|---|---|
| Mundo | −90 a 90 | −180 a 180 |
| Perú y entorno | −20 a 1 | −85 a −68 |
| Sudamérica | −60 a 15 | −90 a −30 |

Los rectángulos incluyen océano y países vecinos; no constituyen fronteras oficiales. No se infiere el país a partir del texto `place`. La cobertura de sismos pequeños varía y el catálogo puede revisarse. Magnitud, intensidad y riesgo no son equivalentes; los tipos de magnitud pueden diferir. Los KPIs describen únicamente la consulta seleccionada.

La aplicación permite hasta 366 días inclusivos y magnitudes entre −2 y 10. USGS limita consultas a 20 000 eventos. Si la respuesta alcanza ese valor, se rechaza con una indicación para reducir el intervalo o aumentar la magnitud mínima; no se muestran estadísticas truncadas. No hay paginación automática, por lo que periodos amplios deben dividirse manualmente.

Registros sin ID, fecha válida o coordenadas válidas se omiten y se informa su cantidad. Magnitudes y profundidades ausentes se mantienen como valores nulos; los agregados correspondientes los omiten. Los reintentos GET cubren 429 y errores 5xx seleccionados, con timeout de conexión de 5 s y lectura de 30 s. Un fallo no se sustituye por datos sintéticos ni por una consulta anterior.

Mapa mediante Plotly MapLibre y teselas OpenStreetMap: requiere acceso a servicios externos desde el navegador; atribución © OpenStreetMap contributors. [Documentación Plotly](https://plotly.com/python/scatter-plots-on-maps/).

## Estructura

```text
app.py                   Interfaz, caché, gráficos y descarga
earthquake/data.py       Consultas, normalización y CSV
tests/                   Pruebas de datos y aplicación
.github/workflows/ci.yml Calidad y pruebas en GitHub Actions
.streamlit/config.toml   Tema y servidor
docs/devto-draft.md       Borrador de artículo
docs/demo-script.md       Guion de demostración y capturas
```

## Publicación y contribuciones

El borrador de Dev.to debe completarse con enlaces y capturas verificadas. No contiene resultados numéricos inventados. Para contribuir: crea una rama, ejecuta las comprobaciones y abre un pull request. Nunca subas `.env`, tokens ni `.streamlit/secrets.toml`.

Licencia MIT para el código. Los datos se atribuyen a USGS y el mapa a OpenStreetMap. Aplicación educativa, sin afiliación con USGS; no predice terremotos ni reemplaza avisos oficiales.
