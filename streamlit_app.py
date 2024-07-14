# __IMPORTS__
import streamlit as st
import streamlit.components.v1 as components
from sys import platform
import os

# map
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen
from folium.plugins import Draw
from shapely.geometry import Polygon
import geopandas as gpd

# 3d
import pyvista as pv
from stpyvista import stpyvista
from stpyvista.utils import start_xvfb

# own 
from src.web.data import *
from src.web.build import *
from src.web.coords import *
from src.web.filter import *
from src.web.map import *

# plot
import plotly.express as px


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

  
st.sidebar.image("media/swiss3d.png")

# __INIT STATES__
if "create" not in st.session_state:
    st.session_state["create"] = False
    delete_stl()

if "downloaded" not in st.session_state:
    st.session_state["downloaded"] = False

if "sponsor" not in st.session_state:
    st.session_state["sponsor"] = False
    
if "given_feedback" not in st.session_state:
    st.session_state["given_feedback"] = False

if "points" not in st.session_state:
    st.session_state["points"] = []
    
if platform == "linux" or platform == "linux2":
    if "IS_XVFB_RUNNING" not in st.session_state:
        start_xvfb()
        st.session_state.IS_XVFB_RUNNING = True 


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
    delete_stl()


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
    
    st.balloons()
    """
    ## Done!
    You will find your custom model in the **download folder**.  
    """
    st.text("")
    st.divider()
    st.markdown("**If you have a minute to share your experience...**")
    cols = st.columns((.6,.4), gap="large")
    
    if os.path.isfile("survey_results.pkl"):
        survey_results = pd.read_pickle("survey_results.pkl")
        df_plot = survey_results.melt(var_name="Feature", value_name="Rating").sort_values("Feature")
        fig = px.bar_polar(df_plot, r="Rating", theta="Feature", color="Feature")
        fig = px.box(df_plot, color="Feature", orientation="h", y="Feature", x="Rating", range_x=(0,10), title=f"Feedback<br><sub>from {survey_results.shape[0]} users")
        fig.add_vline(5, line_color="grey")
        cols[0].plotly_chart(fig, use_container_width=True)
    else:
        cols[0].info("no survey results available yet...")
    if not st.session_state["given_feedback"]:
        with cols[1].form("feedback"):
            features = {}
            for feature in np.sort(["Usability", "Simplicity", "Design", "Appreciation"]):
                features[feature] = st.slider(feature, 0, 10, value=5, help="from 0 ~ horrible to 10 ~ awesome")

            # Every form must have a submit button.
            submitted = st.form_submit_button("Add your feedback", type="primary", use_container_width=True)
            if submitted:
                if os.path.isfile("survey_results.pkl"):
                    survey_result = pd.DataFrame(features, index=[survey_results.shape[0]])
                    survey_results = pd.concat([survey_results, survey_result])
                    survey_results.to_pickle("survey_results.pkl")
                else:
                    survey_result = pd.DataFrame(features, index=[0])
                    survey_result.to_pickle("survey_results.pkl")
                st.session_state["given_feedback"] = True
                st.rerun()
    else:
        cols[1].info("Thanks for your feedback!")

# __INFORMATION__
with st.sidebar: # GRID
    st.markdown(
        """
        ## Grid Resolution
        Higher grid resolution means more resources, which results in higher hosting-costs.  

        🌍 Deployed App is fixed to **200m**.   
        🖥️ Local up to **25m** is supported.  
           
           
        Become a sponsor and available grid resolutions up to **0.5m**! Get in contact with me...  
        📬 https://schabidesigns.ch
        """
        )