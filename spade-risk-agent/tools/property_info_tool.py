def get_property_info(property_type: str):
    """
    Get exposure risk for different property types.
    
    Property types have different base risk levels because of how they're used.
    """
    mapping = {
        "home": 25,  # Primary residence - people around = lower base risk
        "rental": 35,  # Rental - moderate, depends on tenant
        "vacation home": 45,  # Empty most of the time = higher risk
        "business": 50  # Commercial - highest base risk
    }
    return {"base_exposure": mapping.get(property_type.lower(), 30)}


