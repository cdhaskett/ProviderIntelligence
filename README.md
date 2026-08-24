# Provider Coverage Intelligence

A portfolio project that turns field-service provider data into an interactive decision-support tool. Built with **Python, Streamlit, pandas, and Plotly**, the app helps users find qualified providers, identify geographic coverage gaps, and evaluate historical provider performance.

All providers, clients, jobs, locations, and performance metrics are **fully synthetic**. No employer, customer, or confidential operational data is included.

## Business problem

Field-service teams often need to answer several questions at once:

- Which providers perform the required service?
- Which are close enough to the client location?
- Do they have available capacity?
- Are their agreements active?
- How have they performed historically?
- Where does the provider network have thin or missing coverage?

This project combines those questions into one interactive workflow rather than relying on separate spreadsheets, maps, and manual lookups.

## What the app does

### Provider Finder
Search from a client site or ZIP code, then filter providers by service, rating, agreement status, search radius, and estimated drive time. Qualified providers are ranked using a transparent recommendation score that considers:

- historical rating
- spare capacity
- proximity
- average response time

Results are displayed on an interactive map and can be exported to CSV.

### Coverage Gaps
Evaluate a service category against a chosen coverage radius and classify client locations as:

- **Critical gap** — no qualified providers in range
- **Thin coverage** — one or two providers in range
- **Adequate** — three or more providers in range

### Performance Overview
Summarize completed-job history by provider, including job volume, completed job value, response time, completion speed, and quality scores.

## Technical highlights

- **Normalized many-to-many data model:** provider service capabilities are stored in a `provider_services` bridge table rather than relying on substring matching.
- **Geospatial analysis:** provider proximity is calculated with the Haversine formula.
- **Transparent drive-time estimate:** straight-line distance is adjusted with a road-circuity factor and divided by an assumed average speed.
- **Explainable ranking:** recommendation weights are documented in code rather than hidden in a black-box model.
- **Synthetic data generation:** reproducible scripts create 300 providers, 75 client locations, 1,000 jobs, eight service categories, and ZIP centroids across Midwestern markets.
- **Data-quality workflow:** a separate script deliberately introduces realistic data problems, and a pandas notebook cleans and validates them.
- **Automated tests:** core distance, drive-time, scoring, coverage, and ZIP functions are covered with pytest and run through GitHub Actions.

## Recommendation logic

The core analytical functions live in `provider_intel.py`, separate from the Streamlit UI so they can be tested independently.

The recommendation score blends:

```text
rating × 16
+ spare-capacity score × 0.25
+ proximity score (0–20)
− average response hours × 0.10
```

The weighting intentionally favors provider quality while still accounting for availability, distance, and responsiveness.

## Project structure

```text
ProviderIntelligence/
├── .github/workflows/tests.yml    # Automated pytest workflow
├── app.py                         # Streamlit application
├── provider_intel.py              # Core distance, scoring, and ZIP logic
├── generate_data.py               # Reproducible synthetic data generator
├── make_dirty_data.py             # Creates deliberately messy provider data
├── DATA_DICTIONARY.md             # Field definitions
├── requirements.txt               # Runtime dependencies
├── requirements-dev.txt           # Test/notebook dependencies
├── data/
│   ├── providers.csv
│   ├── client_locations.csv
│   ├── completed_jobs.csv
│   ├── provider_services.csv
│   ├── providers_clean.csv
│   └── zip_centroids.csv
├── notebooks/
│   └── cleaning.ipynb             # Profiling, cleaning, validation, export
└── tests/
    └── test_provider_intel.py     # Unit tests for core analytical logic
```

`data_raw/providers_dirty.csv` is generated locally by `make_dirty_data.py` and is intentionally not required for the running application.

## Data cleaning demo

Operational data rarely arrives analysis-ready. `make_dirty_data.py` injects issues such as inconsistent casing, extra whitespace, mixed service delimiters, text-formatted ratings, percentage strings, malformed ZIP codes, missing coordinates, and duplicates.

Run:

```bash
python make_dirty_data.py
jupyter notebook notebooks/cleaning.ipynb
```

The notebook profiles the problems, standardizes fields, repairs data types, removes unusable records, validates the result with assertions, and writes an analysis-ready provider table.

## Tests

Install the development dependencies and run:

```bash
pip install -r requirements-dev.txt
pytest -q
```

The same test suite also runs automatically through GitHub Actions.

## Run the app locally

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## A note on drive time

Drive time is an intentionally transparent **estimate**, not live routing. Straight-line distance is multiplied by a road-circuity factor (default `1.30`) and divided by an assumed average travel speed. A production implementation could replace this calculation with OSRM, OpenRouteService, Google Directions, or another routing service.

## Data

The repository uses fully synthetic data created specifically for this portfolio project. The dataset is designed to resemble realistic field-service operations without exposing any real company, provider, customer, work-order, or performance information.
