from src.web.coords import coords2LV03
import numpy as np

def filter_dataframe(df, points, cellsize, **kwargs):
    lat = []
    lng = []
    for point in points:
        new_point = coords2LV03(point[1], point[0])
        lat.append(new_point[0])
        lng.append(new_point[1])

    x_min = np.min(lat) - cellsize
    x_max = np.max(lat) + cellsize
    y_min = np.min(lng) - cellsize
    y_max = np.max(lng) + cellsize
    area = df.loc[y_max:y_min, x_min:x_max]
    print("shape:",area.shape)
    return area

def get_bounds_from_points(points, cellsize, **kwargs):
    lat = []
    lng = []
    for point in points:
        new_point = coords2LV03(point[1], point[0])
        lat.append(new_point[0])
        lng.append(new_point[1])

    x_min = np.min(lat) - cellsize
    x_max = np.max(lat) + cellsize
    y_min = np.min(lng) - cellsize
    y_max = np.max(lng) + cellsize
    return ((x_min,x_max), (y_max,y_min))