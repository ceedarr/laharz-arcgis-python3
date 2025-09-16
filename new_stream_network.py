# ---------------------------------------------------------------------------
# new_stream_network.py
#
# Usage: new_stream_network.py is attached to Laharz_py.tbx (toolbox)
#   sys.argv[1] a workspace
#   sys.argv[2] a DEM, input surface raster
#   sys.argv[3] threshold value to demarcate a stream; default is 1000
#   
#
#   This program creates a single stream network raster from an input raster (DEM)
#  It assumes their is an existing flow direction and flow accumulation rasters
#  It uses the new threshold to calculate a new stream network
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
        
        env.Workspace = sys.argv[1]          # set the ArcGIS workspace
        arcpy.extent = sys.argv[2]           # set extent to input DEM
        arcpy.SnapRaster = sys.argv[2]       # ensure new rasters align with input DEM
        env.scratchWorkspace = env.Workspace   # set the ArcGIS scratchworkspace

        # local variables
        curdir = env.Workspace                   # current directory
        Flow_accum_raster = sys.argv[2]      # flow accumulation raster

        Stream_Value = sys.argv[3]           # stream threshold
        if Stream_Value == '#':
            Stream_Value = "1000" # provide a default value if unspecified

        
        arcpy.AddMessage( "____________________________________")
        arcpy.AddMessage( "Calculating  New Stream network:")
        arcpy.AddMessage( "____________________________________")
        arcpy.AddMessage( "Flow Accumulation Raster: " + Flow_accum_raster)
        if Flow_accum_raster.endswith("flac"):
            atemp = Flow_accum_raster.rstrip("flac")
            atemp2 = os.path.basename(atemp)
        arcpy.AddMessage( "Prefix name is: " + atemp2)
        arcpy.AddMessage( "")
        arcpy.AddMessage( "")
        strname = curdir + "\\" + atemp2 +"str" + str(Stream_Value)

        # Applying threshold    
        arcpy.AddMessage( "Calculating new Stream paths:")
        tempb = GreaterThan(Flow_accum_raster, int(Stream_Value))
        tempb.save(strname)

        arcpy.AddMessage( "Created raster: " + strname)
        arcpy.AddMessage( "")
        
        arcpy.AddMessage( "Processing Complete.")


    except:
        print(arcpy.GetMessages(2))

if __name__ == "__main__":
    main()