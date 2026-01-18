import logging
import requests
from typing import Dict, Any, Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from tools.fallback.simulated_geo import simulate_geo
from config.settings import settings

logger = logging.getLogger(__name__)


def _classify_neighborhood_by_coords(latitude: float, longitude: float) -> str:
    """Guess neighborhood type from coordinates"""
    # Simple heuristic - major US cities are around lat 40+, long < 75
    # TODO: Could use actual census data for better accuracy
    if abs(latitude) > 40 or abs(longitude) < 75:
        return "urban"
    elif abs(latitude) > 35 or abs(longitude) < 80:
        return "suburban"
    return "rural"


def _get_population_density(neighborhood_type: str, latitude: float, longitude: float) -> int:
    """Estimate population density - rough numbers"""
    # TODO: Use actual census data for better accuracy
    if neighborhood_type == "urban":
        return 8000
    elif neighborhood_type == "suburban":
        return 3000
    return 500


def _get_nearby_risks(neighborhood_type: str, latitude: float, longitude: float) -> list:
    """Determine nearby risk factors based on location"""
    risks = []
    if neighborhood_type == "urban":
        # Urban areas more likely to have these
        risks.extend(["nightclub", "warehouse"])
    if neighborhood_type in ["urban", "suburban"]:
        risks.append("school")  # Schools common in both
    return risks


def _geocode_with_google(address: str) -> Optional[Dict[str, Any]]:
    """
    Geocode address using Google Maps Geocoding API for high accuracy.
    Returns None if API key not configured or request fails.
    """
    api_key = settings.GOOGLE_MAPS_API_KEY
    if not api_key or api_key == "":
        return None
    
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            logger.debug(f"Google Geocoding API returned status {response.status_code}")
            return None
        
        data = response.json()
        if data.get("status") != "OK" or not data.get("results"):
            logger.debug(f"Google Geocoding API status: {data.get('status')}")
            return None
        
        result = data["results"][0]  # Get first (most accurate) result
        location = result["geometry"]["location"]
        latitude = float(location["lat"])
        longitude = float(location["lng"])
        formatted_address = result.get("formatted_address", address)
        
        logger.info(f"Google Geocoded: {latitude}, {longitude} - {formatted_address}")
        
        neighborhood_type = _classify_neighborhood_by_coords(latitude, longitude)
        population_density = _get_population_density(neighborhood_type, latitude, longitude)
        nearby_risks = _get_nearby_risks(neighborhood_type, latitude, longitude)
        
        return {
            "latitude": latitude,
            "longitude": longitude,
            "neighborhood_type": neighborhood_type,
            "population_density": population_density,
            "nearby_risks": nearby_risks,
            "source": "google_maps",
            "formatted_address": formatted_address
        }
    except requests.exceptions.Timeout:
        logger.debug("Google Geocoding API timeout")
        return None
    except Exception as e:
        logger.debug(f"Google Geocoding API error: {e}")
        return None


def _geocode_with_nominatim(address: str) -> Optional[Dict[str, Any]]:
    """
    Geocode address using Nominatim with multiple strategies for better accuracy.
    """
    geolocator = Nominatim(user_agent="spade_risk_agent_v1.0")
    
    # Try different address formats for better accuracy
    address_variants = [
        address,  # Original address
        address + ", USA",  # Add country
        address + ", United States",  # Full country name
    ]
    
    for addr_variant in address_variants:
        try:
            logger.debug(f"Trying Nominatim geocoding: {addr_variant}")
            location = geolocator.geocode(
                addr_variant, 
                timeout=15, 
                exactly_one=True,
                addressdetails=True,
                language='en'
            )
            
            if location and hasattr(location, 'latitude') and hasattr(location, 'longitude'):
                latitude = float(location.latitude)
                longitude = float(location.longitude)
                
                # Validate coordinates are reasonable (not 0,0 or obviously wrong)
                if abs(latitude) > 90 or abs(longitude) > 180:
                    logger.warning(f"Invalid coordinates: {latitude}, {longitude}")
                    continue
                
                neighborhood_type = _classify_neighborhood_by_coords(latitude, longitude)
                population_density = _get_population_density(neighborhood_type, latitude, longitude)
                nearby_risks = _get_nearby_risks(neighborhood_type, latitude, longitude)
                
                formatted_addr = location.address if hasattr(location, 'address') else address
                logger.info(f"Nominatim Geocoded: {latitude}, {longitude} - {formatted_addr}")
                
                return {
                    "latitude": latitude,
                    "longitude": longitude,
                    "neighborhood_type": neighborhood_type,
                    "population_density": population_density,
                    "nearby_risks": nearby_risks,
                    "source": "nominatim",
                    "formatted_address": formatted_addr
                }
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.debug(f"Nominatim timeout/error for '{addr_variant}': {e}")
            continue
        except Exception as e:
            logger.debug(f"Nominatim error for '{addr_variant}': {e}")
            continue
    
    return None


def _geocode_with_photon(address: str) -> Optional[Dict[str, Any]]:
    """
    Try Photon geocoding API (free, based on OpenStreetMap) as alternative.
    """
    try:
        url = "https://photon.komoot.io/api"
        params = {
            "q": address,
            "limit": 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None
        
        data = response.json()
        if not data.get("features") or len(data["features"]) == 0:
            return None
        
        feature = data["features"][0]
        geometry = feature.get("geometry", {})
        coordinates = geometry.get("coordinates", [])
        
        if len(coordinates) < 2:
            return None
        
        longitude = float(coordinates[0])
        latitude = float(coordinates[1])
        
        # Validate coordinates
        if abs(latitude) > 90 or abs(longitude) > 180:
            return None
        
        properties = feature.get("properties", {})
        formatted_addr = properties.get("name", address)
        if properties.get("city"):
            formatted_addr += f", {properties['city']}"
        if properties.get("country"):
            formatted_addr += f", {properties['country']}"
        
        neighborhood_type = _classify_neighborhood_by_coords(latitude, longitude)
        population_density = _get_population_density(neighborhood_type, latitude, longitude)
        nearby_risks = _get_nearby_risks(neighborhood_type, latitude, longitude)
        
        logger.info(f"Photon Geocoded: {latitude}, {longitude} - {formatted_addr}")
        
        return {
            "latitude": latitude,
            "longitude": longitude,
            "neighborhood_type": neighborhood_type,
            "population_density": population_density,
            "nearby_risks": nearby_risks,
            "source": "photon",
            "formatted_address": formatted_addr
        }
    except Exception as e:
        logger.debug(f"Photon geocoding error: {e}")
        return None


def get_geolocation_info(address: str) -> Dict[str, Any]:
    """
    Get coordinates and location info for an address with multiple fallback strategies.
    
    """
    if not address or not address.strip():
        logger.warning("Empty address provided, using simulated data")
        result = simulate_geo()
        result["source"] = "simulated_empty_address"
        result["formatted_address"] = address
        return result
    
    logger.info(f"Geocoding address: {address}")
    
    # Try Google Maps first (most accurate)
    google_result = _geocode_with_google(address)
    if google_result:
        return google_result
    
    # Try Nominatim with multiple address formats
    nominatim_result = _geocode_with_nominatim(address)
    if nominatim_result:
        return nominatim_result
    
    # Try Photon as alternative
    photon_result = _geocode_with_photon(address)
    if photon_result:
        return photon_result
    
    # Final fallback: simulated data (should rarely happen)
    logger.warning(f"All geocoding methods failed for: {address}, using simulated data")
    result = simulate_geo()
    result["source"] = "simulated_fallback"
    result["formatted_address"] = address  # Keep original address
    return result


