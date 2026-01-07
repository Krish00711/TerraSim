import { useState, useEffect } from 'react';
import { AlertCircle, Loader2, MapPin, Droplets, Thermometer, Wind, CloudRain } from 'lucide-react';

const AgriSimDashboard = () => {
  const [location, setLocation] = useState({ lat: null, lon: null });
  const [crops, setCrops] = useState([]);
  const [selectedCrop, setSelectedCrop] = useState('');
  const [terrainType, setTerrainType] = useState('plain');
  const [weatherData, setWeatherData] = useState(null);
  const [simulationResult, setSimulationResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiEndpoint, setApiEndpoint] = useState('');

  // Fetch location on mount
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            lat: position.coords.latitude,
            lon: position.coords.longitude
          });
        },
        (err) => {
          setError('Location access denied. Please enter coordinates manually.');
        }
      );
    }
  }, []);

  // Fetch crops from Supabase
  const fetchCrops = async () => {
    try {
      const response = await fetch(`${apiEndpoint}/api/crops`);
      const data = await response.json();
      setCrops(data);
    } catch (err) {
      setError('Failed to load crop data');
    }
  };

  // Fetch weather data
  const fetchWeather = async () => {
    if (!location.lat || !location.lon) return;
    
    try {
      const response = await fetch(
        `${apiEndpoint}/api/weather?lat=${location.lat}&lon=${location.lon}`
      );
      const data = await response.json();
      setWeatherData(data);
    } catch (err) {
      setError('Failed to fetch weather data');
    }
  };

  // Run simulation
  const runSimulation = async () => {
    if (!selectedCrop || !location.lat || !location.lon) {
      setError('Please select a crop and ensure location is available');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiEndpoint}/api/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          crop: selectedCrop,
          location: location,
          terrain: terrainType,
          weather: weatherData
        })
      });

      const result = await response.json();
      setSimulationResult(result);
    } catch (err) {
      setError('Simulation failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (risk) => {
    const colors = {
      'Low': 'bg-green-100 text-green-800 border-green-300',
      'Medium': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'High': 'bg-red-100 text-red-800 border-red-300'
    };
    return colors[risk] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Agricultural Simulation Planning System
          </h1>
          <p className="text-gray-600">
            Monte Carlo-based crop success probability analysis with risk assessment
          </p>
        </div>

        {/* API Configuration */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">API Configuration</h2>
          <div className="flex gap-4">
            <input
              type="text"
              placeholder="Enter Flask API endpoint (e.g., http://localhost:5000)"
              value={apiEndpoint}
              onChange={(e) => setApiEndpoint(e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
            />
            <button
              onClick={fetchCrops}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Connect
            </button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3">
            <AlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Input Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Location Card */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <MapPin size={20} className="text-blue-600" />
              Location Data
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Latitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={location.lat || ''}
                  onChange={(e) => setLocation({...location, lat: parseFloat(e.target.value)})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Longitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={location.lon || ''}
                  onChange={(e) => setLocation({...location, lon: parseFloat(e.target.value)})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <button
                onClick={fetchWeather}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Fetch Weather Data
              </button>
            </div>
          </div>

          {/* Crop Selection Card */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Crop & Terrain</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Crop
                </label>
                <select
                  value={selectedCrop}
                  onChange={(e) => setSelectedCrop(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="">Choose a crop...</option>
                  {crops.map((crop) => (
                    <option key={crop.id} value={crop.name}>
                      {crop.name} ({crop.category})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Terrain Type
                </label>
                <select
                  value={terrainType}
                  onChange={(e) => setTerrainType(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="plain">Plain</option>
                  <option value="plateau">Plateau</option>
                  <option value="mountain">Mountain</option>
                  <option value="valley">Valley</option>
                  <option value="coastal">Coastal</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Weather Display */}
        {weatherData && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Current Environmental Conditions</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-3 p-4 bg-orange-50 rounded-lg">
                <Thermometer className="text-orange-600" size={24} />
                <div>
                  <p className="text-sm text-gray-600">Temperature</p>
                  <p className="text-lg font-semibold">{weatherData.temp}°C</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg">
                <Droplets className="text-blue-600" size={24} />
                <div>
                  <p className="text-sm text-gray-600">Humidity</p>
                  <p className="text-lg font-semibold">{weatherData.humidity}%</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-4 bg-cyan-50 rounded-lg">
                <CloudRain className="text-cyan-600" size={24} />
                <div>
                  <p className="text-sm text-gray-600">Rainfall</p>
                  <p className="text-lg font-semibold">{weatherData.rainfall} mm</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                <Wind className="text-gray-600" size={24} />
                <div>
                  <p className="text-sm text-gray-600">Wind Speed</p>
                  <p className="text-lg font-semibold">{weatherData.wind} km/h</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Run Simulation Button */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <button
            onClick={runSimulation}
            disabled={loading || !selectedCrop}
            className="w-full px-6 py-4 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-lg font-semibold"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={24} />
                Running 10,000 Monte Carlo Simulations...
              </>
            ) : (
              'Run Crop Simulation'
            )}
          </button>
        </div>

        {/* Results Display */}
        {simulationResult && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-6">Simulation Results</h2>
            
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border-2 border-green-200">
                <p className="text-sm text-gray-600 mb-2">Success Probability</p>
                <p className="text-4xl font-bold text-green-700">
                  {(simulationResult.success_probability * 100).toFixed(1)}%
                </p>
              </div>
              
              <div className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border-2 border-blue-200">
                <p className="text-sm text-gray-600 mb-2">Expected Yield</p>
                <p className="text-4xl font-bold text-blue-700">
                  {simulationResult.expected_yield.toFixed(0)}
                </p>
                <p className="text-xs text-gray-600">kg/hectare</p>
              </div>
              
              <div className={`p-6 rounded-lg border-2 ${getRiskColor(simulationResult.risk_level)}`}>
                <p className="text-sm mb-2">Risk Level</p>
                <p className="text-4xl font-bold">
                  {simulationResult.risk_level}
                </p>
              </div>
            </div>

            {/* Explanation */}
            <div className="p-6 bg-gray-50 rounded-lg border border-gray-200">
              <h3 className="font-semibold text-lg mb-3">Analysis & Limiting Factors</h3>
              <p className="text-gray-700 leading-relaxed">
                {simulationResult.explanation}
              </p>
            </div>

            {/* Override Warning */}
            {simulationResult.is_override && (
              <div className="mt-6 p-6 bg-amber-50 border-2 border-amber-300 rounded-lg">
                <div className="flex items-start gap-3">
                  <AlertCircle className="text-amber-600 flex-shrink-0 mt-1" size={24} />
                  <div>
                    <h3 className="font-semibold text-amber-900 mb-2">
                      Crop Override Detected
                    </h3>
                    <p className="text-amber-800">
                      This crop is not recommended for the selected location. The simulation 
                      has applied environmental mismatch penalties. Proceed with caution and 
                      consider alternative crops or mitigation strategies.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Yield Range */}
            {simulationResult.yield_range && (
              <div className="mt-6 p-6 bg-blue-50 rounded-lg border border-blue-200">
                <h3 className="font-semibold text-lg mb-3">Yield Range (Variability)</h3>
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm text-gray-600">Worst Case</p>
                    <p className="text-xl font-bold text-red-600">
                      {simulationResult.yield_range.min} kg/ha
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-600">Average</p>
                    <p className="text-xl font-bold text-blue-600">
                      {simulationResult.yield_range.avg} kg/ha
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Best Case</p>
                    <p className="text-xl font-bold text-green-600">
                      {simulationResult.yield_range.max} kg/ha
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgriSimDashboard;