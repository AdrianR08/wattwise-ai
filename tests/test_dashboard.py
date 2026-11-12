import tempfile
import unittest
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


class DashboardTests(unittest.TestCase):
    def test_landing_page_without_upload(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox[0].value, 'kW')

    def render_csv(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'upload.csv'
            path.write_text(text, encoding='utf-8')
            source = f"""
from io import BytesIO
from pathlib import Path
from src.dashboard import render_analysis
render_analysis(BytesIO(Path({str(path)!r}).read_bytes()), unit='kWh', timezone='UTC', electricity_rate=.15)
"""
            return AppTest.from_string(source).run(timeout=30)

    def test_upload_analysis_and_forecast_render(self):
        times = pd.date_range('2024-01-01', '2025-01-01', freq='h', inclusive='left', tz='UTC')
        app = self.render_csv(pd.DataFrame({'timestamp': times, 'usage': 1.}).to_csv(index=False))
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        forecast = [m for m in app.metric if 'Expected consumption' in m.label]
        self.assertEqual(forecast[0].value, '744 kWh')

    def test_invalid_upload_shows_error(self):
        app = self.render_csv('timestamp,usage\ninvalid,10\n')
        self.assertFalse(app.exception)
        self.assertIn('invalid timestamps', app.error[0].value)
