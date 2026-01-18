# SPADE Risk Assessment Agent - Code Documentation

This document provides a detailed explanation of what each code file does in the SPADE Risk Assessment Agent project.

---

## 📁 Project Structure Overview

```
test_spades/
├── README.md                    # Main project documentation
├── readme2.md                   # This file - code explanations
├── start.ps1                    # PowerShell startup script
│
├── spade-risk-agent/            # Backend (FastAPI)
│   ├── main.py                  # FastAPI application entry point
│   ├── requirements.txt         # Python dependencies
│   ├── start.bat                # Windows batch startup script
│   │
│   ├── api/
│   │   └── router.py            # API routes and endpoint handlers
│   │
│   ├── core/
│   │   ├── validation.py        # Input validation using Pydantic
│   │   ├── scoring_engine.py   # Risk dimension calculations
│   │   ├── aggregation.py      # Overall score computation
│   │   └── recommendations.py  # Security recommendations generator
│   │
│   ├── tools/
│   │   ├── crime_data_tool.py   # Crime data fetching from APIs
│   │   ├── geolocation_tool.py  # Address geocoding services
│   │   ├── property_info_tool.py # Property type data
│   │   └── fallback/
│   │       ├── simulated_crime.py # Fallback crime data
│   │       └── simulated_geo.py  # Fallback geolocation data
│   │
│   ├── config/
│   │   └── settings.py          # Configuration settings
│   │
│   └── tests/
│       ├── test_api.py          # API endpoint tests
│       └── test_scoring.py      # Scoring engine tests
│
└── frontend/                     # Frontend (React)
    ├── package.json             # Node.js dependencies and scripts
    ├── tailwind.config.js       # Tailwind CSS configuration
    ├── postcss.config.js        # PostCSS configuration
    │
    └── src/
        ├── index.js             # React application entry point
        ├── index.css            # Global styles
        └── App.js               # Main React component
```

---

## 🔧 Backend Files (spade-risk-agent/)

### **main.py** - FastAPI Application Entry Point

**Purpose**: Initializes the FastAPI application and configures middleware, routing, and error handling.

**Key Components**:
- **Logging Configuration** (lines 9-13): Sets up production-ready logging with timestamps and log levels
- **FastAPI App Initialization** (lines 16-22): Creates the FastAPI app with title, description, version, and API documentation URLs
- **CORS Middleware** (lines 26-32): Enables Cross-Origin Resource Sharing to allow frontend (port 3000) to communicate with backend (port 8000)
- **Router Inclusion** (line 34): Includes the API router from `api/router.py` to handle `/assess/` endpoint
- **Root Endpoint** (lines 37-47): Returns basic API information and service status
- **Health Check Endpoint** (lines 50-56): Simple endpoint for monitoring/deployment health checks
- **Global Exception Handler** (lines 59-69): Catches all unexpected errors and returns user-friendly error responses

**What it does**: This is the entry point that starts the web server. It sets up the FastAPI framework, enables CORS for frontend communication, includes the assessment router, and provides basic endpoints for API info and health checks.

---

### **api/router.py** - API Routes and Endpoint Handlers

**Purpose**: Defines the main risk assessment endpoint that orchestrates the entire assessment workflow.

**Key Components**:
- **Router Setup** (line 12): Creates an APIRouter with prefix `/assess` and tags for API documentation
- **Main Assessment Endpoint** (lines 15-139): The `/assess/` POST endpoint that handles risk assessment requests

**Workflow (4 Phases)**:

1. **Phase 1: Data Collection** (lines 44-75)
   - **Geocoding** (lines 48-51): Converts address to coordinates using `get_geolocation_info()`
   - **City Detection** (lines 53-64): Detects city name from address to select appropriate crime API
   - **Crime Data Fetching** (line 68): Gets crime statistics using `get_crime_data()`
   - **Property Data** (line 72): Gets property-specific risk data using `get_property_info()`

2. **Phase 2: Risk Calculation** (lines 77-92)
   - Calculates 5 risk dimension scores (0-100 each) using `compute_risk_dimensions()`
   - Factors in crime data, geolocation, property type, security features, operating hours, and notes

3. **Phase 3: Score Aggregation** (lines 94-100)
   - Computes weighted overall score and confidence level using `compute_overall_score()`
   - Confidence depends on whether real APIs or simulated data were used

4. **Phase 4: Recommendation Generation** (lines 102-108)
   - Generates security recommendations based on overall risk score using `generate_recommendations()`

**Response Building** (lines 111-133): Constructs JSON response with all assessment data including scores, recommendations, coordinates, and data source information.

**What it does**: This is the main API endpoint that receives property information, fetches external data (crime, geolocation), calculates risk scores, and returns comprehensive assessment results.

---

### **core/validation.py** - Input Validation

**Purpose**: Validates and sanitizes user input using Pydantic models.

**Key Components**:
- **AssessmentInput Model** (lines 5-31): Pydantic BaseModel that defines the structure and validation rules for assessment requests

**Fields**:
- `address` (line 7): Required string, minimum length 1, trimmed of whitespace
- `property_type` (line 8): Required string, validated against allowed types
- `fenced` (line 9): Boolean indicating if property has fencing
- `gated` (line 10): Boolean indicating if property has gating
- `operating_hours` (line 11): Optional string for operating hours
- `notes` (line 12): Optional string for additional notes

**Validators**:
- **Property Type Validator** (lines 14-22): Ensures property_type is one of: "home", "rental", "vacation home", "business" (case-insensitive)
- **Address Validator** (lines 24-30): Trims whitespace and ensures address is not empty

**What it does**: Validates incoming API requests to ensure data integrity before processing. Rejects invalid property types and empty addresses, preventing errors in downstream processing.

---

### **core/scoring_engine.py** - Risk Dimension Calculations

**Purpose**: Calculates risk scores across 5 dimensions based on various factors.

**Key Function**: `compute_risk_dimensions()` (lines 4-110)

**5 Risk Dimensions Calculated**:

1. **Crime Risk** (lines 22-31)
   - Formula: `min(violent_crime_index × 0.6 + property_crime_index × 0.3 + recent_incidents × 3, 100)`
   - Uses crime data indices and recent incident count
   - Recent incidents weighted heavily (×3 multiplier)

2. **Property Exposure Risk** (lines 33-44)
   - Base exposure from property type (home=25, rental=35, vacation home=45, business=50)
   - Adjustments: +10 if not fenced, -5 if fenced; +10 if not gated, -5 if gated
   - Vacation homes get +15 (empty most of the time)
   - Homes get -5 (people around = natural deterrence)

3. **Accessibility Risk** (lines 46-57)
   - Base: 60 for urban, 40 for suburban/rural
   - Adjustments: +10 if not fenced, -5 if fenced
   - Vacation homes get +12 (less monitoring)
   - Homes get -3 (regular presence)

4. **Neighborhood Risk** (lines 59-73)
   - Base: population_density / 100
   - Adjustments: +20 for nightclubs, +15 for warehouses, +5 for schools
   - Capped at 0-100 range

5. **Operational Risk** (lines 75-92)
   - Base: 20
   - Vacation homes: +25 (extended unoccupied) + 10 (predictable absence)
   - Homes: -5 (regular occupancy)
   - 24/7 operations: +30
   - Notes mentioning "theft": +20

**Summary Functions** (lines 113-204): Generate human-readable summaries for each dimension explaining the risk factors.

**What it does**: Takes crime data, geolocation info, property characteristics, and user input to calculate 5 separate risk scores (0-100 each) that represent different aspects of property vulnerability.

---

### **core/aggregation.py** - Overall Score Computation

**Purpose**: Combines all 5 risk dimensions into a single overall score with confidence level.

**Key Function**: `compute_overall_score()` (lines 4-37)

**Score Calculation** (lines 16-24):
- Weighted average formula:
  ```
  Overall = (Crime × 0.35) + (Property Exposure × 0.25) + 
            (Accessibility × 0.15) + (Neighborhood × 0.15) + 
            (Operational × 0.10)
  ```
- Crime risk has highest weight (35%) as it's most important
- Score clamped to 0-100 range

**Confidence Calculation** (lines 26-35):
- **1.0** (100%): Both crime and geolocation data from real APIs
- **0.7** (70%): One real API, one simulated
- **0.5** (50%): Both simulated data

**What it does**: Aggregates the 5 dimension scores into one overall risk score (0-100) and calculates confidence based on data source quality. This is the final score shown to users.

---

### **core/recommendations.py** - Security Recommendations Generator

**Purpose**: Generates security recommendations based on overall risk score.

**Key Function**: `generate_recommendations()` (lines 4-38)

**Recommendation Tiers**:

- **Score > 75** (Very High Risk): Advanced security measures
  - Advanced CCTV with remote monitoring
  - Security patrols
  - Smart perimeter lighting
  - Upgraded fences and gates
  - Controlled access systems

- **Score > 60** (High Risk): Enhanced security
  - 1080p CCTV cameras
  - Motion-activated lighting
  - Improved fencing and gate systems

- **Score > 40** (Moderate Risk): Standard security
  - Basic CCTV
  - Improved door/window locks
  - Trim shrubs for visibility

- **Score ≤ 40** (Low Risk): Basic security
  - Basic home security recommended

**What it does**: Takes the overall risk score and returns a list of actionable security recommendations tailored to the risk level. Uses CPTED (Crime Prevention Through Environmental Design) principles.

---

### **tools/crime_data_tool.py** - Crime Data Fetching

**Purpose**: Fetches crime statistics from public city APIs with intelligent fallbacks.

**Key Function**: `get_crime_data()` (lines 430-499)

**Data Sources (Priority Order)**:

1. **Real City APIs** (lines 11-33): Public crime data APIs for:
   - Chicago: `data.cityofchicago.org`
   - New York: `data.cityofnewyork.us` (NYPD)
   - Los Angeles: `data.lacity.org`
   - San Francisco: `data.sfgov.org`
   - Philadelphia: `phl.carto.com` (Carto API)

2. **Coordinate-Based Estimation** (lines 317-427): When APIs unavailable, estimates crime based on coordinates:
   - Brooklyn 11212 (high-crime area): violent=85, property=75
   - General Brooklyn: varies by location
   - Manhattan: moderate crime with property crime emphasis
   - General NYC: urban crime estimates
   - General urban: base urban crime rates

3. **Simulated Data** (lines 488-492): Last resort fallback using `simulate_crime()`

**City-Specific API Functions**:
- `_query_chicago_crime_api()` (lines 54-125): Queries Chicago's Socrata API, filters last 30 days, categorizes violent vs property crimes
- `_query_nyc_crime_api()` (lines 128-188): Queries NYPD complaint data, handles various field name formats
- `_query_la_crime_api()` (lines 191-242): Queries LA crime data API
- `_query_sf_crime_api()` (lines 245-296): Queries San Francisco crime API

**Return Format**: Dictionary with:
- `violent_crime_index`: 0-100 scale
- `property_crime_index`: 0-100 scale
- `recent_incidents`: Count of recent incidents
- `source`: Data source identifier

**What it does**: Attempts to fetch real crime data from city APIs. If that fails, estimates crime based on coordinates. If that fails, uses simulated data. Always returns data - never fails completely.

---

### **tools/geolocation_tool.py** - Address Geocoding

**Purpose**: Converts addresses to coordinates (latitude/longitude) using multiple geocoding services.

**Key Function**: `get_geolocation_info()` (lines 218-259)

**Geocoding Services (Priority Order)**:

1. **Google Maps Geocoding API** (lines 44-96): `_geocode_with_google()`
   - Most accurate, requires API key
   - Returns formatted address, coordinates, neighborhood type

2. **Nominatim (OpenStreetMap)** (lines 99-155): `_geocode_with_nominatim()`
   - Free, no API key required
   - Tries multiple address formats: original, "+ USA", "+ United States"
   - Validates coordinates are reasonable (not 0,0 or invalid)

3. **Photon Geocoding API** (lines 158-215): `_geocode_with_photon()`
   - Free alternative based on OpenStreetMap
   - Backup service if Nominatim fails

4. **Simulated Data** (lines 256-258): Last resort using `simulate_geo()`

**Helper Functions**:
- `_classify_neighborhood_by_coords()` (lines 12-20): Classifies as urban/suburban/rural based on coordinates
- `_get_population_density()` (lines 23-30): Estimates population density by neighborhood type
- `_get_nearby_risks()` (lines 33-41): Determines nearby risk factors (nightclubs, warehouses, schools)

**Return Format**: Dictionary with:
- `latitude`, `longitude`: Coordinates for map display
- `neighborhood_type`: "urban", "suburban", or "rural"
- `population_density`: Estimated density per square mile
- `nearby_risks`: List of nearby risk factors
- `formatted_address`: Standardized address
- `source`: Geocoding service used

**What it does**: Converts human-readable addresses into coordinates for map display and crime data lookup. Tries multiple free services before falling back to simulation. Always returns coordinates.

---

### **tools/property_info_tool.py** - Property Type Data

**Purpose**: Provides base exposure risk values for different property types.

**Key Function**: `get_property_info()` (lines 1-14)

**Property Type Base Risks**:
- `home`: 25 (primary residence - people around = lower risk)
- `rental`: 35 (moderate risk, depends on tenant)
- `vacation home`: 45 (empty most of the time = higher risk)
- `business`: 50 (commercial - highest base risk)

**What it does**: Returns base exposure risk value for a property type. This base value is then adjusted by security features (fencing, gating) in the scoring engine.

---

### **tools/fallback/simulated_crime.py** - Simulated Crime Data

**Purpose**: Generates realistic simulated crime data when real APIs are unavailable.

**Key Function**: `simulate_crime()` (lines 4-10)

**What it does**: Returns random crime indices within realistic ranges:
- `violent_crime_index`: 20-80
- `property_crime_index`: 15-70
- `recent_incidents`: 0-10
- `source`: "simulated"

Used as last resort when all real crime data sources fail.

---

### **tools/fallback/simulated_geo.py** - Simulated Geolocation Data

**Purpose**: Generates realistic simulated geolocation data with coordinates.

**Key Function**: `simulate_geo()` (lines 4-40)

**What it does**: Generates coordinates and location data based on neighborhood type:
- **Urban**: NYC area coordinates (40.0-41.0 lat, -74.0 to -73.0 lon), density=8000, risks=[nightclub, warehouse, school]
- **Suburban**: Mid-Atlantic coordinates (38.0-42.0 lat, -75.0 to -70.0 lon), density=3000, risks=[school]
- **Rural**: General US coordinates (35.0-45.0 lat, -85.0 to -70.0 lon), density=500, risks=[]

Always includes valid coordinates for map display, even when simulated.

---

### **config/settings.py** - Configuration Settings

**Purpose**: Centralized configuration for API keys and service URLs.

**Key Components**:
- `CRIMEOMETER_API_KEY`: Optional API key for Crimeometer service (currently unused)
- `NOMINATIM_URL`: OpenStreetMap Nominatim service URL
- `GOOGLE_MAPS_API_KEY`: Optional Google Maps API key for enhanced geocoding

**What it does**: Stores configuration settings. Google Maps API key can be added here for more accurate geocoding (optional - system works without it using free services).

---

### **tests/test_api.py** - API Endpoint Tests

**Purpose**: Tests the main assessment API endpoint.

**Key Test**: `test_assess_endpoint_basic()` (lines 9-27)

**What it does**: Sends a POST request to `/assess/` endpoint with sample data and verifies:
- Response status is 200
- Response contains required fields: `risk_dimensions`, `overall_score`, `confidence`, `recommendations`, `api_sources_used`
- Recommendations is a list

---

### **tests/test_scoring.py** - Scoring Engine Tests

**Purpose**: Tests individual scoring functions (NOTE: These tests reference functions that may have been refactored).

**What it does**: Tests various scoring calculations to ensure they work correctly. Some tests may need updating if scoring functions have changed.

---

### **start.bat** - Windows Batch Startup Script

**Purpose**: Automates starting both backend and frontend servers on Windows.

**What it does**:
1. Checks if Python and Node.js are installed
2. Starts FastAPI backend in new window (port 8000)
3. Checks/installs frontend dependencies if needed
4. Starts React frontend in new window (port 3000)
5. Displays server URLs

---

## 🎨 Frontend Files (frontend/)

### **src/index.js** - React Application Entry Point

**Purpose**: Initializes and renders the React application.

**What it does**:
- Imports React and ReactDOM
- Imports global CSS styles
- Imports the main App component
- Creates a root element and renders App in React StrictMode
- This is the entry point that React uses to start the application

---

### **src/App.js** - Main React Component

**Purpose**: Complete frontend application with form, API communication, and results display.

**Key Components**:

#### **State Management** (lines 152-176):
- `form`: Stores user input (address, property_type, fenced, gated, operating_hours, notes)
- `loading`: Boolean for API request status
- `result`: Stores API response data
- `success`: Boolean for successful assessment
- `error`: Stores error messages
- `showJsonModal`: Controls JSON modal visibility

#### **MapWidget Component** (lines 47-132):
- **Dynamic Loading** (lines 50-81): Dynamically imports Leaflet and react-leaflet libraries
- **Icon Fix** (lines 64-69): Fixes Leaflet marker icon paths using CDN URLs
- **Map Rendering** (lines 100-131): Creates interactive map with:
  - OpenStreetMap tiles (free, no API key)
  - Marker at property location
  - Popup showing address and coordinates
  - Zoom level 17 for detailed view

#### **Helper Functions**:
- `update()` (lines 188-190): Updates form state for specific field
- `extractNumericScore()` (lines 199-206): Handles various score formats (number, object, string)
- `getRiskLevel()` (lines 214-222): Categorizes score as High (≥75), Medium (≥50), or Low (<50)

#### **API Communication** (lines 237-279):
- `assessRisk()`: 
  - Validates required fields
  - Sends POST request to `http://localhost:8000/assess/`
  - Handles response and errors
  - Updates UI state

#### **UI Sections**:
- **Header** (lines 340-350): SPADE branding with logo
- **Left Panel** (lines 359-485): Property information form with:
  - Address input with MapPin icon
  - Property type dropdown
  - Security features checkboxes (fenced, gated)
  - Operating hours input
  - Additional notes textarea
  - Submit button with loading state
  - Error/success messages
- **Right Panel** (lines 490-614): Results display with:
  - Overall risk score card (gradient background)
  - Risk dimensions grid (5 cards showing each dimension)
  - Interactive map (if coordinates available)
  - Security recommendations list
  - Data sources information
  - View Raw JSON button
- **JSON Modal** (lines 621-671): Modal showing raw API response with copy-to-clipboard functionality

**What it does**: Provides complete user interface for risk assessment. Users enter property information, click "Assess Risk", and see results including scores, map, and recommendations.

---

### **package.json** - Node.js Dependencies and Scripts

**Purpose**: Defines frontend dependencies, build scripts, and configuration.

**Key Components**:
- **Dependencies** (lines 5-13):
  - `react`, `react-dom`: React framework (v18.2.0)
  - `react-scripts`: Create React App tooling
  - `leaflet`, `react-leaflet`: Map library (OpenStreetMap)
  - `lucide-react`: Icon library
  - `tailwindcss`, `autoprefixer`, `postcss`: CSS framework
- **Scripts** (lines 15-19):
  - `start`: Starts development server (port 3000)
  - `build`: Creates production build
  - `test`: Runs tests
  - `eject`: Ejects from Create React App
- **Proxy** (line 43): Proxies API requests to `http://localhost:8000`

**What it does**: Defines all frontend dependencies and build scripts. Running `npm install` installs all packages listed here.

---

### **tailwind.config.js** - Tailwind CSS Configuration

**Purpose**: Configures Tailwind CSS styling framework.

**What it does**: Defines custom color palette (SPADE brand colors) and configures Tailwind to scan React files for class names. Custom colors like `spade-blue`, `spade-navy`, `spade-light`, `spade-gray`, `spade-sky` are defined here.

---

### **postcss.config.js** - PostCSS Configuration

**Purpose**: Configures PostCSS for processing CSS.

**What it does**: Sets up PostCSS with Tailwind CSS and Autoprefixer plugins. PostCSS processes CSS files during build.

---

## 🚀 Startup Scripts

### **start.ps1** - PowerShell Startup Script

**Purpose**: Advanced PowerShell script to start both servers with dependency checking and browser opening.

**What it does**:
1. Stops existing processes on ports 8000 and 3000
2. Starts backend in new PowerShell window
3. Checks/installs frontend dependencies
4. Starts frontend in new PowerShell window
5. Waits for frontend to compile (up to 60 seconds)
6. Opens browser automatically to http://localhost:3000
7. Displays server URLs

More advanced than `start.bat` with better error handling and browser automation.

---

## 📊 Data Flow Summary

1. **User Input** → Frontend form (`App.js`)
2. **API Request** → POST to `/assess/` (`api/router.py`)
3. **Validation** → `core/validation.py` validates input
4. **Geocoding** → `tools/geolocation_tool.py` converts address to coordinates
5. **Crime Data** → `tools/crime_data_tool.py` fetches crime statistics
6. **Property Data** → `tools/property_info_tool.py` gets property type info
7. **Risk Calculation** → `core/scoring_engine.py` calculates 5 dimension scores
8. **Score Aggregation** → `core/aggregation.py` computes overall score
9. **Recommendations** → `core/recommendations.py` generates security advice
10. **Response** → JSON response sent back to frontend
11. **Display** → Frontend shows scores, map, and recommendations

---

## 🔄 Fallback Strategy

The system uses a multi-tier fallback strategy to ensure 100% uptime:

1. **Real APIs** (Best): City crime APIs, Google Maps geocoding
2. **Free APIs** (Good): Nominatim, Photon geocoding
3. **Coordinate Estimation** (Acceptable): Estimates based on known locations
4. **Simulated Data** (Last Resort): Realistic random data

This ensures the system always returns results, even when external APIs are down.

---

## 📝 Notes

- All coordinates are always included in responses (even simulated) for map display
- Crime data sources are clearly labeled in API responses
- Confidence scores indicate data quality (1.0 = real APIs, 0.5 = simulated)
- Frontend uses OpenStreetMap (completely free, no API key needed)
- Backend can optionally use Google Maps API for better geocoding accuracy

---

**End of Code Documentation**

