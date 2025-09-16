# ---------------------------------------------------------------------------
# raster_to_shapefile.py
# 
# Usage: raster_to_shapefile.py is attached to Laharz_py.tbx (toolbox)
#   sys.argv[1] a workspace
#   sys.argv[2] name of new shapefile
#   sys.argv[3] name of existing raster data set
#
#   This program converts a raster data set of volumes into a polygon
# shapefile.  The shapefile retains the coding from the raster, storing
# the information in an associated attribute table
# ---------------------------------------------------------------------------

# Start Up - Import system modules
import sys, string, os, arcpy, time
from arcpy import env
from arcpy.sa import *
#from math import *

starttimetot = time.clock()  # calculate time for program run

# Check out license
arcpy.CheckOutExtension("Spatial")

def main():            
    try:
        #===========================================================================
        # Assign user inputs from menu to appropriate variables
        #===========================================================================

        arcpy.AddMessage("Parsing user inputs:")

        env.workspace = sys.argv[1]      # set the ArcGIS workspace
        shapename = sys.argv[2]          # a name of new shapefile
        Raster_to_convert = sys.argv[3]  # name of raster to convert

        #=============================================
        # Set the ArcGIS environment settings
        #=============================================     
        env.scratchWorkspace = env.workspace  # scratchworkspace
        curpath = env.workspace               # directory path
    ##    env.extent = Raster_to_convert        # set the extent
    ##    env.cellSize = Raster_to_convert      # set the cell size
    ##    env.snapRaster = Raster_to_convert    # set the raster to aligh
        PathName = env.workspace + "\\"       # set the path to files on disk

        #==========================
        # Set local variables
        #==========================
        inRaster = Raster_to_convert
        outPolygons = PathName + "laharz_shapefiles\\" + shapename + ".shp"
        field = "VALUE"

        #==========================
        # apply the conversion
        #==========================  
        arcpy.RasterToPolygon_conversion(inRaster, outPolygons, "NO_SIMPLIFY", field)    
        endtimetot = time.clock()
        tottime = endtimetot - starttimetot
        
        arcpy.AddMessage("...Processing Complete...")   
        arcpy.AddMessage("TOTAL TIME:  " + str(tottime) + " seconds")
        
    except:
        arcpy.GetMessages(2)

if __name__ == "__main__":
    main()   

        