# __IMPORTS__
# sys
from sys import platform
import os

# app
import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from streamlit_theme import st_theme

# map
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen
from folium.plugins import Draw
from shapely.geometry import Polygon
import geopandas as gpd

# 3d
import pyvista as pv
#from stpyvista import stpyvista
from stpyvista.trame_backend import stpyvista
#from stpyvista.utils import start_xvfb

# own 
from src.data import *
from src.build import *
from src.coords import *
from src.filter import *
from src.map import *
from src.utilities import print_memory_usage

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
    
# __INIT STATES__
if "created" not in st.session_state:
    st.session_state["created"] = False
    delete_stl()

if "downloaded" not in st.session_state:
    st.session_state["downloaded"] = False

if "given_feedback" not in st.session_state:
    st.session_state["given_feedback"] = False


if "sponsor" not in st.session_state:
    st.session_state["sponsor"] = False

if "points" not in st.session_state:
    st.session_state["points"] = []
    
if "3d_plot" not in st.session_state:
    st.session_state["3d_plot"] = None

if platform == "linux" or platform == "linux2":
    if "IS_XVFB_RUNNING" not in st.session_state: 
        pv.start_xvfb()
        st.session_state.IS_XVFB_RUNNING = True 


# __VARIABLES__
window_height = 900 # how to set to vh????
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

def build_stl(area_3d):
    return create_stl(object=area_3d)

def reset_page():
    delete_stl()
    # delete pyvista plotter to free memory
    del st.session_state["3d_plot"]
    st.session_state["created"] = False
    st.session_state["downloaded"] = False
    streamlit_js_eval(js_expressions="parent.window.location.reload()")



# __MAIN PAGE__
theme = st_theme()
if theme:
    if theme.get("base")== "light":
        st.sidebar.image("media/swiss3d.png")
    else:
        st.sidebar.image("media/swiss3d_dark.png")

if st.session_state["downloaded"] == False:
    if st.session_state["created"] == False:
        st.sidebar.markdown("""
            # Instruction
            1. Draw your area in Switzerland
            2. Inspect the 3D-model  
            3. Download STL
            """)
        
        button_container = st.sidebar.container(height=140, border=False)

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
        output = st_folium(m, use_container_width=True, height=window_height, key="map")
        st.session_state["output"] = output
        
        # if something has been drawn
        if output["last_active_drawing"] and output["all_drawings"]:

            geo = []
            disabled = True
            
            # check if drawing is within border
            st.session_state["geometry"] = output["last_active_drawing"]["geometry"]
            st.session_state["type"] = output["last_active_drawing"]["geometry"]["type"]
            
            if st.session_state["type"]=="Polygon":

                # store this information for cutting 3D object
                st.session_state["points"] = st.session_state["geometry"]["coordinates"][0]

                geo = gpd.GeoSeries(Polygon(st.session_state["points"]), crs="epsg:4326")
            else:
                button_container.error("Drawing type not implemented yet... use other drawing object.")

            if all(geo.covered_by(get_border())):
                # Convert to a projected coordinate system (e.g., EPSG:3857)
                geo_projected = geo.to_crs(epsg=3857)
                # Calculate the area in square meters
                area_sqkm = geo_projected.area[0]/1e6
                if area_sqkm<10000:
                    disabled = False
                else: 
                    button_container.error(f"The area of {area_sqkm:,.0f}km² is too big to render. (max 10'000km²)".replace(",","'"))
            else: 
                button_container.error("The area must be in switzerland")
            
            if button_container.button("Build 3D-object", key="button_build_3d", disabled=disabled, use_container_width=True, type="primary"):
                        st.session_state["created"] = True
                        st.rerun()
        else:
            button_container.info("No drawings on the map")
            
    if st.session_state["created"] == True:
        if st.session_state["type"]=="Polygon":
            st.sidebar.markdown("""
                # Instruction
                1. Draw your area in Switzerland ✔️ 
                2. Inspect the 3D-model ⏳
                3. Download STL
                """)
            button_container = st.sidebar.container(height=140, border=False)
            col1, col2 = button_container.columns([0.3, 0.7], gap="small")
            if col1.button("Back", use_container_width=True, key="button_inspect_back"):
                reset_page()
                
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
                pl.background_color = theme.get("backgroundColor")
                pl.remove_scalar_bar()
                pl.camera_position = "xz"
                pl.camera.azimuth = 0
                pl.camera.elevation = 45
                pl.reset_camera(bounds=mesh.bounds)
                stpyvista(pl, use_container_width=True, key=f"3d_plot{theme.get('base')}")
                pv.close_all()
            
            if col2.download_button("Download your STL file", data=build_stl(area_3d), file_name="your_custom_model.stl", type="primary", use_container_width=True):
                st.session_state["downloaded"] = True
                st.rerun()
                        
                    
if st.session_state["downloaded"] == True:
    st.sidebar.markdown("""
        # Instruction
        1. Draw your area in Switzerland ✔️ 
        2. Inspect the 3D-model ✔️ 
        3. Download STL ✔️ 
        """)
    
    button_container = st.sidebar.container(height=140, border=False)

    st.markdown(
        """
        ## Done!
        You will find your custom model in the **download folder**.  
        """)
    st.text("")
    st.divider()
    st.subheader("Mini survey")
    cols = st.columns((.6,.4), gap="large")
    
    if os.path.isfile("survey_results.pkl"):
        survey_results = pd.read_pickle("survey_results.pkl")
        df_plot = survey_results.melt(var_name="Feature", value_name="Rating").sort_values("Feature")
        fig = px.bar_polar(df_plot, r="Rating", theta="Feature", color="Feature")
        fig = px.box(df_plot, color="Feature", orientation="h", y="Feature", x="Rating", range_x=(0,10), title=f"Collected feedback<br><sub>from {survey_results.shape[0]} users")
        fig.add_vline(5, line_color="lightgrey", line_dash="dash")
        cols[0].plotly_chart(fig, use_container_width=True)
    else:
        cols[0].info("no survey results available yet...")
    if not st.session_state["given_feedback"]:
        with cols[1].form("feedback"):
            st.markdown("**If you have a minute to share your experience...**")
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
        
    if button_container.button("Create another model", use_container_width=True, type="primary", key="button_survey_new"):
        reset_page()

# __INFORMATION__
with st.sidebar: # GRID
    st.markdown(
        """        
        ## Grid Resolutions
        Higher grid resolution means more resources, which results in higher hosting-costs.  

        🌍 Deployed App is fixed to **200m**.   
        🖥️ Local up to **25m** is supported.  
        
        SPOILER *Grid resolutions up to **0.5m** are possible!*
        
        ⚙️ **Contribute**  
        https://github.com/SchabiDesigns/swiss3d
        
        
        🍻 **Support**  
        https://buymeacoffee.com/schabi
        """
        )