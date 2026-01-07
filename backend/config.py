import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Weather API
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    
    # Simulation
    DEFAULT_SIMULATION_RUNS = int(os.getenv('DEFAULT_SIMULATION_RUNS', 10000))
    MAX_SIMULATION_RUNS = int(os.getenv('MAX_SIMULATION_RUNS', 50000))
    
    # CORS
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        required = ['SUPABASE_URL', 'SUPABASE_KEY']
        missing = [key for key in required if not os.getenv(key)]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True