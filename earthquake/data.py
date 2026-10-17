"""Validated USGS queries and defensive GeoJSON normalization."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import math

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
REGIONS = {
    "Mundo": None,
    "Perú y entorno": (-20, 1, -85, -68),
    "Sudamérica": (-60, 15, -90, -30),
}
COLUMNS = ["id", "time_utc", "place", "magnitude", "magnitude_type", "depth_km",
           "latitude", "longitude", "url"]


class DataError(Exception):
    """Readable error at the API boundary."""


@dataclass(frozen=True)
class Query:
    start: date
    end: date
    min_magnitude: float = 2.5
    max_magnitude: float = 10.0
    region: str = "Mundo"

    def params(self):
        if self.start > self.end:
            raise ValueError("La fecha inicial debe ser anterior o igual a la final.")
        if (self.end - self.start).days > 365:
            raise ValueError("Selecciona como máximo 366 días inclusivos.")
        if self.region not in REGIONS:
            raise ValueError("Región desconocida.")
        if not (-2 <= self.min_magnitude <= self.max_magnitude <= 10):
            raise ValueError("Rango de magnitud inválido.")
        start = datetime.combine(self.start, time.min, timezone.utc)
        # USGS endtime is inclusive; include the entire selected final day.
        end = datetime.combine(self.end + timedelta(days=1), time.min, timezone.utc)
        end -= timedelta(microseconds=1)
        params = dict(format="geojson", starttime=start.isoformat(), endtime=end.isoformat(),
                      minmagnitude=self.min_magnitude, maxmagnitude=self.max_magnitude,
                      eventtype="earthquake", orderby="time", limit=20000)
        bounds = REGIONS[self.region]
        if bounds:
            params.update(zip(("minlatitude", "maxlatitude", "minlongitude", "maxlongitude"), bounds))
        return params


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def normalize(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("features"), list):
        raise DataError("USGS devolvió una estructura GeoJSON inesperada.")
    rows = []
    skipped = 0
    for feature in payload["features"]:
        try:
            props = feature.get("properties") or {}
            coordinates = feature["geometry"]["coordinates"]
            lon, lat, depth = [number(x) for x in coordinates[:3]]
            timestamp = pd.to_datetime(props.get("time"), unit="ms", utc=True, errors="coerce")
            if lon is None or lat is None or not (-180 <= lon <= 180 and -90 <= lat <= 90):
                raise ValueError("coordinates")
            if pd.isna(timestamp) or not feature.get("id"):
                raise ValueError("identity/time")
            rows.append(dict(id=feature["id"], time_utc=timestamp,
                             place=props.get("place") or "Ubicación no disponible",
                             magnitude=number(props.get("mag")), magnitude_type=props.get("magType"),
                             depth_km=depth, latitude=lat, longitude=lon, url=props.get("url")))
        except (KeyError, TypeError, ValueError, AttributeError):
            skipped += 1
    frame = pd.DataFrame(rows, columns=COLUMNS)
    for col in ("magnitude", "depth_km", "latitude", "longitude"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame["time_utc"] = pd.to_datetime(frame["time_utc"], utc=True)
    frame = frame.drop_duplicates("id").sort_values("time_utc", ascending=False).reset_index(drop=True)
    return frame, skipped


def fetch(query, session=None):
    params = query.params()
    own_session = session is None
    if own_session:
        session = requests.Session()
        retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504],
                      allowed_methods=["GET"], respect_retry_after_header=False)
        session.mount("https://", HTTPAdapter(max_retries=retry))
    try:
        response = session.get(API_URL, params=params, timeout=(5, 30))
        if response.status_code == 204:
            return normalize({"features": []})
        response.raise_for_status()
        payload = response.json()
        frame, skipped = normalize(payload)
        if len(payload["features"]) >= 20000:
            raise DataError("La consulta alcanzó 20 000 eventos. Reduce fechas o aumenta la magnitud mínima.")
        return frame, skipped
    except (requests.RequestException, ValueError) as exc:
        raise DataError("No se pudo consultar USGS. Reduce el rango o inténtalo de nuevo.") from exc
    finally:
        if own_session:
            session.close()


def export_csv(frame):
    """Neutralize spreadsheet formulas in external text fields."""
    safe = frame.copy()
    for column in safe.select_dtypes(include=["object", "string"]).columns:
        safe[column] = safe[column].map(
            lambda value: "'" + value if isinstance(value, str)
            and value.lstrip().startswith(("=", "+", "-", "@")) else value)
    return safe.to_csv(index=False).encode("utf-8-sig")
