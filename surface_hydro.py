# ---------------------------------------------------------------------------
# surface_hydro.py
#
# Usage: surface_hydro.py is attached to Laharz_py.tbx (toolbox)
#   sys.argv[1] a workspace
#   sys.argv[2] a DEM, input surface raster
#   sys.argv[3] a prefix string for surface hydrology datasets
#   sys.argv[4] threshold value to demarcate a stream; default is 1000
#
#   This program creates surface hydrology datasets from an input raster (DEM)
#  It fills sinks in the original DEM, then calculates flow direction, flow accumulation,
#  and delineates streams from flow accumulation according to the stream threshold
#  
# ---------------------------------------------------------------------------

# Start Up - Import system modules
import sys, string, os, arcpy
from arcpy import env
from arcpy.sa import *

# Check out license
arcpy.CheckOutExtension("Spatial")


def main():
    try:
        #===========================================================================
        # Assign user inputs from menu to appropriate variables
        #===========================================================================
        arcpy.AddMessage("Parsing user inputs:")
          
        env.workspace = sys.argv[1]         # set the ArcGIS workspace
        env.extent = sys.argv[2]            # set extent to input DEM
        env.snapRaster = sys.argv[2]        # ensure new rasters align with input DEM
        env.cellSize = sys.argv[2]          # set cell size of new rasters same as input DEM
        env.scratchWorkspace = env.workspace # set the ArcGIS scratchworkspace

        Input_surface_raster = sys.argv[2]  # name of DEM
        PreName = sys.argv[3]               # prefix for surface raster data sets
        Stream_Value = sys.argv[4]          # threshold of flow accumulation to demarcate streams

        # local variables
        curdir = env.workspace              # current directory
        textdir = curdir + "\\laharz_textfiles\\"
        shapedir = curdir + "\\laharz_shapefiles\\"

        if Stream_Value == '#':
            Stream_Value = "1000" # provide a default value if unspecified

        #=============================================
        # Set filenames and directories
        #=============================================       
        fillname = curdir + "\\" + PreName + "fill"
        dirname = curdir + "\\" + PreName + "dir"
        flacname = curdir + "\\" + PreName + "flac"
        strname = curdir + "\\" + PreName + "str" + str(Stream_Value)

        #===========================================================================
        arcpy.AddMessage( "____________________________________")
        arcpy.AddMessage( "Calculating  Supplementary grids:")
        arcpy.AddMessage( "____________________________________")
        arcpy.AddMessage( "")
        arcpy.AddMessage( "Filling sinks in DEM:  " + Input_surface_raster)

        # Fill
        arcpy.AddMessage( 'searching for sinks >>')
        tempa = Fill(Input_surface_raster)
        tempa.save(fillname)
        arcpy.AddMessage( 'Created filled DEM: ' + fillname)
        
        # Flow Direction
        arcpy.AddMessage( "Calculating Flow Direction >>")    
        tempa2 = FlowDirection(fillname)
        tempa2.save(dirname)
        arcpy.AddMessage( 'Created Raster: ' + dirname)

        # Flow Accumulation    
        arcpy.AddMessage( "Calculating Flow Accumulation >>")
        tempa3 = FlowAccumulation(dirname, "", "INTEGER")
        tempa3.save(flacname)
        arcpy.AddMessage( 'Created Raster: ' + flacname)

        # Applying stream threshold    
        arcpy.AddMessage( "Calculating Streams >> ")
        tempa4 = GreaterThan(flacname, int(Stream_Value))
        tempa4.save(strname)
        arcpy.AddMessage( "Created Raster: " + strname)
        
        arcpy.AddMessage( "Processing Complete.")

        arcpy.AddMessage( "")
    except:
        print arcpy.GetMessages(2)

if __name__ == "__main__":
    main()