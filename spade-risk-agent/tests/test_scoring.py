from core.scoring_engine import (
    crime_risk_score,
    property_exposure_risk_score,
    accessibility_risk_score,
    neighborhood_risk_score,
    operational_risk_score,
)
from core.aggregation import aggregate_scores


def test_crime_risk_score_basic():
    data = {"violent_crime_index": 50, "property_crime_index": 40, "recent_incidents": 10}
    score = crime_risk_score(data)
    expected = 50 * 0.6 + 40 * 0.3 + 10 * 3
    assert score == expected


def test_property_exposure_risk_score():
    assert property_exposure_risk_score(25, fenced=False, gated=False) == 25 + 10 + 10
    assert property_exposure_risk_score(25, fenced=True, gated=True) == 25 - 5 - 5


def test_accessibility_risk_score():
    assert accessibility_risk_score("urban", fenced=False) == 70
    assert accessibility_risk_score("suburban", fenced=True) == 35


def test_neighborhood_risk_score_caps():
    score = neighborhood_risk_score(20000, ["nightclub", "warehouse", "school"])
    assert score <= 100.0


def test_operational_risk_score():
    score = operational_risk_score("24/7", "previous theft in the area")
    assert score == 20 + 30 + 20


def test_aggregate_scores_and_confidence():
    overall, conf = aggregate_scores(
        crime_risk=50,
        property_exposure_risk=40,
        accessibility_risk=30,
        neighborhood_risk=20,
        operational_risk=10,
        crime_used_fallback=False,
        geo_used_fallback=False,
    )
    assert overall == round(50 * 0.35 + 40 * 0.25 + 30 * 0.15 + 20 * 0.15 + 10 * 0.10, 2)
    assert conf == 1.0


