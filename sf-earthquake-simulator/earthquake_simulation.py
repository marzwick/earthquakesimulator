"""
San Francisco Earthquake Building Simulation
Complete working version with social vulnerability integration
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
    # Social vulnerability attributes (optional for backward compatibility)
    elderly_percent: float = 0.0
    poverty_percent: float = 0.0
    population_density: float = 0.0
    sovi_score: float = 0.5

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
            return 1.2  # Tall buildings, more vulnerable

    def get_social_vulnerability_multiplier(self) -> float:
        """
        Calculate recovery/resilience challenges based on social factors
        Returns multiplier (1.0-2.0) where higher means slower recovery
        """
        multiplier = 1.0
        
        # Elderly populations face mobility challenges
        if self.elderly_percent > 25:
            multiplier += 0.3
        elif self.elderly_percent > 15:
            multiplier += 0.15
        
        # Low-income residents face financial barriers
        if self.poverty_percent > 15:
            multiplier += 0.3
        elif self.poverty_percent > 10:
            multiplier += 0.15
        
        # High density increases evacuation challenges
        if self.population_density > 10000:
            multiplier += 0.2
        elif self.population_density > 5000:
            multiplier += 0.1
        
        # SoVI direct impact
        multiplier += self.sovi_score * 0.4
        
        return min(2.0, multiplier)


@dataclass
class Earthquake:
    """Represents an earthquake event"""
    magnitude: float
    epicenter_lat: float
    epicenter_lon: float
    depth_km: float
    fault_name: str = "San Andreas Fault"

    def get_ground_acceleration(self, distance_km: float) -> float:
        """Calculate peak ground acceleration (PGA) in g's"""
        if distance_km < 0.1:
            distance_km = 0.1

        # Base PGA from magnitude
        base_pga = 0.01 * (10 ** (0.5 * (self.magnitude - 4.0)))

        # Distance attenuation
        attenuation = 1 / ((distance_km + 5) ** 1.5)

        # Depth effect
        depth_factor = 1.0 / (1 + self.depth_km / 20)

        return base_pga * attenuation * depth_factor

    def get_modified_mercalli_intensity(self, distance_km: float) -> int:
        """Estimate Modified Mercalli Intensity scale (I-XII)"""
        pga = self.get_ground_acceleration(distance_km)

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

    # Physical damage calculation
    damage_factor = (pga * height_vuln * 200) / resistance
    physical_damage = min(100, max(0, damage_factor))

    # Social vulnerability multiplier
    social_multiplier = building.get_social_vulnerability_multiplier()
    
    # Combined vulnerability score
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

    # Recovery time estimate (days)
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
        'damage_percent': physical_damage,
        'physical_damage_percent': physical_damage,
        'damage_state': damage_state,
        'structural_resistance': resistance,
        'social_vulnerability_multiplier': social_multiplier,
        'combined_vulnerability_score': combined_vulnerability,
        'elderly_percent': building.elderly_percent,
        'poverty_percent': building.poverty_percent,
        'population_density': building.population_density,
        'sovi_score': building.sovi_score,
        'estimated_recovery_days': estimated_recovery_days
    }


def create_sf_buildings() -> List[Building]:
    """Create building dataset - ORIGINAL FUNCTION NAME"""
    buildings = [
        # San Francisco
        Building(1, "Transamerica Pyramid", "modern_seismic", 48, 1972, 37.7952, -122.4028,
                18, 9, 15000, 0.3),
        Building(2, "Salesforce Tower", "modern_seismic", 61, 2018, 37.7897, -122.3968,
                15, 8, 18000, 0.25),
        Building(3, "Financial District Office", "steel", 30, 1985, 37.7933, -122.3968,
                16, 10, 16000, 0.3),
        Building(4, "Bayview-Hunters Point Apartment", "masonry", 4, 1955, 37.7299, -122.3880,
                22, 28, 8500, 0.85),
        Building(5, "Visitacion Valley Housing", "wood", 3, 1940, 37.7130, -122.4040,
                26, 24, 9000, 0.82),
        Building(6, "Chinatown Building", "masonry", 5, 1910, 37.7948, -122.4078,
                38, 20, 22000, 0.75),
        Building(7, "Marina District House", "wood", 2, 1925, 37.8021, -122.4383,
                28, 7, 12000, 0.55),
        Building(8, "SOMA Warehouse", "concrete", 3, 1960, 37.7758, -122.4128,
                14, 12, 11000, 0.4),
        Building(9, "Civic Center Building", "concrete", 8, 1955, 37.7799, -122.4193,
                32, 22, 9500, 0.72),
        Building(10, "Modern Condo (SOMA)", "modern_seismic", 12, 2015, 37.7794, -122.4039,
                12, 6, 13000, 0.28),
        Building(11, "Sunset District Home", "wood", 2, 1950, 37.7536, -122.4663,
                30, 11, 7500, 0.58),
        Building(12, "Richmond District Duplex", "wood", 3, 1940, 37.7796, -122.4687,
                29, 10, 8000, 0.56),
        Building(13, "Hayes Valley Apartment", "masonry", 4, 1915, 37.7755, -122.4238,
                24, 16, 13500, 0.65),
        Building(14, "Nob Hill High-rise", "steel", 25, 1978, 37.7925, -122.4152,
                35, 8, 14500, 0.48),
        Building(15, "Embarcadero Office", "modern_seismic", 20, 2005, 37.7946, -122.3965,
                17, 9, 15500, 0.32),
        
        # San Mateo County
        Building(16, "Pacifica Coastal Home", "wood", 2, 1965, 37.6139, -122.4869,
                31, 9, 3800, 0.62),
        Building(17, "Daly City Apartment", "concrete", 5, 1970, 37.7058, -122.4664,
                27, 11, 9500, 0.58),
        Building(18, "South San Francisco Office", "steel", 8, 1988, 37.6547, -122.4077,
                23, 8, 7200, 0.45),
        Building(19, "East Palo Alto Community Building", "masonry", 3, 1962, 37.4688, -122.1411,
                18, 19, 6500, 0.78),
        Building(20, "San Bruno Residential", "wood", 3, 1955, 37.6305, -122.4111,
                25, 10, 8800, 0.54),
        Building(21, "Millbrae Station Area", "concrete", 4, 1975, 37.5985, -122.3867,
                28, 7, 6900, 0.48),
        Building(22, "Half Moon Bay House", "wood", 2, 1968, 37.4636, -122.4286,
                33, 8, 2100, 0.58),
        Building(23, "Redwood City Apartment", "modern_seismic", 6, 2010, 37.4852, -122.2364,
                21, 9, 5800, 0.38),
        Building(24, "San Mateo Downtown Office", "steel", 12, 1982, 37.5630, -122.3255,
                24, 8, 7400, 0.42),
        Building(25, "Foster City Condo", "modern_seismic", 8, 2008, 37.5585, -122.2711,
                26, 5, 4900, 0.35),
    ]
    return buildings


def create_sf_san_mateo_buildings() -> List[Building]:
    """Alias for create_sf_buildings - for compatibility"""
    return create_sf_buildings()


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
            damage['fault_name'] = earthquake.fault_name
            results.append(damage)

    return pd.DataFrame(results)


def main():
    """Main simulation function"""
    print("=" * 80)
    print("San Francisco & San Mateo Counties Earthquake Simulation")
    print("=" * 80)

    buildings = create_sf_buildings()
    print(f"\nAnalyzing {len(buildings)} buildings")

    epicenter_lat = 37.7949
    epicenter_lon = -122.4194

    earthquakes = [
        Earthquake(magnitude=5.5, epicenter_lat=epicenter_lat, epicenter_lon=epicenter_lon, depth_km=10),
        Earthquake(magnitude=6.5, epicenter_lat=epicenter_lat, epicenter_lon=epicenter_lon, depth_km=10),
        Earthquake(magnitude=7.0, epicenter_lat=epicenter_lat, epicenter_lon=epicenter_lon, depth_km=10),
    ]

    results = run_simulation(buildings, earthquakes)

    output_csv = 'earthquake_results.csv'
    results.to_csv(output_csv, index=False)
    print(f"\nResults saved: {output_csv}")

    largest_eq = results[results['magnitude'] == results['magnitude'].max()]
    print(f"\nAverage Damage (M{largest_eq['magnitude'].iloc[0]}): {largest_eq['physical_damage_percent'].mean():.1f}%")
    print(f"Buildings with Severe+ Damage: {len(largest_eq[largest_eq['damage_state'].isin(['Severe', 'Collapse'])])}")


if __name__ == "__main__":
    main()
