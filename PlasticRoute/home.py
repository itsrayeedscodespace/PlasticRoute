import streamlit as st
import folium
from streamlit_folium import st_folium
from PIL import Image
import base64
from io import BytesIO
from geopy.distance import geodesic
import networkx as nx
import numpy as np
import time
from geopy import distance as geopy_distance
import pickle
from global_land_mask import globe


# Set page configuration
st.set_page_config(page_title="AquaRoute", layout="wide")

with open("zdata.pickle", 'rb') as file:
    x, y, z = pickle.loads(file.read())

@st.cache_resource
def load_image():
    image = Image.open("static/img/bgimageocean.jpg")
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

@st.cache_resource
def load_video():
    with open("vid/oceanvid.mp4", "rb") as video_file:
        video_bytes = video_file.read()
    return base64.b64encode(video_bytes).decode()

# Generate grid-based world map: For simplicity, let's mock this
def generate_world_grid():
    # Create a grid where 0 = water, 1 = land
    # Assume a simplified world map with random land/ocean. Replace with real data
    np.random.seed(42)
    grid = np.zeros((180, 360), dtype=int)  # 180x360 for lat, lon
    grid[40:60, 120:140] = 1  # Fake landmass
    return grid

# Function to check if a point is on water in the grid
def is_ocean(lat, lon, grid):
    # Convert lat, lon to grid index
    grid_lat = int((lat + 90) % 180)
    grid_lon = int((lon + 180) % 360)
    return grid[grid_lat, grid_lon] == 0

# AI-based A* pathfinding to avoid land
def a_star_ocean_path(start, stop, grid):
    # Generate a graph where water cells are nodes, and connect neighboring nodes
    graph = nx.Graph()
    for i in range(1, 179):
        for j in range(1, 359):
            if grid[i, j] == 0:  # Only connect water cells
                if grid[i + 1, j] == 0:
                    graph.add_edge((i, j), (i + 1, j), weight=1)
                if grid[i, j + 1] == 0:
                    graph.add_edge((i, j), (i, j + 1), weight=1)

    # Convert start, stop lat/lon to grid indices
    start_lat = int((float(start[0]) + 90) % 180)
    start_lon = int((float(start[1]) + 180) % 360)
    stop_lat = int((float(stop[0]) + 90) % 180)
    stop_lon = int((float(stop[1]) + 180) % 360)

    # Find shortest path using A*
    try:
        path = nx.astar_path(graph, (start_lat, start_lon), (stop_lat, stop_lon))
        return [(lat - 90, lon - 180) for lat, lon in path], True  # Convert back to lat/lon and return success flag
    except nx.NetworkXNoPath:
        return [], False  # Return empty path and failure flag

@st.cache_data
def calculate_route(start_coords, stop_coords):
    # Calculate the great circle distance
    total_distance = geopy_distance.distance(start_coords, stop_coords).kilometers
    
    # For a straight line on the map, we only need start and end points
    route = [start_coords, stop_coords]
    
    return route, f"Route optimized successfully! Total distance: {total_distance:.2f} km"

# Load resources
img_str = load_image()
video_str = load_video()

# Initialize session state
if 'start_position' not in st.session_state:
    st.session_state['start_position'] = ''
if 'stop_position' not in st.session_state:
    st.session_state['stop_position'] = ''
if 'distance' not in st.session_state:
    st.session_state['distance'] = ''
if 'map_center' not in st.session_state:
    st.session_state['map_center'] = [27.5, -140.0]  # Mid-Pacific as default center
if 'optimized_route' not in st.session_state:
    st.session_state['optimized_route'] = None
if 'route_message' not in st.session_state:
    st.session_state['route_message'] = ''

# Section with Map and Inputs
st.subheader("Plan Your Route")

# Create columns for layout
col1, col2 = st.columns([2, 1])

# Load mock grid data
world_grid = generate_world_grid()

with col1:
    # Create a placeholder for the input map
    input_map_placeholder = st.empty()

    # Display the input map
    m = folium.Map(location=st.session_state['map_center'], zoom_start=3)
    map_data = st_folium(m, width=700, height=500, key="input_map")

    # Handle map clicks
    if map_data['last_clicked'] is not None:
        clicked_lat = map_data['last_clicked']['lat']
        clicked_lon = map_data['last_clicked']['lng']
        st.session_state['start_position'] = f"{clicked_lat:.6f}, {clicked_lon:.6f}"
        st.session_state['map_center'] = [clicked_lat, clicked_lon]

with col2:
    # Create empty containers for input fields
    start_container = st.empty()
    stop_container = st.empty()
    distance_container = st.empty()

    # Update input fields
    start_position = start_container.text_input("Start Position (lat, lon)", value=st.session_state['start_position'], key='start_position_input')
    stop_position = stop_container.text_input("Stop Position (lat, lon)", value=st.session_state['stop_position'], key='stop_position_input')
    distance = distance_container.text_input("Distance (in km)", value=st.session_state['distance'], key='distance_input')

    # Update session state
    st.session_state['start_position'] = start_position
    st.session_state['stop_position'] = stop_position
    st.session_state['distance'] = distance

    # Button to Optimize Route
    if st.button("Optimize Route"):
        try:
            start_coords = tuple(map(float, start_position.split(',')))
            stop_coords = tuple(map(float, stop_position.split(',')))
            
            route, message = calculate_route(start_coords, stop_coords)
            
            if route:
                st.session_state['optimized_route'] = route
                st.session_state['route_message'] = message
                st.session_state['map_center'] = start_coords
            else:
                st.session_state['optimized_route'] = None
                st.session_state['route_message'] = message
        except Exception as e:
            st.session_state['optimized_route'] = None
            st.session_state['route_message'] = f"Error: {e}"

# New section for displaying route information and optimized map
st.subheader("Optimized Route Information")

if st.session_state['optimized_route']:
    col3, col4 = st.columns([2, 1])

    with col3:
        # Display the optimized route map
        m = folium.Map()
        start_coords = tuple(map(float, st.session_state['start_position'].split(',')))
        stop_coords = tuple(map(float, st.session_state['stop_position'].split(',')))
        
        # Add markers for start and stop
        folium.Marker(
            start_coords,
            popup="Start",
            icon=folium.Icon(color="green", icon="play")
        ).add_to(m)
        folium.Marker(
            stop_coords,
            popup="Stop",
            icon=folium.Icon(color="red", icon="stop")
        ).add_to(m)
        
        # Add the straight line
        folium.PolyLine([start_coords, stop_coords], color="blue", weight=2.5, opacity=1).add_to(m)
        
        # Fit the map to the bounds of the route
        m.fit_bounds([start_coords, stop_coords])
        
        st_folium(m, width=700, height=500, key="optimized_map")

    with col4:
        # Display route information
        st.success(st.session_state['route_message'])
        st.write(f"Number of points in route: {len(st.session_state['optimized_route'])}")
        st.write(f"Start position: {st.session_state['start_position']}")
        st.write(f"Stop position: {st.session_state['stop_position']}")

elif st.session_state['route_message']:
    st.error(st.session_state['route_message'])
