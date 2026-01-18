import logging
from fastapi import APIRouter, HTTPException
from core.validation import AssessmentInput
from core.scoring_engine import compute_risk_dimensions
from core.aggregation import compute_overall_score
from core.recommendations import generate_recommendations
from tools.crime_data_tool import get_crime_data
from tools.geolocation_tool import get_geolocation_info
from tools.property_info_tool import get_property_info

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assess", tags=["Risk Assessment"])


@router.post("/")
def assess_risk(payload: AssessmentInput):
    """
    Main risk assessment endpoint.
    
    Performs comprehensive risk analysis for a property based on:
    - Address and geolocation data
    - Crime statistics for the area
    - Property characteristics (type, security features)
    - User-provided operational information
    
    Returns detailed risk scores across 5 dimensions, overall score,
    security recommendations, and location coordinates.
    
    Args:
        payload: AssessmentInput containing address, property_type, 
                 security features, operating_hours, and notes
    
    Returns:
        JSON response with risk assessment results including:
        - Risk dimension scores (0-100 each)
        - Overall risk score (0-100)
        - Security recommendations
        - Location coordinates for map display
        - Data source information
    """
    try:
        logger.info(f"Assessing risk for: {payload.address}")
        
        # Phase 1: Data Collection
        try:
            # Step 1: Geocode address to get coordinates
            # Coordinates are needed for crime data lookup and map display
            geo_data = get_geolocation_info(payload.address)
            latitude = geo_data.get("latitude")
            longitude = geo_data.get("longitude")
            formatted_address = geo_data.get("formatted_address", payload.address)
            
            # Step 2: Detect city for appropriate crime API selection
            # Different cities have different public crime data APIs
            city = None
            address_lower = formatted_address.lower()
            supported_cities = {
                "chicago", "new york", "los angeles", 
                "san francisco", "philadelphia"
            }
            for city_name in supported_cities:
                if city_name in address_lower:
                    city = city_name
                    break
            
            # Step 3: Fetch crime statistics
            # Attempts real APIs first, falls back to coordinate-based estimation
            crime_data = get_crime_data(payload.address, latitude, longitude, city)
            
            # Step 4: Get property-specific data
            # Property type influences risk scoring calculations
            prop_data = get_property_info(payload.property_type)
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            raise HTTPException(status_code=500, detail=f"Error fetching assessment data: {str(e)}")

        # Phase 2: Risk Calculation
        try:
            # Calculate risk scores across 5 dimensions (0-100 each)
            dimensions = compute_risk_dimensions(
                crime_data,
                geo_data,
                prop_data,
                payload.property_type,
                payload.fenced,
                payload.gated,
                payload.operating_hours,
                payload.notes
            )
        except Exception as e:
            logger.error(f"Risk calculation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Error computing risk scores: {str(e)}")

        # Phase 3: Score Aggregation
        try:
            # Compute weighted overall score and confidence level
            overall, confidence = compute_overall_score(dimensions, crime_data, geo_data)
        except Exception as e:
            logger.error(f"Score aggregation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Error computing overall score: {str(e)}")

        # Phase 4: Recommendation Generation
        try:
            # Generate security recommendations based on overall risk score
            recommendations = generate_recommendations(overall)
        except Exception as e:
            logger.warning(f"Recommendation generation failed: {e}")
            recommendations = ["Unable to generate recommendations"]  # Fallback

        # Build response
        response = {
            "address": payload.address,
            "property_type": payload.property_type,
            "fenced": payload.fenced,
            "gated": payload.gated,
            "operating_hours": payload.operating_hours,
            "notes": payload.notes,
            "risk_dimensions": dimensions,
            "overall_score": overall,
            "confidence": confidence,
            "recommendations": recommendations,
            "api_sources_used": {
                "crime_data": crime_data.get("source", "simulated"),
                "geolocation": geo_data.get("source", "simulated")
            },
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude
            } if (latitude is not None and longitude is not None) else None
        }
        
        logger.info(f"Assessment complete - Score: {overall}, Confidence: {confidence}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in assess_risk: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")





