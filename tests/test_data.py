from datetime import date
from unittest.mock import Mock

import pandas as pd
import pytest
import requests

from earthquake.data import DataError, Query, export_csv, fetch, normalize


def event(identifier="a", mag=4.5):
    return {"id": identifier, "geometry": {"coordinates": [-75, -12, 30]},
            "properties": {"time": 1704067200000, "mag": mag, "place": "Perú"}}


def query(**kwargs):
    return Query(date(2024, 1, 1), date(2024, 1, 2), **kwargs)


def test_inclusive_dates_and_region():
    params = query(region="Perú y entorno").params()
    assert params["endtime"] == "2024-01-02T23:59:59.999999+00:00"
    assert params["minlongitude"] == -85
    assert params["eventtype"] == "earthquake"


@pytest.mark.parametrize("q", [Query(date(2024, 2, 1), date(2024, 1, 1)),
    query(region="invalid"), query(min_magnitude=8, max_magnitude=2),
    Query(date(2020, 1, 1), date(2024, 1, 1))])
def test_validation(q):
    with pytest.raises(ValueError):
        q.params()


def test_normalization_deduplication_and_nulls():
    frame, skipped = normalize({"features": [event(), event(), event("b", None), {}, None]})
    assert len(frame) == 2
    assert skipped == 2
    assert pd.isna(frame.loc[frame.id == "b", "magnitude"]).all()
    assert str(frame.time_utc.dtype) == "datetime64[ns, UTC]"


def test_invalid_and_empty():
    with pytest.raises(DataError):
        normalize({"bad": []})
    assert normalize({"features": []})[0].empty


def test_bad_coordinates_and_time():
    bad = event()
    bad["geometry"]["coordinates"][0] = float("inf")
    bad_time = event("b")
    bad_time["properties"]["time"] = "bad"
    assert normalize({"features": [bad, bad_time]})[1] == 2


def test_fetch_success_and_timeout():
    session = Mock()
    session.get.return_value.status_code = 200
    session.get.return_value.json.return_value = {"features": [event()]}
    assert len(fetch(query(), session)[0]) == 1
    assert session.get.call_args.kwargs["timeout"] == (5, 30)
    session.get.side_effect = requests.Timeout()
    with pytest.raises(DataError):
        fetch(query(), session)


@pytest.mark.parametrize("mode", ["http", "json", "schema", "limit", "empty"])
def test_api_boundaries(mode):
    session = Mock()
    response = session.get.return_value
    response.status_code = 204 if mode == "empty" else 200
    response.json.return_value = {"features": [event()]}
    if mode == "http":
        response.raise_for_status.side_effect = requests.HTTPError()
    elif mode == "json":
        response.json.side_effect = ValueError()
    elif mode == "schema":
        response.json.return_value = {}
    elif mode == "limit":
        response.json.return_value = {"features": [event()] * 20000}
    if mode == "empty":
        assert fetch(query(), session)[0].empty
    else:
        with pytest.raises(DataError):
            fetch(query(), session)


def test_csv_injection_and_unicode():
    frame, _ = normalize({"features": [event()]})
    frame.loc[0, "place"] = "=1+1"
    csv = export_csv(frame).decode("utf-8-sig")
    assert "'=1+1" in csv
    assert "time_utc" in csv
