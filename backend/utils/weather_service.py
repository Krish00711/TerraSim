import requests
from typing import Dict, Optional

class WeatherService:
    """
    Service for fetching real-time weather data from external APIs.
    Supports multiple providers with fallback mechanisms.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize weather service
        
        Args:
            api_key: API key for weather service (OpenWeatherMap recommended)
        """
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    def get_current_weather(self, lat: float, lon: float) -> Dict:
        """
        Fetch current weather data for given coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with weather data
        """
        if not self.api_key:
            # Return mock data if no API key provided
            return self._get_mock_weather_data(lat, lon)
        
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'temp': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'wind': data['wind']['speed'] * 3.6,  # Convert m/s to km/h
                'rainfall': self._estimate_annual_rainfall(data),
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description']
            }
            
        except Exception as e:
            print(f"Weather API error: {str(e)}")
            return self._get_mock_weather_data(lat, lon)
    
    def _estimate_annual_rainfall(self, weather_data: Dict) -> float:
        """
        Estimate annual rainfall from current weather data.
        This is a simplified estimation - ideally use historical climate data.
        
        Args:
            weather_data: Current weather response
            
        Returns:
            Estimated annual rainfall in mm
        """
        # If rain data is available in last hour
        if 'rain' in weather_data and '1h' in weather_data['rain']:
            hourly_rain = weather_data['rain']['1h']
            # Very rough estimation: multiply by hours in year
            return hourly_rain * 8760 * 0.1  # Scale factor for realism
        
        # Fallback: estimate based on humidity and location
        humidity = weather_data['main']['humidity']
        
        # Simple heuristic based on humidity
        if humidity > 80:
            return 1500  # High rainfall region
        elif humidity > 60:
            return 1000  # Moderate rainfall
        else:
            return 600  # Low rainfall region
    
    def _get_mock_weather_data(self, lat: float, lon: float) -> Dict:
        """
        Generate realistic mock weather data based on latitude.
        Used when API is unavailable or for testing.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Mock weather dictionary
        """
        # Estimate climate zone based on latitude
        abs_lat = abs(lat)
        
        if abs_lat < 23.5:  # Tropical
            return {
                'temp': 28,
                'humidity': 75,
                'wind': 12,
                'rainfall': 1800,
                'pressure': 1013,
                'description': 'tropical climate (mock data)'
            }
        elif abs_lat < 35:  # Subtropical
            return {
                'temp': 22,
                'humidity': 65,
                'wind': 15,
                'rainfall': 900,
                'pressure': 1015,
                'description': 'subtropical climate (mock data)'
            }
        elif abs_lat < 60:  # Temperate
            return {
                'temp': 15,
                'humidity': 70,
                'wind': 18,
                'rainfall': 700,
                'pressure': 1012,
                'description': 'temperate climate (mock data)'
            }
        else:  # Polar
            return {
                'temp': -5,
                'humidity': 80,
                'wind': 25,
                'rainfall': 300,
                'pressure': 1010,
                'description': 'polar climate (mock data)'
            }
    
    def get_historical_climate(self, lat: float, lon: float) -> Dict:
        """
        Fetch historical climate averages (if API supports it).
        This would provide more accurate baseline data for simulations.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Historical climate data
        """
        # Placeholder for historical data integration
        # Could integrate with APIs like Climate Data Online (CDO)
        return {
            'avg_temp_annual': 20,
            'avg_rainfall_annual': 1000,
            'temp_variance': 5,
            'rainfall_variance': 200
        }