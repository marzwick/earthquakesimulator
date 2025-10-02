"""
San Francisco Earthquake GIS Animation
Creates an animated video showing earthquake wave propagation and building damage over time
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle
import pandas as pd
from earthquake_simulation import (
    Building, Earthquake, create_sf_buildings,
    calculate_damage, calculate_distance
)

# Set up for animation
plt.rcParams['animation.ffmpeg_path'] = '/opt/homebrew/bin/ffmpeg'  # macOS path


def calculate_time_dependent_damage(building: Building, earthquake: Earthquake, current_time: float) -> dict:
    """
    Calculate damage at a specific time after earthquake starts

    Args:
        building: Building object
        earthquake: Earthquake object
        current_time: Time in seconds after earthquake starts

    Returns:
        Dictionary with damage info at this time
    """
    # Calculate distance from epicenter
    distance = calculate_distance(
        building.latitude, building.longitude,
        earthquake.epicenter_lat, earthquake.epicenter_lon
    )

    # S-wave velocity approximately 3.5 km/s
    s_wave_velocity = 3.5  # km/s
    arrival_time = distance / s_wave_velocity

    # P-wave arrives earlier (about 1.7x faster)
    p_wave_velocity = 6.0  # km/s
    p_arrival_time = distance / p_wave_velocity

    # Shaking duration depends on magnitude (roughly 10-60 seconds)
    shake_duration = 10 + (earthquake.magnitude - 5) * 8

    # Calculate damage progression
    if current_time < p_arrival_time:
        # No shaking yet
        damage_factor = 0
    elif current_time < arrival_time:
        # P-wave has arrived (minor shaking)
        damage_factor = 0.1
    elif current_time < arrival_time + shake_duration:
        # Main shaking period (S-wave)
        time_in_shake = current_time - arrival_time
        # Damage builds up during shaking
        progress = min(1.0, time_in_shake / shake_duration)
        # Get final damage from original calculation
        final_damage = calculate_damage(building, earthquake)
        damage_factor = progress * final_damage['damage_percent'] / 100
    else:
        # Shaking is over, damage is final
        final_damage = calculate_damage(building, earthquake)
        damage_factor = final_damage['damage_percent'] / 100

    damage_percent = damage_factor * 100

    # Damage state (match colors with main app)
    if damage_percent < 5:
        damage_state = "None"
        color = '#00ff00'
    elif damage_percent < 15:
        damage_state = "Slight"
        color = '#adff2f'
    elif damage_percent < 30:
        damage_state = "Moderate"
        color = '#ffff00'
    elif damage_percent < 60:
        damage_state = "Extensive"
        color = '#ffa500'
    elif damage_percent < 90:
        damage_state = "Severe"
        color = '#ff4500'
    else:
        damage_state = "Collapse"
        color = '#8b0000'

    return {
        'building_id': building.id,
        'building_name': building.name,
        'distance_km': distance,
        'p_arrival_time': p_arrival_time,
        's_arrival_time': arrival_time,
        'shake_end_time': arrival_time + shake_duration,
        'damage_percent': damage_percent,
        'damage_state': damage_state,
        'color': color,
        'is_shaking': (current_time >= arrival_time and
                      current_time < arrival_time + shake_duration)
    }


def create_animation(earthquake: Earthquake, buildings: list, output_file: str = 'earthquake_animation.mp4'):
    """Create animated visualization of earthquake propagation"""

    print(f"\nCreating animation for Magnitude {earthquake.magnitude} earthquake...")
    print("This may take a few minutes...")

    # Set up the figure
    fig, (ax_map, ax_stats) = plt.subplots(1, 2, figsize=(18, 8))

    # Calculate maximum time (when farthest building stops shaking)
    max_distance = max([calculate_distance(b.latitude, b.longitude,
                                          earthquake.epicenter_lat,
                                          earthquake.epicenter_lon)
                       for b in buildings])
    s_wave_velocity = 3.5
    shake_duration = 10 + (earthquake.magnitude - 5) * 8
    max_time = (max_distance / s_wave_velocity) + shake_duration + 5

    # Time points for animation (60 fps = smooth)
    fps = 30
    time_points = np.linspace(0, max_time, int(max_time * fps))

    def init():
        """Initialize animation"""
        ax_map.clear()
        ax_stats.clear()
        return []

    def animate(frame):
        """Animation frame update"""
        current_time = time_points[frame]

        # Clear axes
        ax_map.clear()
        ax_stats.clear()

        # --- MAP VIEW ---
        ax_map.set_xlim(-122.48, -122.35)
        ax_map.set_ylim(37.70, 37.82)
        ax_map.set_xlabel('Longitude', fontsize=12)
        ax_map.set_ylabel('Latitude', fontsize=12)
        ax_map.set_title(f'San Francisco Earthquake Simulation (M{earthquake.magnitude})\nTime: {current_time:.1f}s',
                        fontsize=14, fontweight='bold')
        ax_map.grid(True, alpha=0.3)
        ax_map.set_aspect('equal')

        # Plot epicenter
        ax_map.scatter(earthquake.epicenter_lon, earthquake.epicenter_lat,
                      marker='*', c='red', s=1500, edgecolors='black',
                      linewidth=3, label='Epicenter', zorder=100)

        # Draw expanding wave fronts
        s_wave_velocity = 3.5  # km/s
        p_wave_velocity = 6.0  # km/s
        deg_per_km = 1 / 111.0

        # P-wave circle
        p_radius = p_wave_velocity * current_time
        if p_radius > 0:
            p_circle = Circle((earthquake.epicenter_lon, earthquake.epicenter_lat),
                            p_radius * deg_per_km, fill=False,
                            linestyle='--', color='blue', linewidth=2,
                            alpha=0.7, label='P-wave')
            ax_map.add_patch(p_circle)

        # S-wave circle (main shaking)
        s_radius = s_wave_velocity * current_time
        if s_radius > 0:
            s_circle = Circle((earthquake.epicenter_lon, earthquake.epicenter_lat),
                            s_radius * deg_per_km, fill=False,
                            linestyle='-', color='red', linewidth=3,
                            alpha=0.8, label='S-wave (main shaking)')
            ax_map.add_patch(s_circle)

        # Plot buildings with time-dependent damage
        damage_data = []
        for building in buildings:
            damage = calculate_time_dependent_damage(building, earthquake, current_time)
            damage_data.append(damage)

            # Size based on height and shaking intensity
            base_size = 100 + building.height_stories * 10
            if damage['is_shaking']:
                size = base_size * 1.8  # Larger when shaking
                edgewidth = 3
                alpha = 0.9
            else:
                size = base_size
                edgewidth = 1
                alpha = 0.7

            # Plot building
            ax_map.scatter(building.longitude, building.latitude,
                          c=damage['color'], s=size, alpha=alpha,
                          edgecolors='black', linewidth=edgewidth,
                          zorder=50)

        ax_map.legend(loc='upper right', fontsize=10)

        # --- STATISTICS PANEL ---
        ax_stats.axis('off')

        # Calculate statistics
        df = pd.DataFrame(damage_data)
        shaking_count = df['is_shaking'].sum()
        avg_damage = df['damage_percent'].mean()
        max_damage = df['damage_percent'].max()

        damage_counts = df['damage_state'].value_counts()

        # Create text display
        stats_text = f"""
EARTHQUAKE STATISTICS
{'='*40}

Time: {current_time:.1f} seconds
Magnitude: {earthquake.magnitude}
Epicenter: ({earthquake.epicenter_lat:.4f}, {earthquake.epicenter_lon:.4f})
Depth: {earthquake.depth_km} km

WAVE PROPAGATION
{'='*40}
P-wave radius: {p_wave_velocity * current_time:.1f} km
S-wave radius: {s_wave_velocity * current_time:.1f} km

BUILDING STATUS
{'='*40}
Buildings currently shaking: {shaking_count}/15
Average damage: {avg_damage:.1f}%
Maximum damage: {max_damage:.1f}%

DAMAGE DISTRIBUTION
{'='*40}
"""

        for state in ["None", "Slight", "Moderate", "Extensive", "Severe", "Collapse"]:
            count = damage_counts.get(state, 0)
            bar = '█' * count
            stats_text += f"{state:12s}: {bar} ({count})\n"

        ax_stats.text(0.05, 0.95, stats_text, transform=ax_stats.transAxes,
                     fontsize=11, verticalalignment='top',
                     fontfamily='monospace',
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        return []

    # Create animation
    anim = animation.FuncAnimation(fig, animate, init_func=init,
                                  frames=len(time_points),
                                  interval=1000/fps, blit=True)

    # Save animation
    print(f"\nSaving animation to {output_file}...")
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=fps, metadata=dict(artist='Earthquake Simulator'), bitrate=3000)

    try:
        anim.save(output_file, writer=writer, dpi=150)
        print(f"✓ Animation saved successfully!")
        print(f"  Duration: {max_time:.1f} seconds")
        print(f"  Frames: {len(time_points)}")
        print(f"  File: {output_file}")
    except Exception as e:
        print(f"✗ Error saving animation: {e}")
        print("\nTrying alternative method with pillow...")
        try:
            anim.save(output_file.replace('.mp4', '.gif'), writer='pillow', fps=fps//2, dpi=100)
            print(f"✓ Animation saved as GIF instead!")
        except Exception as e2:
            print(f"✗ Also failed to save as GIF: {e2}")

    plt.close()


def create_static_gis_map(earthquake: Earthquake, buildings: list, output_file: str = 'gis_damage_map.png'):
    """Create a detailed static GIS-style map"""

    print(f"\nCreating detailed GIS map...")

    fig, ax = plt.subplots(figsize=(16, 12))

    # Calculate final damage for all buildings
    damage_data = []
    for building in buildings:
        damage = calculate_damage(building, earthquake)
        damage_data.append(damage)

    df = pd.DataFrame(damage_data)

    # Set up map
    ax.set_xlim(-122.49, -122.35)
    ax.set_ylim(37.70, 37.83)
    ax.set_xlabel('Longitude', fontsize=14, fontweight='bold')
    ax.set_ylabel('Latitude', fontsize=14, fontweight='bold')
    ax.set_title(f'San Francisco Earthquake Damage Assessment (M{earthquake.magnitude})\nPeak Ground Acceleration & Building Damage',
                fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_aspect('equal')

    # Add background shading for PGA intensity zones
    x = np.linspace(-122.49, -122.35, 200)
    y = np.linspace(37.70, 37.83, 200)
    X, Y = np.meshgrid(x, y)

    # Calculate PGA for each grid point
    PGA_grid = np.zeros_like(X)
    for i in range(len(x)):
        for j in range(len(y)):
            dist = calculate_distance(Y[j, i], X[j, i],
                                     earthquake.epicenter_lat,
                                     earthquake.epicenter_lon)
            pga = earthquake.get_ground_acceleration(dist)
            PGA_grid[j, i] = pga

    # Plot PGA contours
    contour = ax.contourf(X, Y, PGA_grid, levels=20, cmap='YlOrRd', alpha=0.3)
    cbar = plt.colorbar(contour, ax=ax, label='Peak Ground Acceleration (g)', pad=0.02)
    cbar.ax.tick_params(labelsize=10)

    # Plot concentric distance circles
    deg_per_km = 1 / 111.0
    for radius_km in [2, 5, 10, 15]:
        circle = Circle((earthquake.epicenter_lon, earthquake.epicenter_lat),
                       radius_km * deg_per_km, fill=False,
                       linestyle=':', color='gray', linewidth=1.5, alpha=0.6)
        ax.add_patch(circle)
        # Add distance label
        ax.text(earthquake.epicenter_lon + radius_km * deg_per_km,
               earthquake.epicenter_lat, f'{radius_km}km',
               fontsize=9, color='gray', fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

    # Plot buildings with detailed labels
    damage_colors = {
        "None": 'green',
        "Slight": 'yellowgreen',
        "Moderate": 'yellow',
        "Extensive": 'orange',
        "Severe": 'red',
        "Collapse": 'darkred'
    }

    for _, row in df.iterrows():
        building = next(b for b in buildings if b.id == row['building_id'])

        # Building marker
        size = 150 + building.height_stories * 12
        color = damage_colors.get(row['damage_state'], 'gray')

        ax.scatter(building.longitude, building.latitude,
                  c=color, s=size, alpha=0.85,
                  edgecolors='black', linewidth=2, zorder=100)

        # Add label with building info
        label = f"{building.name}\n{row['damage_state']} ({row['damage_percent']:.1f}%)"
        ax.annotate(label, xy=(building.longitude, building.latitude),
                   xytext=(8, 8), textcoords='offset points',
                   fontsize=8, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                           edgecolor=color, alpha=0.9, linewidth=2),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0',
                                 color='black', lw=1))

    # Plot epicenter
    ax.scatter(earthquake.epicenter_lon, earthquake.epicenter_lat,
              marker='*', c='red', s=2000, edgecolors='black',
              linewidth=4, label=f'Epicenter (M{earthquake.magnitude})', zorder=200)

    # Add legend for damage states
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=color, edgecolor='black', label=state)
                      for state, color in damage_colors.items()]
    legend_elements.insert(0, ax.scatter([], [], marker='*', c='red', s=200,
                                        edgecolors='black', linewidth=2,
                                        label='Epicenter'))

    ax.legend(handles=legend_elements, loc='upper left',
             fontsize=11, title='Damage Classification',
             title_fontsize=12, framealpha=0.95)

    # Add statistics box
    stats_text = (f"Magnitude: {earthquake.magnitude}\n"
                 f"Depth: {earthquake.depth_km} km\n"
                 f"Avg Damage: {df['damage_percent'].mean():.1f}%\n"
                 f"Max Damage: {df['damage_percent'].max():.1f}%")

    ax.text(0.02, 0.02, stats_text, transform=ax.transAxes,
           fontsize=11, verticalalignment='bottom',
           bbox=dict(boxstyle='round', facecolor='lightyellow',
                    alpha=0.9, edgecolor='black', linewidth=2))

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ GIS map saved as {output_file}")
    plt.close()


def main():
    """Main function to create animations and maps"""
    print("=" * 70)
    print("San Francisco Earthquake GIS Animation Generator")
    print("=" * 70)

    # Create buildings
    buildings = create_sf_buildings()

    # Define earthquake (choose magnitude)
    print("\nAvailable earthquake scenarios:")
    print("1. Magnitude 5.5 (Moderate)")
    print("2. Magnitude 6.5 (Strong)")
    print("3. Magnitude 7.0 (Major)")
    print("4. Magnitude 7.5 (Great)")

    # Default to 7.0 for non-interactive mode
    magnitude = 7.0

    # Epicenter near downtown SF (Financial District)
    earthquake = Earthquake(
        magnitude=magnitude,
        epicenter_lat=37.7949,
        epicenter_lon=-122.4194,
        depth_km=10
    )

    print(f"\nGenerating visualizations for M{magnitude} earthquake...")

    # Create detailed GIS map
    create_static_gis_map(earthquake, buildings,
                         f'earthquake_gis_map_M{magnitude}.png')

    # Create animation
    print("\n" + "=" * 70)
    print("Creating animation (this will take a few minutes)...")
    print("=" * 70)
    create_animation(earthquake, buildings,
                    f'earthquake_animation_M{magnitude}.mp4')

    print("\n" + "=" * 70)
    print("All visualizations complete!")
    print("=" * 70)
    print(f"\nGenerated files:")
    print(f"  • earthquake_gis_map_M{magnitude}.png - Detailed GIS damage map")
    print(f"  • earthquake_animation_M{magnitude}.mp4 - Animated wave propagation")


if __name__ == "__main__":
    main()
