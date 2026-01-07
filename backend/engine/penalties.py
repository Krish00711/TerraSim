from typing import Dict

class PenaltyEngine:
    """
    Calculates penalties for environmental mismatches and terrain constraints.
    Critical for handling crop override scenarios where users select unsuitable crops.
    """
    
    def __init__(self, crop_profile: Dict, environment: Dict, terrain_modifiers: Dict):
        """
        Initialize penalty engine
        
        Args:
            crop_profile: Crop requirements and tolerances
            environment: Current environmental conditions
            terrain_modifiers: Terrain-specific adjustment factors
        """
        self.crop = crop_profile
        self.env = environment
        self.terrain_mods = terrain_modifiers
        
        # Extract crop requirements
        self.temp_min = crop_profile.get('temp_min', 15)
        self.temp_max = crop_profile.get('temp_max', 35)
        self.rainfall_min = crop_profile.get('rainfall_min', 500)
        self.rainfall_max = crop_profile.get('rainfall_max', 2000)
        
    def check_compatibility(self) -> bool:
        """
        Check if crop is fundamentally incompatible with location.
        Returns True if this is an override scenario.
        """
        temp = self.env['avg_temp']
        rainfall = self.env['avg_rainfall']
        
        # Major temperature mismatch
        temp_mismatch = (
            temp < self.temp_min - 5 or 
            temp > self.temp_max + 5
        )
        
        # Major rainfall mismatch
        rainfall_deficit = rainfall < self.rainfall_min * 0.6
        rainfall_excess = rainfall > self.rainfall_max * 1.5
        
        return temp_mismatch or rainfall_deficit or rainfall_excess
    
    def calculate_terrain_penalty(self) -> float:
        """
        Calculate penalty based on terrain suitability.
        
        Returns:
            Penalty factor (0.0 to 1.0, where 1.0 = total failure)
        """
        terrain_type = self.env.get('terrain', 'plain')
        
        # Get modifiers from database or use defaults
        water_retention = self.terrain_mods.get('water_retention_factor', 1.0)
        soil_depth = self.terrain_mods.get('soil_depth_factor', 1.0)
        erosion_risk = self.terrain_mods.get('erosion_risk', 0.0)
        
        penalty = 0.0
        
        # Water retention impact (critical for crops needing consistent moisture)
        if water_retention < 0.7:
            penalty += (0.7 - water_retention) * 0.3
        
        # Soil depth impact (critical for deep-rooted crops)
        if soil_depth < 0.8:
            penalty += (0.8 - soil_depth) * 0.2
        
        # Erosion risk (mountain/steep slopes)
        if erosion_risk > 0.5:
            penalty += erosion_risk * 0.25
        
        # Terrain-specific adjustments
        if terrain_type == 'mountain':
            if self.crop.get('root_depth', 'medium') == 'deep':
                penalty += 0.15  # Shallow soil on mountains
            penalty += 0.1  # General difficulty
        
        elif terrain_type == 'coastal':
            if self.crop.get('salt_tolerance', 'low') == 'low':
                penalty += 0.25  # Salt spray damage
        
        return min(penalty, 0.9)  # Cap at 90%
    
    def calculate_mismatch_penalty(
        self, 
        temp: float, 
        rainfall: float, 
        humidity: float
    ) -> float:
        """
        Calculate penalty for environmental parameter mismatches.
        This is the core of the override penalty system.
        
        Args:
            temp: Actual temperature in this simulation run
            rainfall: Actual rainfall in this simulation run
            humidity: Actual humidity in this simulation run
            
        Returns:
            Penalty factor (0.0 to 1.0)
        """
        penalty = 0.0
        
        # Temperature penalty (progressive)
        if temp < self.temp_min:
            deficit = self.temp_min - temp
            # Severe penalty for major mismatches
            if deficit > 10:
                penalty += 0.5
            elif deficit > 5:
                penalty += 0.3
            else:
                penalty += deficit / 20
        
        elif temp > self.temp_max:
            excess = temp - self.temp_max
            if excess > 10:
                penalty += 0.5
            elif excess > 5:
                penalty += 0.3
            else:
                penalty += excess / 20
        
        # Rainfall penalty (critical factor)
        if rainfall < self.rainfall_min:
            deficit_pct = 1 - (rainfall / self.rainfall_min)
            # Water deficit is often catastrophic
            if deficit_pct > 0.5:
                penalty += 0.6
            elif deficit_pct > 0.3:
                penalty += 0.4
            else:
                penalty += deficit_pct * 0.5
        
        elif rainfall > self.rainfall_max:
            excess_pct = (rainfall - self.rainfall_max) / self.rainfall_max
            # Waterlogging penalty
            if excess_pct > 0.5:
                penalty += 0.4
            else:
                penalty += excess_pct * 0.3
        
        # Humidity penalty (moderate impact)
        optimal_humidity = 65
        humidity_diff = abs(humidity - optimal_humidity)
        if humidity_diff > 25:
            penalty += 0.1
        
        return min(penalty, 0.95)  # Cap at 95%
    
    def get_mismatch_summary(self) -> Dict[str, str]:
        """
        Generate human-readable summary of major mismatches.
        Used for explanation generation.
        """
        mismatches = {}
        
        temp = self.env['avg_temp']
        rainfall = self.env['avg_rainfall']
        
        if temp < self.temp_min:
            mismatches['temperature'] = f"Temperature is {self.temp_min - temp:.1f}°C below minimum requirement"
        elif temp > self.temp_max:
            mismatches['temperature'] = f"Temperature is {temp - self.temp_max:.1f}°C above maximum tolerance"
        
        if rainfall < self.rainfall_min:
            deficit_pct = (1 - rainfall / self.rainfall_min) * 100
            mismatches['rainfall'] = f"Rainfall is {deficit_pct:.0f}% below minimum requirement"
        elif rainfall > self.rainfall_max:
            excess_pct = ((rainfall - self.rainfall_max) / self.rainfall_max) * 100
            mismatches['rainfall'] = f"Rainfall is {excess_pct:.0f}% above maximum tolerance"
        
        terrain = self.env.get('terrain', 'plain')
        if terrain in ['mountain', 'plateau']:
            mismatches['terrain'] = f"Terrain type '{terrain}' may cause water runoff and soil erosion issues"
        
        return mismatches