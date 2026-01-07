from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from supabase import create_client, Client

from engine.simulator import MonteCarloSimulator
from engine.penalties import PenaltyEngine
from engine.scoring import compute_metrics
from engine.explainability import generate_explanation
from utils.validators import validate_input
from utils.weather_service import WeatherService

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Supabase
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

weather_service = WeatherService(os.getenv("WEATHER_API_KEY"))

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "Agricultural Simulation Engine"})

@app.route('/api/crops', methods=['GET'])
def get_crops():
    """Fetch all crops from Supabase"""
    try:
        response = supabase.table('crops').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/crops/<crop_name>', methods=['GET'])
def get_crop(crop_name):
    """Fetch specific crop details"""
    try:
        response = supabase.table('crops').select('*').eq('name', crop_name).execute()
        if not response.data:
            return jsonify({"error": "Crop not found"}), 404
        return jsonify(response.data[0])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/weather', methods=['GET'])
def get_weather():
    """Fetch weather data for given coordinates"""
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        
        weather_data = weather_service.get_current_weather(lat, lon)
        return jsonify(weather_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulate', methods=['POST'])
def simulate():
    """
    Main simulation endpoint
    Expected payload:
    {
        "crop": "rice",
        "location": {"lat": 13.08, "lon": 80.27},
        "terrain": "plain",
        "weather": {...}
    }
    """
    try:
        data = request.json
        
        # Validate input
        validation_error = validate_input(data)
        if validation_error:
            return jsonify({"error": validation_error}), 400
        
        # Fetch crop profile from Supabase
        crop_response = supabase.table('crops').select('*').eq('name', data['crop']).execute()
        if not crop_response.data:
            return jsonify({"error": "Crop not found"}), 404
        
        crop_profile = crop_response.data[0]
        
        # Fetch terrain modifiers
        terrain_response = supabase.table('terrain_modifiers').select('*').eq(
            'terrain_type', data['terrain']
        ).execute()
        terrain_modifiers = terrain_response.data[0] if terrain_response.data else {}
        
        # Prepare environment data
        environment = {
            "avg_temp": data['weather'].get('temp', 25),
            "avg_rainfall": data['weather'].get('rainfall', 800),
            "humidity": data['weather'].get('humidity', 70),
            "wind_speed": data['weather'].get('wind', 10),
            "elevation": data.get('elevation', 100),
            "terrain": data['terrain'],
            "latitude": data['location']['lat'],
            "longitude": data['location']['lon']
        }
        
        # Initialize penalty engine
        penalty_engine = PenaltyEngine(crop_profile, environment, terrain_modifiers)
        
        # Determine if this is an override scenario
        is_override = penalty_engine.check_compatibility()
        
        # Run Monte Carlo simulation
        simulator = MonteCarloSimulator(
            crop_profile=crop_profile,
            environment=environment,
            penalty_engine=penalty_engine,
            runs=10000
        )
        
        results = simulator.run()
        
        # Compute metrics
        success_rate, avg_yield, risk_level, yield_range = compute_metrics(results)
        
        # Generate explanation
        explanation = generate_explanation(results, crop_profile, environment, is_override)
        
        # Save simulation to database
        simulation_record = {
            "crop_name": data['crop'],
            "latitude": data['location']['lat'],
            "longitude": data['location']['lon'],
            "terrain": data['terrain'],
            "success_probability": success_rate,
            "expected_yield": avg_yield,
            "risk_level": risk_level,
            "is_override": is_override
        }
        supabase.table('simulations').insert(simulation_record).execute()
        
        # Return response
        return jsonify({
            "success_probability": round(success_rate, 3),
            "expected_yield": round(avg_yield, 2),
            "risk_level": risk_level,
            "explanation": explanation,
            "is_override": is_override,
            "yield_range": {
                "min": round(yield_range[0], 2),
                "avg": round(yield_range[1], 2),
                "max": round(yield_range[2], 2)
            },
            "simulation_runs": len(results)
        })
        
    except Exception as e:
        app.logger.error(f"Simulation error: {str(e)}")
        return jsonify({"error": f"Simulation failed: {str(e)}"}), 500

@app.route('/api/simulations/history', methods=['GET'])
def get_simulation_history():
    """Fetch simulation history"""
    try:
        limit = int(request.args.get('limit', 50))
        response = supabase.table('simulations').select('*').order(
            'created_at', desc=True
        ).limit(limit).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)