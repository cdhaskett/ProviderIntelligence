# Data Dictionary

## providers.csv

| Field | Description |
|---|---|
| provider_id | Synthetic provider identifier |
| provider_name | Fictional provider company name |
| city / state | Approximate operating market |
| latitude / longitude | Synthetic point near the listed market |
| services | Pipe-delimited service capabilities |
| capacity | Estimated concurrent job capacity |
| active_jobs | Current synthetic workload |
| utilization_pct | Active jobs divided by capacity |
| rating | Synthetic historical performance rating |
| average_response_hours | Typical response time |
| agreement_status | Active, expiring, pending, or inactive |

## client_locations.csv

| Field | Description |
|---|---|
| location_id | Synthetic client-site identifier |
| client_name | Fictional customer organization |
| site_name | Fictional site label |
| city / state | Approximate client market |
| latitude / longitude | Synthetic client location |
| priority_level | High, medium, or standard |
| required_service | Default service need |

## completed_jobs.csv

| Field | Description |
|---|---|
| job_id | Synthetic job identifier |
| provider_id | Assigned provider |
| location_id | Client site |
| service | Work category |
| completion_date | Synthetic job date |
| job_cost | Synthetic job value |
| distance_miles | Straight-line assignment distance |
| response_hours | Time to respond |
| days_to_complete | Duration |
| quality_score | Synthetic quality rating |
| job_status | Completed, cancelled, or rework required |
