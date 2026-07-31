"""Core domain logic for Provider Coverage Intelligence.

These functions are deliberately kept free of Streamlit / pandas so they are
pure, fast, and easy to unit-test. The Streamlit app and the test-suite both
import from here, so the behaviour shown in the UI is exactly what is tested.
"""

from __future__ import annotations

import math

EARTH_RADIUS_MILES = 3958.8

# Tuning constants for the drive-time estimate. Straight-line (haversine)
# distance is scaled by a "circuity factor" to approximate real road distance,
# then divided by an average travel speed. These are documented estimates, not
# a live routing service — see estimate_drive_time_minutes().
DEFAULT_CIRCUITY_FACTOR = 1.30
DEFAULT_AVG_MPH = 45.0


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points, in miles."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    )
    return EARTH_RADIUS_MILES * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def estimate_road_miles(
    straight_line_miles: float, circuity_factor: float = DEFAULT_CIRCUITY_FACTOR
) -> float:
    """Approximate driving distance from straight-line distance.

    Real roads are longer than a straight line; the circuity factor (~1.3 for
    typical US regional travel) scales the haversine distance up accordingly.
    """
    if straight_line_miles < 0:
        raise ValueError("straight_line_miles cannot be negative")
    if circuity_factor <= 0:
        raise ValueError("circuity_factor must be positive")
    return straight_line_miles * circuity_factor


def estimate_drive_time_minutes(
    straight_line_miles: float,
    avg_mph: float = DEFAULT_AVG_MPH,
    circuity_factor: float = DEFAULT_CIRCUITY_FACTOR,
) -> float:
    """Estimate drive time (minutes) from straight-line distance.

    This is a transparent estimate, not a live routing API: road distance is
    approximated as haversine * circuity_factor, then divided by an average
    speed. Swap in an OSRM/Google Directions call here for true routing.
    """
    if avg_mph <= 0:
        raise ValueError("avg_mph must be positive")
    road_miles = estimate_road_miles(straight_line_miles, circuity_factor)
    return road_miles / avg_mph * 60.0


def availability_score(utilization_pct: float) -> float:
    """Higher when a provider has more spare capacity (0-100)."""
    return max(0.0, 100.0 - utilization_pct)


def proximity_score(distance_miles: float, radius_miles: float) -> float:
    """0-20 points, full marks at the origin, 0 at/over the search radius."""
    if radius_miles <= 0:
        return 0.0
    return max(0.0, radius_miles - distance_miles) / radius_miles * 20.0


def recommendation_score(
    rating: float,
    utilization_pct: float,
    distance_miles: float,
    radius_miles: float,
    average_response_hours: float,
) -> float:
    """Blend rating, spare capacity, proximity, and responsiveness into a score.

    Weighting (higher is better):
      * rating              x16   (quality is the dominant factor)
      * availability        x0.25 (spare capacity)
      * proximity           0-20  (closer is better, relative to the radius)
      * response hours      -0.10 (slower response subtracts)
    """
    score = (
        rating * 16.0
        + availability_score(utilization_pct) * 0.25
        + proximity_score(distance_miles, radius_miles)
        - average_response_hours * 0.10
    )
    return round(score, 1)


def coverage_status(providers_in_radius: int) -> str:
    """Label a client location's coverage given how many providers are in range."""
    if providers_in_radius <= 0:
        return "Critical gap"
    if providers_in_radius <= 2:
        return "Thin coverage"
    return "Adequate"


def normalize_zip(zip_code) -> str:
    """Normalize a ZIP to a 5-character string ('46204'); '' if unusable."""
    if zip_code is None:
        return ""
    digits = "".join(ch for ch in str(zip_code).strip() if ch.isdigit())
    if not digits:
        return ""
    return digits[:5].zfill(5)


def resolve_zip_centroid(zip_code, centroids):
    """Return (lat, lon) for a ZIP from a centroids table, or None.

    `centroids` is any iterable of mappings with 'zip_code', 'latitude',
    'longitude' keys (e.g. a list of dicts or DataFrame.to_dict('records')).
    """
    target = normalize_zip(zip_code)
    if not target:
        return None
    for row in centroids:
        if normalize_zip(row["zip_code"]) == target:
            return (float(row["latitude"]), float(row["longitude"]))
    return None
