import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from experiments.compare_monthly_weather import weather_examples
from src.monthly_weather import WEATHER_FEATURES


class RollingWeatherTests(unittest.TestCase):
    def test_future_weather_cannot_change_monthly_features(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'data/bdg2/processed'
            folder.mkdir(parents=True)
            pd.DataFrame([dict(building_id='office', site_id='Panther', timezone='UTC')]).to_csv(folder / 'buildings_info.csv', index=False)
            times = pd.date_range('2016-01-01', '2017-02-01', freq='h', inclusive='left', tz='UTC')
            weather = pd.DataFrame(dict(airTemperature=10.), index=times)
            example = pd.DataFrame([dict(building_id='office', month='2017-01')])
            with patch('experiments.compare_monthly_weather.ROOT', root), patch('experiments.compare_monthly_weather.examples', return_value=example):
                with patch('experiments.compare_monthly_weather.site_weather', return_value=weather):
                    before = weather_examples()
                    weather.loc['2017-01-01':, 'airTemperature'] = 100.
                    after = weather_examples()
            np.testing.assert_allclose(before[WEATHER_FEATURES], after[WEATHER_FEATURES])
