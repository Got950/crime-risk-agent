from typing import Dict, Any, Tuple


def compute_overall_score(
    dim: Dict[str, int],
    crime_data: Dict[str, Any],
    geo_data: Dict[str, Any]
) -> Tuple[float, float]:
    """
    Combine all risk dimensions into a single overall scor.
    
    Returns (overall_score, confidence) tuple.
    """
    # Weighted combination - crime risk is most important (35%)
    # Use .get() to handle missing keys gracefully
    score = (
        dim.get("crime_risk", 0) * 0.35 +
        dim.get("property_exposure_risk", 0) * 0.25 +
        dim.get("accessibility_risk", 0) * 0.15 +
        dim.get("neighborhood_risk", 0) * 0.15 +
        dim.get("operational_risk", 0) * 0.10
    )
    score = round(score, 2)
    score = max(0.0, min(100.0, score))  # Keep it between 0 and 100

    # Confidence depends on whether we used real APIs or simulated data
    crime_source = crime_data.get("source", "simulated")
    geo_source = geo_data.get("source", "simulated")

    if crime_source != "simulated" and geo_source != "simulated":
        confidence = 1.0  # Both real
    elif crime_source == "simulated" and geo_source != "simulated":
        confidence = 0.7  # One real
    else:
        confidence = 0.5  # Both simulated

    return score, confidence


