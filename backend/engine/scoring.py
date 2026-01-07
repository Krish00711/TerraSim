from typing import List, Dict, Tuple
import numpy as np

def compute_metrics(results: List[Dict]) -> Tuple[float, float, str, Tuple[float, float, float]]:
    """
    Compute aggregate metrics from Monte Carlo simulation results.
    
    Args:
        results: List of simulation run results
        
    Returns:
        Tuple of (success_rate, avg_yield, risk_level, yield_range)
        where yield_range is (min, avg, max)
    """
    if not results:
        return 0.0, 0.0, "High", (0, 0, 0)
    
    total_runs = len(results)
    
    # Calculate success rate
    successful_runs = [r for r in results if r['success']]
    success_rate = len(successful_runs) / total_runs
    
    # Calculate yield statistics
    all_yields = [r['yield'] for r in results]
    successful_yields = [r['yield'] for r in successful_runs] if successful_runs else [0]
    
    avg_yield = np.mean(all_yields)
    min_yield = np.min(all_yields)
    max_yield = np.max(all_yields)
    yield_std = np.std(all_yields)
    
    # Calculate risk level based on multiple factors
    risk_level = calculate_risk_level(
        success_rate,
        yield_std,
        avg_yield,
        results
    )
    
    return (
        success_rate,
        avg_yield,
        risk_level,
        (min_yield, avg_yield, max_yield)
    )

def calculate_risk_level(
    success_rate: float,
    yield_std: float,
    avg_yield: float,
    results: List[Dict]
) -> str:
    """
    Calculate categorical risk level using multiple factors.
    
    Risk assessment considers:
    1. Success probability
    2. Yield variability (standard deviation)
    3. Frequency of catastrophic failures
    4. Presence of limiting factors
    
    Args:
        success_rate: Proportion of successful runs
        yield_std: Standard deviation of yield
        avg_yield: Average yield across all runs
        results: Full simulation results
        
    Returns:
        Risk level: "Low", "Medium", or "High"
    """
    risk_score = 0
    
    # Factor 1: Success rate (weighted 40%)
    if success_rate >= 0.85:
        risk_score += 0
    elif success_rate >= 0.70:
        risk_score += 1
    elif success_rate >= 0.50:
        risk_score += 2
    else:
        risk_score += 3
    
    # Factor 2: Yield variability (weighted 30%)
    # High variability = high risk
    if avg_yield > 0:
        coefficient_of_variation = yield_std / avg_yield
        if coefficient_of_variation > 0.5:
            risk_score += 2
        elif coefficient_of_variation > 0.3:
            risk_score += 1
    
    # Factor 3: Catastrophic failure rate (weighted 30%)
    # Count runs with near-zero yield
    catastrophic_failures = sum(1 for r in results if r['yield'] < avg_yield * 0.1)
    failure_rate = catastrophic_failures / len(results)
    
    if failure_rate > 0.15:
        risk_score += 2
    elif failure_rate > 0.05:
        risk_score += 1
    
    # Factor 4: Frequency of random adverse events
    pest_frequency = sum(1 for r in results if r.get('had_pest', False)) / len(results)
    disease_frequency = sum(1 for r in results if r.get('had_disease', False)) / len(results)
    extreme_weather_frequency = sum(1 for r in results if r.get('had_extreme_weather', False)) / len(results)
    
    adverse_event_rate = pest_frequency + disease_frequency + extreme_weather_frequency
    if adverse_event_rate > 0.12:  # Above expected combined rate
        risk_score += 1
    
    # Convert risk score to categorical level
    if risk_score <= 1:
        return "Low"
    elif risk_score <= 3:
        return "Medium"
    else:
        return "High"

def calculate_confidence_interval(yields: List[float], confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for yield estimates.
    
    Args:
        yields: List of yield values from simulations
        confidence: Confidence level (default 95%)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if not yields:
        return 0.0, 0.0
    
    sorted_yields = sorted(yields)
    n = len(sorted_yields)
    
    # Calculate percentile indices
    lower_idx = int(n * (1 - confidence) / 2)
    upper_idx = int(n * (1 + confidence) / 2)
    
    return sorted_yields[lower_idx], sorted_yields[upper_idx]

def analyze_failure_patterns(results: List[Dict]) -> Dict[str, float]:
    """
    Analyze patterns in failed simulations to identify primary risk factors.
    
    Args:
        results: Simulation results
        
    Returns:
        Dictionary mapping failure reasons to their frequency
    """
    failed_runs = [r for r in results if not r['success']]
    
    if not failed_runs:
        return {}
    
    # Count occurrences of each limiting factor
    factor_counts = {}
    for run in failed_runs:
        for factor in run['limiting_factors']:
            # Extract factor type (remove specific values)
            if 'Temperature' in factor:
                factor_type = 'Temperature Stress'
            elif 'Rainfall' in factor or 'rainfall' in factor:
                factor_type = 'Water Availability'
            elif 'humidity' in factor:
                factor_type = 'Humidity Issues'
            elif 'wind' in factor:
                factor_type = 'Wind Damage'
            elif 'Pest' in factor:
                factor_type = 'Pest Damage'
            elif 'Disease' in factor:
                factor_type = 'Disease Outbreak'
            elif 'Extreme' in factor:
                factor_type = 'Extreme Weather'
            else:
                factor_type = 'Other Factors'
            
            factor_counts[factor_type] = factor_counts.get(factor_type, 0) + 1
    
    # Convert to percentages
    total_failed = len(failed_runs)
    factor_percentages = {
        k: (v / total_failed) * 100 
        for k, v in factor_counts.items()
    }
    
    return dict(sorted(factor_percentages.items(), key=lambda x: x[1], reverse=True))