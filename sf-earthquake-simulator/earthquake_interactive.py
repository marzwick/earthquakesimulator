"""
San Francisco Earthquake Simulator
Professional seismic risk assessment platform
"""

import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from earthquake_simulation import (
    Building, Earthquake, create_sf_buildings,
    calculate_damage, calculate_distance
)


# Page configuration
st.set_page_config(
    page_title="SF Earthquake Simulator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Complete redesign to look nothing like Streamlit
st.markdown("""
    <style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Complete background redesign */
    .main {
        background: #0a0e27;
        color: #e8eaf6;
        padding: 0 !important;
    }

    .block-container {
        padding: 2rem 3rem !important;
        max-width: 100% !important;
    }

    /* Custom header styling */
    .custom-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 3rem;
        margin: -2rem -3rem 2rem -3rem;
        border-bottom: 4px solid #ffd700;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }

    .custom-header h1 {
        color: #ffffff !important;
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    .custom-header p {
        color: #e0e0e0 !important;
        font-size: 1.15rem !important;
        margin: 0.5rem 0 0 0 !important;
    }

    /* Headings */
    h3 {
        color: #ffd700 !important;
        font-size: 1.3rem !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(102, 126, 234, 0.4);
    }

    h4 {
        color: #ffd700 !important;
        margin-top: 0 !important;
        font-size: 1.1rem !important;
    }

    /* Metrics redesign */
    [data-testid="stMetricValue"] {
        color: #ffd700 !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
    }

    [data-testid="stMetricLabel"] {
        color: #b0bec5 !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stMetric {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }

    /* Button redesign */
    .stButton > button {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 1rem 2.5rem !important;
        font-weight: 700 !important;
        font-size: 1.2rem !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4) !important;
        transition: all 0.3s !important;
    }

    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 10px 30px rgba(255, 107, 107, 0.6) !important;
    }

    /* Slider customization */
    .stSlider {
        padding: 1rem 0;
    }

    .stSlider > div > div > div > div {
        background: #667eea !important;
    }

    .stSlider label {
        color: #e8eaf6 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }

    /* Select box styling */
    .stSelectbox label {
        color: #e8eaf6 !important;
        font-weight: 600 !important;
    }

    .stSelectbox > div > div {
        background: rgba(42, 45, 74, 0.95) !important;
        color: #e8eaf6 !important;
        border: 2px solid #667eea !important;
        border-radius: 8px !important;
    }

    .stSelectbox div[data-baseweb="select"] > div {
        color: #e8eaf6 !important;
    }

    .stSelectbox option {
        background: #2a2d4a !important;
        color: #e8eaf6 !important;
    }

    /* Checkbox styling */
    .stCheckbox label {
        color: #e8eaf6 !important;
        font-weight: 500 !important;
    }

    /* Tabs complete redesign */
    .stTabs {
        background: transparent;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background: linear-gradient(135deg, #1a1f3a 0%, #2a1f3a 100%);
        border-radius: 12px;
        padding: 0.5rem;
        border: 2px solid #667eea;
    }

    .stTabs [data-baseweb="tab"] {
        color: #b0bec5;
        background: transparent;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        border: none;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    /* DataFrame styling */
    .dataframe {
        background: #1e2139 !important;
        color: #e8eaf6 !important;
        border: 2px solid #4a5080 !important;
        border-radius: 8px !important;
    }

    .dataframe th {
        background: #667eea !important;
        color: white !important;
        font-weight: 700 !important;
    }

    .dataframe td {
        background: #2a2d4a !important;
        color: #e8eaf6 !important;
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    }

    /* Alert boxes */
    .stAlert {
        background: rgba(102, 126, 234, 0.1) !important;
        border: 2px solid #667eea !important;
        color: #e8eaf6 !important;
        border-radius: 12px !important;
    }

    /* Map container fix */
    .map-container {
        width: 100%;
        height: 650px;
        border: 3px solid #667eea;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }

    /* Legend styling */
    .legend-item {
        display: flex;
        align-items: center;
        padding: 0.5rem;
        margin: 0.3rem 0;
        border-left: 3px solid;
    }

    .legend-color {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        margin-right: 0.6rem;
        border: 2px solid rgba(255,255,255,0.3);
    }


    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    </style>
""", unsafe_allow_html=True)

# Simple title
st.markdown("<h2 style='text-align: center; color: #ffd700; margin-bottom: 2rem;'>San Francisco Earthquake Hazard Simulator</h2>", unsafe_allow_html=True)

# Initialize session state
if 'simulation_run' not in st.session_state:
    st.session_state.simulation_run = False
if 'damage_data' not in st.session_state:
    st.session_state.damage_data = None
if 'last_params' not in st.session_state:
    st.session_state.last_params = None

# Load buildings
buildings = create_sf_buildings()

# Control Panel
col1, col2, col3, col4 = st.columns(4)

with col1:
    magnitude = st.slider(
        "Magnitude (Mw)",
        min_value=4.0,
        max_value=8.0,
        value=7.0,
        step=0.1,
        help="Moment magnitude scale (Kanamori, 1977)"
    )

    if magnitude < 5.0:
        st.markdown("<p style='color: #4CAF50; font-weight: bold;'>Light Event</p>", unsafe_allow_html=True)
    elif magnitude < 6.0:
        st.markdown("<p style='color: #FFC107; font-weight: bold;'>Moderate</p>", unsafe_allow_html=True)
    elif magnitude < 7.0:
        st.markdown("<p style='color: #FF9800; font-weight: bold;'>Strong</p>", unsafe_allow_html=True)
    elif magnitude < 7.5:
        st.markdown("<p style='color: #FF5722; font-weight: bold;'>Major</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #D32F2F; font-weight: bold;'>Catastrophic</p>", unsafe_allow_html=True)

with col2:
    epicenter_preset = st.selectbox(
        "Fault Zone / Location",
        ["Financial District", "Mission District", "Marina District",
         "SOMA", "Hayward Fault", "San Andreas Fault", "Custom"]
    )

    epicenter_presets = {
        "Financial District": (37.7949, -122.4194),
        "Mission District": (37.7599, -122.4148),
        "Marina District": (37.8021, -122.4383),
        "SOMA": (37.7758, -122.4128),
        "Hayward Fault": (37.6688, -122.0808),
        "San Andreas Fault": (37.7000, -122.5000)
    }

    if epicenter_preset == "Custom":
        epicenter_lat = st.number_input("Latitude", value=37.7949, format="%.4f")
        epicenter_lon = st.number_input("Longitude", value=-122.4194, format="%.4f")
    else:
        epicenter_lat, epicenter_lon = epicenter_presets[epicenter_preset]
        st.markdown(f"<small style='color: #ffd700;'>Coordinates: {epicenter_lat:.4f}, {epicenter_lon:.4f}</small>", unsafe_allow_html=True)

with col3:
    depth = st.slider(
        "Focal Depth (km)",
        min_value=5,
        max_value=30,
        value=10,
        help="Earthquake depth below surface"
    )

    if depth < 15:
        st.markdown("<p style='color: #FF9800; font-size: 0.9rem;'>Shallow (High Impact)</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #4CAF50; font-size: 0.9rem;'>Deep (Lower Impact)</p>", unsafe_allow_html=True)

with col4:
    show_pga = st.checkbox("Ground Motion Heatmap", value=True)
    show_labels = st.checkbox("Building Names", value=True)
    st.markdown("<br>", unsafe_allow_html=True)
    run_simulation = st.button("ANALYZE", use_container_width=True, type="primary")

# Create earthquake object
earthquake = Earthquake(
    magnitude=magnitude,
    epicenter_lat=epicenter_lat,
    epicenter_lon=epicenter_lon,
    depth_km=depth
)

# Check if parameters changed - if so, recalculate automatically
current_params = (magnitude, epicenter_lat, epicenter_lon, depth, epicenter_preset)
params_changed = st.session_state.last_params != current_params

if run_simulation or (st.session_state.simulation_run and params_changed):
    st.session_state.simulation_run = True
    st.session_state.last_params = current_params

    with st.spinner('Calculating seismic wave propagation...'):
        damage_results = []
        progress_bar = st.progress(0)

        for idx, building in enumerate(buildings):
            damage = calculate_damage(building, earthquake)
            damage_results.append(damage)
            progress_bar.progress((idx + 1) / len(buildings))
            time.sleep(0.02)

        st.session_state.damage_data = pd.DataFrame(damage_results)
        progress_bar.empty()
        if run_simulation:
            st.success('Analysis Complete')
        else:
            st.info('Parameters changed - damage recalculated')

# Display results
if st.session_state.simulation_run and st.session_state.damage_data is not None:
    df = st.session_state.damage_data

    # Metrics Dashboard
    st.markdown("### IMPACT SUMMARY")

    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        st.metric("Event Magnitude", f"{magnitude:.1f} Mw")

    with m2:
        avg_damage = df['damage_percent'].mean()
        st.metric("Mean Damage", f"{avg_damage:.1f}%")

    with m3:
        max_damage = df['damage_percent'].max()
        st.metric("Peak Damage", f"{max_damage:.1f}%")

    with m4:
        critical = len(df[df['damage_state'].isin(['Extensive', 'Severe', 'Collapse'])])
        st.metric("Critical Structures", f"{critical}")

    with m5:
        avg_pga = df['pga_g'].mean()
        st.metric("Avg PGA", f"{avg_pga:.3f}g")

    # Main visualization area - no tabs, just the map
    # Animation controls - slider based
    play_animation = st.checkbox("Show Wave Propagation Timeline", value=False)

    if play_animation:
        col_slider, col_info = st.columns([3, 1])

        with col_slider:
            time_step = st.slider(
                "Drag to see waves expand over time (seconds after earthquake)",
                min_value=0.0,
                max_value=60.0,
                value=10.0,
                step=0.5
            )

        with col_info:
            p_radius = time_step * 6.0
            s_radius = time_step * 3.5
            st.info(f"""
            **t = {time_step:.1f}s**

            P-wave: {p_radius:.1f} km
            S-wave: {s_radius:.1f} km
            """)
    else:
        time_step = 0.0

    viz_col1, viz_col2 = st.columns([3.5, 1])

    # Define damage colors (used by both map and legend)
    damage_colors = {
        "None": '#00ff00',
        "Slight": '#adff2f',
        "Moderate": '#ffff00',
        "Extensive": '#ffa500',
        "Severe": '#ff4500',
        "Collapse": '#8b0000'
    }

    with viz_col1:
        # INTERACTIVE FOLIUM MAP
        # Calculate dynamic zoom based on wave radius when animating
        if play_animation and time_step > 0:
            # S-wave is larger, use it for bounds
            wave_radius_km = time_step * 3.5
            # Convert km to degrees (roughly 111 km per degree)
            radius_deg = wave_radius_km / 111.0

            # Calculate bounds to fit the wave
            bounds = [
                [epicenter_lat - radius_deg * 1.2, epicenter_lon - radius_deg * 1.2],
                [epicenter_lat + radius_deg * 1.2, epicenter_lon + radius_deg * 1.2]
            ]

            # Create map centered on epicenter
            m = folium.Map(
                location=[epicenter_lat, epicenter_lon],
                tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
                attr='CartoDB',
                prefer_canvas=True,
                zoom_control=True,
                scrollWheelZoom=True
            )

            # Fit map to wave bounds
            m.fit_bounds(bounds)
        else:
            # Static view centered on SF
            m = folium.Map(
                location=[37.7749, -122.4194],
                zoom_start=13,
                tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
                attr='CartoDB',
                prefer_canvas=True,
                zoom_control=True,
                scrollWheelZoom=True
            )

        # Ground motion heatmap
        if show_pga:
            # San Francisco County approximate boundary polygon
            # Simplified boundary coordinates (clockwise from northwest)
            from shapely.geometry import Point, Polygon

            sf_boundary = Polygon([
                (-122.5145, 37.8105),  # NW - Point Lobos
                (-122.3927, 37.8105),  # NE - Treasure Island
                (-122.3480, 37.7083),  # SE - San Bruno Mountain
                (-122.3927, 37.7083),  # S - near Daly City
                (-122.5145, 37.7083),  # SW - Ocean/Pacific
            ])

            heat_data = []
            # Use finer grid for better coverage (60x60 = 3600 points)
            for lat in np.linspace(37.70, 37.83, 60):
                for lon in np.linspace(-122.52, -122.35, 60):
                    # Check if point is within SF county boundary
                    point = Point(lon, lat)
                    if sf_boundary.contains(point):
                        dist = calculate_distance(lat, lon, epicenter_lat, epicenter_lon)
                        pga = earthquake.get_ground_acceleration(dist)
                        if pga > 0.0003:
                            heat_data.append([lat, lon, pga * 200])

            plugins.HeatMap(
                heat_data,
                min_opacity=0.4,
                max_opacity=0.8,
                radius=18,
                blur=20,
                gradient={0.0: '#00ff00', 0.25: '#adff2f', 0.5: '#ffff00',
                         0.65: '#ffa500', 0.8: '#ff4500', 1.0: '#8b0000'}
            ).add_to(m)

            # Optionally add SF county boundary outline
            folium.GeoJson(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [list(sf_boundary.exterior.coords)]
                    }
                },
                style_function=lambda x: {
                    'fillColor': 'transparent',
                    'color': '#ffffff',
                    'weight': 2,
                    'dashArray': '5, 5',
                    'opacity': 0.6
                }
            ).add_to(m)

        # Animation: Wave circles if enabled
        if play_animation:
            # P-wave (faster, blue)
            p_wave_velocity = 6.0  # km/s
            p_radius_km = p_wave_velocity * time_step
            if p_radius_km > 0.1:  # Show if there's any meaningful radius
                folium.Circle(
                    location=[epicenter_lat, epicenter_lon],
                    radius=p_radius_km * 1000,  # convert to meters
                    color='#4169E1',
                    fill=False,
                    weight=3,
                    opacity=0.8,
                    dash_array='5, 5',
                    popup=f"P-wave at {time_step:.1f}s<br>Radius: {p_radius_km:.1f} km"
                ).add_to(m)

            # S-wave (slower, red - main damage)
            s_wave_velocity = 3.5  # km/s
            s_radius_km = s_wave_velocity * time_step
            if s_radius_km > 0.1:
                folium.Circle(
                    location=[epicenter_lat, epicenter_lon],
                    radius=s_radius_km * 1000,
                    color='#FF4500',
                    fill=True,
                    fillColor='#FF4500',
                    fillOpacity=0.15,
                    weight=4,
                    opacity=0.9,
                    popup=f"S-wave (shaking) at {time_step:.1f}s<br>Radius: {s_radius_km:.1f} km"
                ).add_to(m)

        # Epicenter
        folium.Marker(
            location=[epicenter_lat, epicenter_lon],
            popup=f"<b>EPICENTER</b><br>M{magnitude:.1f} @ {depth}km depth<br>Time: {time_step:.1f}s" if play_animation else f"<b>EPICENTER</b><br>M{magnitude:.1f} @ {depth}km depth",
            icon=folium.Icon(color='red', icon='star', prefix='fa')
        ).add_to(m)

        # Distance reference circles with labels (only show if not animating)
        if not play_animation:
            for radius_km, label_pos in [(5, 'top'), (10, 'middle'), (15, 'bottom')]:
                circle = folium.Circle(
                    location=[epicenter_lat, epicenter_lon],
                    radius=radius_km * 1000,
                    color='#ff6b6b',
                    fill=False,
                    weight=2,
                    opacity=0.6,
                    dash_array='8, 4',
                    popup=f"{radius_km}km from epicenter"
                ).add_to(m)

                # Add distance label
                offset_lat = epicenter_lat + (radius_km / 111.0) if label_pos == 'top' else epicenter_lat
                folium.Marker(
                    location=[offset_lat, epicenter_lon + (radius_km / 111.0 / np.cos(np.radians(epicenter_lat)))],
                    icon=folium.DivIcon(html=f"""
                        <div style="background: rgba(255,107,107,0.8);
                                    color: white;
                                    padding: 4px 8px;
                                    border-radius: 4px;
                                    font-weight: bold;
                                    font-size: 11px;
                                    border: 2px solid #fff;">
                            {radius_km}km
                        </div>
                    """)
                ).add_to(m)

        # Buildings
        # Import time-dependent damage function if animating
        if play_animation:
            from earthquake_animation import calculate_time_dependent_damage

        for _, row in df.iterrows():
            building = next(b for b in buildings if b.id == row['building_id'])

            # Calculate time-dependent damage if animating
            if play_animation:
                time_damage = calculate_time_dependent_damage(building, earthquake, time_step)
                color = time_damage['color']
                current_damage = time_damage['damage_percent']
                damage_state = time_damage['damage_state']
                is_shaking = time_damage.get('is_shaking', False)
                radius_multiplier = 1.5 if is_shaking else 1.0
            else:
                color = damage_colors.get(row['damage_state'], '#808080')
                current_damage = row['damage_percent']
                damage_state = row['damage_state']
                is_shaking = False
                radius_multiplier = 1.0

            popup_html = f"""
            <div style="width: 240px; background: #1a1f3a; color: white;
                        padding: 12px; border-radius: 8px; border: 3px solid {color};">
                <h4 style="margin: 0 0 8px 0; color: {color}; font-size: 1.1rem;">
                    {building.name}
                </h4>
                <div style="border-top: 1px solid #444; padding-top: 8px;">
                    <p style="margin: 4px 0;"><b>Type:</b> {building.building_type.replace('_', ' ').title()}</p>
                    <p style="margin: 4px 0;"><b>Height:</b> {building.height_stories} stories</p>
                    <p style="margin: 4px 0;"><b>Built:</b> {building.year_built}</p>
                </div>
                <div style="border-top: 1px solid #444; margin-top: 8px; padding-top: 8px;">
                    <p style="margin: 4px 0;"><b>Distance:</b> {row['distance_km']:.2f} km</p>
                    <p style="margin: 4px 0;"><b>Peak Accel:</b> {row['pga_g']:.4f}g</p>
                    <p style="margin: 4px 0;"><b>MMI:</b> {row['mmi']}</p>
                </div>
                <div style="background: {color}; padding: 10px; margin-top: 8px;
                            border-radius: 6px; text-align: center;">
                    <p style="margin: 0; font-weight: bold; font-size: 1.2rem;
                              color: {'white' if damage_state in ['Severe', 'Collapse'] else 'black'};">
                        {damage_state.upper()}: {current_damage:.1f}%
                        {' (SHAKING)' if play_animation and time_step > 0 and is_shaking else ''}
                    </p>
                </div>
            </div>
            """

            radius = (7 + (building.height_stories / 4)) * radius_multiplier

            folium.CircleMarker(
                location=[building.latitude, building.longitude],
                radius=radius,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=building.name if show_labels else None,
                color='#000',
                fillColor=color,
                fillOpacity=0.85,
                weight=2.5
            ).add_to(m)

        # Render map
        st_folium(m, width=None, height=650, returned_objects=[])

    with viz_col2:
        # Damage distribution panel
        st.markdown("#### DAMAGE LEVELS")

        # Calculate current damage distribution (time-dependent if animating)
        if play_animation and time_step > 0:
            from earthquake_animation import calculate_time_dependent_damage
            current_damage_states = []
            for _, row in df.iterrows():
                building = next(b for b in buildings if b.id == row['building_id'])
                time_damage = calculate_time_dependent_damage(building, earthquake, time_step)
                current_damage_states.append(time_damage['damage_state'])
            damage_counts = pd.Series(current_damage_states).value_counts()
        else:
            damage_counts = df['damage_state'].value_counts()

        for state in ["None", "Slight", "Moderate", "Extensive", "Severe", "Collapse"]:
            count = damage_counts.get(state, 0)
            if count > 0:
                pct = (count / len(df)) * 100
                color = damage_colors[state]
                st.markdown(f"""
                    <div class='legend-item' style='border-left-color: {color};'>
                        <div class='legend-color' style='background: {color};'></div>
                        <div>
                            <strong style='color: #fff;'>{state}</strong><br>
                            <small style='color: #b0bec5;'>{count} bldg ({pct:.0f}%)</small>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Map legend
        st.markdown("#### VISUALIZATION KEY")
        st.markdown("""
            <div style='font-size: 0.9rem; line-height: 1.8; color: #e8eaf6;'>
            <b style='color: #ffd700;'>Heat Colors:</b><br>
            • <span style='color: #00ff00;'>Green</span> = Low shaking<br>
            • <span style='color: #ffff00;'>Yellow</span> = Moderate<br>
            • <span style='color: #ffa500;'>Orange</span> = Strong<br>
            • <span style='color: #ff4500;'>Red</span> = Severe<br>
            <br>
            <b style='color: #ffd700;'>Circles:</b><br>
            • Dashed rings = Distance zones<br>
            • Filled dots = Buildings<br>
            • Size = Building height<br>
            <br>
            <b style='color: #ffd700;'>Click markers</b> for details
            </div>
        """, unsafe_allow_html=True)

