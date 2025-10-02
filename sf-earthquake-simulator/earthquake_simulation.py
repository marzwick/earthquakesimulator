"""
San Francisco Earthquake Building Simulation
Simulates the effects of earthquakes of varying magnitudes on different building types
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple
import pandas as pd


@dataclass
class Building:
    """Represents a building with structural properties"""
    id: int
    name: str
    building_type: str  # 'wood', 'steel', 'concrete', 'masonry', 'modern_seismic'
    height_stories: int
    year_built: int
    latitude: float
    longitude: float

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


@dataclass
class Earthquake:
    """Represents an earthquake event"""
    magnitude: float
    epicenter_lat: float
    epicenter_lon: float
    depth_km: float

    def get_ground_acceleration(self, distance_km: float) -> float:
        """Calculate peak ground acceleration (PGA) in g's"""
        # Simplified attenuation model
        if distance_km < 0.1:
            distance_km = 0.1

        # Base PGA from magnitude using more realistic scaling
        # M5.0 ~ 0.1g, M6.0 ~ 0.3g, M7.0 ~ 0.6g near epicenter
        base_pga = 0.01 * (10 ** (0.5 * (self.magnitude - 4.0)))

        # Distance attenuation with more realistic decay
        attenuation = 1 / ((distance_km + 5) ** 1.5)

        # Depth effect (deeper = less surface shaking)
        depth_factor = 1.0 / (1 + self.depth_km / 20)

        return base_pga * attenuation * depth_factor

    def get_modified_mercalli_intensity(self, distance_km: float) -> int:
        """Estimate Modified Mercalli Intensity scale (I-XII)"""
        pga = self.get_ground_acceleration(distance_km)

        # Convert PGA to MMI (simplified)
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
    """Calculate distance in km between two lat/lon points"""
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def calculate_damage(building: Building, earthquake: Earthquake) -> dict:
    """Calculate damage to a building from an earthquake"""
    # Calculate distance from epicenter
    distance = calculate_distance(
        building.latitude, building.longitude,
        earthquake.epicenter_lat, earthquake.epicenter_lon
    )

    # Get ground motion parameters
    pga = earthquake.get_ground_acceleration(distance)
    mmi = earthquake.get_modified_mercalli_intensity(distance)

    # Building response
    resistance = building.get_structural_resistance()
    height_vuln = building.get_height_vulnerability()

    # Damage calculation (0-100%)
    # Scale PGA impact more realistically
    # Use exponential scaling to show more dramatic effects at higher magnitudes
    damage_factor = (pga * height_vuln * 200) / resistance
    damage_percent = min(100, max(0, damage_factor))

    # Damage classification
    if damage_percent < 5:
        damage_state = "None"
    elif damage_percent < 15:
        damage_state = "Slight"
    elif damage_percent < 30:
        damage_state = "Moderate"
    elif damage_percent < 60:
        damage_state = "Extensive"
    elif damage_percent < 90:
        damage_state = "Severe"
    else:
        damage_state = "Collapse"

    return {
        'building_id': building.id,
        'building_name': building.name,
        'building_type': building.building_type,
        'stories': building.height_stories,
        'distance_km': distance,
        'pga_g': pga,
        'mmi': mmi,
        'damage_percent': damage_percent,
        'damage_state': damage_state,
        'structural_resistance': resistance
    }


def create_sf_buildings() -> List[Building]:
    """Create a sample set of buildings in San Francisco"""
    # Notable SF locations (approximate coordinates)
    buildings = [
        Building(1, "Transamerica Pyramid", "modern_seismic", 48, 1972, 37.7952, -122.4028),
        Building(2, "Salesforce Tower", "modern_seismic", 61, 2018, 37.7897, -122.3968),
        Building(3, "Financial District Office", "steel", 30, 1985, 37.7933, -122.3968),
        Building(4, "Victorian Home (Pacific Heights)", "wood", 3, 1895, 37.7930, -122.4334),
        Building(5, "Mission District Apartment", "wood", 4, 1920, 37.7599, -122.4148),
        Building(6, "Chinatown Building", "masonry", 5, 1910, 37.7948, -122.4078),
        Building(7, "Marina District House", "wood", 2, 1925, 37.8021, -122.4383),
        Building(8, "SOMA Warehouse", "concrete", 3, 1960, 37.7758, -122.4128),
        Building(9, "Civic Center Building", "concrete", 8, 1955, 37.7799, -122.4193),
        Building(10, "Modern Condo (SOMA)", "modern_seismic", 12, 2015, 37.7794, -122.4039),
        Building(11, "Sunset District Home", "wood", 2, 1950, 37.7536, -122.4663),
        Building(12, "Richmond District Duplex", "wood", 3, 1940, 37.7796, -122.4687),
        Building(13, "Hayes Valley Apartment", "masonry", 4, 1915, 37.7755, -122.4238),
        Building(14, "Nob Hill High-rise", "steel", 25, 1978, 37.7925, -122.4152),
        Building(15, "Embarcadero Office", "modern_seismic", 20, 2005, 37.7946, -122.3965),
    ]

    return buildings


def run_simulation(buildings: List[Building], earthquakes: List[Earthquake]) -> pd.DataFrame:
    """Run earthquake simulation for all buildings and earthquakes"""
    results = []

    for eq_idx, earthquake in enumerate(earthquakes):
        print(f"\nSimulating Magnitude {earthquake.magnitude} earthquake...")
        print(f"Epicenter: {earthquake.epicenter_lat:.4f}, {earthquake.epicenter_lon:.4f}")
        print(f"Depth: {earthquake.depth_km} km\n")

        for building in buildings:
            damage = calculate_damage(building, earthquake)
            damage['earthquake_id'] = eq_idx
            damage['magnitude'] = earthquake.magnitude
            results.append(damage)

    return pd.DataFrame(results)


def visualize_results(results: pd.DataFrame, buildings: List[Building], earthquakes: List[Earthquake]):
    """Create visualizations of simulation results"""

    # Figure 1: Damage by magnitude for each building type
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))

    # Plot 1: Damage vs Magnitude by Building Type
    ax = axes[0, 0]
    for btype in results['building_type'].unique():
        data = results[results['building_type'] == btype]
        avg_damage = data.groupby('magnitude')['damage_percent'].mean()
        ax.plot(avg_damage.index, avg_damage.values, marker='o', label=btype, linewidth=2)

    ax.set_xlabel('Earthquake Magnitude', fontsize=12)
    ax.set_ylabel('Average Damage (%)', fontsize=12)
    ax.set_title('Average Damage by Building Type and Magnitude', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 2: Damage State Distribution for Largest Earthquake
    ax = axes[0, 1]
    largest_eq = results[results['magnitude'] == results['magnitude'].max()]
    damage_counts = largest_eq['damage_state'].value_counts()
    damage_order = ["None", "Slight", "Moderate", "Extensive", "Severe", "Collapse"]
    damage_counts = damage_counts.reindex(damage_order, fill_value=0)

    colors = ['green', 'yellowgreen', 'yellow', 'orange', 'red', 'darkred']
    ax.bar(range(len(damage_counts)), damage_counts.values, color=colors)
    ax.set_xticks(range(len(damage_counts)))
    ax.set_xticklabels(damage_counts.index, rotation=45)
    ax.set_ylabel('Number of Buildings', fontsize=12)
    ax.set_title(f'Damage Distribution (M{results["magnitude"].max()})', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    # Plot 3: Damage vs Distance
    ax = axes[1, 0]
    for mag in sorted(results['magnitude'].unique()):
        data = results[results['magnitude'] == mag]
        ax.scatter(data['distance_km'], data['damage_percent'],
                  alpha=0.6, s=60, label=f'M{mag}')

    ax.set_xlabel('Distance from Epicenter (km)', fontsize=12)
    ax.set_ylabel('Damage (%)', fontsize=12)
    ax.set_title('Damage vs Distance from Epicenter', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 4: Building Age vs Damage (for largest earthquake)
    ax = axes[1, 1]
    largest_eq_data = results[results['magnitude'] == results['magnitude'].max()].copy()
    building_years = {b.id: b.year_built for b in buildings}
    largest_eq_data['year_built'] = largest_eq_data['building_id'].map(building_years)
    largest_eq_data['age'] = 2025 - largest_eq_data['year_built']

    scatter = ax.scatter(largest_eq_data['age'], largest_eq_data['damage_percent'],
                        c=largest_eq_data['stories'], s=100, alpha=0.6, cmap='viridis')
    ax.set_xlabel('Building Age (years)', fontsize=12)
    ax.set_ylabel('Damage (%)', fontsize=12)
    ax.set_title(f'Age vs Damage (M{results["magnitude"].max()})', fontsize=14, fontweight='bold')
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Stories', fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/Users/marazwicker/earthquake_simulation_results.png', dpi=300, bbox_inches='tight')
    print("\nVisualization saved as 'earthquake_simulation_results.png'")

    # Figure 2: Map view of damage for largest earthquake
    fig, ax = plt.subplots(figsize=(12, 10))

    largest_eq_idx = results['magnitude'].idxmax()
    largest_eq = earthquakes[results.loc[largest_eq_idx, 'earthquake_id']]
    largest_eq_results = results[results['magnitude'] == largest_eq.magnitude]

    # Plot buildings
    for _, row in largest_eq_results.iterrows():
        building = next(b for b in buildings if b.id == row['building_id'])

        # Color by damage state
        damage_colors = {
            "None": 'green',
            "Slight": 'yellowgreen',
            "Moderate": 'yellow',
            "Extensive": 'orange',
            "Severe": 'red',
            "Collapse": 'darkred'
        }
        color = damage_colors.get(row['damage_state'], 'gray')

        # Size by building height
        size = 100 + building.height_stories * 10

        ax.scatter(building.longitude, building.latitude,
                  c=color, s=size, alpha=0.7, edgecolors='black', linewidth=1)

    # Plot epicenter
    ax.scatter(largest_eq.epicenter_lon, largest_eq.epicenter_lat,
              marker='*', c='red', s=1000, edgecolors='black', linewidth=2,
              label=f'Epicenter (M{largest_eq.magnitude})', zorder=10)

    # Draw circles for distance reference
    for radius_km in [5, 10, 15]:
        # Approximate degree conversion (at SF latitude)
        deg_per_km = 1 / 111.0
        circle = plt.Circle((largest_eq.epicenter_lon, largest_eq.epicenter_lat),
                          radius_km * deg_per_km, fill=False,
                          linestyle='--', color='gray', alpha=0.5)
        ax.add_patch(circle)
        ax.text(largest_eq.epicenter_lon + radius_km * deg_per_km,
               largest_eq.epicenter_lat, f'{radius_km}km',
               fontsize=9, color='gray')

    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    ax.set_title(f'San Francisco Earthquake Damage Map (M{largest_eq.magnitude})',
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    ax.set_aspect('equal')

    plt.tight_layout()
    plt.savefig('/Users/marazwicker/earthquake_damage_map.png', dpi=300, bbox_inches='tight')
    print("Map visualization saved as 'earthquake_damage_map.png'")


def main():
    """Main simulation function"""
    print("=" * 70)
    print("San Francisco Earthquake Building Simulation")
    print("=" * 70)

    # Create buildings
    buildings = create_sf_buildings()
    print(f"\nSimulating {len(buildings)} buildings in San Francisco")

    # Define earthquake scenarios
    # Epicenter near downtown SF (approximately Financial District)
    epicenter_lat = 37.7949
    epicenter_lon = -122.4194

    earthquakes = [
        Earthquake(magnitude=4.5, epicenter_lat=epicenter_lat, epicenter_lon=epicenter_lon, depth_km=10),
        Earthquake(magnitude=5.5, epicenter_lat=epicenter_lat, epicenter_lon=epicenter_lon, depth_km=10),
        Earthquake(magnitude=6.5, epicenter_lat=epicenter_lat, epicenter_lon=epicenter_lon, depth_km=10),
        Earthquake(magnitude=7.0, epicenter_lat=epicenter_lat, epicenter_lon=epicenter_lon, depth_km=10),
        Earthquake(magnitude=7.5, epicenter_lat=epicenter_lat, epicenter_lon=epicenter_lon, depth_km=10),
    ]

    # Run simulation
    results = run_simulation(buildings, earthquakes)

    # Save detailed results
    results.to_csv('/Users/marazwicker/earthquake_simulation_results.csv', index=False)
    print("\n" + "=" * 70)
    print(f"Detailed results saved to 'earthquake_simulation_results.csv'")

    # Print summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)

    for magnitude in sorted(results['magnitude'].unique()):
        mag_data = results[results['magnitude'] == magnitude]
        print(f"\nMagnitude {magnitude}:")
        print(f"  Average Damage: {mag_data['damage_percent'].mean():.1f}%")
        print(f"  Max Damage: {mag_data['damage_percent'].max():.1f}%")
        print(f"  Buildings with Severe/Collapse: {len(mag_data[mag_data['damage_state'].isin(['Severe', 'Collapse'])])}")
        print(f"  Damage State Distribution:")
        for state in ["None", "Slight", "Moderate", "Extensive", "Severe", "Collapse"]:
            count = len(mag_data[mag_data['damage_state'] == state])
            if count > 0:
                print(f"    {state}: {count}")

    # Create visualizations
    print("\n" + "=" * 70)
    print("Generating visualizations...")
    visualize_results(results, buildings, earthquakes)

    print("\n" + "=" * 70)
    print("Simulation complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
