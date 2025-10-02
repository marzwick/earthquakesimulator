# San Francisco Earthquake Hazard Simulator

Interactive earthquake simulation tool for analyzing seismic hazard and infrastructure damage in San Francisco County.

## Features

- **Interactive Map**: Visualize earthquake impacts across San Francisco
- **Wave Propagation**: See P-waves and S-waves expand in real-time
- **Building Damage Assessment**: 15 representative structures with FEMA HAZUS damage classification
- **Ground Motion Heatmap**: Peak Ground Acceleration (PGA) visualization constrained to SF County boundaries
- **Multiple Scenarios**: Test different magnitudes (4.0-8.0 Mw), locations, and depths

## Physics Model

- **Ground Motion**: Boore-Atkinson (2008) attenuation model
- **Wave Propagation**: P-wave (6.0 km/s) and S-wave (3.5 km/s) velocities
- **Damage Assessment**: FEMA HAZUS methodology
- **Coordinate System**: WGS84 (EPSG:4326)

## Live Demo

[Access the live simulator here](https://share.streamlit.io) *(link will be added after deployment)*

## Local Installation

```bash
pip install -r requirements.txt
streamlit run earthquake_interactive.py
```

## Project Context

This tool was developed as a supporting analysis for a GIS vulnerability assessment, demonstrating the physical hazard component of earthquake risk in San Francisco County.
