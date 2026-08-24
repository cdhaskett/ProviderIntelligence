import math

import pytest

import provider_intel as pi


def test_haversine_same_point_is_zero():
    assert pi.haversine_miles(39.7684, -86.1581, 39.7684, -86.1581) == pytest.approx(0.0)


def test_haversine_indianapolis_to_chicago_is_reasonable():
    distance = pi.haversine_miles(39.7684, -86.1581, 41.8781, -87.6298)
    assert 160 < distance < 175


def test_estimate_road_miles_uses_circuity_factor():
    assert pi.estimate_road_miles(100, circuity_factor=1.3) == pytest.approx(130.0)


def test_estimate_road_miles_rejects_negative_distance():
    with pytest.raises(ValueError):
        pi.estimate_road_miles(-1)


def test_estimate_drive_time_minutes():
    # 100 straight-line miles * 1.3 road factor / 65 mph = 120 minutes.
    assert pi.estimate_drive_time_minutes(100, avg_mph=65, circuity_factor=1.3) == pytest.approx(120.0)


def test_estimate_drive_time_rejects_nonpositive_speed():
    with pytest.raises(ValueError):
        pi.estimate_drive_time_minutes(10, avg_mph=0)


def test_availability_score_rewards_spare_capacity():
    assert pi.availability_score(25) == pytest.approx(75.0)
    assert pi.availability_score(120) == pytest.approx(0.0)


def test_proximity_score_declines_with_distance():
    assert pi.proximity_score(0, 100) == pytest.approx(20.0)
    assert pi.proximity_score(50, 100) == pytest.approx(10.0)
    assert pi.proximity_score(100, 100) == pytest.approx(0.0)


def test_recommendation_score_favors_better_provider():
    strong = pi.recommendation_score(
        rating=4.8,
        utilization_pct=35,
        distance_miles=20,
        radius_miles=100,
        average_response_hours=8,
    )
    weak = pi.recommendation_score(
        rating=3.6,
        utilization_pct=85,
        distance_miles=85,
        radius_miles=100,
        average_response_hours=36,
    )
    assert strong > weak


def test_coverage_status_thresholds():
    assert pi.coverage_status(0) == "Critical gap"
    assert pi.coverage_status(1) == "Thin coverage"
    assert pi.coverage_status(2) == "Thin coverage"
    assert pi.coverage_status(3) == "Adequate"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("46204", "46204"),
        (46204, "46204"),
        (" 46204-1234 ", "46204"),
        ("1234", "01234"),
        (None, ""),
        ("not-a-zip", ""),
    ],
)
def test_normalize_zip(raw, expected):
    assert pi.normalize_zip(raw) == expected


def test_resolve_zip_centroid_finds_normalized_zip():
    centroids = [
        {"zip_code": "46204", "latitude": 39.7684, "longitude": -86.1581},
        {"zip_code": "60601", "latitude": 41.8853, "longitude": -87.6229},
    ]
    result = pi.resolve_zip_centroid("46204-9999", centroids)
    assert result == pytest.approx((39.7684, -86.1581))


def test_resolve_zip_centroid_returns_none_when_missing():
    centroids = [{"zip_code": "46204", "latitude": 39.7684, "longitude": -86.1581}]
    assert pi.resolve_zip_centroid("99999", centroids) is None
