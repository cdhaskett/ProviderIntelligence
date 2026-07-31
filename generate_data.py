"""Generate the synthetic data used by the Streamlit portfolio app.

Run from the project folder:
    python generate_data.py

Optional custom output folder:
    python generate_data.py --output data_test
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42

CITY_CENTERS = [
    ("Indianapolis", "IN", 39.7684, -86.1581),
    ("Fort Wayne", "IN", 41.0793, -85.1394),
    ("South Bend", "IN", 41.6764, -86.2520),
    ("Evansville", "IN", 37.9716, -87.5711),
    ("Lafayette", "IN", 40.4167, -86.8753),
    ("Terre Haute", "IN", 39.4667, -87.4139),
    ("Cincinnati", "OH", 39.1031, -84.5120),
    ("Columbus", "OH", 39.9612, -82.9988),
    ("Dayton", "OH", 39.7589, -84.1916),
    ("Toledo", "OH", 41.6528, -83.5379),
    ("Cleveland", "OH", 41.4993, -81.6944),
    ("Louisville", "KY", 38.2527, -85.7585),
    ("Lexington", "KY", 38.0406, -84.5037),
    ("Chicago", "IL", 41.8781, -87.6298),
    ("Peoria", "IL", 40.6936, -89.5890),
    ("Springfield", "IL", 39.7817, -89.6501),
    ("Detroit", "MI", 42.3314, -83.0458),
    ("Grand Rapids", "MI", 42.9634, -85.6681),
    ("Lansing", "MI", 42.7325, -84.5555),
    ("Milwaukee", "WI", 43.0389, -87.9065),
]

# Representative downtown ZIP for each market, used to give every synthetic
# record a plausible ZIP and to power ZIP-code search.
CITY_ZIPS = {
    "Indianapolis": "46204",
    "Fort Wayne": "46802",
    "South Bend": "46601",
    "Evansville": "47708",
    "Lafayette": "47901",
    "Terre Haute": "47807",
    "Cincinnati": "45202",
    "Columbus": "43215",
    "Dayton": "45402",
    "Toledo": "43604",
    "Cleveland": "44113",
    "Louisville": "40202",
    "Lexington": "40507",
    "Chicago": "60601",
    "Peoria": "61602",
    "Springfield": "62701",
    "Detroit": "48226",
    "Grand Rapids": "49503",
    "Lansing": "48933",
    "Milwaukee": "53202",
}

SERVICES = [
    "Vactor / Jet Vac",
    "CCTV Inspection",
    "Pipe Lining",
    "Catch Basin Repair",
    "Pond Maintenance",
    "Erosion Control",
    "Stormwater Inspection",
    "Emergency Callout",
]

PREFIXES = [
    "Blue River", "Heartland", "Summit", "Clearwater", "Evergreen",
    "Midwest", "Premier", "Central", "Ironwood", "Northstar",
    "Red Oak", "Great Lakes", "Prairie", "Crossroads", "Keystone",
]

SUFFIXES = [
    "Environmental", "Infrastructure", "Utility Services", "Site Solutions",
    "Drainage Group", "Contracting", "Waterworks", "Field Services",
    "Restoration", "Municipal Services",
]

CLIENT_NAMES = [
    "Northline Retail", "Civic Square Properties", "Harbor Foods",
    "Maple Street Markets", "Atlas Distribution", "Juniper Health",
    "Pioneer Storage", "Brightway Pharmacy", "Unity Manufacturing",
    "Metro Office Partners", "Riverside Hospitality", "Oak & Main Retail",
]

BASE_COSTS = {
    "Vactor / Jet Vac": 3200,
    "CCTV Inspection": 1800,
    "Pipe Lining": 8500,
    "Catch Basin Repair": 4200,
    "Pond Maintenance": 6100,
    "Erosion Control": 5200,
    "Stormwater Inspection": 950,
    "Emergency Callout": 2700,
}


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return straight-line distance between two coordinates in miles."""
    radius = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def make_providers(rng: np.random.Generator, count: int = 300) -> pd.DataFrame:
    rows: list[dict] = []
    used_names: set[str] = set()

    for provider_number in range(1, count + 1):
        city, state, base_lat, base_lon = random.choice(CITY_CENTERS)
        latitude = base_lat + rng.normal(0, 0.28)
        longitude = base_lon + rng.normal(0, 0.32)

        base_name = f"{random.choice(PREFIXES)} {random.choice(SUFFIXES)}"
        name = base_name
        if name in used_names:
            name = f"{base_name} {provider_number}"
        used_names.add(name)

        service_count = random.choices(
            [1, 2, 3, 4], weights=[0.30, 0.40, 0.22, 0.08]
        )[0]
        provider_services = sorted(random.sample(SERVICES, service_count))
        capacity = random.randint(4, 24)
        active_jobs = min(
            capacity + random.randint(0, 4),
            max(0, int(rng.normal(capacity * 0.55, 3))),
        )

        rows.append(
            {
                "provider_id": f"P{provider_number:04d}",
                "provider_name": name,
                "city": city,
                "state": state,
                "zip_code": CITY_ZIPS[city],
                "latitude": round(float(latitude), 6),
                "longitude": round(float(longitude), 6),
                "services": " | ".join(provider_services),
                "capacity": capacity,
                "active_jobs": active_jobs,
                "utilization_pct": round(active_jobs / capacity * 100, 1),
                "rating": round(float(np.clip(rng.normal(4.2, 0.45), 2.5, 5.0)), 1),
                "average_response_hours": max(1, int(rng.normal(20, 11))),
                "agreement_status": random.choices(
                    ["Active", "Expiring Soon", "Pending", "Inactive"],
                    weights=[0.68, 0.14, 0.10, 0.08],
                )[0],
            }
        )

    return pd.DataFrame(rows)


def make_clients(rng: np.random.Generator, count: int = 75) -> pd.DataFrame:
    rows: list[dict] = []
    for location_number in range(1, count + 1):
        city, state, base_lat, base_lon = random.choice(CITY_CENTERS)
        rows.append(
            {
                "location_id": f"L{location_number:03d}",
                "client_name": random.choice(CLIENT_NAMES),
                "site_name": f"{city} Site {location_number:02d}",
                "city": city,
                "state": state,
                "zip_code": CITY_ZIPS[city],
                "latitude": round(float(base_lat + rng.normal(0, 0.18)), 6),
                "longitude": round(float(base_lon + rng.normal(0, 0.20)), 6),
                "priority_level": random.choices(
                    ["High", "Medium", "Standard"], weights=[0.22, 0.43, 0.35]
                )[0],
                "required_service": random.choice(SERVICES),
            }
        )
    return pd.DataFrame(rows)


def make_jobs(
    rng: np.random.Generator,
    providers: pd.DataFrame,
    clients: pd.DataFrame,
    count: int = 1000,
) -> pd.DataFrame:
    rows: list[dict] = []
    start_date = pd.Timestamp("2024-01-01")
    end_date = pd.Timestamp("2026-07-15")
    date_span = (end_date - start_date).days

    for job_number in range(1, count + 1):
        client = clients.sample(1, random_state=SEED + job_number).iloc[0]
        service = random.choice(SERVICES)

        eligible = providers[
            providers["services"].str.contains(service, regex=False)
        ].copy()
        eligible["distance_miles"] = eligible.apply(
            lambda row: haversine_miles(
                client["latitude"],
                client["longitude"],
                row["latitude"],
                row["longitude"],
            ),
            axis=1,
        )

        nearby = eligible[eligible["distance_miles"] <= 175]
        provider_pool = nearby if not nearby.empty and random.random() < 0.9 else eligible
        provider = provider_pool.sample(
            1, random_state=SEED * 1000 + job_number
        ).iloc[0]

        completion_date = start_date + pd.Timedelta(
            days=random.randint(0, date_span)
        )
        base_cost = BASE_COSTS[service]
        distance = float(provider["distance_miles"])

        rows.append(
            {
                "job_id": f"J{job_number:05d}",
                "provider_id": provider["provider_id"],
                "location_id": client["location_id"],
                "service": service,
                "completion_date": completion_date.date().isoformat(),
                "job_cost": round(
                    max(
                        350,
                        rng.normal(base_cost + distance * 7, base_cost * 0.22),
                    ),
                    2,
                ),
                "distance_miles": round(distance, 1),
                "response_hours": max(
                    1,
                    int(
                        rng.normal(
                            provider["average_response_hours"] + distance / 25,
                            6,
                        )
                    ),
                ),
                "days_to_complete": max(
                    1, int(rng.normal(4 + base_cost / 2500, 2.5))
                ),
                "quality_score": round(
                    float(np.clip(rng.normal(provider["rating"], 0.35), 1.0, 5.0)),
                    1,
                ),
                "job_status": random.choices(
                    ["Completed", "Completed", "Completed", "Cancelled", "Rework Required"],
                    weights=[0.45, 0.30, 0.15, 0.05, 0.05],
                )[0],
            }
        )

    return pd.DataFrame(rows)


def make_provider_services(providers: pd.DataFrame) -> pd.DataFrame:
    """Normalize the pipe-delimited `services` column into a bridge table.

    One row per (provider_id, service) pair — a proper many-to-many link that
    is far easier to join and filter than substring-matching a packed string.
    """
    rows: list[dict] = []
    for _, provider in providers.iterrows():
        for service in str(provider["services"]).split(" | "):
            service = service.strip()
            if service:
                rows.append(
                    {"provider_id": provider["provider_id"], "service": service}
                )
    return pd.DataFrame(rows).drop_duplicates().reset_index(drop=True)


def make_zip_centroids() -> pd.DataFrame:
    """Small ZIP -> lat/lon lookup for the markets in this dataset."""
    rows = [
        {
            "zip_code": CITY_ZIPS[city],
            "city": city,
            "state": state,
            "latitude": lat,
            "longitude": lon,
        }
        for city, state, lat, lon in CITY_CENTERS
    ]
    return pd.DataFrame(rows).drop_duplicates("zip_code").reset_index(drop=True)


def generate_data(output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate and save all synthetic tables."""
    random.seed(SEED)
    rng = np.random.default_rng(SEED)
    output_dir.mkdir(parents=True, exist_ok=True)

    providers = make_providers(rng)
    clients = make_clients(rng)
    jobs = make_jobs(rng, providers, clients)
    provider_services = make_provider_services(providers)
    zip_centroids = make_zip_centroids()

    providers.to_csv(output_dir / "providers.csv", index=False)
    clients.to_csv(output_dir / "client_locations.csv", index=False)
    jobs.to_csv(output_dir / "completed_jobs.csv", index=False)
    provider_services.to_csv(output_dir / "provider_services.csv", index=False)
    zip_centroids.to_csv(output_dir / "zip_centroids.csv", index=False)
    return providers, clients, jobs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "data",
        help="Folder where the CSV files will be written.",
    )
    args = parser.parse_args()

    providers, clients, jobs = generate_data(args.output)
    print(f"Created {len(providers):,} providers")
    print(f"Created {len(clients):,} client locations")
    print(f"Created {len(jobs):,} jobs")
    print("Also wrote provider_services.csv (bridge table) and zip_centroids.csv")
    print(f"Saved files to {args.output.resolve()}")


if __name__ == "__main__":
    main()
