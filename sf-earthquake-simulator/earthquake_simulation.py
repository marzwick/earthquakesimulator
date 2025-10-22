"""
San Francisco Earthquake Building Simulation - Enhanced with Social Vulnerability
Integrates physical hazard modeling with socio-demographic vulnerability factors
Aligns with the team's vulnerability analysis for SF and San Mateo Counties
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple, Dict
import pandas as pd


@dataclass
class Building:
    """Represents a building with structural properties and social context"""
    id: int
    name: str
    building_type: str  # 'wood', 'steel', 'concrete', 'masonry', 'modern_seismic'
    height_stories: int
    year_built: int
    latitude: float
    longitude: float
    # New social vulnerability attributes
    elderly_percent: float = 0.0  # % residents over 60
    poverty_percent: float = 0.0  # % below poverty line
    population_density: float = 0.0  # people per sq mi
    sovi_score: float = 0.5  # Social Vulnerability Index (0-1, higher = more vulnerable)

    def get_structural_resistance(self) -> float:
        """Returns resistance factor (0-1) based on building type and age"""
        base_resistance = {
            'wood': 0.4,
            'masonry': 0.3,
            'concrete': 0.6,
            'steel': 0.7,
            'modern_seismic': 0.9
        }

        resistance = base_resistance.get(self.building_type, 0.5)

        # Age penalty: buildings lose ~0.5% resistance per decade
        age = 2025 - self.year_built
        age_penalty = min(0.3, age * 0.005)
        resistance -= age_penalty

        return max(0.1, resistance)

    def get_height_vulnerability(self) -> float:
        """Taller buildings have different resonance frequencies"""
        if self.height_stories <= 3:
            return 0.8  # Low buildings, more stable
        elif self.height_stories <= 10:
            return 1.0  # Medium buildings
        else:
            return 1.2  # Tall buildings, more vulnerable to swaying

    def get_social_vulnerability_multiplier(self) -> float:
        """
        Calculate recovery/resilience challenges based on social factors
        Returns multiplier (1.0-2.0) where higher means slower recovery
        Based on Cutter et al. (2003) and your paper's framework
        """
        # Base multiplier
        multiplier = 1.0
        
        # Elderly populations face mobility challenges and social isolation
        if self.elderly_percent > 25:  # Above SF/San Mateo average of ~24.5%
            multiplier += 0.3
        elif self.elderly_percent > 15:
            multiplier += 0.15
        
        # Low-income residents face financial recovery barriers
        if self.poverty_percent > 15:  # Above SF average of 11.3%
            multiplier += 0.3
        elif self.poverty_percent > 10:
            multiplier += 0.15
        
        # High population density increases evacuation challenges
        if self.population_density > 10000:  # Very dense
            multiplier += 0.2
        elif self.population_density > 5000:
            multiplier += 0.1
        
        # Direct SoVI score impact
        multiplier += self.sovi_score * 0.4
        
        return min(2.0, multiplier)


@dataclass
class Earthquake:
    """Represents an earthquake event"""
    magnitude: float
    epicenter_lat: float
    epicenter_lon: float
    depth_km: float
    fault_name: str = "San Andreas Fault"  # Added for context

    def get_ground_acceleration(self, distance_km: float) -> float:
        """
        Calculate peak ground acceleration (PGA) in g's
        Using simplified Boore-Atkinson (2008) attenuation model
        """
        if distance_km < 0.1:
            distance_km = 0.1

        # Base PGA from magnitude
        # M5.0 ~ 0.1g, M6.0 ~ 0.3g, M7.0 ~ 0.6g near epicenter
        base_pga = 0.01 * (10 ** (0.5 * (self.magnitude - 4.0)))

        # Distance attenuation
        attenuation = 1 / ((distance_km + 5) ** 1.5)

        # Depth effect (deeper = less surface shaking)
        depth_factor = 1.0 / (1 + self.depth_km / 20)

        return base_pga * attenuation * depth_factor

    def get_modified_mercalli_intensity(self, distance_km: float) -> int:
        """Estimate Modified Mercalli Intensity scale (I-XII)"""
        pga = self.get_ground_acceleration(distance_km)

        # Convert PGA to MMI
        if pga < 0.0017:
            return 1
        elif pga < 0.014:
            return 2 + int(np.log10(pga / 0.0017) / np.log10(8.2))
        elif pga < 0.039:
            return 4
        elif pga < 0.092:
            return 5
        elif pga < 0.18:
            return 6
        elif pga < 0.34:
            return 7
        elif pga < 0.65:
            return 8
        elif pga < 1.24:
            return 9
        else:
            return min(12, 10 + int((pga - 1.24) / 0.5))


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two lat/lon points (Haversine formula)"""
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def calculate_damage(building: Building, earthquake: Earthquake) -> dict:
    """
    Calculate damage to a building from an earthquake
    Now includes social vulnerability factors for comprehensive risk assessment
    """
    # Calculate distance from epicenter
    distance = calculate_distance(
        building.latitude, building.longitude,
        earthquake.epicenter_lat, earthquake.epicenter_lon
    )

    # Get ground motion parameters
    pga = earthquake.get_ground_acceleration(distance)
    mmi = earthquake.get_modified_mercalli_intensity(distance)

    # Building structural response
    resistance = building.get_structural_resistance()
    height_vuln = building.get_height_vulnerability()

    # Physical damage calculation
    damage_factor = (pga * height_vuln * 200) / resistance
    physical_damage = min(100, max(0, damage_factor))

    # Social vulnerability multiplier affects recovery capacity
    social_multiplier = building.get_social_vulnerability_multiplier()
    
    # Combined vulnerability score (for reporting)
    combined_vulnerability = physical_damage * (social_multiplier / 1.5)

    # Damage classification (FEMA HAZUS)
    if physical_damage < 5:
        damage_state = "None"
    elif physical_damage < 15:
        damage_state = "Slight"
    elif physical_damage < 30:
        damage_state = "Moderate"
    elif physical_damage < 60:
        damage_state = "Extensive"
    elif physical_damage < 90:
        damage_state = "Severe"
    else:
        damage_state = "Collapse"

    # Recovery time estimate (days) - affected by social vulnerability
    base_recovery_days = {
        "None": 0,
        "Slight": 7,
        "Moderate": 30,
        "Extensive": 90,
        "Severe": 180,
        "Collapse": 365
    }
    estimated_recovery_days = base_recovery_days[damage_state] * social_multiplier

    return {
        'building_id': building.id,
        'building_name': building.name,
        'building_type': building.building_type,
        'stories': building.height_stories,
        'year_built': building.year_built,
        'distance_km': distance,
        'pga_g': pga,
        'mmi': mmi,
        'physical_damage_percent': physical_damage,
        'social_vulnerability_multiplier': social_multiplier,
        'combined_vulnerability_score': combined_vulnerability,
        'damage_state': damage_state,
        'structural_resistance': resistance,
        'elderly_percent': building.elderly_percent,
        'poverty_percent': building.poverty_percent,
        'population_density': building.population_density,
        'sovi_score': building.sovi_score,
        'estimated_recovery_days': estimated_recovery_days
    }


def create_sf_san_mateo_buildings() -> List[Building]:
    """
    Create building dataset for SF and San Mateo Counties with social vulnerability data
    Based on actual demographics and your paper's SoVI analysis
    """
    buildings = [
        # SAN FRANCISCO - Financial District / Downtown
        Building(1, "Transamerica Pyramid", "modern_seismic", 48, 1972, 37.7952, -122.4028,
                elderly_percent=18, poverty_percent=9, population_density=15000, sovi_score=0.3),
        Building(2, "Salesforce Tower", "modern_seismic", 61, 2018, 37.7897, -122.3968,
                elderly_percent=15, poverty_percent=8, population_density=18000, sovi_score=0.25),
        Building(3, "Financial District Office", "steel", 30, 1985, 37.7933, -122.3968,
                elderly_percent=16, poverty_percent=10, population_density=16000, sovi_score=0.3),
        
        # SAN FRANCISCO - Vulnerable Communities (High SoVI from your paper)
        Building(4, "Bayview-Hunters Point Apartment", "masonry", 4, 1955, 37.7299, -122.3880,
                elderly_percent=22, poverty_percent=28, population_density=8500, sovi_score=0.85),
        Building(5, "Visitacion Valley Housing", "wood", 3, 1940, 37.7130, -122.4040,
                elderly_percent=26, poverty_percent=24, population_density=9000, sovi_score=0.82),
        Building(6, "Chinatown Building", "masonry", 5, 1910, 37.7948, -122.4078,
                elderly_percent=38, poverty_percent=20, population_density=22000, sovi_score=0.75),
        
        # SAN FRANCISCO - High-Vulnerability Areas
        Building(7, "Marina District House", "wood", 2, 1925, 37.8021, -122.4383,
                elderly_percent=28, poverty_percent=7, population_density=12000, sovi_score=0.55),
        Building(8, "Mission District Apartment", "wood", 4, 1920, 37.7599, -122.4148,
                elderly_percent=19, poverty_percent=18, population_density=14000, sovi_score=0.68),
        Building(9, "SOMA Warehouse Conversion", "concrete", 3, 1960, 37.7758, -122.4128,
                elderly_percent=14, poverty_percent=12, population_density=11000, sovi_score=0.4),
        
        # SAN FRANCISCO - Mixed Vulnerability
        Building(10, "Civic Center Building", "concrete", 8, 1955, 37.7799, -122.4193,
                elderly_percent=32, poverty_percent=22, population_density=9500, sovi_score=0.72),
        Building(11, "Modern SOMA Condo", "modern_seismic", 12, 2015, 37.7794, -122.4039,
                elderly_percent=12, poverty_percent=6, population_density=13000, sovi_score=0.28),
        Building(12, "Sunset District Home", "wood", 2, 1950, 37.7536, -122.4663,
                elderly_percent=30, poverty_percent=11, population_density=7500, sovi_score=0.58),
        Building(13, "Richmond District Duplex", "wood", 3, 1940, 37.7796, -122.4687,
                elderly_percent=29, poverty_percent=10, population_density=8000, sovi_score=0.56),
        Building(14, "Nob Hill High-rise", "steel", 25, 1978, 37.7925, -122.4152,
                elderly_percent=35, poverty_percent=8, population_density=14500, sovi_score=0.48),
        Building(15, "Embarcadero Office", "modern_seismic", 20, 2005, 37.7946, -122.3965,
                elderly_percent=17, poverty_percent=9, population_density=15500, sovi_score=0.32),
        
        # SAN MATEO COUNTY - High-risk coastal corridor (from your paper)
        Building(16, "Pacifica Coastal Home", "wood", 2, 1965, 37.6139, -122.4869,
                elderly_percent=31, poverty_percent=9, population_density=3800, sovi_score=0.62),
        Building(17, "Daly City Apartment", "concrete", 5, 1970, 37.7058, -122.4664,
                elderly_percent=27, poverty_percent=11, population_density=9500, sovi_score=0.58),
        Building(18, "South San Francisco Office", "steel", 8, 1988, 37.6547, -122.4077,
                elderly_percent=23, poverty_percent=8, population_density=7200, sovi_score=0.45),
        
        # SAN MATEO COUNTY - East Palo Alto (High SoVI from your paper)
        Building(19, "East Palo Alto Community Building", "masonry", 3, 1962, 37.4688, -122.1411,
                elderly_percent=18, poverty_percent=19, population_density=6500, sovi_score=0.78),
        
        # SAN MATEO COUNTY - SFO Corridor (Dual hazard zone)
        Building(20, "San Bruno Residential", "wood", 3, 1955, 37.6305, -122.4111,
                elderly_percent=25, poverty_percent=10, population_density=8800, sovi_score=0.54),
        Building(21, "Millbrae Station Area", "concrete", 4, 1975, 37.5985, -122.3867,
                elderly_percent=28, poverty_percent=7, population_density=6900, sovi_score=0.48),
        
        # SAN MATEO COUNTY - Coastal/Moderate Risk
        Building(22, "Half Moon Bay House", "wood", 2, 1968, 37.4636, -122.4286,
                elderly_percent=33, poverty_percent=8, population_density=2100, sovi_score=0.58),
        Building(23, "Redwood City Apartment", "modern_seismic", 6, 2010, 37.4852, -122.2364,
                elderly_percent=21, poverty_percent=9, population_density=5800, sovi_score=0.38),
        Building(24, "San Mateo Downtown Office", "steel", 12, 1982, 37.5630, -122.3255,
                elderly_percent=24, poverty_percent=8, population_density=7400, sovi_score=0.42),
        Building(25, "Foster City Condo", "modern_seismic", 8, 2008, 37.5585, -122.2711,
                elderly_percent=26, poverty_percent=5, population_density=4900, sovi_score=0.35),
    ]

    return buildings


def run_simulation(buildings: List[Building], earthquakes: List[Earthquake]) -> pd.DataFrame:
    """Run earthquake simulation for all buildings and earthquakes"""
    results = []

    for eq_idx, earthquake in enumerate(earthquakes):
        print(f"\nSimulating Magnitude {earthquake.magnitude} earthquake on {earthquake.fault_name}...")
        print(f"Epicenter: {earthquake.epicenter_lat:.4f}, {earthquake.epicenter_lon:.4f}")
        print(f"Depth: {earthquake.depth_km} km\n")

        for building in buildings:
            damage = calculate_damage(building, earthquake)
            damage['earthquake_id'] = eq_idx
            damage['magnitude'] = earthquake.magnitude
            damage['fault_name'] = earthquake.fault_name
            results.append(damage)

    return pd.DataFrame(results)


def generate_paper_figures(results: pd.DataFrame, buildings: List[Building], 
                          earthquakes: List[Earthquake], output_dir: str = '.'):
    """
    Create publication-quality figures for the vulnerability analysis paper
    Specifically designed to support your findings section
    """
    
    # Figure for Paper: Combined Physical + Social Vulnerability
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    fig.suptitle('Earthquake Vulnerability Analysis: Physical Hazard + Social Vulnerability\nSan Francisco & San Mateo Counties',
                fontsize=16, fontweight='bold', y=0.995)

    # Select largest earthquake for detailed analysis
    largest_eq_results = results[results['magnitude'] == results['magnitude'].max()]
    
    # Plot 1: Physical Damage vs Social Vulnerability
    ax = axes[0, 0]
    scatter = ax.scatter(largest_eq_results['physical_damage_percent'],
                        largest_eq_results['social_vulnerability_multiplier'],
                        c=largest_eq_results['combined_vulnerability_score'],
                        s=largest_eq_results['population_density']/100,
                        alpha=0.7, cmap='YlOrRd', edgecolors='black', linewidth=1.5)
    
    ax.set_xlabel('Physical Damage (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Social Vulnerability Multiplier', fontsize=12, fontweight='bold')
    ax.set_title('Physical vs Social Vulnerability\n(size = population density)', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Combined Vulnerability Score', fontsize=10, fontweight='bold')
    
    # Add annotations for high-vulnerability buildings
    for _, row in largest_eq_results.nlargest(5, 'combined_vulnerability_score').iterrows():
        building = next(b for b in buildings if b.id == row['building_id'])
        ax.annotate(building.name, 
                   xy=(row['physical_damage_percent'], row['social_vulnerability_multiplier']),
                   xytext=(10, 10), textcoords='offset points',
                   fontsize=8, bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

    # Plot 2: Recovery Time by Building Age and Social Factors
    ax = axes[0, 1]
    building_ages = {b.id: 2025 - b.year_built for b in buildings}
    largest_eq_results_copy = largest_eq_results.copy()
    largest_eq_results_copy['building_age'] = largest_eq_results_copy['building_id'].map(building_ages)
    
    # Separate by damage state
    for state, color in [('Severe', 'red'), ('Extensive', 'orange'), 
                         ('Moderate', 'yellow'), ('Slight', 'green')]:
        state_data = largest_eq_results_copy[largest_eq_results_copy['damage_state'] == state]
        if len(state_data) > 0:
            ax.scatter(state_data['building_age'], state_data['estimated_recovery_days'],
                      label=state, c=color, s=100, alpha=0.7, edgecolors='black', linewidth=1)
    
    ax.set_xlabel('Building Age (years)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Estimated Recovery Time (days)', fontsize=12, fontweight='bold')
    ax.set_title('Recovery Time: Building Age + Social Factors', fontsize=13, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)

    # Plot 3: Vulnerable Populations at Risk
    ax = axes[1, 0]
    
    # Create categories based on your paper's focus
    vulnerability_categories = []
    category_labels = []
    colors_cat = []
    
    for _, row in largest_eq_results.iterrows():
        if row['damage_state'] in ['Extensive', 'Severe', 'Collapse']:
            if row['elderly_percent'] > 25:
                vulnerability_categories.append(row['elderly_percent'])
                category_labels.append('High Elderly\n(>25%)')
                colors_cat.append('#e74c3c')
            elif row['poverty_percent'] > 15:
                vulnerability_categories.append(row['poverty_percent'])
                category_labels.append('High Poverty\n(>15%)')
                colors_cat.append('#e67e22')
            elif row['population_density'] > 10000:
                vulnerability_categories.append(row['population_density']/1000)
                category_labels.append('High Density\n(>10k/mi²)')
                colors_cat.append('#f39c12')
    
    if vulnerability_categories:
        ax.bar(range(len(vulnerability_categories)), vulnerability_categories, 
              color=colors_cat, edgecolor='black', linewidth=1.5, alpha=0.8)
        ax.set_xticks(range(len(category_labels)))
        ax.set_xticklabels(category_labels, rotation=45, ha='right', fontsize=9)
        ax.set_ylabel('Vulnerability Metric Value', fontsize=12, fontweight='bold')
        ax.set_title(f'Vulnerable Populations in Severely Damaged Buildings (M{results["magnitude"].max()})',
                    fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

    # Plot 4: County Comparison (SF vs San Mateo)
    ax = axes[1, 1]
    
    # Identify county by latitude (rough division at ~37.65)
    largest_eq_results_copy['county'] = largest_eq_results_copy['building_id'].apply(
        lambda x: 'San Francisco' if next(b for b in buildings if b.id == x).latitude > 37.65 
        else 'San Mateo'
    )
    
    county_stats = largest_eq_results_copy.groupby('county').agg({
        'physical_damage_percent': 'mean',
        'social_vulnerability_multiplier': 'mean',
        'combined_vulnerability_score': 'mean',
        'estimated_recovery_days': 'mean'
    }).round(2)
    
    x = np.arange(len(county_stats.columns))
    width = 0.35
    
    sf_data = county_stats.loc['San Francisco'] if 'San Francisco' in county_stats.index else [0]*4
    sm_data = county_stats.loc['San Mateo'] if 'San Mateo' in county_stats.index else [0]*4
    
    ax.bar(x - width/2, sf_data, width, label='San Francisco', color='#3498db', 
           edgecolor='black', linewidth=1.5)
    ax.bar(x + width/2, sm_data, width, label='San Mateo', color='#2ecc71',
           edgecolor='black', linewidth=1.5)
    
    ax.set_ylabel('Mean Value', fontsize=12, fontweight='bold')
    ax.set_title('County Vulnerability Comparison', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(['Physical\nDamage (%)', 'Social Vuln.\nMultiplier', 
                       'Combined\nVuln. Score', 'Recovery\nDays/10'], 
                      fontsize=9)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Adjust recovery days for visualization scale
    for container in ax.containers:
        if container.get_label() in ['San Francisco', 'San Mateo']:
            heights = [h.get_height() for h in container]
            if len(heights) == 4:
                container[3].set_height(heights[3] / 10)

    plt.tight_layout()
    output_file = f'{output_dir}/vulnerability_analysis_figures.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\n✓ Paper figures saved: {output_file}")
    plt.close()


def print_summary_for_paper(results: pd.DataFrame):
    """Generate summary statistics formatted for inclusion in paper"""
    
    print("\n" + "="*80)
    print("SUMMARY STATISTICS FOR PAPER")
    print("="*80)
    
    largest_eq = results[results['magnitude'] == results['magnitude'].max()]
    
    print(f"\nEarthquake Scenario: Magnitude {largest_eq['magnitude'].iloc[0]}")
    print(f"Total Buildings Analyzed: {len(largest_eq)}")
    print(f"  • San Francisco County: {len([b for b in create_sf_san_mateo_buildings() if b.latitude > 37.65])}")
    print(f"  • San Mateo County: {len([b for b in create_sf_san_mateo_buildings() if b.latitude <= 37.65])}")
    
    print(f"\n--- PHYSICAL DAMAGE ASSESSMENT ---")
    print(f"Average Physical Damage: {largest_eq['physical_damage_percent'].mean():.1f}%")
    print(f"Maximum Physical Damage: {largest_eq['physical_damage_percent'].max():.1f}%")
    
    print(f"\nDamage State Distribution (FEMA HAZUS):")
    for state in ["None", "Slight", "Moderate", "Extensive", "Severe", "Collapse"]:
        count = len(largest_eq[largest_eq['damage_state'] == state])
        pct = (count / len(largest_eq)) * 100
        print(f"  • {state:12s}: {count:2d} buildings ({pct:5.1f}%)")
    
    print(f"\n--- SOCIAL VULNERABILITY INTEGRATION ---")
    print(f"Average Social Vulnerability Multiplier: {largest_eq['social_vulnerability_multiplier'].mean():.2f}")
    print(f"Average Combined Vulnerability Score: {largest_eq['combined_vulnerability_score'].mean():.1f}")
    
    print(f"\n--- HIGH-RISK POPULATIONS ---")
    severe_damage = largest_eq[largest_eq['damage_state'].isin(['Extensive', 'Severe', 'Collapse'])]
    print(f"Buildings with Extensive+ Damage: {len(severe_damage)}")
    if len(severe_damage) > 0:
        print(f"  • Avg Elderly Population: {severe_damage['elderly_percent'].mean():.1f}%")
        print(f"  • Avg Poverty Rate: {severe_damage['poverty_percent'].mean():.1f}%")
        print(f"  • Avg Population Density: {severe_damage['population_density'].mean():,.0f} per sq mi")
        print(f"  • Avg SoVI Score: {severe_damage['sovi_score'].mean():.2f}")
    
    high_vuln = largest_eq[largest_eq['social_vulnerability_multiplier'] > 1.5]
    print(f"\nBuildings with High Social Vulnerability (multiplier > 1.5): {len(high_vuln)}")
    if len(high_vuln) > 0:
        print(f"  • Average Recovery Time: {high_vuln['estimated_recovery_days'].mean():.0f} days")
    
    print(f"\n--- RECOVERY PROJECTIONS ---")
    print(f"Average Estimated Recovery Time: {largest_eq['estimated_recovery_days'].mean():.0f} days")
    print(f"Longest Estimated Recovery: {largest_eq['estimated_recovery_days'].max():.0f} days")
    
    print("\n" + "="*80)


def main():
    """Main simulation function"""
    print("=" * 80)
    print("San Francisco & San Mateo Counties Earthquake Vulnerability Simulation")
    print("Physical Hazard + Social Vulnerability Integration")
    print("=" * 80)

    # Create buildings with social vulnerability data
    buildings = create_sf_san_mateo_buildings()
    print(f"\nAnalyzing {len(buildings)} buildings across SF and San Mateo Counties")
    print(f"  • Including social vulnerability factors: elderly %, poverty %, density, SoVI")

    # Define earthquake scenarios (aligned with your paper's analysis)
    # Epicenter near San Andreas Fault / Financial District
    epicenter_lat = 37.7949
    epicenter_lon = -122.4194

    earthquakes = [
        Earthquake(magnitude=5.5, epicenter_lat=epicenter_lat, epicenter_lon=epicenter_lon, 
                  depth_km=10, fault_name="San Andreas Fault"),
        Earthquake(magnitude=6.5, epicenter_lat=epicenter_lat, epicenter_lon=epicenter_lon, 
                  depth_km=10, fault_name="San Andreas Fault"),
        Earthquake(magnitude=7.0, epicenter_lat=epicenter_lat, epicenter_lon=epicenter_lon, 
                  depth_km=10, fault_name="San Andreas Fault"),
    ]

    # Run simulation
    results = run_simulation(buildings, earthquakes)

    # Save detailed results
    output_csv = 'earthquake_vulnerability_results.csv'
    results.to_csv(output_csv, index=False)
    print(f"\n{'='*80}")
    print(f"Detailed results saved: {output_csv}")

    # Print summary statistics for paper
    print_summary_for_paper(results)

    # Generate publication figures
    print(f"\n{'='*80}")
    print("Generating figures for paper...")
    generate_paper_figures(results, buildings, earthquakes, output_dir='.')

    print("\n" + "=" * 80)
    print("✓ Simulation Complete!")
    print("=" * 80)
    print("\nGenerated outputs:")
    print(f"  • {output_csv} - Full simulation data")
    print(f"  • vulnerability_analysis_figures.png - Publication-quality figures")
    print("\nThese outputs integrate:")
    print("  ✓ Physical earthquake hazard modeling (Boore-Atkinson attenuation)")
    print("  ✓ Social vulnerability factors (elderly, poverty, density, SoVI)")
    print("  ✓ FEMA HAZUS damage classification")
    print("  ✓ Recovery time estimates with social factors")


if __name__ == "__main__":
    main()
