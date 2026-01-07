from typing import List, Dict
from collections import Counter

def generate_explanation(
    results: List[Dict], 
    crop_profile: Dict, 
    environment: Dict,
    is_override: bool
) -> str:
    """
    Generate plain-language explanation of simulation results.
    This is critical for user trust and educational value.
    
    Args:
        results: Simulation run results
        crop_profile: Crop requirements
        environment: Environmental conditions
        is_override: Whether this is an override scenario
        
    Returns:
        Human-readable explanation string
    """
    total_runs = len(results)
    successful_runs = [r for r in results if r['success']]
    success_rate = len(successful_runs) / total_runs if total_runs else 0
    
    # Collect all limiting factors across all runs
    all_factors = []
    for run in results:
        all_factors.extend(run['limiting_factors'])
    
    # If no limiting factors, generate positive explanation
    if not all_factors:
        return generate_positive_explanation(crop_profile, environment, success_rate)
    
    # Count factor occurrences
    factor_counts = Counter()
    for factor in all_factors:
        # Categorize factors
        if 'Temperature' in factor:
            factor_counts['Temperature Stress'] += 1
        elif 'Rainfall' in factor or 'rainfall' in factor:
            factor_counts['Water Availability'] += 1
        elif 'humidity' in factor:
            factor_counts['Humidity Imbalance'] += 1
        elif 'wind' in factor or 'Wind' in factor:
            factor_counts['Wind Damage'] += 1
        elif 'Pest' in factor:
            factor_counts['Pest Infestation'] += 1
        elif 'Disease' in factor:
            factor_counts['Disease Outbreak'] += 1
        elif 'Extreme' in factor:
            factor_counts['Extreme Weather Events'] += 1
    
    # Get top factors
    top_factors = factor_counts.most_common(3)
    
    # Build explanation
    if is_override:
        explanation = generate_override_explanation(
            top_factors, 
            total_runs, 
            success_rate,
            crop_profile,
            environment
        )
    else:
        explanation = generate_standard_explanation(
            top_factors,
            total_runs,
            success_rate
        )
    
    return explanation

def generate_positive_explanation(crop_profile: Dict, environment: Dict, success_rate: float) -> str:
    """Generate explanation when conditions are favorable"""
    crop_name = crop_profile.get('name', 'the selected crop')
    
    if success_rate >= 0.9:
        return (
            f"Excellent conditions for {crop_name} cultivation. Environmental parameters "
            f"are well within the optimal range. Temperature, rainfall, and humidity levels "
            f"consistently support healthy crop development across simulation scenarios. "
            f"The risk of crop failure is minimal under current conditions."
        )
    elif success_rate >= 0.7:
        return (
            f"Good conditions for {crop_name} cultivation. Most environmental factors align "
            f"well with crop requirements. Minor variability in weather patterns may cause "
            f"slight yield fluctuations, but overall success probability remains strong. "
            f"Standard agricultural practices should yield positive results."
        )
    else:
        return (
            f"Moderate conditions for {crop_name}. While basic requirements are met, "
            f"environmental variability introduces uncertainty. Consider implementing "
            f"mitigation strategies such as irrigation systems or protective measures "
            f"to improve success probability."
        )

def generate_standard_explanation(
    top_factors: List[tuple],
    total_runs: int,
    success_rate: float
) -> str:
    """Generate explanation for standard (non-override) scenarios"""
    
    if not top_factors:
        return "Simulation completed without identifying major limiting factors."
    
    primary_factor, primary_count = top_factors[0]
    primary_frequency = (primary_count / total_runs) * 100
    
    explanation_parts = []
    
    # Primary limiting factor
    explanation_parts.append(
        f"The primary limiting factor is {primary_factor}, which affected "
        f"{primary_frequency:.1f}% of simulation runs."
    )
    
    # Add context based on the factor
    if primary_factor == 'Temperature Stress':
        explanation_parts.append(
            "Temperature variations outside the crop's tolerance range significantly "
            "impact germination, growth rate, and reproductive success. Consider selecting "
            "temperature-tolerant varieties or adjusting planting schedules."
        )
    elif primary_factor == 'Water Availability':
        explanation_parts.append(
            "Insufficient or excessive rainfall creates water stress that limits nutrient "
            "uptake and can cause root damage. Irrigation systems or improved drainage "
            "may mitigate this risk."
        )
    elif primary_factor in ['Pest Infestation', 'Disease Outbreak']:
        explanation_parts.append(
            "Random pest and disease events are inherent risks in agriculture. Integrated "
            "pest management and disease-resistant varieties can reduce impact."
        )
    elif primary_factor == 'Extreme Weather Events':
        explanation_parts.append(
            "Unpredictable extreme weather events pose significant risk. While these are "
            "rare, their impact can be severe. Insurance and diversification strategies "
            "are recommended."
        )
    
    # Secondary factors if present
    if len(top_factors) > 1:
        secondary_factor, secondary_count = top_factors[1]
        secondary_frequency = (secondary_count / total_runs) * 100
        explanation_parts.append(
            f"Secondary risk factor: {secondary_factor} ({secondary_frequency:.1f}% of runs)."
        )
    
    # Success rate context
    if success_rate >= 0.7:
        explanation_parts.append(
            "Despite these challenges, the overall success probability remains favorable "
            "with proper management practices."
        )
    elif success_rate >= 0.5:
        explanation_parts.append(
            "These factors create moderate risk. Consider risk mitigation strategies to "
            "improve outcomes."
        )
    else:
        explanation_parts.append(
            "Multiple risk factors significantly reduce success probability. Alternative "
            "crops or substantial environmental modifications may be necessary."
        )
    
    return " ".join(explanation_parts)

def generate_override_explanation(
    top_factors: List[tuple],
    total_runs: int,
    success_rate: float,
    crop_profile: Dict,
    environment: Dict
) -> str:
    """Generate explanation for override scenarios with explicit warnings"""
    
    crop_name = crop_profile.get('name', 'this crop')
    
    explanation_parts = [
        f"CROP OVERRIDE DETECTED: {crop_name.upper()} is not recommended for this location. "
        f"The simulation has applied environmental mismatch penalties."
    ]
    
    # Identify specific mismatches
    temp = environment['avg_temp']
    temp_min = crop_profile.get('temp_min', 15)
    temp_max = crop_profile.get('temp_max', 35)
    rainfall = environment['avg_rainfall']
    rainfall_min = crop_profile.get('rainfall_min', 500)
    rainfall_max = crop_profile.get('rainfall_max', 2000)
    
    mismatches = []
    if temp < temp_min:
        mismatches.append(
            f"Temperature is {temp_min - temp:.1f}°C below the minimum requirement "
            f"({temp_min}°C), causing severe germination and growth delays."
        )
    elif temp > temp_max:
        mismatches.append(
            f"Temperature is {temp - temp_max:.1f}°C above the maximum tolerance "
            f"({temp_max}°C), leading to heat stress and reduced photosynthesis."
        )
    
    if rainfall < rainfall_min:
        deficit_pct = ((rainfall_min - rainfall) / rainfall_min) * 100
        mismatches.append(
            f"Annual rainfall is {deficit_pct:.0f}% below minimum requirement "
            f"({rainfall_min}mm), creating chronic water stress."
        )
    elif rainfall > rainfall_max:
        excess_pct = ((rainfall - rainfall_max) / rainfall_max) * 100
        mismatches.append(
            f"Annual rainfall is {excess_pct:.0f}% above maximum tolerance "
            f"({rainfall_max}mm), risking waterlogging and root diseases."
        )
    
    if mismatches:
        explanation_parts.append(" ".join(mismatches))
    
    # Add primary limiting factor analysis
    if top_factors:
        primary_factor, primary_count = top_factors[0]
        primary_frequency = (primary_count / total_runs) * 100
        explanation_parts.append(
            f"{primary_factor} was the dominant failure cause in {primary_frequency:.1f}% "
            f"of simulation runs."
        )
    
    # Risk assessment
    if success_rate < 0.3:
        explanation_parts.append(
            "Success probability is critically low. This crop is highly unlikely to produce "
            "viable yields without substantial environmental modifications (e.g., greenhouse "
            "cultivation, advanced irrigation, climate control systems)."
        )
    elif success_rate < 0.5:
        explanation_parts.append(
            "Success probability is low. While not impossible, cultivation would require "
            "significant resource investment and carries high financial risk."
        )
    else:
        explanation_parts.append(
            "Despite the mismatch, some success scenarios exist. However, yields will be "
            "highly variable and below optimal levels."
        )
    
    return " ".join(explanation_parts)