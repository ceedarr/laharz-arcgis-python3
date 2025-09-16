# ---------------------------------------------------------------------------
# merge_runs.py
#
# Usage: merge_runs.py is attached to Laharz_py.tbx (toolbox)
#   sys.argv[1] a workspace
#   sys.argv[2] a DEM, input surface raster
#   sys.argv[3] text file storing names of raster runs to merge
#   sys.argv[4] text file storing the volumes
#
#   This program will merge runs of the same volume from separate rasters.
#   The output is a raster containing cells for one volume from all runs at
#   a volcano.
# ---------------------------------------------------------------------------

# Start Up - Import system modules
import sys, string, os, arcpy, time
from arcpy import env
from arcpy.sa import *

starttimetot = time.clock()  # calculate time for program run

# Check out license
arcpy.CheckOutExtension("Spatial")

#===========================================================================
#  Local Functions
#===========================================================================

def ConvertTxtToList(atxtfilename,alist):
    # =====================================
    # Parameters:
    #   atxtfilename:  name of a textfile
    #   alist:  empty python list
    #
    # Opens volume or starting coordinate textfile,
    # appends values read from textfile to the list,
    # volume list is sorted smallest to largest
    #
    # Returns:  list
    # =====================================

    afile = open(atxtfilename, 'r')
    
    for aline in afile:
        if aline.find(',') != -1: # if it does have a ','
            x = aline.rstrip('\n')
            z = x.lstrip(' ')
            y = z.split(',')
            alist = y
    afile.close   
    return alist

def main():            
    try:
        #===========================================================================
        # Assign user inputs from menu to appropriate variables
        #===========================================================================

        arcpy.AddMessage("Parsing user inputs:")

        env.workspace = sys.argv[1]     # set the ArcGIS workspace
        Input_raster = sys.argv[2]      # name of DEM
        rasterTextFile = sys.argv[3]    # textfile of runs to merge
        volumesTextFile = sys.argv[4]   # textfile of volumes used to create runs


        #=============================================
        # Set the ArcGIS environment settings
        #=============================================      
        env.scratchWorkspace = env.workspace  # set ArcGIS scratchworkspace
        PathName = env.workspace + "\\"       # directory path
        rasterList = []                       # empty list to store rasters
        volumeList = []                       # empty list to store volumes
           


        # =====================================    
        # Call ConvertTxtToList function with  
        # rasters to merge and with volumns
        # =====================================
        
        arcpy.AddMessage( "________ Convert Textfile to List ________")
        
        rasterList = ConvertTxtToList(rasterTextFile, rasterList)
        numrasters = len(rasterList)
        rasterList.sort()

        volumeList = ConvertTxtToList(volumesTextFile, volumeList)
        numvolumes = len(volumeList)
        volumeList.sort()
        volumeList.reverse()

        # =====================================    
        # Get the lower left cell coordinates
        # and cell size
        # =====================================

        xxcellsize = arcpy.GetRasterProperties_management(Input_raster,"CELLSIZEX")
        cellWidth = float(xxcellsize.getOutput(0))
        xxllx = arcpy.GetRasterProperties_management(Input_raster,"LEFT")
        lowLeftX = float(xxllx.getOutput(0))
        xxlly = arcpy.GetRasterProperties_management(Input_raster,"BOTTOM")
        lowLeftY = float(xxlly.getOutput(0))

        # =====================================
        #  Convert DEM to NumPyArray and
        #  get row, column values for boundaries
        # =====================================
        arcpy.AddMessage("_________ Convert DEM to Array _________")
        A = arcpy.RasterToNumPyArray(Input_raster)

        # =====================================
        #    Get NumPyArray Dimensions
        # =====================================    
        arcpy.AddMessage("_________ Get Array Dimensions _________")    

        arcpy.AddMessage('Shape is: ' + str(A.shape) + " (rows, colums)") 
        number_rows = A.shape[0]
        number_cols = A.shape[1]
        arcpy.AddMessage('Number of rows is: ' + str(number_rows))
        arcpy.AddMessage('Number of columns is: ' + str(number_cols))
        del A
        
        #=============================================
        # For each volume in volume list
        #=============================================                                 
        for x in range(len(volumeList)):
            z = x + 1
            w = x + 2
            s = 0
            t = 0
            A = arcpy.RasterToNumPyArray(Input_raster) # create numpyarray
            
            # =====================================
            #   Set array values to 1
            # ===================================== 
            while t < number_rows:
                for s in range(number_cols):
                    A[t,s] = 1
                t = t + 1
                
            # =====================================
            #  For each raster in the list of rasters
            # =====================================             
            for r in range(len(rasterList)):        
                B = arcpy.RasterToNumPyArray(rasterList[r]) # create numpyarray

                number_rowsi = B.shape[0]
                number_colsi = B.shape[1]
                
                i = 0
                j = 0

                while j < number_rowsi:
                    for i in range(number_colsi):
                       if B[j,i] > z:
                           A[j,i] = w
                    j = j + 1

                del B  # delete numpyarray of rasters
                arcpy.AddMessage('Completed rasterlist number : ' + str(r+1))
                
            #================================
            # if raster already exists, delete it
            #================================
            currentname = PathName + "merge_" + str(w)
            if arcpy.Exists(currentname):
                arcpy.Delete_management(currentname) 
            myRaster = arcpy.NumPyArrayToRaster(A,arcpy.Point(lowLeftX, lowLeftY),cellWidth,cellWidth)
            # convert to integer raster
            outInt = Int(myRaster)
            outInt.save(currentname)
            # build vat for raster
            arcpy.BuildRasterAttributeTable_management(currentname)

            
            del A   # delete numpyarray of merged rasters
            
            arcpy.AddMessage('Completed merge of : ' + "merge_" + str(w))

        endtimetot = time.clock()
        tottime = endtimetot - starttimetot
        
        arcpy.AddMessage("...Processing Complete...")   
        arcpy.AddMessage("TOTAL TIME:  " + str(tottime) + " seconds")
        
        
    except:
        arcpy.GetMessages(2)

if __name__ == "__main__":
    main()   


        