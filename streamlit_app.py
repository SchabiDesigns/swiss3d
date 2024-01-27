# __IMPORTS__
import streamlit as st
import streamlit.components.v1 as components
from sys import platform
import webbrowser

# map
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen
from folium.plugins import Draw
from shapely.geometry import Polygon
import geopandas as gpd
import numpy as np

# 3d
import pyvista as pv
from stpyvista import stpyvista

# own 
from src.web.data import *
from src.web.build import *
from src.web.coords import *
from src.web.filter import *
from src.web.map import *


# __PAGE CONFIGS__
st.set_page_config(
    page_title="3D - Mountains",
    page_icon="🇨🇭",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://github.com/SchabiDesigns/swiss3d/discussions",
        "Report a bug": "https://github.com/SchabiDesigns/swiss3d/issues",
        "About": """
        Developed by [SchabiDesigns](https://schabidesigns.ch).  
        Data from [swisstopo](https://www.swisstopo.admin.ch).
        """
    }
)

if platform == "linux" or platform == "linux2":
    pv.start_xvfb()

st.sidebar.image("media/swiss3d.png")

# __INIT STATES__
if "create" not in st.session_state:
    st.session_state["create"] = False

if "downloaded" not in st.session_state:
    st.session_state["downloaded"] = False

if "sponsor" not in st.session_state:
    st.session_state["sponsor"] = False

if "points" not in st.session_state:
    st.session_state["points"] = []


# __VARIABLES__
window_height = 1000 # how to set to vh????
DEV = False

# __FUNCTIONS__
@st.cache_data
def read_data(sponsor):
    if sponsor:
        with st.spinner("loading 25m"):
            df, meta = check_cache(file="dhm25")
    else:
        with st.spinner("loading 200m"):
            df, meta = check_cache(file='dhm200')
    return df, meta

@st.cache_data
def get_border():
    return get_switzerland()

def reset_create():
    st.session_state["create"] = False


# __MAIN PAGE__
if not st.session_state["downloaded"]:
    if not st.session_state["create"]:
        with st.sidebar:
            """

            # Instruction
            1. Draw your area in Switzerland
            2. Inspect the 3D-model  
            3. Download STL
            """

            placeholder = st.container(height=90, border=False)

        m = folium.Map(attr="swisstopo")

        # add drawing tools
        Draw(export = False,
            draw_options={
                "marker"       : False,
                "circlemarker" : False,
                "polyline"     : False,
                "circle"       : False
            }).add_to(m)

        # add country borders
        folium.GeoJson(get_border(), 
                    smooth_factor=2, 
                    style_function=lambda feature: {
                            "fillColor": "red",
                            "fillOpacity": 0,
                            "color": "red",
                            "weight": 2
                        }).add_to(m)

        # set level of zoom automatically to border
        m.fit_bounds(m.get_bounds(), padding=(10, 10))
        Fullscreen(position="topleft").add_to(m)
        output = st_folium(m, use_container_width=True, height=window_height)
        st.session_state["output"] = output
        
        # if something has been drawn
        if output["last_active_drawing"] and output["all_drawings"]:

            geo = []

            # check if drawing is within border
            st.session_state["geometry"] = output["last_active_drawing"]["geometry"]
            st.session_state["type"] = output["last_active_drawing"]["geometry"]["type"]

            if st.session_state["type"]=="Polygon":

                # store this information for cutting 3D object
                st.session_state["points"] = st.session_state["geometry"]["coordinates"][0]

                geo = gpd.GeoSeries(Polygon(st.session_state["points"]), crs="epsg:4326")
            else:
                st.error("Drawing type not implemented yet... use other drawing object.")

            not_in_swiss = not all(geo.covered_by(get_border()))

            with placeholder:
                if not_in_swiss:
                    st.error("The area must be in switzerland")
                else:
                    st.button("Build 3D-object", key="create", disabled=not_in_swiss, use_container_width=True, type="primary")
        else:
            with placeholder:
                st.info("No drawings on the map")

    else:
        if st.session_state["type"]=="Polygon":
            with st.sidebar:
                """
                # Instruction
                1. Draw your area in Switzerland ✔️ 
                2. Inspect the 3D-model ⏳
                3. Download STL
                """
                placeholder = st.container(height=90, border=False)
            
            df, meta = read_data(st.session_state["sponsor"])
            with st.spinner("creating your custom 3D model..."):
                area = filter_dataframe(df, st.session_state["points"], **meta)
                
                height = area.max().max()
                zero = area.min().min()
                
                #add fundament of 10%
                zero -= (height-zero)*0.1

                mesh = create_surface(area)
                model = create_model(mesh,zero)
                border = create_border_from_points(st.session_state["points"], zero, height)
                area_3d = cut_model(model, border)

                pl = pv.Plotter()
                pl.add_mesh(area_3d.triangulate())
        
                ## Final touches
                pl.camera_position = "xz"
                pl.camera.azimuth = 0
                pl.camera.elevation = 45
                pl.reset_camera(bounds=mesh.bounds)
                
                stpyvista(pl, use_container_width=True)
            with placeholder:
                col1, col2 = st.columns([0.3, 0.7], gap="small")
                with col1:
                    st.button("Back", on_click=reset_create, use_container_width=True)
                with col2:
                    st.download_button("Download your STL file", create_stl(area_3d), file_name="your_custom_model.stl", type="primary", key="downloaded", use_container_width=True)
else:
    st.balloons()
    """
    ## Done!
    You will find your custom model in the download folder.  
    
    
    """
    with st.expander("Please take a minute for a small feedback."):
        components.iframe("https://forms.gle/oWQ9Mah8Mx6ma1oYA", height=window_height)
    
    with st.sidebar:
        """
        # Instruction
        1. Draw your area in Switzerland ✔️ 
        2. Inspect the 3D-model ✔️ 
        3. Download STL ✔️ 
        """
        placeholder = st.container(height=90, border=False)
        with placeholder:
            st.button("Create another model", on_click=reset_create, use_container_width=True, type="primary")


# __INFORMATION__
with st.sidebar: # GRID
    st.markdown(
        """
        ## Grid Resolution
        Higher grid resolution means more resources, which results in higher hosting-costs.  

        🌍 Deployed App is fixed to **200m**.   
        🖥️ Local up to **25m** is supported.  
          
        Become a sponsor and available grid resolutions up to **0.5m**! Get in contact with the developer...  
        📬 https://schabidesigns.ch
        """
        )


# __DEVELOPMENT__
if DEV:
    with st.sidebar:
        st.divider()
        """
        ## Licence
        """
        st.toggle("sponsor", key="sponsor")

        if st.session_state["sponsor"]:
            st.info("pro version (25m)")
        else:
            st.info("standard version (200m)")

        st.divider()
        """## Development
        """
        with st.expander("dataset info"):
            try:
                st.write("shape of df: " + df.shape)
                st.write("shape of area: " + area.shape)
            except:
                st.write("actually no map data")

        with st.expander("area"):
            try:
                bounds = get_bounds_from_points(st.session_state["points"], 200)
                bounds
            except:
                st.write("actually no area data")

        with st.expander("session state"):
            st.session_state
    

# __OTHER STUF TO NOT FORGET__
# with st.sidebar:
#     tile = st.selectbox("Map Style",options=["Standard", "Satellite"], index=0)

        
# # add satellite images doens"t work with polyline
# if tile!="Standard":
#     folium.TileLayer(
#         tiles   = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
#         attr    = "Esri",
#         name    = "Esri Satellite",
#         overlay = False,
#         control = True
#     ).add_to(m)

# # check if circle in border
# elif object["type"]=="Feature":
#     geo = gpd.GeoSeries([Point(object["geometry"]["coordinates"])],**args)
#     geo = geo.to_crs(epsg=32634).buffer(object["properties"]["radius"]).to_crs(epsg=4326)
#     st.sidebar.info("Size of the circle can be minimal different.")
        
        