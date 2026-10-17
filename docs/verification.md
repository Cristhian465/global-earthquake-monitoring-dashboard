# Verificación local

Verificado el 17 de octubre de 2026 con Python 3.12.14 en macOS.

- Instalación de `requirements-dev.txt`: completada en un entorno virtual limpio.
- `ruff check .`: All checks passed.
- `pytest -q`: 18 passed (15.29 s).
- Consulta real USGS: 2024-01-01 a 2024-01-07 UTC, magnitud 4 a 10, Perú y entorno. Resultado: 8 eventos, 0 registros omitidos, magnitud máxima 5.3.

Las pruebas de interfaz usan Streamlit AppTest y respuestas controladas; no equivalen a una inspección visual manual del mapa ni verifican la disponibilidad de teselas. La consulta real verifica el cliente HTTP y la normalización por separado.

CI está configurado para Python 3.11 y 3.12. No se afirma una ejecución remota exitosa ni un despliegue en Community Cloud sin observarlos.

Pruebas y Ruff completados correctamente en GitHub Actions con Python 3.11 y 3.12 para el commit `90f9d34`. [Ejecución CI](https://github.com/Cristhian465/global-earthquake-monitoring-dashboard/actions/runs/39080894370).
