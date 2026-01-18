import random


def simulate_crime():
    return {
        "violent_crime_index": random.randint(20, 80),
        "property_crime_index": random.randint(15, 70),
        "recent_incidents": random.randint(0, 10),
        "source": "simulated"
    }


