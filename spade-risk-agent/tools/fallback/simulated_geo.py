import random


def simulate_geo():
    """
    Generate simulated geolocation data with coordinates.
    Always includes latitude and longitude for map display.
    """
    neighborhood = random.choice(["urban", "suburban", "rural"])
    density_map = {"urban": 8000, "suburban": 3000, "rural": 500}
    risks_map = {
        "urban": ["nightclub", "warehouse", "school"],
        "suburban": ["school"],
        "rural": []
    }
    
    # Generate realistic US coordinates based on neighborhood type
    if neighborhood == "urban":
        # Major US cities (NYC, LA, Chicago, etc.)
        latitude = random.uniform(40.0, 41.0)  # NYC area
        longitude = random.uniform(-74.0, -73.0)  # NYC area
    elif neighborhood == "suburban":
        # Suburban areas
        latitude = random.uniform(38.0, 42.0)
        longitude = random.uniform(-75.0, -70.0)
    else:  # rural
        # Rural areas
        latitude = random.uniform(35.0, 45.0)
        longitude = random.uniform(-85.0, -70.0)
    
    return {
        "latitude": latitude,
        "longitude": longitude,
        "neighborhood_type": neighborhood,
        "population_density": density_map[neighborhood],
        "nearby_risks": risks_map[neighborhood],
        "source": "simulated",
        "formatted_address": f"Simulated {neighborhood} location"
    }


