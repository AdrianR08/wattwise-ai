# Automatic location weather

The app defaults to Miami, Florida for this entry-level demonstration; no city search is required. It sends only the default coordinates and requested date to Open-Meteo, not consumption records. Weather is cached for one hour. Miami is an assumption, not a verified location for an uploaded building.

The next-hour model requires weather from the preceding elapsed hour. Files older than seven days use the Historical Weather API; recent files use the Forecast API's recent model estimates. UTC timestamp matching prevents DST shifts. Celsius and metres per second match the model inputs. Missing hours or service failures retain consumption-only forecasting. Future-dated file readings are not supplied with later weather.

Historical API data is reanalysis, not an observation available at forecast time. Recent model data is not an on-site measurement. Neither should be used to claim leakage-free operational backtest results. The trained model's BDG2 weather comparison does not validate its performance with Open-Meteo inputs. Archived, issue-time forecasts and independent evaluation are needed for such claims.

The bundled anonymized BDG2 office sample retains its known original weather match; a customer-entered city does not replace its matched site. Manual site controls are hidden to keep the demonstration simple.

The public API needs no key for this student/noncommercial demonstration. Commercial deployment must review Open-Meteo's current service terms and pricing. Attribution appears in the app.

Documentation: [Geocoding](https://open-meteo.com/en/docs/geocoding-api), [Historical Weather](https://open-meteo.com/en/docs/historical-weather-api), [Forecast](https://open-meteo.com/en/docs), [Pricing and terms](https://open-meteo.com/en/pricing).
