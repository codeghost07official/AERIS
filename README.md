# AERIS
AERIS (Aerospace Equipment &amp; Reliability Intelligence System) is a Python web application for spacecraft telemetry anomaly detection and space image analysis using real NASA datasets (SMAP/MSL), scikit-learn, Neon PostgreSQL, and a clean, responsive interface.

## Run locally

Use Python 3.12, then install the pinned dependencies:

```powershell
python -m pip install -r requirements.txt
python run.py
```

Set `DATABASE_URL` and `SECRET_KEY` in `.env`. Set `GOOGLE_CLIENT_ID` and
`GOOGLE_CLIENT_SECRET` as well to enable Google sign-in.

## Tests

Run the database schema regression tests with:

```powershell
python -m unittest discover -s tests -v
```
