import numpy as np
import pyvista as pv

import sys
import vtk

from src.web.coords import coords2LV03
from shapely.geometry import Polygon

def create_surface(df, **kwargs):
    x = np.ones(df.shape)
    y = x.copy()
    x *= np.array(df.columns)
    y = (y.T*np.array(df.index)).T
    z = np.array(df)
    mesh = pv.StructuredGrid(x, y, z)
    mesh = mesh.elevation()
    return mesh

def create_border_from_points(points, zero, height, **kwargs):
    if Polygon(points).exterior.is_ccw:
        ex_z = height-zero
        ref = zero
    else: 
        ex_z = -(height - zero)
        ref = height

    points_lv03 = []
    for point in points:
        point_lv03 = list(coords2LV03(lat=point[1], lng=point[0]))
        point_lv03.append(ref)
        points_lv03.append(point_lv03)
    poly = pv.lines_from_points(points_lv03)
    return poly.extrude([0, 0, ex_z], capping=False)

def create_model(mesh, zero, **kwargs):
    top = mesh.points.copy()
    bottom = mesh.points.copy()
    bottom[:, -1] = zero

    model = pv.StructuredGrid()
    model.points = np.vstack((top, bottom))
    model.dimensions = [*mesh.dimensions[0:2], 2]
    model = model.elevation()
    return model

def cut_model(model, border, **kwargs):
    area = model.clip_surface(border)
    area = area.elevation()
    return area


def create_stl(object, output_name="data/cache/model.stl"):
    surface_filter = vtk.vtkDataSetSurfaceFilter()
    surface_filter.SetInputDataObject(object)

    triangle_filter = vtk.vtkTriangleFilter()
    triangle_filter.SetInputConnection(surface_filter.GetOutputPort())

    writer = vtk.vtkSTLWriter()
    writer.SetFileName(output_name)
    writer.SetInputConnection(triangle_filter.GetOutputPort())
    writer.Write()
    return open(output_name, mode='r')