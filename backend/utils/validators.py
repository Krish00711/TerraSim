from typing import Dict, Optional

def validate_input(data: Dict) -> Optional[str]:
    """
    Validate simulation input data.
    
    Args:
        data: Input payload from API request
        
    Returns:
        Error message if validation fails, None otherwise
    """
    # Check required fields
    required_fields = ['crop', 'location', 'terrain']
    for field in required_fields:
        if field not in data:
            return f"Missing required field: {field}"
    
    # Validate crop
    if not isinstance(data['crop'], str) or not data['crop'].strip():
        return "Invalid crop name"
    
    # Validate location
    if not isinstance(data['location'], dict):
        return "Location must be an object with lat and lon"
    
    if 'lat' not in data['location'] or 'lon' not in data['location']:
        return "Location must contain lat and lon"
    
    try:
        lat = float(data['location']['lat'])
        lon = float(data['location']['lon'])
        
        if not (-90 <= lat <= 90):
            return "Latitude must be between -90 and 90"
        
        if not (-180 <= lon <= 180):
            return "Longitude must be between -180 and 180"
    except (ValueError, TypeError):
        return "Invalid latitude or longitude values"
    
    # Validate terrain
    valid_terrains = ['plain', 'plateau', 'mountain', 'valley', 'coastal']
    if data['terrain'] not in valid_terrains:
        return f"Terrain must be one of: {', '.join(valid_terrains)}"
    
    # Validate weather data if provided
    if 'weather' in data:
        weather = data['weather']
        
        if not isinstance(weather, dict):
            return "Weather must be an object"
        
        # Check temperature if provided
        if 'temp' in weather:
            try:
                temp = float(weather['temp'])
                if not (-50 <= temp <= 60):
                    return "Temperature must be between -50°C and 60°C"
            except (ValueError, TypeError):
                return "Invalid temperature value"
        
        # Check rainfall if provided
        if 'rainfall' in weather:
            try:
                rainfall = float(weather['rainfall'])
                if rainfall < 0:
                    return "Rainfall cannot be negative"
            except (ValueError, TypeError):
                return "Invalid rainfall value"
        
        # Check humidity if provided
        if 'humidity' in weather:
            try:
                humidity = float(weather['humidity'])
                if not (0 <= humidity <= 100):
                    return "Humidity must be between 0 and 100"
            except (ValueError, TypeError):
                return "Invalid humidity value"
    
    return None

def validate_crop_profile(crop: Dict) -> Optional[str]:
    """
    Validate crop profile from database.
    
    Args:
        crop: Crop profile dictionary
        
    Returns:
        Error message if invalid, None otherwise
    """
    required_fields = ['name', 'temp_min', 'temp_max', 'rainfall_min', 'rainfall_max', 'ideal_yield']
    
    for field in required_fields:
        if field not in crop:
            return f"Crop profile missing required field: {field}"
    
    # Validate numeric ranges
    if crop['temp_min'] >= crop['temp_max']:
        return "temp_min must be less than temp_max"
    
    if crop['rainfall_min'] >= crop['rainfall_max']:
        return "rainfall_min must be less than rainfall_max"
    
    if crop['ideal_yield'] <= 0:
        return "ideal_yield must be positive"
    
    return None