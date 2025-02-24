import streamlit as st
from streamlit_stl import stl_from_text

file_input = st.file_uploader("Or upload an STL file", type=["stl"])

if file_input is not None:
    success = stl_from_text(
        text=file_input.getvalue(),  # Content of the STL file as text
        color='#FF9900',             # Color of the STL file (hexadecimal value)
        material='material',         # Material of the STL file ('material', 'flat', or 'wireframe')
        auto_rotate=True,            # Enable auto-rotation of the STL model
        opacity=1,                   # Opacity of the STL model (0 to 1)
        shininess=10,                # How shiny the specular highlight is, when using the 'material' style.
        cam_v_angle=60,              # Vertical angle (in degrees) of the camera
        cam_h_angle=-90,             # Horizontal angle (in degrees) of the camera
        cam_distance=None,           # Distance of the camera from the object (defaults to 3x bounding box size)
        height=500,                  # Height of the viewer frame
        max_view_distance=1000,      # Maximum viewing distance for the camera
        key=None                     # Streamlit component key
    )