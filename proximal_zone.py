# ---------------------------------------------------------------------------
# proximal_zone.py
# 
# Usage: hlcone_startpts.py is attached to Laharz_py.tbx (toolbox)
#   sys.argv[1] a workspace
#   sys.argv[2] a DEM, input surface raster
#   sys.argv[3] an input stream raster
#   sys.argv[4] a decimal slope value for the H/L cone; default is 0.3
#   sys.argv[5] an apex choice for the cone (max elev, XY point, or textfile coords
#   sys.argv[6] coordinates for apex of cone from text file
#   sys.argv[7] coordinates for apex of cone from typed coordinates
#   
#

#   This program calculates a raster dataset that represents an H/L cone from 
#  the input raster (DEM), user defined slope, and user identified location of the cone apex 
#  The resulting line where the cone intersects the DEM defines the boundary
#  Point coordinates where the boundary intersects streams are stored in a text file
#  In general, cells between the line and the apex are above the cone surface whereas
#  Outboard of the line, the cone surface is below the DEM.
# ---------------------------------------------------------------------------

# Start Up - Import system modules
import sys, string, os, arcpy
from arcpy import env
from arcpy.sa import *

# Check out license
arcpy.CheckOutExtension("Spatial")

#===========================================================================
#  Local Functions
#===========================================================================

##def getdat(atxtfilename,alist):
##    # =====================================
##    # Parameters:
##    #   atxtfilename:  name of a textfile
##    #   alist:  empty python list
##    #
##    # This function takes a textfile with X,Y coordinates
##    # and an empty list
##    # It returns a list with X and Y coordinates as elements in the list
##    #
##    # Returns:  alist
##    # =====================================
##    afile = open(atxtfilename, 'r')
##    for aline in afile:
##        if aline.find(',') <> -1: # if it does have a ','
##            a = aline.rstrip('\n')
##            b = a.split(',')
##            for i in range(len(b)):
##                y = round(float(b[i].lstrip(' ')))
##                alist.append(y)
##    afile.close
##    arcpy.AddMessage( "Coordinates from textfile:  " + str(alist))
##    return alist

def ConvertTxtToList(atxtfilename,alist,dattype):
    # =====================================
    # Parameters:
    #   atxtfilename:  name of a textfile
    #   alist:  empty python list
    #   dattype:  keyword 'volumes' or 'points' to determine how text file
    #             is manipulated
    #
    # Opens volume or starting coordinate textfile,
    # appends values read from textfile to the list,
    # volume list is sorted smallest to largest
    #
    # Returns:  list
    # =====================================

    afile = open(atxtfilename, 'r')

    for aline in afile:

        if dattype == 'volumes':
            x = aline.rstrip('\n')
            y = round(float(x.lstrip(' ')))
            alist.append(y)

        else:
            if aline.find(',') <> -1: # if it does have a ','
                x = aline.rstrip('\n')
                y = x.split(',')
                for i in range(len(y)):
                    y[i] = round(float(y[i].lstrip(' ')))
                if dattype == 'volumes':

                    y.sort()
                    alist = y
                else:
                    alist.append(y)
    afile.close()

    return alist

def makepointlist(cellx,celly,oneptlist):
    # =====================================
    # Parameters:
    #   cellx:  X coordinate of the current cell
    #   celly:  Y coordinate of the current cell
    #   oneptlist: a list to store coordinates
    #
    # Appends the X and Y of current cell to a list
    # 
    # =====================================
 
    onePoint = arcpy.Point(cellx, celly)
    oneptlist.append(onePoint)

    return oneptlist
     
def main():        
    try:

        #===========================================================================
        # Assign user inputs from menu to appropriate variables
        #===========================================================================
        arcpy.AddMessage("Parsing user inputs:")
        env.workspace = sys.argv[1]        # set the ArcGIS workspace 
        Input_surface_raster = sys.argv[2] # name of DEM
        Input_stream_raster = sys.argv[3]  # name of stream raster
        slope_value = sys.argv[4]          # decimal slope entered by user
        apex_choice = sys.argv[5]          # max elev, XY point, or textfile coords
        coordstxt = sys.argv[6]            # name of textfile with apex coordinates
        coordspnt = sys.argv[7]            # coordinates entered at keyboard
        
        #=============================================
        # Set the ArcGIS environment settings
        #=============================================
        
        env.scratchWorkspace = env.workspace
        env.extent = Input_surface_raster
        env.snapRaster = Input_surface_raster
        curdir = env.workspace
        textdir = curdir + "\\laharz_textfiles\\"
        shapedir = curdir + "\\laharz_shapefiles\\"

        #=============================================
        # report dem selected back to user
        #=============================================        
        arcpy.AddMessage( "_________ Input Values _________")    
        arcpy.AddMessage( 'Surface Raster Is: ' + Input_surface_raster)
        arcpy.AddMessage( 'Stream Raster Is: ' + Input_stream_raster)

        #=============================================
        # Set filenames and directories
        #=============================================   
        BName = os.path.basename(Input_surface_raster)
        DName = env.workspace + "\\"

        # if the filename suffix is "fill", get prefix name
        if BName.endswith("fill"):
            PreName = BName.rstrip("fill")

        # assign complete names for supplementary files,
        # path and basename(prefix and suffix)
        fillname = DName+PreName+"fill"
        dirname = DName+PreName+"dir"
        flacname = DName+PreName+"flac"
        strname = DName+PreName+"str"

        pfillname = PreName+"fill"
        pdirname = PreName+"dir"
        pflacname = PreName+"flac"
        pstrname = PreName+"str"

        arcpy.AddMessage("full path fill  :" + fillname)
        arcpy.AddMessage("full path dir   :" + dirname)
        arcpy.AddMessage("full path flac  :" + flacname)
        arcpy.AddMessage("full path str   :" + strname)

        arcpy.AddMessage("partial path fill  :" + pfillname)
        arcpy.AddMessage("partial path dir   :" + pdirname)
        arcpy.AddMessage("partial path flac  :" + pflacname)
        arcpy.AddMessage("partial path str   :" + pstrname)
        
        # assign the flow direction and flow accumulation grids to variables
        Input_direction_raster = dirname
        Input_flowaccumulation_raster = flacname


        # use slope value as part of grid and shapefile name

        y = slope_value.split('.')
        slopename = str(y[1])

        hlconename = "hlcone"+slopename+"_g"
        hlshapename = shapedir + "startpts_"+slopename+".shp"
        hlgridname = "stpts_g"+slopename


        # =====================================
        # set file name for two textfiles storing X,Y coordinates  
        # one storing an arbitrary single starting point
        # the other file storing all stream/hl cone intersections as starting points
        # =====================================
        txfileuno = textdir + "firstpnt_"+slopename+".txt"
        txfile = textdir + "startpnts_"+slopename+".txt"
        

        arcpy.AddMessage( "")
        arcpy.AddMessage( "_______________________________")
        arcpy.AddMessage( "Calculating H/L Cone: ")
        arcpy.AddMessage( "_______________________________")
        arcpy.AddMessage( "")
        arcpy.AddMessage( "Apex Choice is :" + apex_choice)
        arcpy.AddMessage( "")

        # variables for above and below the cone
        cone_gt_elev = "0"
        cone_lt_elev = "1"

        # =====================================    
        # Apex_choice is either Maximum elevation,
        # textfile elevation, or manually entered coordinate
        # as apex of an H/L cone
        # =====================================
        # if maximum elevation, find it and store elevation, make const_g and cond_g 
        if apex_choice == "Maximum_Elevation": 
            
            arcpy.AddMessage("Searching for Maximum Elevation:")
            arcpy.AddMessage( "        ")
            currhipnt = arcpy.GetRasterProperties_management(Input_surface_raster, "MAXIMUM")
            arcpy.AddMessage("Maximum Elevation Found:  " + str(currhipnt))
            arcpy.AddMessage( "        ")
     
            arcpy.AddMessage("Creating grid with constant values of MAXIMUM Elevation:")
            arcpy.AddMessage( "        ")
            const_g = CreateConstantRaster(currhipnt, "FLOAT", Input_surface_raster, Input_surface_raster)
      
            arcpy.AddMessage( "Creating grid with single data value at highest elevation:")
            arcpy.AddMessage( "        ")
            cond_g = Con(Raster(Input_surface_raster) == const_g,const_g)
            
# After maxelev have const_g and cond_g

        if apex_choice == "XY_coordinate":
            coords = str(coordspnt)           
            currhipnt = arcpy.GetCellValue_management(Input_surface_raster,coords,"")
            a = coords.split(' ')
            x = a[0]
            y = a[1]

            arcpy.AddMessage("Entered coordinates are: " + coords)
            arcpy.AddMessage("Elevation at that coordinate is:  " + str(currhipnt))
            

            # make a point list
            onePointList = []
            onePointList = makepointlist(float(x),float(y),onePointList)
            #arcpy.AddMessage("made onepointlist:  " )
            arcpy.AddMessage("Creating grid with value of elevation at coordinate:  ")
            arcpy.AddMessage( "        ")
            const_g = CreateConstantRaster(currhipnt, "FLOAT", Input_surface_raster, Input_surface_raster)

            # Process: Extract By Points - cond_g
            cond_g = ExtractByPoints(Input_surface_raster,onePointList,"INSIDE")

# After x,y coord have const_g and cond_g
            
        if apex_choice == "Maximum_Elevation" or apex_choice == "XY_coordinate":
            # =====================================
            # Create the cone
            # =====================================
            # Calculate Euclidean Distance
            arcpy.AddMessage( "Calculating Euclidean Distance of each cell from SELECTED Location:")
            arcpy.AddMessage( "        ")
            eucdist_g = EucDistance(cond_g)

            # Multipy slope value by euclidean distance
            arcpy.AddMessage( "slope is: " + slope_value)
            arcpy.AddMessage( "Multiplying slope value times euclidean distance")
            arcpy.AddMessage( "        ")
            slopeeuc_g = Times(eucdist_g, float(slope_value))

            # Subtractions
            arcpy.AddMessage( "Processing values:")
            arcpy.AddMessage( "        ")
            hl_cone_g1 = Minus(const_g, slopeeuc_g)
            c_minus_dem = Minus(hl_cone_g1,Input_surface_raster)

            # LessThan and SetNull 
            
            hl_cone_g2 = Con(c_minus_dem > 0, 1)
            #hl_cone_g2.save(curdir + "\\" + "hl_cone_g2")
            hl_cone_g2.save(curdir + "\\" + "xhltemp")
            
# after xy_coordinate have onePointList
            
        if apex_choice == "Textfile":
            interlist = []
            gridlist = []
            hipnts = []
            onePointList = []
            xstartpoint = []
            xstartpoints = []                                # array to hold point
            dattype = "apex"
            xstartpoints = ConvertTxtToList(coordstxt,xstartpoints,dattype)

            arcpy.AddMessage("xstartpoints array is :  " + str(xstartpoints))
            arcpy.AddMessage( "        ")
            numxstartpnts = len(xstartpoints)
            arcpy.AddMessage("number of points in array is :  " + str(numxstartpnts))
            arcpy.AddMessage( "        ")
            
            for i in range(len(xstartpoints)):
                xstartpoint = xstartpoints[i]
                
                
                currx = float(xstartpoint[0])                        # float X coord
                curry = float(xstartpoint[1])                        # float Y coord
                coords = str(currx)+" "+str(curry)
                #arcpy.AddMessage("xstartpoint array is :  " + str(xstartpoint))
                #arcpy.AddMessage("coordinates are :  " + coords)
                
                # make a point list
                
                onePointList = makepointlist(currx,curry,onePointList)
                #arcpy.AddMessage("onePointList array is :  " + str(onePointList))
                
                # Get Cell Value at X,Y
                Result = arcpy.GetCellValue_management(Input_surface_raster,coords)
                currhipnt = Result.getOutput(0)
                hipnts.append(currhipnt)
                #arcpy.AddMessage("Elevation at point [" + str(i) + "] coordinates is:  " + str(currhipnt))
                #arcpy.AddMessage("Elevations are :  " + str(hipnts))


            
        # =====================================
        # if textfile or manually entered coordinate, make const_g and cond_g
        # =====================================
        if apex_choice == "Textfile":
            for i in range(len(onePointList)):
                arcpy.AddMessage("Creating grid with value of elevation at coordinate:  ")
                arcpy.AddMessage( "        ")
                const_g = CreateConstantRaster(hipnts[i], "FLOAT", Input_surface_raster, Input_surface_raster)

                # Process: Extract By Points - cond_g
                cond_g = ExtractByPoints(Input_surface_raster,onePointList[i],"INSIDE")

                # =====================================
                # Create the cone
                # =====================================
                # Calculate Euclidean Distance
                arcpy.AddMessage( "Calculating Euclidean Distance of each cell from SELECTED Location:")
                arcpy.AddMessage( "        ")
                eucdist_g = EucDistance(cond_g)

                # Multipy slope value by euclidean distance
                arcpy.AddMessage( "slope is: " + slope_value)
                arcpy.AddMessage( "Multiplying slope value times euclidean distance")
                arcpy.AddMessage( "        ")
                slopeeuc_g = Times(eucdist_g, float(slope_value))

                # Subtractions
                arcpy.AddMessage( "Processing values:")
                arcpy.AddMessage( "        ")
                hl_cone_g1 = Minus(const_g, slopeeuc_g)

                c_minus_dem = Minus(hl_cone_g1,Input_surface_raster)

                # LessThan and SetNull 
                
                hl_cone_g2 = Con(c_minus_dem > 0, 1,0)
                hl_cone_g2.save(curdir + "\\" + "hl_cone_g2" + str(i))
                
                
                gridlist.append("hl_cone_g2" + str(i))
                #arcpy.AddMessage( "Gridlist is:" + str(gridlist))
            interlist.extend(gridlist)

            
            if len(gridlist) > 1:
                arcpy.AddMessage( "        ")
                #arcpy.AddMessage( "Multi gridlist is:" + str(gridlist))
                #arcpy.AddMessage( "        ")
                
                arcpy.CopyRaster_management(gridlist[0],"grid1")
                
                del gridlist[0]
                #arcpy.AddMessage( "Shortened Multi gridlist is:" + str(gridlist))
                #arcpy.AddMessage( "        ")
                
                for i in range(len(gridlist)):
                    temp = Con(Raster("grid1") > 0, Raster("grid1"),Raster(gridlist[i]))
                    temp.save(curdir + "\\" + "temp")
                    if arcpy.Exists(curdir + "\\" + "grid1"):
                        arcpy.Delete_management(curdir + "\\" + "grid1")
                    arcpy.CopyRaster_management("temp","grid1")
                    if arcpy.Exists(curdir + "\\" + "temp"):
                        arcpy.Delete_management(curdir + "\\" + "temp")
                if arcpy.Exists(curdir + "\\" + "grid1"):
                    arcpy.CopyRaster_management("grid1","xhltempx")
                    arcpy.Delete_management(curdir + "\\" + "grid1")
                for i in range(len(interlist)):
                    if arcpy.Exists(curdir + "\\" + interlist[i]):
                        arcpy.AddMessage( "Deleting:" + interlist[i])
                        arcpy.Delete_management(curdir + "\\" + interlist[i])
            else:
                if arcpy.Exists(curdir + "\\" + "hl_cone_g20"):
                    arcpy.CopyRaster_management("hl_cone_g20","xhltempx")
                    arcpy.Delete_management(curdir + "\\" + "hl_cone_g20")
            if arcpy.Exists(curdir + "\\" + "xhltempx"):
                temp = Con(Raster("xhltempx") > 0, Raster("xhltempx"))
                temp.save(curdir + "\\" + "xhltemp")
                arcpy.Delete_management(curdir + "\\" + "xhltempx")
                    
# after textfile, have an xhltemp of all merged


        # =====================================   
        # convert the gridline of intersection of the cone and DEM to a polygon
        # =====================================
        # Raster to Polygon
        arcpy.AddMessage( "Converting cone/elevation intersection Raster to Polygon:")
        arcpy.AddMessage( "        ")
        arcpy.RasterToPolygon_conversion(curdir + "\\" + "xhltemp", curdir + "\\" + "hl_cone_1.shp", "SIMPLIFY", "VALUE")
        arcpy.RasterToPolygon_conversion(curdir + "\\" + "xhltemp", curdir + "\\laharz_shapefiles\\" + "hl_cone" + slopename + ".shp", "SIMPLIFY", "VALUE")
        
        # convert the polygon to a polyline
        # Polygon Feature To Line
        arcpy.AddMessage( "Converting Cone Polygon to Line:")
        arcpy.AddMessage( "        ")
        arcpy.FeatureToLine_management(curdir + "\\" + "hl_cone_1.shp", curdir + "\\" + "hl_cone_2.shp", "", "ATTRIBUTES")

        # =====================================
        # convert the polyline back to a raster
        # =====================================
        # Polyline to Raster
        arcpy.AddMessage( "Converting Cone line back to a Cone outline Raster:")
        arcpy.AddMessage( "        ")
        arcpy.PolylineToRaster_conversion(curdir + "\\" + "hl_cone_2.shp", "GRIDCODE", hlconename, "MAXIMUM_LENGTH", "NONE", Input_surface_raster)
        
        arcpy.AddMessage( "")
        arcpy.AddMessage( "_______________________________")
        arcpy.AddMessage( "Finding Intersection locations of streams")
        arcpy.AddMessage( "and H/L Cone and store coordinates as start points:")
        arcpy.AddMessage( "_______________________________")
        arcpy.AddMessage( "")

        # intersect_g
        arcpy.AddMessage( "Finding intersections of streams and hlcone:")
        arcpy.AddMessage( "        ")
        intersect_g = Plus(hlconename, Input_stream_raster)
        
        # Extract by Attributes
        arcpy.AddMessage( "Extracting intersections from raster:")
        arcpy.AddMessage( "        ")
        temp11c = ExtractByAttributes(intersect_g, "VALUE = 2")
        temp11c.save(curdir + "\\" + hlgridname)

        # Raster to Point
        arcpy.AddMessage( "Converting intersection locations to point shape file:")
        arcpy.AddMessage( "        ")
        arcpy.RasterToPoint_conversion(hlgridname, hlshapename, "VALUE")
        
        # Add X and Y coordinates to shape file
        arcpy.AddMessage( "adding X and Y coordinates to attribute table:")
        arcpy.AddMessage( "        ")
        arcpy.AddXY_management(hlshapename)
        
        arcpy.AddMessage( "")
        arcpy.AddMessage( "_______________________________")
        arcpy.AddMessage( "Writing X and Y locations of  ")
        arcpy.AddMessage( "intersections to a textfile:")
        arcpy.AddMessage( "_______________________________")
        arcpy.AddMessage( "")
        
        # =====================================
        # open files for write, write heading to file of list of coordinates
        # =====================================
        runo = open(txfileuno, 'w')    
        report = open(txfile, 'w')
        #report.write('Northing,Easting')
        #report.write('\n')
        
        # set up search cursor
        rows = arcpy.SearchCursor(hlshapename,"","","POINT_X; POINT_Y","")

        # Get the first feature in the searchcursor
        row = rows.next()

        # local variables
        currentloc = ""
        count = 1

        # Iterate through the rows in the cursor
        while row:
            if currentloc != row.POINT_X:
                currentloc = row.POINT_X
            # write first X, Y to file
            if count == 1:
                runo.write(" %d,%d" % (row.POINT_X, row.POINT_Y))
            report.write(" %d,%d" % (row.POINT_X, row.POINT_Y))
            report.write("\n") 
            row = rows.next()
            count += 1

        # close files
        report.close()
        runo.close()

        # report writing to files complete
        arcpy.AddMessage( "")   
        arcpy.AddMessage( "File write complete...")
        
        # =====================================
        # Cleaning up intermediate grids and shape files
        # =====================================
        
        arcpy.AddMessage( "_______________________________")
        arcpy.AddMessage( "Cleaning up intermediate files...")
        arcpy.AddMessage( "_______________________________")    
        if arcpy.Exists(curdir + "\\" + "const_g"):
            arcpy.Delete_management(curdir + "\\" + "const_g")
        if arcpy.Exists(curdir + "\\" + "above_g"):
            arcpy.Delete_management(curdir + "\\" + "above_g")
        if arcpy.Exists(curdir + "\\" + "c_minus_dem"):
            arcpy.Delete_management(curdir + "\\" + "c_minus_dem")
        if arcpy.Exists(curdir + "\\" + "notequ_g"):
            arcpy.Delete_management(curdir + "\\" + "notequ_g")
        if arcpy.Exists(curdir + "\\" + "cond_g"):
            arcpy.Delete_management(curdir + "\\" + "cond_g")
        if arcpy.Exists(curdir + "\\" + "Eucdist_g"):
            arcpy.Delete_management(curdir + "\\" + "Eucdist_g")
        if arcpy.Exists(curdir + "\\" + "Slopeeuc_g"):
            arcpy.Delete_management(curdir + "\\" + "Slopeeuc_g")
        if arcpy.Exists(curdir + "\\" + "hl_cone_g1"):
            arcpy.Delete_management(curdir + "\\" + "hl_cone_g1")
        if arcpy.Exists(curdir + "\\" + "hl_cone_g2"):
            arcpy.Delete_management(curdir + "\\" + "hl_cone_g2")
        if arcpy.Exists(curdir + "\\" + hlgridname):
            arcpy.Delete_management(curdir + "\\" + hlgridname)
        if arcpy.Exists(curdir + "\\" + "hl_cone.shp"):
            arcpy.Delete_management(curdir + "\\" + "hl_cone.shp")
        if arcpy.Exists(curdir + "\\" + "hl_cone_1.shp"):
            arcpy.Delete_management(curdir + "\\" + "hl_cone_1.shp")
        if arcpy.Exists(curdir + "\\" + "hl_cone_2.shp"):
            arcpy.Delete_management(curdir + "\\" + "hl_cone_2.shp")
        if arcpy.Exists(curdir + "\\" + "intersect_g"):
            arcpy.Delete_management(curdir + "\\" + "intersect_g")
        if arcpy.Exists(curdir + "\\" + "xhltemp"):
            arcpy.Delete_management(curdir + "\\" + "xhltemp")

        arcpy.AddMessage( "Processing Complete.")
        arcpy.AddMessage( "")

        
    except:
        arcpy.GetMessages(2)

if __name__ == "__main__":
    main()
   