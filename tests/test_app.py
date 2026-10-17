from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from earthquake.data import normalize
from test_data import event


def run_app(frame=None, error=None):
    import streamlit as st
    st.cache_data.clear()
    if frame is None:
        frame = normalize({"features": [event()]})[0]
    with patch("earthquake.data.fetch", side_effect=error, return_value=(frame, 0)):
        app = AppTest.from_file("app.py", default_timeout=30)
        app.run()
    return app


def test_dashboard_renders():
    app = run_app()
    assert not app.exception
    assert len(app.metric) == 4
    assert app.metric[0].value == "1"
    assert len(app.dataframe) == 2


def test_empty_state():
    import streamlit as st
    st.cache_data.clear()
    app = run_app(normalize({"features": []})[0])
    assert not app.exception
    assert any("No hay eventos" in item.value for item in app.warning)


def test_error_state():
    import streamlit as st
    from earthquake.data import DataError
    st.cache_data.clear()
    app = run_app(error=DataError("USGS no disponible"))
    assert not app.exception
    assert app.error[0].value == "USGS no disponible"
