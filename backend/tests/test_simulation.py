import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.simulator import MonteCarloSimulator
from engine.penalties import PenaltyEngine
from engine.scoring import compute_metrics, calculate_risk_level
from engine.explainability import generate_explanation
from utils.validators import validate_input, validate_crop_profile

# ============================================
# Test Data Fixtures
# ============================================

@pytest.fixture
def sample_crop_profile():
    """Sample crop profile for testing"""
    return {
        'id': 'test-id',
        'name': 'Test Wheat',
        'category': 'cereal',
        'temp_min': 10,
        'temp_max': 25,
        'temp_optimal': 18,
        'rainfall_min': 400,
        'rainfall_max': 900,
        'rainfall_optimal': 650,
        'ideal_yield': 4500,
        'humidity_tolerance': 0.7,
        'root_depth': 'medium',
        'salt_tolerance': 'low'
    }

@pytest.fixture
def good_environment():
    """Favorable environmental conditions"""
    return {
        'avg_temp': 18,
        'avg_rainfall': 650,
        'humidity': 65,
        'wind_speed': 10,
        'elevation': 100,
        'terrain': 'plain',
        'latitude': 28.7,
        'longitude': 77.1
    }

@pytest.fixture
def poor_environment():
    """Unfavorable environmental conditions (override scenario)"""
    return {
        'avg_temp': 35,  # Too hot
        'avg_rainfall': 200,  # Too dry
        'humidity': 30,
        'wind_speed': 25,
        'elevation': 100,
        'terrain': 'mountain',
        'latitude': 28.7,
        'longitude': 77.1
    }

@pytest.fixture
def terrain_modifiers():
    """Standard terrain modifiers"""
    return {
        'water_retention_factor': 1.0,
        'soil_depth_factor': 1.0,
        'erosion_risk': 0.1,
        'drainage_quality': 0.9
    }

# ============================================
# Validator Tests
# ============================================

class TestValidators:
    """Test input validation functions"""
    
    def test_valid_input(self):
        """Test validation with correct input"""
        valid_data = {
            'crop': 'Wheat',
            'location': {'lat': 28.7, 'lon': 77.1},
            'terrain': 'plain',
            'weather': {
                'temp': 20,
                'humidity': 60,
                'rainfall': 700,
                'wind': 15
            }
        }
        assert validate_input(valid_data) is None
    
    def test_missing_required_fields(self):
        """Test validation fails with missing fields"""
        invalid_data = {
            'crop': 'Wheat',
            'location': {'lat': 28.7, 'lon': 77.1}
            # Missing terrain
        }
        error = validate_input(invalid_data)
        assert error is not None
        assert 'terrain' in error.lower()
    
    def test_invalid_latitude(self):
        """Test validation fails with invalid latitude"""
        invalid_data = {
            'crop': 'Wheat',
            'location': {'lat': 100, 'lon': 77.1},  # Invalid lat
            'terrain': 'plain'
        }
        error = validate_input(invalid_data)
        assert error is not None
        assert 'latitude' in error.lower()
    
    def test_invalid_terrain(self):
        """Test validation fails with invalid terrain"""
        invalid_data = {
            'crop': 'Wheat',
            'location': {'lat': 28.7, 'lon': 77.1},
            'terrain': 'invalid_terrain'
        }
        error = validate_input(invalid_data)
        assert error is not None
    
    def test_crop_profile_validation(self, sample_crop_profile):
        """Test crop profile validation"""
        assert validate_crop_profile(sample_crop_profile) is None
        
        # Test invalid profile
        invalid_profile = sample_crop_profile.copy()
        invalid_profile['temp_min'] = 30
        invalid_profile['temp_max'] = 20  # Min > Max
        error = validate_crop_profile(invalid_profile)
        assert error is not None

# ============================================
# Penalty Engine Tests
# ============================================

class TestPenaltyEngine:
    """Test penalty calculation system"""
    
    def test_compatible_conditions(self, sample_crop_profile, good_environment, terrain_modifiers):
        """Test that compatible conditions don't trigger override"""
        penalty_engine = PenaltyEngine(
            sample_crop_profile,
            good_environment,
            terrain_modifiers
        )
        
        is_override = penalty_engine.check_compatibility()
        assert is_override is False
    
    def test_incompatible_conditions(self, sample_crop_profile, poor_environment, terrain_modifiers):
        """Test that incompatible conditions trigger override"""
        penalty_engine = PenaltyEngine(
            sample_crop_profile,
            poor_environment,
            terrain_modifiers
        )
        
        is_override = penalty_engine.check_compatibility()
        assert is_override is True
    
    def test_terrain_penalty_calculation(self, sample_crop_profile, good_environment, terrain_modifiers):
        """Test terrain penalty calculation"""
        penalty_engine = PenaltyEngine(
            sample_crop_profile,
            good_environment,
            terrain_modifiers
        )
        
        penalty = penalty_engine.calculate_terrain_penalty()
        assert 0 <= penalty <= 1
        assert penalty < 0.2  # Should be low for good conditions
    
    def test_mismatch_penalty_temperature(self, sample_crop_profile, good_environment, terrain_modifiers):
        """Test temperature mismatch penalty"""
        penalty_engine = PenaltyEngine(
            sample_crop_profile,
            good_environment,
            terrain_modifiers
        )
        
        # Test with optimal temperature
        penalty_optimal = penalty_engine.calculate_mismatch_penalty(18, 650, 65)
        
        # Test with too hot temperature
        penalty_hot = penalty_engine.calculate_mismatch_penalty(35, 650, 65)
        
        assert penalty_hot > penalty_optimal
        assert penalty_hot > 0.3  # Significant penalty
    
    def test_mismatch_penalty_rainfall(self, sample_crop_profile, good_environment, terrain_modifiers):
        """Test rainfall mismatch penalty"""
        penalty_engine = PenaltyEngine(
            sample_crop_profile,
            good_environment,
            terrain_modifiers
        )
        
        # Test with optimal rainfall
        penalty_optimal = penalty_engine.calculate_mismatch_penalty(18, 650, 65)
        
        # Test with insufficient rainfall
        penalty_dry = penalty_engine.calculate_mismatch_penalty(18, 200, 65)
        
        assert penalty_dry > penalty_optimal
        assert penalty_dry > 0.4  # High penalty for water deficit

# ============================================
# Simulator Tests
# ============================================

class TestMonteCarloSimulator:
    """Test Monte Carlo simulation engine"""
    
    def test_simulator_runs(self, sample_crop_profile, good_environment, terrain_modifiers):
        """Test that simulator completes all runs"""
        penalty_engine = PenaltyEngine(
            sample_crop_profile,
            good_environment,
            terrain_modifiers
        )
        
        simulator = MonteCarloSimulator(
            sample_crop_profile,
            good_environment,
            penalty_engine,
            runs=100  # Small number for testing
        )
        
        results = simulator.run()
        assert len(results) == 100
    
    def test_simulator_good_conditions(self, sample_crop_profile, good_environment, terrain_modifiers):
        """Test simulator with favorable conditions"""
        penalty_engine = PenaltyEngine(
            sample_crop_profile,
            good_environment,
            terrain_modifiers
        )
        
        simulator = MonteCarloSimulator(
            sample_crop_profile,
            good_environment,
            penalty_engine,
            runs=1000
        )
        
        results = simulator.run()
        success_count = sum(1 for r in results if r['success'])
        success_rate = success_count / len(results)
        
        # With good conditions, success rate should be high
        assert success_rate > 0.7
    
    def test_simulator_poor_conditions(self, sample_crop_profile, poor_environment, terrain_modifiers):
        """Test simulator with unfavorable conditions"""
        penalty_engine = PenaltyEngine(
            sample_crop_profile,
            poor_environment,
            terrain_modifiers
        )
        
        simulator = MonteCarloSimulator(
            sample_crop_profile,
            poor_environment,
            penalty_engine,
            runs=1000
        )
        
        results = simulator.run()
        success_count = sum(1 for r in results if r['success'])
        success_rate = success_count / len(results)
        
        # With poor conditions, success rate should be low
        assert success_rate < 0.5
    
    def test_result_structure(self, sample_crop_profile, good_environment, terrain_modifiers):
        """Test that results have correct structure"""
        penalty_engine = PenaltyEngine(
            sample_crop_profile,
            good_environment,
            terrain_modifiers
        )
        
        simulator = MonteCarloSimulator(
            sample_crop_profile,
            good_environment,
            penalty_engine,
            runs=10
        )
        
        results = simulator.run()
        
        for result in results:
            assert 'success' in result
            assert 'yield' in result
            assert 'limiting_factors' in result
            assert isinstance(result['success'], bool)
            assert isinstance(result['yield'], (int, float))
            assert isinstance(result['limiting_factors'], list)

# ============================================
# Scoring Tests
# ============================================

class TestScoring:
    """Test scoring and risk calculation"""
    
    def test_compute_metrics(self):
        """Test metric computation"""
        mock_results = [
            {'success': True, 'yield': 4500, 'limiting_factors': []},
            {'success': True, 'yield': 4300, 'limiting_factors': []},
            {'success': True, 'yield': 4700, 'limiting_factors': []},
            {'success': False, 'yield': 1000, 'limiting_factors': ['Temperature stress']},
        ]
        
        success_rate, avg_yield, risk_level, yield_range = compute_metrics(mock_results)
        
        assert 0 <= success_rate <= 1
        assert success_rate == 0.75  # 3 out of 4
        assert avg_yield > 0
        assert risk_level in ['Low', 'Medium', 'High']
        assert len(yield_range) == 3
    
    def test_risk_level_calculation(self):
        """Test risk level categorization"""
        # High success, low variability = Low risk
        risk = calculate_risk_level(0.9, 500, 4500, [
            {'success': True, 'yield': 4500, 'limiting_factors': [], 'had_pest': False, 'had_disease': False, 'had_extreme_weather': False}
        ] * 100)
        assert risk == 'Low'
        
        # Low success = High risk
        risk = calculate_risk_level(0.3, 2000, 2000, [
            {'success': False, 'yield': 0, 'limiting_factors': ['Multiple'], 'had_pest': False, 'had_disease': False, 'had_extreme_weather': False}
        ] * 100)
        assert risk == 'High'

# ============================================
# Explainability Tests
# ============================================

class TestExplainability:
    """Test explanation generation"""
    
    def test_positive_explanation(self, sample_crop_profile, good_environment):
        """Test explanation for favorable conditions"""
        results = [
            {'success': True, 'yield': 4500, 'limiting_factors': []}
            for _ in range(100)
        ]
        
        explanation = generate_explanation(
            results,
            sample_crop_profile,
            good_environment,
            is_override=False
        )
        
        assert len(explanation) > 0
        assert 'excellent' in explanation.lower() or 'good' in explanation.lower()
    
    def test_override_explanation(self, sample_crop_profile, poor_environment):
        """Test explanation for override scenario"""
        results = [
            {'success': False, 'yield': 500, 'limiting_factors': ['Temperature stress', 'Rainfall deficit']}
            for _ in range(100)
        ]
        
        explanation = generate_explanation(
            results,
            sample_crop_profile,
            poor_environment,
            is_override=True
        )
        
        assert len(explanation) > 0
        assert 'override' in explanation.lower()
        assert 'not recommended' in explanation.lower()
    
    def test_explanation_with_limiting_factors(self, sample_crop_profile, good_environment):
        """Test explanation identifies limiting factors"""
        results = [
            {'success': False, 'yield': 2000, 'limiting_factors': ['Temperature stress']}
            for _ in range(80)
        ] + [
            {'success': True, 'yield': 4000, 'limiting_factors': []}
            for _ in range(20)
        ]
        
        explanation = generate_explanation(
            results,
            sample_crop_profile,
            good_environment,
            is_override=False
        )
        
        assert 'temperature' in explanation.lower()

# ============================================
# Integration Tests
# ============================================

class TestIntegration:
    """Integration tests for complete simulation flow"""
    
    def test_full_simulation_flow(self, sample_crop_profile, good_environment, terrain_modifiers):
        """Test complete simulation from input to output"""
        # Initialize components
        penalty_engine = PenaltyEngine(
            sample_crop_profile,
            good_environment,
            terrain_modifiers
        )
        
        # Run simulation
        simulator = MonteCarloSimulator(
            sample_crop_profile,
            good_environment,
            penalty_engine,
            runs=1000
        )
        results = simulator.run()
        
        # Compute metrics
        success_rate, avg_yield, risk_level, yield_range = compute_metrics(results)
        
        # Generate explanation
        is_override = penalty_engine.check_compatibility()
        explanation = generate_explanation(
            results,
            sample_crop_profile,
            good_environment,
            is_override
        )
        
        # Validate complete output
        assert 0 <= success_rate <= 1
        assert avg_yield >= 0
        assert risk_level in ['Low', 'Medium', 'High']
        assert len(explanation) > 50  # Should have substantial explanation
        assert isinstance(is_override, bool)

# ============================================
# Run Tests
# ============================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])