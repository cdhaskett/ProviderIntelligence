# Provider Coverage Intelligence

An interactive **Streamlit + Plotly** portfolio project that helps a fictional
field-service company find qualified providers, evaluate geographic coverage,
and review historical performance — powered entirely by synthetic data.

![Demo](assets/demo.gif)

> The images in `assets/` are generated from the project's real data and logic.
> For full-UI screenshots, capture them from the deployed app (see
> [Deploy to Streamlit Community Cloud](#deploy-to-streamlit-community-cloud)).

| Provider network | Coverage gaps | Performance |
|---|---|---|
| ![map](assets/preview_map.png) | ![gaps](assets/preview_gaps.png) | ![performance](assets/preview_performance.png) |

## Features

- **Search by client location _or_ ZIP code** — pick a client site or type any
  ZIP; the app resolves it to coordinates and searches around it.
- **Distance + drive-time** — straight-line distance via the Haversine formula,
  plus an estimated **drive time** (road distance ÷ average speed) with a
  max-drive-time filter and an assumed-speed control.
- **Provider ranking** — a transparent recommendation score blending rating,
  spare capacity, proximity, and responsiveness.
- **Normalized service filtering** — a proper `provider_services` bridge table
  drives the service filter instead of substring matching.
- **Coverage-gap analysis** — flags client locations with thin or no coverage
  for a given service and radius.
- **Performance overview** — completed-job value, quality, speed, and volume.
- **CSV export** of the ranked recommendations.

## Project structure

```text
ProviderIntelligence/
├── app.py                     # Streamlit app (3 tabs)
├── provider_intel.py          # Pure, tested core logic (distance, drive-time, scoring)
├── generate_data.py           # Builds the clean synthetic tables + bridge/centroid tables
├── make_dirty_data.py         # Injects realistic mess into a copy of the data
├── requirements.txt           # Runtime dependencies
├── requirements-dev.txt       # Test / notebook dependencies
├── DATA_DICTIONARY.md
├── README.md
├── .gitignore
├── data/
│   ├── providers.csv
│   ├── client_locations.csv
│   ├── completed_jobs.csv
│   ├── provider_services.csv  # NEW: many-to-many bridge table
│   └── zip_centroids.csv      # NEW: ZIP -> lat/lon lookup for the markets
├── data_raw/
│   └── providers_dirty.csv    # deliberately messy input for the cleaning demo
├── notebooks/
│   └── cleaning.ipynb         # profiles + cleans the dirty data
├── tests/
│   └── test_provider_intel.py # pytest suite (distance + scoring)
└── assets/                    # preview images + demo GIF
```

## Core logic is unit-tested

Distance, drive-time, and scoring live in `provider_intel.py` — pure functions
with no Streamlit/pandas dependency, so the exact behaviour shown in the app is
what the tests cover.

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Data cleaning demo

Real operational data is messy. `make_dirty_data.py` injects that mess
(inconsistent casing, stray whitespace, mixed delimiters, `"4.1 stars"` ratings,
`"43.8%"` utilization, malformed ZIPs, missing values, duplicate rows), and
`notebooks/cleaning.ipynb` profiles every issue, fixes it step by step, validates
the result, and writes a clean, analysis-ready table.

```bash
python make_dirty_data.py           # -> data_raw/providers_dirty.csv
jupyter notebook notebooks/cleaning.ipynb
```

## Run the app locally

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Windows PowerShell
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Regenerate the data

```bash
python generate_data.py     # writes all 5 CSVs into data/
```

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (files must include `app.py`, `provider_intel.py`,
   `requirements.txt`, and the `data/` folder).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. **Create app → Deploy from GitHub**, set **Main file path** to `app.py`, deploy.
4. You'll get a permanent URL like `cdhaskett-providerintelligence.streamlit.app`.

To capture true full-UI screenshots and a GIF, open the deployed app and use a
screen-recorder / screenshot tool on each tab, then drop them into `assets/`.

## A note on drive-time

Drive time is a transparent **estimate** — straight-line distance is scaled by a
road-circuity factor (~1.3) and divided by an average speed. For true routing,
swap `estimate_drive_time_minutes()` in `provider_intel.py` for a call to a
routing service (OSRM, OpenRouteService, or Google Directions).

## Portfolio talking points

> Built an interactive Python app (Streamlit, pandas, Plotly) that searches
> field-service providers by ZIP or client site, estimates drive time, and ranks
> recommendations by rating, capacity, proximity, and responsiveness.

> Modeled a normalized provider-service bridge table, engineered a deliberately
> dirty dataset with a documented pandas cleaning pipeline, and unit-tested the
> distance and scoring logic with pytest.

## Data

Fully synthetic: 300 providers, 75 client locations, 1,000 jobs, 8 service
categories across Indiana and nearby Midwestern states. No employer, client, or
confidential operational data is included.
