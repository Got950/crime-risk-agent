/**
 * SPADE Risk Assessment Agent - Frontend Application
 * 
 * This React application provides a user-friendly interface for assessing
 * property risk based on address, property type, and security features.
 * 
 * Features:
 * - Interactive property information form
 * - Real-time risk assessment via FastAPI backend
 * - Visual risk score display with breakdown by dimension
 * - Interactive map visualization using Leaflet
 * - Security recommendations based on assessment
 * - Raw JSON data export functionality
 * 
 * @author SPADE Development Team
 * @version 1.0.0
 * @since 2024
 */

import React, { useState } from "react";
import {
  Shield,
  MapPin,
  Clock,
  FileCheck,
  AlertTriangle,
  Code,
  X,
} from "lucide-react";

// ============================================================================
// COMPONENT: MapWidget
// ============================================================================
/**
 * Interactive map component using Leaflet with OpenStreetMap (100% Free, No API Key)
 * 
 * Uses Leaflet library with OpenStreetMap tiles for completely free map display.
 * Geocodes the address using the coordinates provided by the backend.
 * 
 * @param {Object} props - Component props
 * @param {number} props.latitude - Latitude coordinate
 * @param {number} props.longitude - Longitude coordinate
 * @param {string} props.address - Property address for marker label
 * 
 * @returns {JSX.Element} Leaflet map component or loading placeholder
 */
const MapWidget = ({ latitude, longitude, address }) => {
  const [MapComponents, setMapComponents] = React.useState(null);

  React.useEffect(() => {
    /**
     * Dynamically load Leaflet library (completely free, no API key needed)
     * Uses OpenStreetMap tiles which are free and open source
     */
    const loadMap = async () => {
      try {
        console.log("Loading Leaflet map (OpenStreetMap - Free)...", { latitude, longitude });
        
        // Dynamically import Leaflet and react-leaflet
        const { MapContainer, TileLayer, Marker, Popup } = await import("react-leaflet");
        const L = (await import("leaflet")).default;
        
        // Fix marker icons for proper display
        delete L.Icon.Default.prototype._getIconUrl;
        L.Icon.Default.mergeOptions({
          iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
          iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
          shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
        });
        
        console.log("Leaflet map components loaded successfully");
        setMapComponents({ MapContainer, TileLayer, Marker, Popup });
      } catch (err) {
        console.error("Failed to load Leaflet map:", err);
      }
    };
    
    if (latitude != null && longitude != null) {
      loadMap();
    }
  }, [latitude, longitude]);

  // Loading state while map libraries are being loaded
  if (!MapComponents) {
    return (
      <div 
        className="w-full rounded-lg border-2 border-spade-blue flex items-center justify-center bg-gray-100"
        style={{ height: '400px' }}
      >
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-spade-blue mx-auto mb-2"></div>
          <p className="text-gray-500">Loading map (OpenStreetMap)...</p>
        </div>
      </div>
    );
  }

  const { MapContainer, TileLayer, Marker, Popup } = MapComponents;

  return (
    <div 
      className="w-full rounded-lg overflow-hidden border-2 border-spade-blue bg-white" 
      style={{ height: '400px', position: 'relative', zIndex: 1, minHeight: '400px' }}
    >
      <MapContainer
        key={`${latitude}-${longitude}`}
        center={[latitude, longitude]}
        zoom={17}
        style={{ height: "100%", width: "100%", zIndex: 1, minHeight: '400px' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={[latitude, longitude]}>
          <Popup>
            <div className="text-center">
              <strong className="text-spade-blue">{address}</strong>
              <br />
              <span className="text-sm text-gray-600">Risk Assessment Location</span>
              <br />
              <span className="text-xs text-gray-500">
                {latitude.toFixed(6)}, {longitude.toFixed(6)}
              </span>
            </div>
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
};

// ============================================================================
// MAIN APPLICATION COMPONENT
// ============================================================================
/**
 * Main application component for SPADE Risk Assessment Agent
 * 
 * Manages the complete risk assessment workflow:
 * 1. User input collection (address, property type, security features)
 * 2. API communication with FastAPI backend
 * 3. Results visualization (scores, map, recommendations)
 * 4. Data export functionality
 * 
 * @returns {JSX.Element} Complete application UI
 */
function App() {
  // ========================================================================
  // STATE MANAGEMENT
  // ========================================================================
  
  /** Form data state - stores all user input */
  const [form, setForm] = useState({
    address: "",
    property_type: "home",
    fenced: false,
    gated: false,
    operating_hours: "",
    notes: "",
  });

  /** Loading state - indicates API request in progress */
  const [loading, setLoading] = useState(false);
  
  /** Assessment results from API */
  const [result, setResult] = useState(null);
  
  /** Success state - indicates successful assessment */
  const [success, setSuccess] = useState(false);
  
  /** Error state - stores error messages */
  const [error, setError] = useState(null);
  
  /** Modal state - controls JSON modal visibility */
  const [showJsonModal, setShowJsonModal] = useState(false);

  // ========================================================================
  // HELPER FUNCTIONS
  // ========================================================================
  
  /**
   * Updates form state for a specific field
   * 
   * @param {string} field - Field name to update
   * @param {*} value - New value for the field
   */
  const update = (field, value) => {
    setForm({ ...form, [field]: value });
  };

  /**
   * Extracts numeric value from potentially nested score objects
   * Handles various API response formats for backward compatibility
   * 
   * @param {number|object|string} score - Score value in various formats
   * @returns {number} Numeric score value
   */
  const extractNumericScore = (score) => {
    if (typeof score === 'number') return score;
    if (typeof score === 'object' && score !== null && score.value !== undefined) {
      return score.value;
    }
    const parsed = parseFloat(score);
    return isNaN(parsed) ? 0 : parsed;
  };

  /**
   * Determines risk level category based on numeric score
   * 
   * @param {number} score - Risk score (0-100)
   * @returns {Object} Risk level information with label and color
   */
  const getRiskLevel = (score) => {
    if (score >= 75) {
      return { label: "High", color: "text-red-600", bgColor: "bg-red-50" };
    } else if (score >= 50) {
      return { label: "Medium", color: "text-yellow-600", bgColor: "bg-yellow-50" };
    } else {
      return { label: "Low", color: "text-green-600", bgColor: "bg-green-50" };
    }
  };

  // ========================================================================
  // API COMMUNICATION
  // ========================================================================
  
  /**
   * Sends risk assessment request to FastAPI backend
   * 
   * Validates form data, makes API call, and handles response/errors.
   * Updates UI state based on API response.
   * 
   * @async
   * @returns {Promise<void>}
   */
  const assessRisk = async () => {
    // Validate required fields
    if (!form.address || !form.property_type) {
      setError("Please fill in all required fields (Address and Property Type)");
      return;
    }

    setLoading(true);
    setSuccess(false);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/assess/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || 
          errorData.message || 
          `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();
      console.log("API Response:", data);
      console.log("Coordinates in response:", data.coordinates);
      setResult(data);
      setSuccess(true);
    } catch (err) {
      setError(
        err.message || 
        "Failed to assess risk. Please ensure the backend server is running at http://localhost:8000"
      );
      console.error("Risk assessment error:", err);
    } finally {
      setLoading(false);
    }
  };

  // ========================================================================
  // RENDER FUNCTIONS
  // ========================================================================
  
  /**
   * Renders risk dimension cards in a grid layout
   * 
   * @param {Object} riskDimensions - Object containing risk scores by dimension and summaries
   * @returns {JSX.Element[]} Array of risk dimension card components
   */
  const renderRiskDimensions = (riskDimensions) => {
    if (!riskDimensions || typeof riskDimensions !== 'object') {
      return null;
    }

    // Extract summaries if they exist
    const summaries = riskDimensions.summaries || {};
    
    // Filter out the summaries key and only render actual risk dimensions
    return Object.entries(riskDimensions)
      .filter(([key]) => key !== 'summaries')
      .map(([key, value]) => {
        const numericValue = extractNumericScore(value);
        const riskLevel = getRiskLevel(numericValue);
        const summary = summaries[key] || '';
        
        return (
          <div
            key={key}
            className="p-4 bg-white border border-spade-light rounded-lg shadow-sm hover:shadow-md transition"
          >
            <p className="font-semibold capitalize text-spade-blue text-sm mb-2">
              {key.replace(/_/g, " ")}
            </p>
            <div className="flex items-baseline gap-2 mb-2">
              <p className="text-3xl font-bold">{numericValue}</p>
              <span className={`text-sm font-medium ${riskLevel.color}`}>
                {riskLevel.label}
              </span>
            </div>
            {summary && (
              <p className="text-xs text-gray-600 mt-2 leading-relaxed">
                {summary}
              </p>
            )}
          </div>
        );
      });
  };

  // ========================================================================
  // MAIN RENDER
  // ========================================================================
  
  return (
    <div className="min-h-screen bg-spade-gray">
      {/* ====================================================================
          HEADER SECTION
          ==================================================================== */}
      <header className="w-full p-6 bg-gradient-to-r from-spade-navy to-spade-blue text-white shadow-lg flex items-center gap-4">
        <Shield size={42} className="flex-shrink-0" />
        <div>
          <h1 className="text-3xl font-bold tracking-wide">
            SPADE Risk Assessment Agent
          </h1>
          <p className="text-spade-light text-sm">
            Address-Based Vulnerability & Risk Analysis
          </p>
        </div>
      </header>

      {/* ====================================================================
          MAIN CONTENT AREA
          ==================================================================== */}
      <div className="flex flex-col lg:flex-row gap-6 p-6">
        {/* ================================================================
            LEFT PANEL: Property Information Form
            ================================================================ */}
        <div className="w-full lg:w-1/3 bg-white shadow-md rounded-xl p-6 border border-spade-light">
          <h2 className="text-xl font-semibold text-spade-blue mb-4">
            Property Information
          </h2>

          {/* Address Input */}
          <label className="text-sm font-medium block">
            Address *
            <div className="flex items-center border rounded-md p-2 mt-1 border-gray-300 focus-within:border-spade-blue focus-within:ring-1 focus-within:ring-spade-blue">
              <MapPin className="text-spade-blue mr-2 flex-shrink-0" size={18} />
              <input
                type="text"
                className="w-full outline-none"
                placeholder="123 Main St, New York, NY"
                value={form.address}
                onChange={(e) => update("address", e.target.value)}
                required
                disabled={loading}
              />
            </div>
          </label>

          {/* Property Type Selection */}
          <label className="text-sm font-medium mt-4 block">
            Property Type *
          </label>
          <select
            className="w-full border p-2 rounded-md mt-1 border-gray-300 focus:border-spade-blue focus:ring-1 focus:ring-spade-blue"
            value={form.property_type}
            onChange={(e) => update("property_type", e.target.value)}
            disabled={loading}
          >
            <option value="home">Home</option>
            <option value="rental">Rental</option>
            <option value="vacation home">Vacation Home</option>
            <option value="business">Business</option>
          </select>

          {/* Security Features Checkboxes */}
          <div className="mt-4">
            <h3 className="text-sm font-medium mb-1">Security Features</h3>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.fenced}
                  onChange={() => update("fenced", !form.fenced)}
                  className="w-4 h-4 text-spade-blue border-gray-300 rounded focus:ring-spade-blue"
                  disabled={loading}
                />
                <span className="text-sm">Fenced</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.gated}
                  onChange={() => update("gated", !form.gated)}
                  className="w-4 h-4 text-spade-blue border-gray-300 rounded focus:ring-spade-blue"
                  disabled={loading}
                />
                <span className="text-sm">Gated</span>
              </label>
            </div>
          </div>

          {/* Operating Hours Input */}
          <label className="text-sm font-medium mt-4 block">
            Operating Hours
          </label>
          <div className="flex items-center border rounded-md p-2 mt-1 border-gray-300 focus-within:border-spade-blue focus-within:ring-1 focus-within:ring-spade-blue">
            <Clock className="text-spade-blue mr-2 flex-shrink-0" size={18} />
            <input
              type="text"
              className="w-full outline-none"
              placeholder="24/7, Mon-Fri 9-5, etc."
              value={form.operating_hours}
              onChange={(e) => update("operating_hours", e.target.value)}
              disabled={loading}
            />
          </div>

          {/* Additional Notes Textarea */}
          <label className="text-sm font-medium mt-4 block">
            Additional Notes
          </label>
          <textarea
            className="w-full border p-2 rounded-md mt-1 border-gray-300 focus:border-spade-blue focus:ring-1 focus:ring-spade-blue resize-none"
            rows={3}
            placeholder="e.g., recent theft in the area, high foot traffic, etc."
            value={form.notes}
            onChange={(e) => update("notes", e.target.value)}
            disabled={loading}
          />

          {/* Submit Button */}
          <button
            onClick={assessRisk}
            disabled={loading || !form.address || !form.property_type}
            className="w-full bg-spade-blue text-white py-3 rounded-lg mt-4 font-semibold hover:bg-spade-sky transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Assessing...
              </>
            ) : (
              <>
                <Shield size={18} />
                Assess Risk
              </>
            )}
          </button>

          {/* Error Message Display */}
          {error && (
            <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-md text-sm border border-red-300">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Success Message Display */}
          {success && !error && (
            <div className="mt-4 p-3 bg-green-100 text-green-700 rounded-md text-sm border border-green-300">
              ✓ Risk assessment completed successfully!
            </div>
          )}
        </div>

        {/* ================================================================
            RIGHT PANEL: Results Display
            ================================================================ */}
        <div className="w-full lg:w-2/3">
          {!result ? (
            // Empty State
            <div className="w-full h-full flex items-center justify-center text-gray-400 bg-white rounded-xl shadow-md min-h-[400px]">
              <div className="text-center">
                <FileCheck size={48} className="mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium">No Assessment Yet</p>
                <p className="text-sm mt-2">Fill in the property details and click "Assess Risk" to begin</p>
              </div>
            </div>
          ) : (
            // Results Display
            <div className="bg-white shadow-xl rounded-xl p-6">
              <h2 className="text-xl font-bold text-spade-blue flex items-center gap-2 mb-6">
                <FileCheck size={24} /> Risk Assessment Results
              </h2>

              {/* Overall Risk Score Display */}
              <div className="mt-4 p-6 rounded-xl bg-gradient-to-r from-spade-navy to-spade-blue text-white text-center shadow-lg">
                <p className="text-lg font-medium">Overall Risk Score</p>
                <p className="text-5xl font-bold mt-2">
                  {extractNumericScore(result.overall_score)}
                </p>
                <p className="text-sm mt-2 opacity-90">
                  Confidence: {Math.round(extractNumericScore(result.confidence) * 100)}%
                </p>
              </div>

              {/* Risk Dimensions Grid */}
              {result.risk_dimensions && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                  {renderRiskDimensions(result.risk_dimensions)}
                </div>
              )}

              {/* Interactive Map - Always show section if coordinates exist */}
              {result.coordinates && result.coordinates.latitude != null && result.coordinates.longitude != null && (
                <div className="mt-6 p-6 bg-white rounded-xl border-2 border-spade-blue shadow-lg">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-spade-blue flex items-center gap-2">
                      <MapPin size={24} /> Location Map
                    </h3>
                    <a
                      href={`https://www.google.com/maps?q=${result.coordinates.latitude},${result.coordinates.longitude}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-spade-blue hover:text-spade-sky underline font-medium px-3 py-1 border border-spade-blue rounded hover:bg-spade-light transition"
                    >
                      Verify in Google Maps →
                    </a>
                  </div>
                  
                  {/* Address Verification */}
                  <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-xs font-semibold text-blue-800 mb-1">📍 Address Entered:</p>
                    <p className="text-sm text-blue-900">{result.address || form.address}</p>
                    {result.risk_dimensions && result.risk_dimensions.summaries && (
                      <p className="text-xs text-blue-700 mt-1">
                        Geocoded by: {result.api_sources_used?.geolocation || 'unknown'}
                      </p>
                    )}
                  </div>
                  
                  <div className="w-full" style={{ minHeight: '400px', position: 'relative' }}>
                    <MapWidget 
                      latitude={Number(result.coordinates.latitude)}
                      longitude={Number(result.coordinates.longitude)}
                      address={result.address || form.address}
                    />
                  </div>
                  
                  <div className="mt-3 p-2 bg-gray-50 rounded border border-gray-200">
                    <p className="text-xs text-gray-600 font-mono text-center">
                      📍 Coordinates: {Number(result.coordinates.latitude).toFixed(6)}, {Number(result.coordinates.longitude).toFixed(6)}
                    </p>
                    <p className="text-xs text-gray-500 text-center mt-1">
                      Click "Verify in Google Maps" to confirm this location matches your address
                    </p>
                  </div>
                </div>
              )}

              {/* Security Recommendations */}
              {result.recommendations && 
               Array.isArray(result.recommendations) && 
               result.recommendations.length > 0 && (
                <div className="mt-8 p-4 bg-spade-light rounded-lg border border-spade-light">
                  <h3 className="font-bold text-spade-blue mb-3 flex items-center gap-2">
                    <AlertTriangle size={20} /> Security Recommendations
                  </h3>
                  <ul className="list-disc pl-6 space-y-2">
                    {result.recommendations.map((recommendation, index) => (
                      <li key={index} className="text-gray-700">
                        {typeof recommendation === 'string' 
                          ? recommendation 
                          : JSON.stringify(recommendation)}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Data Sources Information */}
              {result.api_sources_used && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">
                    <span className="font-semibold">Data Sources:</span>{" "}
                    Crime Data ({result.api_sources_used.crime_data || "simulated"}),{" "}
                    Geolocation ({result.api_sources_used.geolocation || "simulated"})
                  </p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="mt-6 flex gap-3">
                <button
                  onClick={() => setShowJsonModal(true)}
                  className="flex-1 bg-spade-light text-spade-blue py-2 px-4 rounded-lg font-semibold hover:bg-spade-sky hover:text-white transition flex items-center justify-center gap-2 border border-spade-blue"
                >
                  <Code size={18} />
                  View Raw JSON
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ====================================================================
          JSON MODAL - Raw Data Export
          ==================================================================== */}
      {showJsonModal && result && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="text-xl font-bold text-spade-blue flex items-center gap-2">
                <Code size={24} />
                Raw JSON Response
              </h3>
              <button
                onClick={() => setShowJsonModal(false)}
                className="text-gray-500 hover:text-gray-700 transition p-1"
                aria-label="Close modal"
              >
                <X size={24} />
              </button>
            </div>

            {/* JSON Content */}
            <div className="flex-1 overflow-auto p-4 bg-gray-900">
              <pre className="text-sm text-green-400 font-mono whitespace-pre-wrap">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(JSON.stringify(result, null, 2));
                    alert("JSON copied to clipboard!");
                  } catch (err) {
                    console.error("Failed to copy to clipboard:", err);
                    alert("Failed to copy. Please select and copy manually.");
                  }
                }}
                className="px-4 py-2 bg-spade-blue text-white rounded-lg hover:bg-spade-sky transition font-medium"
              >
                Copy to Clipboard
              </button>
              <button
                onClick={() => setShowJsonModal(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
