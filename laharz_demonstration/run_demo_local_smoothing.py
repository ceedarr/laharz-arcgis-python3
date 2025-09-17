# PoC: Local path smoothing + angle-normal cross section demo
# This PoC does NOT modify original LaharZ code. It demonstrates how to:
# 1) Read DEM fill and flow direction rasters
# 2) Build a short downstream path (D8) and a sliding window for tangent estimation
# 3) Compute normal angle and trace a symmetric cross-section as polyline(s)
# 4) Save the cross-section as a feature class in a GDB or as a shapefile

import os
import arcpy
from arcpy import env
from arcpy.sa import *

from path_smoothing import estimate_tangent_angle, compute_normal_angle, window_push
from cross_section_angle import trace_cross_section_symmetric

arcpy.CheckOutExtension("Spatial")


def rc_to_xy(row: int, col: int, llx: float, lly: float, cell: float):
    """Convert array indices (row, col) to raster X,Y (cell centers)."""
    x = llx + (col + 0.5) * cell
    y = lly + (row + 0.5) * cell
    return (x, y)


def downstream_next_rc(r, c, flow_dir):
    """Move one step downstream given D8 flow direction code."""
    if flow_dir == 1:
        return (r, c + 1)
    elif flow_dir == 2:
        return (r + 1, c + 1)
    elif flow_dir == 4:
        return (r + 1, c)
    elif flow_dir == 8:
        return (r + 1, c - 1)
    elif flow_dir == 16:
        return (r, c - 1)
    elif flow_dir == 32:
        return (r - 1, c - 1)
    elif flow_dir == 64:
        return (r - 1, c)
    elif flow_dir == 128:
        return (r - 1, c + 1)
    else:
        raise ValueError(f"Bad flow direction: {flow_dir}")


def main(workspace, dem_fill, flow_dir_raster, start_xy, out_fc, window_len=7, max_delta_deg=25.0, max_steps=500):
    env.workspace = workspace
    env.extent = dem_fill
    env.snapRaster = dem_fill
    env.cellSize = dem_fill

    # DEM properties
    xxcellsize = arcpy.GetRasterProperties_management(dem_fill, "CELLSIZEX")
    cell = float(xxcellsize.getOutput(0))
    xxllx = arcpy.GetRasterProperties_management(dem_fill, "LEFT")
    llx = float(xxllx.getOutput(0))
    xxlly = arcpy.GetRasterProperties_management(dem_fill, "BOTTOM")
    lly = float(xxlly.getOutput(0))

    # Arrays
    A = arcpy.RasterToNumPyArray(dem_fill)
    C = arcpy.RasterToNumPyArray(flow_dir_raster)
    nrows, ncols = A.shape

    # Find start RC from XY
    start_x, start_y = start_xy
    col = int((start_x - llx) // cell)
    row = int((start_y - lly) // cell)
    if not (0 <= row < nrows and 0 <= col < ncols):
        raise ValueError("Start point outside raster extent")

    # Prepare output feature class
    out_dir = os.path.dirname(out_fc)
    if out_dir and not arcpy.Exists(out_dir):
        arcpy.CreateFolder_management(os.path.dirname(out_dir), os.path.basename(out_dir))

    spatial_ref = arcpy.Describe(dem_fill).spatialReference
    if out_fc.lower().endswith(".shp"):
        arcpy.CreateFeatureclass_management(out_dir, os.path.basename(out_fc), "POLYLINE", spatial_reference=spatial_ref)
    else:
        # assume GDB path
        arcpy.CreateFeatureclass_management(out_dir, os.path.basename(out_fc), "POLYLINE", spatial_reference=spatial_ref)

    with arcpy.da.InsertCursor(out_fc, ["SHAPE@"]) as ic:
        # sliding window of recent RCs
        win = []
        prev_normal = None

        r, c = row, col
        steps = 0
        while 0 <= r < nrows and 0 <= c < ncols and steps < max_steps:
            window_push(win, (r, c), window_len)
            tan = estimate_tangent_angle(win)
            if tan is None:
                # not enough history; move downstream and continue
                fd = int(C[r, c])
                r, c = downstream_next_rc(r, c, fd)
                steps += 1
                continue
            normal = compute_normal_angle(tan, max_delta_deg=max_delta_deg, prev_normal=prev_normal)
            prev_normal = normal

            # Trace symmetric cross section for a small demo target area (e.g., 20 cells)
            targets = [10 * (cell * cell), 20 * (cell * cell)]
            res = trace_cross_section_symmetric((r, c), normal, 0, nrows - 1, 0, ncols - 1, targets, cell * cell)

            # Build a polyline from left+right visited cells
            pts = []
            for rr, cc in reversed(res['cells_left']):
                pts.append(arcpy.Point(*rc_to_xy(rr, cc, llx, lly, cell)))
            for rr, cc in res['cells_right']:
                pts.append(arcpy.Point(*rc_to_xy(rr, cc, llx, lly, cell)))
            if len(pts) >= 2:
                ic.insertRow([arcpy.Polyline(arcpy.Array(pts), spatial_ref)])

            # move downstream
            fd = int(C[r, c])
            r, c = downstream_next_rc(r, c, fd)
            steps += 1


if __name__ == "__main__":
    # Example usage (edit these paths/values to your environment or call from ArcGIS tool)
    # main(
    #     workspace=r"C:\\path\\to\\workspace",
    #     dem_fill=r"C:\\path\\to\\workspace\\tktfill",
    #     flow_dir_raster=r"C:\\path\\to\\workspace\\tktdir",
    #     start_xy=(500000.0, 4600000.0),
    #     out_fc=r"C:\\path\\to\\workspace\\laharz_demonstration\\angle_sections.shp",
    #     window_len=7,
    #     max_delta_deg=25.0,
    #     max_steps=200
    # )
    pass
