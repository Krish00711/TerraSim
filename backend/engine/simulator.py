import random
import numpy as np
from typing import List, Dict, Tuple

class MonteCarloSimulator:
    """
    Monte Carlo simulation engine for agricultural yield prediction.
    Runs thousands of randomized scenarios to compute probabilistic outcomes.
    """
    
    def __init__(self, crop_profile: Dict, environment: Dict, penalty_engine, runs: int = 10000):
        """
        Initialize simulator
        
        Args:
            crop_profile: Crop requirements from database
            environment: Environmental conditions
            penalty_engine: PenaltyEngine instance
            runs: Number of simulation iterations
        """
        self.crop = crop_profile
        self.env = environment
        self.penalty_engine = penalty_engine
        self.runs = runs
        self.results = []
        
        # Extract crop requirements
        self.temp_min = crop_profile.get('temp_min', 15)
        self.temp_max = crop_profile.get('temp_max', 35)
        self.rainfall_min = crop_profile.get('rainfall_min', 500)
        self.rainfall_max = crop_profile.get('rainfall_max', 2000)
        self.ideal_yield = crop_profile.get('ideal_yield', 5000)
        self.humidity_tolerance = crop_profile.get('humidity_tolerance', 0.7)
        
    def run(self) -> List[Dict]:
        """
        Execute Monte Carlo simulation
        
        Returns:
            List of simulation results, each containing success status, yield, and reasons
        """
        for iteration in range(self.runs):
            # Randomize environmental factors with realistic variance
            temp = self._randomize_temperature()
            rainfall = self._randomize_rainfall()
            humidity = self._randomize_humidity()
            wind = self._randomize_wind()
            
            # Simulate random events (pests, disease, extreme weather)
            pest_event = random.random() < 0.05  # 5% chance
            disease_event = random.random() < 0.03  # 3% chance
            extreme_weather = random.random() < 0.02  # 2% chance
            
            # Evaluate this simulation run
            success, yield_value, limiting_factors = self._evaluate_run(
                temp, rainfall, humidity, wind,
                pest_event, disease_event, extreme_weather
            )
            
            self.results.append({
                "success": success,
                "yield": yield_value,
                "limiting_factors": limiting_factors,
                "temp": temp,
                "rainfall": rainfall,
                "humidity": humidity,
                "had_pest": pest_event,
                "had_disease": disease_event,
                "had_extreme_weather": extreme_weather
            })
        
        return self.results
    
    def _randomize_temperature(self) -> float:
        """Generate randomized temperature with seasonal variance"""
        base_temp = self.env['avg_temp']
        # Standard deviation of 3°C to simulate daily/seasonal variation
        return random.gauss(base_temp, 3.0)
    
    def _randomize_rainfall(self) -> float:
        """Generate randomized rainfall with high variance"""
        base_rainfall = self.env['avg_rainfall']
        # Rainfall has high variance (20-30%)
        std_dev = base_rainfall * 0.25
        return max(0, random.gauss(base_rainfall, std_dev))
    
    def _randomize_humidity(self) -> float:
        """Generate randomized humidity"""
        base_humidity = self.env['humidity']
        # Lower variance for humidity (10%)
        return max(0, min(100, random.gauss(base_humidity, 10)))
    
    def _randomize_wind(self) -> float:
        """Generate randomized wind speed"""
        base_wind = self.env['wind_speed']
        return max(0, random.gauss(base_wind, base_wind * 0.3))
    
    def _evaluate_run(
        self, 
        temp: float, 
        rainfall: float, 
        humidity: float, 
        wind: float,
        pest_event: bool,
        disease_event: bool,
        extreme_weather: bool
    ) -> Tuple[bool, float, List[str]]:
        """
        Evaluate a single simulation run
        
        Returns:
            (success, yield_value, limiting_factors)
        """
        limiting_factors = []
        penalty_multiplier = 1.0
        
        # Temperature stress
        if temp < self.temp_min:
            deficit = self.temp_min - temp
            limiting_factors.append(f"Temperature {deficit:.1f}°C below minimum")
            penalty_multiplier *= (1 - min(0.8, deficit / 10))
        elif temp > self.temp_max:
            excess = temp - self.temp_max
            limiting_factors.append(f"Temperature {excess:.1f}°C above maximum")
            penalty_multiplier *= (1 - min(0.8, excess / 10))
        
        # Rainfall stress
        if rainfall < self.rainfall_min:
            deficit = self.rainfall_min - rainfall
            limiting_factors.append(f"Rainfall deficit of {deficit:.0f}mm")
            penalty_multiplier *= (1 - min(0.9, deficit / self.rainfall_min))
        elif rainfall > self.rainfall_max:
            excess = rainfall - self.rainfall_max
            limiting_factors.append(f"Excessive rainfall: {excess:.0f}mm over limit")
            penalty_multiplier *= (1 - min(0.7, excess / self.rainfall_max * 0.5))
        
        # Humidity stress
        optimal_humidity = 65
        humidity_diff = abs(humidity - optimal_humidity)
        if humidity_diff > 20:
            limiting_factors.append(f"Suboptimal humidity ({humidity:.0f}%)")
            penalty_multiplier *= 0.95
        
        # Wind damage
        if wind > 40:
            limiting_factors.append(f"High wind speed ({wind:.1f} km/h)")
            penalty_multiplier *= 0.9
        
        # Random events
        if pest_event:
            limiting_factors.append("Pest infestation event")
            penalty_multiplier *= 0.7
        
        if disease_event:
            limiting_factors.append("Disease outbreak event")
            penalty_multiplier *= 0.6
        
        if extreme_weather:
            limiting_factors.append("Extreme weather event")
            penalty_multiplier *= 0.5
        
        # Apply terrain-based penalties from penalty engine
        terrain_penalty = self.penalty_engine.calculate_terrain_penalty()
        penalty_multiplier *= (1 - terrain_penalty)
        
        # Apply mismatch penalties for override scenarios
        mismatch_penalty = self.penalty_engine.calculate_mismatch_penalty(
            temp, rainfall, humidity
        )
        penalty_multiplier *= (1 - mismatch_penalty)
        
        # Calculate final yield
        final_yield = self.ideal_yield * penalty_multiplier
        
        # Determine success (threshold: yield > 30% of ideal)
        success = final_yield > (self.ideal_yield * 0.3) and penalty_multiplier > 0.4
        
        return success, max(0, final_yield), limiting_factors