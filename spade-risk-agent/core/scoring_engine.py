from typing import Dict, Any, Optional


def compute_risk_dimensions(
    crime: Dict[str, Any],
    geo: Dict[str, Any],
    prop: Dict[str, Any],
    property_type: str,
    fenced: bool,
    gated: bool,
    hours: Optional[str],
    notes: Optional[str]
) -> Dict[str, int]:
    """
    Calculate risk scores across 5 dimensions.
    
    Returns scores 0-100 for each dimension plus summaries.
    """
    # Cache lowercase property type to avoid repeated calls
    property_type_lower = property_type.lower()
    
    # Crime risk calculation
    violent = crime.get("violent_crime_index", 0)
    prop_crime = crime.get("property_crime_index", 0)
    recent = crime.get("recent_incidents", 0)

    # Recent incidents matter more (multiplier of 3) - cap at 100
    crime_risk = min(
        violent * 0.6 + prop_crime * 0.3 + recent * 3,
        100
    )

    # Property exposure risk
    exposure = prop.get("base_exposure", 30)
    exposure += 10 if not fenced else -5
    exposure += 10 if not gated else -5
    
    # Property type makes a big difference
    if property_type_lower == "vacation home":
        exposure += 15  # Empty most of the time = higher risk
    elif property_type_lower == "home":
        exposure -= 5  # People around = natural deterrence
    
    property_exposure_risk = min(max(exposure, 0), 100)

    # Accessibility risk - how easy is it to get in?
    neighborhood_type = geo.get("neighborhood_type", "suburban")
    accessibility_risk = 60 if neighborhood_type == "urban" else 40
    accessibility_risk += 10 if not fenced else -5
    
    # Vacation homes aren't watched as much
    if property_type_lower == "vacation home":
        accessibility_risk += 12
    elif property_type_lower == "home":
        accessibility_risk -= 3  # Regular presence = less accessible
    
    accessibility_risk = min(max(accessibility_risk, 0), 100)

    # Neighborhood risk
    population_density = geo.get("population_density", 3000)
    nearby_risks = geo.get("nearby_risks", [])
    neighborhood_risk = population_density / 100.0
    
    # Convert to lowercase once for case-insensitive matching
    risks_lower = {r.lower() if isinstance(r, str) else str(r).lower() for r in nearby_risks}
    
    if "nightclub" in risks_lower:
        neighborhood_risk += 20
    if "warehouse" in risks_lower:
        neighborhood_risk += 15
    if "school" in risks_lower:
        neighborhood_risk += 5
    neighborhood_risk = min(max(neighborhood_risk, 0), 100)

    # Operational risk
    operational = 20.0
    
    # Vacation homes are a bigger target
    if property_type_lower == "vacation home":
        operational += 25  # Extended unoccupied periods
        operational += 10  # Predictable absence patterns
    elif property_type_lower == "home":
        operational -= 5  # Regular occupancy helps
    
    # 24/7 operations = more exposure time
    if hours and "24" in str(hours):
        operational += 30
    # Check user notes for theft mentions
    if notes and "theft" in str(notes).lower():
        operational += 20
    
    operational_risk = min(max(operational, 0), 100)

    # Generate short summaries for each dimension
    summaries = {
        "crime_risk": _get_crime_summary(crime_risk, violent, prop_crime, recent),
        "property_exposure_risk": _get_property_exposure_summary(property_exposure_risk, property_type, fenced, gated),
        "accessibility_risk": _get_accessibility_summary(accessibility_risk, property_type, neighborhood_type, fenced),
        "neighborhood_risk": _get_neighborhood_summary(neighborhood_risk, population_density, nearby_risks),
        "operational_risk": _get_operational_summary(operational_risk, property_type, hours, notes)
    }

    return {
        "crime_risk": int(round(crime_risk)),
        "property_exposure_risk": int(round(property_exposure_risk)),
        "accessibility_risk": int(round(accessibility_risk)),
        "neighborhood_risk": int(round(neighborhood_risk)),
        "operational_risk": int(round(operational_risk)),
        "summaries": summaries
    }


def _get_crime_summary(score: float, violent: int, prop_crime: int, recent: int) -> str:
    """Human-readable crime risk summary"""
    if score >= 70:
        return f"High crime area with {violent} violent and {prop_crime} property crime indices. {recent} recent incidents reported."
    elif score >= 40:
        return f"Moderate crime levels. {violent} violent crime index, {prop_crime} property crime index, {recent} recent incidents."
    else:
        return f"Relatively low crime area. {violent} violent crime index, {prop_crime} property crime index, {recent} recent incidents."


def _get_property_exposure_summary(score: float, property_type: str, fenced: bool, gated: bool) -> str:
    """Summary of how exposed the property is"""
    security_features = []
    if fenced:
        security_features.append("fenced")
    if gated:
        security_features.append("gated")
    
    property_type_lower = property_type.lower()
    property_context = ""
    if property_type_lower == "vacation home":
        property_context = " Vacation homes face higher exposure risk due to extended unoccupied periods."
    elif property_type_lower == "home":
        property_context = " Primary residence benefits from regular occupancy providing natural deterrence."
    
    if not security_features:
        return f"Property lacks perimeter security (no fencing or gating), increasing exposure risk.{property_context}"
    elif len(security_features) == 1:
        return f"Property has {security_features[0]} perimeter, providing moderate protection.{property_context}"
    else:
        return f"Property has both fencing and gating, providing strong perimeter security.{property_context}"


def _get_accessibility_summary(score: float, property_type: str, neighborhood_type: str, fenced: bool) -> str:
    """Summary of how accessible the property is to unauthorized entry"""
    base_desc = f"{neighborhood_type.capitalize()} area"
    
    property_type_lower = property_type.lower()
    property_note = ""
    if property_type_lower == "vacation home":
        property_note = " Vacation homes face higher accessibility risk due to less frequent monitoring."
    elif property_type_lower == "home":
        property_note = " Primary residence benefits from regular presence providing natural monitoring."
    
    if fenced:
        return f"{base_desc} with fencing reduces unauthorized access risk.{property_note}"
    else:
        return f"{base_desc} without fencing increases accessibility risk for potential threats.{property_note}"


def _get_neighborhood_summary(score: float, density: int, risks: list) -> str:
    """Summary of neighborhood-level risk factors"""
    # Pre-compute lowercase set for efficient lookups
    risks_lower = {r.lower() if isinstance(r, str) else str(r).lower() for r in risks}
    
    risk_items = []
    if "nightclub" in risks_lower:
        risk_items.append("nightlife")
    if "warehouse" in risks_lower:
        risk_items.append("industrial activity")
    if "school" in risks_lower:
        risk_items.append("school zone")
    
    density_desc = "high" if density > 5000 else "moderate" if density > 2000 else "low"
    
    if risk_items:
        return f"{density_desc.capitalize()} density area ({density}/sq mi) with nearby {', '.join(risk_items)}."
    else:
        return f"{density_desc.capitalize()} population density ({density}/sq mi) with minimal nearby risk factors."


def _get_operational_summary(score: float, property_type: str, hours: str, notes: str) -> str:
    """Summary of operational risk factors"""
    factors = []
    
    property_type_lower = property_type.lower()
    if property_type_lower == "vacation home":
        factors.append("extended unoccupied periods")
        factors.append("predictable absence patterns")
    elif property_type_lower == "home":
        factors.append("regular occupancy provides deterrence")
    
    if hours and "24" in str(hours):
        factors.append("24/7 operation")
    if notes and "theft" in str(notes).lower():
        factors.append("recent theft incidents")
    
    if factors:
        return f"Operational risk factors: {', '.join(factors)}."
    else:
        return "Standard operational risk with no significant concerns identified."


