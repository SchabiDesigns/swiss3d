import geopandas as gpd
import folium
from folium.plugins import Draw
import geopandas as gpd
import pyogrio
from shapely.geometry import Point, Polygon


def get_switzerland(**kwargs) -> gpd.GeoDataFrame:
    """get switzerland border from swisstopo (local loaded)
    """
    gdf = gpd.read_file("data/borders/swissBOUNDARIES3D_1_4_TLM_LANDESGEBIET.shp", engine="pyogrio").to_crs(epsg=4326)
    return gdf[gdf["NAME"]=="Schweiz"].loc[:,["NAME","geometry"]]


def create_map(border, **kwargs):

    m = folium.Map(attr="swisstopo")

    # add drawing tools
    Draw(export = False,
        draw_options={
            "marker"       : False,
            "circlemarker" : False,
            "polyline"     : False
        }).add_to(m)

    # add country borders
    folium.GeoJson(border, 
                smooth_factor=2, 
                style_function=lambda feature: {
                        "fillColor": "red",
                        "fillOpacity": 0,
                        "color": "red",
                        "weight": 2
                    }).add_to(m)
    
    # set level of zoom
    m.fit_bounds(m.get_bounds(), padding=(10, 10))

    return m