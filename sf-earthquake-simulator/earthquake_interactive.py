"""
San Francisco Bay Area Earthquake Vulnerability Simulator
Interactive tool demonstrating physical + social vulnerability
Supports GIS vulnerability analysis for SF and San Mateo Counties
"""

import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from earthquake_simulation_enhanced import (
    Building, Earthquake, create_sf_san_mateo_buildings,
    calculate_damage, calculate_distance
)

# Page configuration
st.set_page_config(
    page_title="SF Bay Earthquake Vulnerability Simulator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .main {
        background: #0a0e27;
        color: #e8eaf6;
    }
    
    .stMetric {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    h1 {
        color: #ffd700 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    h2, h3 {
        color: #ffd700 !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; margin: -1rem -1rem 2rem -1rem; 
                border-bottom: 4px solid #ffd700;'>
        <h1 style='margin: 0; color: white !important;'>
            🌉 SF Bay Area Earthquake Vulnerability Simulator
        </h1>
        <p style='color: #e0e0e0; font-size: 1.1rem; margin: 0.5rem 0 0 0;'>
            Interactive Analysis of Physical Hazard + Social Vulnerability
        </p>
    </div>
""", unsafe_allow_html=True)

# Sidebar controls
with st.sidebar:
    st.markdown("### ⚙️ Simulation Controls")
    
    # Earthquake parameters
    magnitude = st.slider("Earthquake Magnitude (Mw)", 4.0, 8.0, 7.0, 0.1)
    depth = st.slider("Focal Depth (km)", 1, 30, 10, 1)
    
    st.markdown("---")
    st.markdown("### 📍 Epicenter Location")
    
    location_preset = st.selectbox(
        "Select Location",
        ["Financial District (SF)", "San Andreas Fault", "Hayward Fault", 
         "Custom Location", "Pacifica Coastal", "South San Francisco"]
    )
    
    # Set epicenter based on preset
    if location_preset == "Financial District (SF)":
        epicenter_lat, epicenter_lon = 37.7949, -122.4194
    elif location_preset == "San Andreas Fault":
        epicenter_lat, epicenter_lon = 37.7089, -122.4664  # Near Daly City
    elif location_preset == "Hayward Fault":
        epicenter_lat, epicenter_lon = 37.6688, -122.0808
    elif location_preset == "Pacifica Coastal":
        epicenter_lat, epicenter_lon = 37.6139, -122.4869
    elif location_preset == "South San Francisco":
        epicenter_lat, epicenter_lon = 37.6547, -122.4077
    else:  # Custom
        epicenter_lat = st.number_input("Latitude", value=37.7949, format="%.4f")
        epicenter_lon = st.number_input("Longitude", value=-122.4194, format="%.4f")
    
    st.markdown("---")
    st.markdown("### 🎨 Visualization Options")
    
    show_heatmap = st.checkbox("Show Ground Motion Heatmap", value=True)
    show_labels = st.checkbox("Show Building Labels", value=False)
    color_by = st.selectbox(
        "Color Buildings By",
        ["Physical Damage", "Social Vulnerability", "Combined Vulnerability", "Recovery Time"]
    )
    
    st.markdown("---")
    st.markdown("### 🔬 Social Vulnerability Factors")
    st.markdown("""
    This simulator integrates:
    - 👴 Elderly population %
    - 💰 Poverty rates
    - 🏘️ Population density
    - 📊 Social Vulnerability Index (SoVI)
    
    Based on Cutter et al. (2003) framework
    """)

# Run simulation button
if st.button("🌋 RUN EARTHQUAKE SIMULATION", use_container_width=True):
    st.session_state.simulation_run = True
    st.session_state.earthquake = Earthquake(
        magnitude=magnitude,
        epicenter_lat=epicenter_lat,
        epicenter_lon=epicenter_lon,
        depth_km=depth
    )
    st.session_state.buildings = create_sf_san_mateo_buildings()
    
    # Calculate damage for all buildings
    results = []
    for building in st.session_state.buildings:
        damage = calculate_damage(building, st.session_state.earthquake)
        results.append(damage)
    
    st.session_state.results_df = pd.DataFrame(results)

# Display results if simulation has been run
if hasattr(st.session_state, 'simulation_run') and st.session_state.simulation_run:
    df = st.session_state.results_df
    earthquake = st.session_state.earthquake
    buildings = st.session_state.buildings
    
    # Key metrics
    st.markdown("### 📊 Impact Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        avg_damage = df['physical_damage_percent'].mean()
        st.metric("Avg Physical Damage", f"{avg_damage:.1f}%")
    
    with col2:
        severe_count = len(df[df['damage_state'].isin(['Severe', 'Collapse'])])
        st.metric("Severe+ Damage", f"{severe_count} bldgs")
    
    with col3:
        avg_social_vuln = df['social_vulnerability_multiplier'].mean()
        st.metric("Avg Social Vuln", f"{avg_social_vuln:.2f}x")
    
    with col4:
        avg_recovery = df['estimated_recovery_days'].mean()
        st.metric("Avg Recovery", f"{avg_recovery:.0f} days")
    
    with col5:
        high_risk = len(df[df['combined_vulnerability_score'] > 50])
        st.metric("High-Risk Buildings", f"{high_risk}")
    
    # Main visualization
    st.markdown("---")
    viz_col1, viz_col2 = st.columns([3, 1])
    
    with viz_col1:
        st.markdown("### 🗺️ Interactive Damage Map")
        
        # Create map
        m = folium.Map(
            location=[37.65, -122.35],
            zoom_start=10,
            tiles='CartoDB dark_matter'
        )
        
        # Add heatmap if enabled
        if show_heatmap:
            heat_data = []
            for lat in np.linspace(37.4, 37.85, 50):
                for lon in np.linspace(-122.55, -122.0, 50):
                    dist = calculate_distance(lat, lon, epicenter_lat, epicenter_lon)
                    pga = earthquake.get_ground_acceleration(dist)
                    if pga > 0.001:
                        heat_data.append([lat, lon, pga * 200])
            
            plugins.HeatMap(
                heat_data,
                min_opacity=0.3,
                max_opacity=0.8,
                radius=15,
                blur=18,
                gradient={0.0: '#00ff00', 0.25: '#adff2f', 0.5: '#ffff00',
                         0.65: '#ffa500', 0.8: '#ff4500', 1.0: '#8b0000'}
            ).add_to(m)
        
        # Epicenter marker
        folium.Marker(
            location=[epicenter_lat, epicenter_lon],
            popup=f"<b>EPICENTER</b><br>M{magnitude:.1f} @ {depth}km depth",
            icon=folium.Icon(color='red', icon='star', prefix='fa')
        ).add_to(m)
        
        # Distance circles
        for radius_km in [10, 20, 30]:
            folium.Circle(
                location=[epicenter_lat, epicenter_lon],
                radius=radius_km * 1000,
                color='#ff6b6b',
                fill=False,
                weight=2,
                opacity=0.5,
                dash_array='5, 5'
            ).add_to(m)
        
        # Buildings
        for _, row in df.iterrows():
            building = next(b for b in buildings if b.id == row['building_id'])
            
            # Determine color based on selection
            if color_by == "Physical Damage":
                value = row['physical_damage_percent']
                colors = {
                    "None": '#00ff00', "Slight": '#adff2f', "Moderate": '#ffff00',
                    "Extensive": '#ffa500', "Severe": '#ff4500', "Collapse": '#8b0000'
                }
                color = colors.get(row['damage_state'], '#808080')
            elif color_by == "Social Vulnerability":
                value = row['social_vulnerability_multiplier']
                if value < 1.2:
                    color = '#00ff00'
                elif value < 1.4:
                    color = '#ffff00'
                elif value < 1.6:
                    color = '#ffa500'
                else:
                    color = '#ff4500'
            elif color_by == "Combined Vulnerability":
                value = row['combined_vulnerability_score']
                if value < 20:
                    color = '#00ff00'
                elif value < 40:
                    color = '#ffff00'
                elif value < 60:
                    color = '#ffa500'
                else:
                    color = '#ff4500'
            else:  # Recovery Time
                value = row['estimated_recovery_days']
                if value < 30:
                    color = '#00ff00'
                elif value < 90:
                    color = '#ffff00'
                elif value < 180:
                    color = '#ffa500'
                else:
                    color = '#ff4500'
            
            # Create detailed popup
            popup_html = f"""
            <div style="width: 280px; background: #1a1f3a; color: white;
                        padding: 15px; border-radius: 10px; border: 3px solid {color};">
                <h4 style="margin: 0 0 10px 0; color: {color}; font-size: 1.15rem;">
                    {building.name}
                </h4>
                <div style="border-top: 1px solid #444; padding-top: 10px;">
                    <p style="margin: 5px 0;"><b>Type:</b> {building.building_type.replace('_', ' ').title()}</p>
                    <p style="margin: 5px 0;"><b>Height:</b> {building.height_stories} stories</p>
                    <p style="margin: 5px 0;"><b>Built:</b> {building.year_built}</p>
                </div>
                <div style="border-top: 1px solid #444; margin-top: 10px; padding-top: 10px;">
                    <p style="margin: 5px 0;"><b>Physical Damage:</b> {row['physical_damage_percent']:.1f}%</p>
                    <p style="margin: 5px 0;"><b>Damage State:</b> {row['damage_state']}</p>
                    <p style="margin: 5px 0;"><b>Distance:</b> {row['distance_km']:.2f} km</p>
                    <p style="margin: 5px 0;"><b>Peak Accel:</b> {row['pga_g']:.4f}g</p>
                </div>
                <div style="border-top: 1px solid #444; margin-top: 10px; padding-top: 10px;">
                    <p style="margin: 5px 0; color: #ffd700;"><b>SOCIAL VULNERABILITY</b></p>
                    <p style="margin: 5px 0;"><b>Elderly:</b> {row['elderly_percent']:.1f}%</p>
                    <p style="margin: 5px 0;"><b>Poverty:</b> {row['poverty_percent']:.1f}%</p>
                    <p style="margin: 5px 0;"><b>Density:</b> {row['population_density']:,.0f}/mi²</p>
                    <p style="margin: 5px 0;"><b>SoVI Score:</b> {row['sovi_score']:.2f}</p>
                    <p style="margin: 5px 0;"><b>Vuln. Multiplier:</b> {row['social_vulnerability_multiplier']:.2f}x</p>
                </div>
                <div style="background: {color}; padding: 12px; margin-top: 10px;
                            border-radius: 6px; text-align: center;">
                    <p style="margin: 0; font-weight: bold; font-size: 1.1rem; color: white;">
                        Recovery: {row['estimated_recovery_days']:.0f} days
                    </p>
                </div>
            </div>
            """
            
            radius = 7 + (building.height_stories / 3)
            
            folium.CircleMarker(
                location=[building.latitude, building.longitude],
                radius=radius,
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=building.name if show_labels else None,
                color='#000',
                fillColor=color,
                fillOpacity=0.85,
                weight=2
            ).add_to(m)
        
        st_folium(m, width=None, height=700, returned_objects=[])
    
    with viz_col2:
        st.markdown("### 📈 Distribution")
        
        # Damage state distribution
        damage_counts = df['damage_state'].value_counts()
        damage_colors_chart = {
            "None": '#00ff00', "Slight": '#adff2f', "Moderate": '#ffff00',
            "Extensive": '#ffa500', "Severe": '#ff4500', "Collapse": '#8b0000'
        }
        
        for state in ["None", "Slight", "Moderate", "Extensive", "Severe", "Collapse"]:
            count = damage_counts.get(state, 0)
            if count > 0:
                pct = (count / len(df)) * 100
                color = damage_colors_chart[state]
                st.markdown(f"""
                    <div style='background: {color}; padding: 10px; margin: 5px 0;
                                border-radius: 6px; color: black; font-weight: bold;'>
                        {state}: {count} ({pct:.0f}%)
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🎯 Color Legend")
        
        if color_by == "Physical Damage":
            st.markdown("""
            - 🟢 None/Slight
            - 🟡 Moderate
            - 🟠 Extensive
            - 🔴 Severe/Collapse
            """)
        elif color_by == "Social Vulnerability":
            st.markdown("""
            - 🟢 Low (<1.2x)
            - 🟡 Moderate (1.2-1.4x)
            - 🟠 High (1.4-1.6x)
            - 🔴 Very High (>1.6x)
            """)
        elif color_by == "Combined Vulnerability":
            st.markdown("""
            - 🟢 Low (<20)
            - 🟡 Moderate (20-40)
            - 🟠 High (40-60)
            - 🔴 Critical (>60)
            """)
        else:  # Recovery Time
            st.markdown("""
            - 🟢 <30 days
            - 🟡 30-90 days
            - 🟠 90-180 days
            - 🔴 >180 days
            """)
    
    # Detailed analysis tabs
    st.markdown("---")
    st.markdown("### 🔍 Detailed Analysis")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Vulnerability Analysis", 
        "🏘️ High-Risk Communities", 
        "📈 Recovery Projections",
        "📋 Data Table"
    ])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Physical vs Social Vulnerability")
            fig, ax = plt.subplots(figsize=(8, 6))
            scatter = ax.scatter(
                df['physical_damage_percent'],
                df['social_vulnerability_multiplier'],
                c=df['combined_vulnerability_score'],
                s=df['population_density']/50,
                alpha=0.7,
                cmap='YlOrRd',
                edgecolors='black',
                linewidth=1
            )
            ax.set_xlabel('Physical Damage (%)', fontsize=11, fontweight='bold')
            ax.set_ylabel('Social Vulnerability Multiplier', fontsize=11, fontweight='bold')
            ax.set_title('Vulnerability Intersection\n(size = population density)', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            plt.colorbar(scatter, ax=ax, label='Combined Vulnerability')
            st.pyplot(fig)
            plt.close()
        
        with col2:
            st.markdown("#### Recovery Time Distribution")
            fig, ax = plt.subplots(figsize=(8, 6))
            recovery_bins = [0, 30, 90, 180, 365, 1000]
            recovery_labels = ['<30d', '30-90d', '90-180d', '180-365d', '>365d']
            df['recovery_category'] = pd.cut(df['estimated_recovery_days'], 
                                            bins=recovery_bins, labels=recovery_labels)
            recovery_counts = df['recovery_category'].value_counts().sort_index()
            colors = ['#00ff00', '#adff2f', '#ffff00', '#ffa500', '#ff4500']
            ax.bar(range(len(recovery_counts)), recovery_counts.values, 
                  color=colors[:len(recovery_counts)], edgecolor='black', linewidth=1.5)
            ax.set_xticks(range(len(recovery_counts)))
            ax.set_xticklabels(recovery_counts.index, rotation=45)
            ax.set_ylabel('Number of Buildings', fontsize=11, fontweight='bold')
            ax.set_title('Estimated Recovery Timeline', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            st.pyplot(fig)
            plt.close()
    
    with tab2:
        st.markdown("#### Buildings in High-Risk Communities")
        high_risk = df[
            (df['damage_state'].isin(['Extensive', 'Severe', 'Collapse'])) &
            ((df['elderly_percent'] > 25) | (df['poverty_percent'] > 15) | (df['sovi_score'] > 0.7))
        ].sort_values('combined_vulnerability_score', ascending=False)
        
        if len(high_risk) > 0:
            st.markdown(f"""
            **Found {len(high_risk)} buildings with extensive+ damage in vulnerable communities:**
            - Average elderly population: **{high_risk['elderly_percent'].mean():.1f}%**
            - Average poverty rate: **{high_risk['poverty_percent'].mean():.1f}%**
            - Average SoVI score: **{high_risk['sovi_score'].mean():.2f}**
            - Average recovery time: **{high_risk['estimated_recovery_days'].mean():.0f} days**
            """)
            
            display_cols = ['building_name', 'damage_state', 'physical_damage_percent', 
                          'elderly_percent', 'poverty_percent', 'sovi_score', 
                          'estimated_recovery_days']
            st.dataframe(
                high_risk[display_cols].round(2),
                use_container_width=True,
                height=400
            )
        else:
            st.info("No high-risk communities identified with extensive+ damage in this scenario.")
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Building Age vs Recovery Time")
            building_ages = {b.id: 2025 - b.year_built for b in buildings}
            df_copy = df.copy()
            df_copy['building_age'] = df_copy['building_id'].map(building_ages)
            
            fig, ax = plt.subplots(figsize=(8, 6))
            for state, color in [('Severe', 'red'), ('Extensive', 'orange'), 
                                ('Moderate', 'yellow'), ('Slight', 'green')]:
                state_data = df_copy[df_copy['damage_state'] == state]
                if len(state_data) > 0:
                    ax.scatter(state_data['building_age'], state_data['estimated_recovery_days'],
                             label=state, c=color, s=80, alpha=0.7, edgecolors='black')
            
            ax.set_xlabel('Building Age (years)', fontsize=11, fontweight='bold')
            ax.set_ylabel('Recovery Time (days)', fontsize=11, fontweight='bold')
            ax.set_title('Age, Damage, and Recovery', fontsize=12, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
            plt.close()
        
        with col2:
            st.markdown("#### County Comparison")
            df_copy = df.copy()
            df_copy['county'] = df_copy['building_id'].apply(
                lambda x: 'San Francisco' if next(b for b in buildings if b.id == x).latitude > 37.65 
                else 'San Mateo'
            )
            
            county_stats = df_copy.groupby('county').agg({
                'physical_damage_percent': 'mean',
                'social_vulnerability_multiplier': 'mean',
                'estimated_recovery_days': 'mean'
            }).round(1)
            
            st.markdown("**Average Metrics by County:**")
            st.dataframe(county_stats, use_container_width=True)
            
            if 'San Francisco' in county_stats.index and 'San Mateo' in county_stats.index:
                st.markdown(f"""
                - **San Francisco**: {county_stats.loc['San Francisco', 'physical_damage_percent']:.1f}% avg damage, 
                  {county_stats.loc['San Francisco', 'estimated_recovery_days']:.0f} day avg recovery
                - **San Mateo**: {county_stats.loc['San Mateo', 'physical_damage_percent']:.1f}% avg damage,
                  {county_stats.loc['San Mateo', 'estimated_recovery_days']:.0f} day avg recovery
                """)
    
    with tab4:
        st.markdown("#### Complete Simulation Results")
        st.dataframe(
            df[[
                'building_name', 'building_type', 'stories', 'year_built',
                'distance_km', 'pga_g', 'mmi', 'damage_state', 
                'physical_damage_percent', 'social_vulnerability_multiplier',
                'combined_vulnerability_score', 'elderly_percent', 
                'poverty_percent', 'sovi_score', 'estimated_recovery_days'
            ]].round(2),
            use_container_width=True,
            height=500
        )
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Full Dataset (CSV)",
            data=csv,
            file_name=f"earthquake_simulation_M{magnitude:.1f}.csv",
            mime="text/csv"
        )

else:
    # Welcome screen
    st.markdown("""
    ## 🎯 About This Simulator
    
    This interactive tool demonstrates the integration of **physical earthquake hazards** 
    with **social vulnerability factors** for San Francisco and San Mateo Counties.
    
    ### Key Features:
    - ⚡ **Physics-Based Modeling**: Boore-Atkinson (2008) ground motion attenuation
    - 🏘️ **Social Vulnerability**: Elderly populations, poverty rates, population density, SoVI scores
    - 🏗️ **Building Assessment**: FEMA HAZUS damage classification across 25 representative structures
    - 📊 **Recovery Projections**: Social factors affect recovery timeline estimates
    - 🗺️ **Interactive Mapping**: Visualize spatial patterns of vulnerability
    
    ### Based On:
    - Cutter et al. (2003) Social Vulnerability Framework
    - FEMA HAZUS Methodology
    - California Geological Survey Fault Data
    - U.S. Census Bureau 2024 ACS Data
    
    ### Usage:
    1. **Configure** earthquake parameters in the sidebar
    2. **Select** visualization options
    3. **Click** "RUN EARTHQUAKE SIMULATION"
    4. **Explore** results through interactive maps and charts
    
    ---
    
    **Use the sidebar to configure your simulation and click the button above to begin! 👈**
    """)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #b0bec5; font-size: 0.9rem;'>
        <p>Earthquake Vulnerability Simulator | SF & San Mateo Counties</p>
        <p>Supporting GIS Vulnerability Analysis Research</p>
    </div>
""", unsafe_allow_html=True)
