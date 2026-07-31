# Provider Coverage Intelligence

An interactive Streamlit and Plotly portfolio project that helps a fictional field-service company identify qualified providers, evaluate geographic coverage, and review historical performance.

## Live project features

- Search for providers by client location, service, distance, rating, and agreement status
- Calculate provider-to-client distance with the Haversine formula
- Rank providers using distance, availability, rating, and response time
- Display results on an interactive Plotly map
- Identify client locations with inadequate service coverage
- Review completed-job value, quality, speed, and provider volume
- Download filtered provider recommendations as CSV

## Project structure

```text
provider-coverage-intelligence/
├── app.py
├── generate_data.py
├── requirements.txt
├── README.md
├── .gitignore
└── data/
    ├── providers.csv
    ├── client_locations.csv
    └── completed_jobs.csv
```

## Data

This repository uses fully synthetic data:

- 300 fictional providers
- 75 fictional client locations
- 1,000 fictional service jobs
- 8 service categories across Indiana and nearby Midwestern states

No employer, client, provider, or confidential operational data is included.

## Run the app locally

1. Open a terminal in the project folder.
2. Create and activate a virtual environment.
3. Install the required packages.
4. Start Streamlit.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will open the app in your browser.

## Suggested GitHub workflow

```bash
git init
git add .
git commit -m "Create provider coverage Streamlit MVP"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

For the next feature:

```bash
git checkout -b feature/improve-provider-scoring
```

Make the change, commit it, push the branch, and open a pull request on GitHub.

## Portfolio talking points

> Developed an interactive Python application using Streamlit, pandas, and Plotly to identify qualified field-service providers, calculate geographic coverage, and rank recommendations using capacity, rating, response time, and distance.

> Created a reproducible synthetic dataset to demonstrate a real operational use case without exposing confidential employer or customer information.

## Good next improvements

- Add ZIP-code search
- Add drive-time routing
- Add a provider-service bridge table
- Add deliberate dirty data and a cleaning notebook
- Add unit tests for distance and scoring functions
- Deploy through Streamlit Community Cloud
- Add screenshots and a short demonstration GIF
