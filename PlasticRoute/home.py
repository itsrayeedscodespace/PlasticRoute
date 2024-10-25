import streamlit as st
import folium
from streamlit_folium import folium_static
from streamlit_folium import st_folium
from PIL import Image
import base64
from io import BytesIO

# Set page configuration
st.set_page_config(page_title="AquaRoute", layout="wide")

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
    st.session_state['map_center'] = [34.0522, -118.2437]  # Default to Los Angeles

# Section with Map and Inputs
st.subheader("Plan Your Route")

# Create columns for layout
col1, col2 = st.columns([2, 1])

with col1:
    # Create a Folium map
    m = folium.Map(location=st.session_state['map_center'], zoom_start=10)
    
    # Display the map
    map_data = st_folium(m, width=700, height=500, key="map")

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
        st.success(f"Optimizing route from {st.session_state['start_position']} to {st.session_state['stop_position']}")

# ... (keep the rest of the code unchanged) ...
