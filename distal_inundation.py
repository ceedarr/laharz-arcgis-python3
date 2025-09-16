# ---------------------------------------------------------------------------
# distal_inundation.py
#
# Usage: laharz_py_main.py is attached to Laharz_py.tbx (toolbox)
#   sys.argv[1] a workspace
#   sys.argv[2] a DEM, input surface raster
#   sys.argv[3] name of the output .pts file (drainName)
#   sys.argv[4] text file storing the volumes
#   sys.argv[5] text file storing coordinates to start runs
#   sys.argv[6] flowType (lahar, debris_flow, rock_avalanche)
#
#
#   This program creates an estimate of area of potential inundation by a hypothetical
#  lahar, debris flow, or rock avalanche.  Each planimetric areas stems from a single input
#  volume.  The width and length of the planimetric area is governed by the
#  cross sections calculated, centered at a stream cell.  The calculations are controlled
#  by elevation values of cells from an input surface raster (DEM)
#
# ---------------------------------------------------------------------------

# Start Up - Import system modules
import sys, string, os, arcpy, math, time
from arcpy import env
from arcpy.sa import *
from math import *



# Check out license
arcpy.CheckOutExtension("Spatial")

#===========================================================================
#  Local Functions
#===========================================================================

def ConvertTxtToList(atxtfilename,alist,dattype,conflim):
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

        if conflim and dattype == 'volumes':
            x = aline.rstrip('\n')
            y = round(float(x.lstrip(' ')))
            alist.append(y)

        else:
            if aline.find(',') != -1: # if it does have a ','
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

def CalcTime(tottime):
    # =====================================
    # Parameters:
    #   tottime:  result of subtracting a start time from an
    #             end time
    #
    # Calculates the hours, minutes, seconds from a total
    # number of seconds.
    #
    # Returns:  string of hours, minutes, seconds
    # =====================================

    timehr = 0
    timemin = round(tottime /60)
    timesec = tottime - (timemin * 60)
    if timemin > 60:
        timehr = round(timemin/60)
    if timehr > 0:
        timemin = timemin - (timehr * 60)
    if timehr > 0:
        return str(timehr) + " hrs, " + str(timemin) + " mins, " + str(timesec) + " secs."
    else:
        return str(timemin) + " mins, " + str(timesec) + " secs."

def CalcArea(invollist,coeff,areaoutlist):
    # =====================================
    # Parameters:
    #   invollist: list of volumes
    #   coeff:  coefficient based on lahar, debris flow, or rock avalanche
    #   areaoutlist:  list of calculated planimetric or cross section areas
    #
    # Calculate cross section and planimetric areas
    #
    # Returns:  list of calculated areas
    # =====================================

    for i in range(len(invollist)):
        areaoutlist.append(round((invollist[i] ** 0.666666666666666) * coeff))
    return areaoutlist

def CalcCellDimensions(dem):
    # =====================================
    # Parameters:
    #   dem: name of digital elevation model
    #
    # Extract the length of a cell in a DEM and
    # calculate the length of a cell diagonal
    #
    # Returns:  value of cell width, value of cell diagonal
    # =====================================

    xxwide = arcpy.GetRasterProperties_management(dem,"CELLSIZEX")
    cwidth = float(xxwide.getOutput(0))
    tempdiag = math.sqrt((pow(cwidth,2) * 2))
    cdiag = round(tempdiag * 100) / 100

    return cwidth,cdiag

def StdErrModMean(ABpick,path,UserVol,confLim):
    # =====================================
    # Parameters:
    #   ABpick:  'A' cross section or 'B' planimetric areas
    #   path:    a path to workspace
    #   UserVol: user chosen volume
    #   confLim: level of confidence
    #
    #   calculates the confidence limits (upper and lower) depending on
    #   the user selected level of confidence.  Calculates the volumes
    #   that correlate with those levels of confidence according to
    #   method outlined in accompanying text Appendix.
    #
    # Returns:  two volumes, calculated from upper and lower confidence limits
    # =====================================

    #==================================
    # Set intercepts according to A cross section or B planimetric area.
    # Set the appropriate textfile for statistics
    #==================================
    if ABpick == 'A':
        anintercept = -1.301      # B + 2.301 # A - 1.301
        decintercept = 0.05       # B 200     #A 0.05
        txtfil = path + "laharz_textfiles\\" + "py_xxsecta.txt"
        arcpy.AddMessage("A - textfile:   " + str(txtfil))

    if ABpick == 'B':
        anintercept = 2.301      # B + 2.301 # A - 1.301
        decintercept = 200       # B 200     # A 0.05
        txtfil = path + "laharz_textfiles\\" + "py_xxplanb.txt"
        arcpy.AddMessage("B - textfile:   " + str(txtfil))

    afile = open(txtfil, 'r')

    #==================================
    # Initialize totlogv for use in
    # standard error of mean
    #==================================
    rss = 0
    totlogv = 0
    count_n = 0  # number of data lines in file

    for aline in afile:

        if aline.find(',') != -1: # if it does have a ','
            x = aline.rstrip('\n')
            y = x.split(',')


        #==================================
        #   Loop to read file
        #   extract entries to calculate Mean of Log (V)
        #==================================
        aloc = y[0]
        avol = y[1]
        anarea = y[2]

        # convert the current volume read in file to a
        # log base 10 Volume (e.g. 10000000 => 7)
        logavol = log10(float(avol))

        # Add the log base 10 Volume to the sum totlogv
        # for standard error of the mean calculation
        #  (i.e. Average Log V)used later
        totlogv = totlogv + logavol

        # Convert the current cross sectional area
        # (observation yi) to log base 10 Area
        logayi = log10(float(anarea))

        # Calculate the predicted cross sectional area as
        # shown in appendix and calculated for LaharZ
        logaypred = (logavol * 0.666666666667) + anintercept

        # Calculate the difference between measured (yi)
        # and predicted (ypred)
        # cross sectional areas then square the results
        sqdifyiypred = (logayi - logaypred) * (logayi - logaypred)

        # residual sum of squares => Sum e^2
        rss = rss + sqdifyiypred

        # update count_n => number of lines, i.e. number of observations
        count_n = count_n + 1

    # Close file.
    afile.close()

    #==================================
    # Calculate Residual Mean Square and then
    # Calculate Standard Error of the Model
    #==================================

    #  variable count_n is the number of lines in the file, calculate n - 1
    nminusone = count_n - 1
    rms = rss / nminusone
    semodel = sqrt(rms)

    #==================================
    # Calculate Mean (Average) of Log (V)
    #==================================

    # calculate X bar used in Standard error of the mean
    # use the total of the log10 volumes and count of observations
    meanlogv = totlogv / count_n

    #==================================
    # open file for reading second time
    #==================================
    afile = open(txtfil, 'r')

    #==================================
    # variable meandiftotal is sum of
    # difference between each Log (V) and Mean Log (V)
    #==================================

    meandiftotal = 0.0
    oneovern = 1.0 / count_n
    nminusone = count_n - 1

    for aline in afile:
        if aline.find(',') != -1: # if it does have a ','
            x = aline.rstrip('\n')
            y = x.split(',')

        #==================================
        # Calculate denominator of sum of square of
        # differences in standard error of the mean
        #==================================
        aloc = y[0]
        avol = y[1]
        anarea = y[2]

        # convert volume read in file to log base 10 Volume
        logavol = log10(float(avol))

        # difference between each converted Log (V) and
        # the Mean Log (V) calculated from first time
        # through the loop
        diflogvmean = logavol - meanlogv

        # Square the difference
        difsquared = diflogvmean * diflogvmean

        # add the current square of the difference between
        # observation and the mean of all observations to the
        # total to calculate the sum square of differences
        meandiftotal = meandiftotal + difsquared

    # Close file.
    afile.close

    #==================================
    # Get t-table file from user and open the file.
    #==================================
    txtfil = path + "laharz_textfiles\\" + "py_xxttabl.txt"

    #==================================
    # open t-table text file
    #==================================
    afile = open(txtfil, 'r')
    count = 0

    for aline in afile:
        if aline.find(',') != -1: # if it does have a ','
            x = aline.rstrip('\n')
            y = x.split(',')
        linenum = y[0]
        cf50 = float(y[1])
        cf70 = float(y[2])
        cf80 = float(y[3])
        cf90 = float(y[4])
        cf95 = float(y[5])
        cf975 = float(y[6])
        cf99 = float(y[7])

        count = count + 1

        if count == nminusone:
            break

    # Close file.
    afile.close

    #==================================
    # Standard error of the mean
    # SEm = s * SQRT( 1/n + (X* - Xmean)^2/sum(Xn - Xmean)^2)
    # Value of s and sum(Xn - Xmean)^2 are completed
    # Need to calculate X* - Xmean, difference between user
    # selected X* and mean of X
    #==================================

    LogUserV = log10(float(UserVol))

    UserApow = float(UserVol) ** 0.66666666666667

    UserregressA = round(UserApow * decintercept)

    # calculate difference of log UserV and log (V) mean
    difmean = LogUserV - meanlogv

    # square the result
    difmeansq = difmean * difmean

    #==================================
    # Calculate the Standard Error of the Mean,
    # SEm - Need to calculate for each user V
    #==================================
    sem = (semodel * sqrt(oneovern  + (difmeansq / meandiftotal)))

    sep = sqrt((semodel * semodel) + (sem * sem))

    #==================================
    # Calculate
    # positive and negative confidence limits
    #==================================
    ypm50 = (cf50 * sep)
    ypm70 = (cf70 * sep)
    ypm80 = (cf80 * sep)
    ypm90 = (cf90 * sep)
    ypm95 = (cf95 * sep)
    ypm975 = (cf975 * sep)
    ypm99 = (cf99 * sep)

    # positive values
    pcfl50 = (ypm50 + log10(UserregressA))
    pcfl70 = (ypm70 + log10(UserregressA))
    pcfl80 = (ypm80 + log10(UserregressA))
    pcfl90 = (ypm90 + log10(UserregressA))
    pcfl95 = (ypm95 + log10(UserregressA))
    pcfl975 = (ypm975 + log10(UserregressA))
    pcfl99 = (ypm99 + log10(UserregressA))

    # negative values
    ncfl50 = (log10(UserregressA) - ypm50)
    ncfl70 = (log10(UserregressA) - ypm70)
    ncfl80 = (log10(UserregressA) - ypm80)
    ncfl90 = (log10(UserregressA) - ypm90)
    ncfl95 = (log10(UserregressA) - ypm95)
    ncfl975 = (log10(UserregressA) - ypm975)
    ncfl99 = (log10(UserregressA) - ypm99)


    # list the positives in base 10
    pos50a = 10 ** pcfl50
    pos70a = 10 ** pcfl70
    pos80a = 10 ** pcfl80
    pos90a = 10 ** pcfl90
    pos95a = 10 ** pcfl95
    pos975a = 10 ** pcfl975
    pos99a = 10 ** pcfl99

    # list the negatives in base 10
    neg50a = 10 ** ncfl50
    neg70a = 10 ** ncfl70
    neg80a = 10 ** ncfl80
    neg90a = 10 ** ncfl90
    neg95a = 10 ** ncfl95
    neg975a = 10 ** ncfl975
    neg99a = 10 ** ncfl99

    if ABpick == 'A':
        arcpy.AddMessage("Cross Section Areas base 10")
        if confLim == '50':
            arcpy.AddMessage("Upper Area " + confLim + " = " + str(pos50a))
            arcpy.AddMessage("Lower Area " + confLim + " = " + str(neg50a))
            areaAup = pos50a
            areaAdn = neg50a
        if confLim == '70':
            arcpy.AddMessage("Upper Area " + confLim + " = " + str(pos70a))
            arcpy.AddMessage("Lower Area " + confLim + " = " + str(neg70a))
            areaAup = pos70a
            areaAdn = neg70a
        if confLim == '80':
            arcpy.AddMessage("Upper Area " + confLim + " = " + str(pos80a))
            arcpy.AddMessage("Lower Area " + confLim + " = " + str(neg80a))
            areaAup = pos80a
            areaAdn = neg80a
        if confLim == '90':
            arcpy.AddMessage("Upper Area " + confLim + " = " + str(pos90a))
            arcpy.AddMessage("Lower Area " + confLim + " = " + str(neg90a))
            areaAup = pos90a
            areaAdn = neg90a
        if confLim == '95':
            arcpy.AddMessage("Upper Area " + confLim + " = " + str(pos95a))
            arcpy.AddMessage("Lower Area " + confLim + " = " + str(neg95a))
            areaAup = pos95a
            areaAdn = neg95a
        if confLim == '975':
            arcpy.AddMessage("Upper Area " + confLim + " = " + str(pos975a))
            arcpy.AddMessage("Lower Area " + confLim + " = " + str(neg975a))
            areaAup = pos975a
            areaAdn = neg975a
        if confLim == '99':
            arcpy.AddMessage("Upper Area " + confLim + " = " + str(pos99a))
            arcpy.AddMessage("Lower Area " + confLim + " = " + str(neg99a))
            areaAup = pos99a
            areaAdn = neg99a

    if ABpick == 'B':
        arcpy.AddMessage("Planimetric Areas base 10")
        if confLim == '50':
            arcpy.AddMessage("Upper Area " + confLim + " = " + str(pos50a))
            arcpy.AddMessage("Lower Area " + confLim + " = " + str(neg50a))
            areaBup = pos50a
            areaBdn = neg50a
        if confLim == '70':
            arcpy.AddMessage("Upper Area " + confLim + " = " + str(pos70a))
            arcpy.AddMessage("Lower Area " + confLim + " = " + str(neg70a))
            areaBup = pos70a
            areaBdn = neg70a
        if confLim == '80':
            arcpy.AddMessage("Upper Area " + confLim + " = " + str(pos80a))
            arcpy.AddMessage("Lower Area " + confLim + " = " + str(neg80a))
            areaBup = pos80a
            areaBdn = neg80a
        if confLim == '90':
            arcpy.AddMessage("Upper Area " + confLim + " = " + str(pos90a))
            arcpy.AddMessage("Lower Area " + confLim + " = " + str(neg90a))
            areaBup = pos90a
            areaBdn = neg90a
        if confLim == '95':
            arcpy.AddMessage("Upper Area " + confLim + " = " + str(pos95a))
            arcpy.AddMessage("Lower Area " + confLim + " = " + str(neg95a))
            areaBup = pos95a
            areaBdn = neg95a
        if confLim == '975':
            arcpy.AddMessage("Upper Area " + confLim + " = " + str(pos975a))
            arcpy.AddMessage("Lower Area " + confLim + " = " + str(neg975a))
            areaBup = pos975a
            areaBdn = neg975a
        if confLim == '99':
            arcpy.AddMessage("Upper Area " + confLim + " = " + str(pos99a))
            arcpy.AddMessage("Lower Area " + confLim + " = " + str(neg99a))
            areaBup = pos99a
            areaBdn = neg99a

    if ABpick == 'A':
        return areaAup,areaAdn
    if ABpick == 'B':
        return areaBup,areaBdn


def WriteHeader(headr):
    
    # =====================================
    # Parameters:
    #   drainName: name of the current run(s)
    #
    # writes header to drainName.pts file
    # documents the volumes entered and areas calculated
    #
    # =====================================
    # lists for string output text file
    outstrvolumeList = []
    outstrxsectAreaList = []
    outstrplanAreaList = []
    
    str_volumeList = []
    str_xsectAreaList = []
    str_planAreaList = []

    # Get headr dictionary values   
    drainName=headr['drainName']
    ptsfilename=headr['ptsfilename']
    volumeList=headr['volumeList']
    masterXsectList=headr['masterXsectList']
    masterPlanList=headr['masterPlanList']
   

    outfile = open(ptsfilename, "a")
    outfile.write("DRAINAGE NAME ENTERED: " + str(drainName) + "\n")
    outfile.write("VALUES SORTED LARGEST TO SMALLEST"+ "\n")
    outfile.write("VOLUMES ENTERED:"+ "\n")
    for i in range(len(volumeList)):
        if i+1 == len(volumeList):
            str_volumeList.append(str(volumeList[i]) + "\n")
        else:
            str_volumeList.append(str(volumeList[i]) + " : ")
    outstrvolumeList = ''.join(str_volumeList)
    outfile.write(outstrvolumeList)
    outfile.write("_________________________________________________________"+ "\n")
    outfile.write("")
    outfile.write('CROSS SECTION AREAS :'+ "\n")
    for i in range(len(masterXsectList)):
        if i+1 == len(masterXsectList):
            str_xsectAreaList.append(str(masterXsectList[i]) + "\n")
        else:
            str_xsectAreaList.append(str(masterXsectList[i]) + " : ")
    outstrxsectAreaList = ''.join(str_xsectAreaList)
    outfile.write(outstrxsectAreaList)
    outfile.write('PLANIMETRIC AREAS :'+ "\n")
    for i in range(len(masterPlanList)):
        if i+1 == len(masterPlanList):
            str_planAreaList.append(str(masterPlanList[i]) + "\n")
        else:
            str_planAreaList.append(str(masterPlanList[i]) + " : ")
    outstrplanAreaList = ''.join(str_planAreaList)
    outfile.write(outstrplanAreaList)
    outfile.write("_________________________________________________________"+ "\n")
    outfile.write("DECREASING PLANIMETRIC AREAS LISTED BELOW"+ "\n")
    outfile.write("_________________________________________________________"+ "\n")
    endtimewh = time.process_time()

def AppendCurrPointToPointArrays(cellx,celly,currxarea,planvals,B):
    # =====================================
    # Parameters:
    #   cellx:  X coordinate of the current cell
    #   celly:  Y coordinate of the current cell
    #   currxarea: copy of xsectAreaList and created in the CalcCrossSection function
    #              xsectAreaList is a list of the calculated cross section areas
    #   planvals:  starts as a list of 0's; one for each planimetric area
    #
    # Track planametric cells in B array on the fly as cross sections are constructed
    #
    # Returns:  planvals, B
    # =====================================

    currxareaCount = len(currxarea) + 1 # number of xsect areas + 1, changes over time
    demArrayValue = B[cellx,celly]      # Array value at current X, Y

    if demArrayValue == 1:              # 1 is background value
        B[cellx,celly] = currxareaCount # set B value to current number of cross section values
        planvals[currxareaCount - 2] = planvals[currxareaCount - 2] + 1 # increase appropriate planvals count by 1
    else:
        if demArrayValue < currxareaCount:
            B[cellx,celly] = currxareaCount  # set B value to current number of cross section values
            planvals[demArrayValue - 2] = planvals[demArrayValue - 2] - 1   # remove from one planvals column
            planvals[currxareaCount - 2] = planvals[currxareaCount - 2] + 1 # add to another planvals column

    return planvals,B

def CheckForWindowBoundaries(cellx,celly,cellbuffx,cellbuffy,cellelev,wXmax,wXmin,wYmax,wYmin,A):
    # =====================================
    # Parameters:
    #   cellx:  X coordinate of the current cell
    #   celly:  Y coordinate of the current cell
    #   cellbuffx:  X coordinate of previous cell
    #   cellbuffy:  Y coordinate of previous cell
    #   cellelev:  DEM elevation at current cell
    #   wXmax,wXmin,wYmax,wYmin:  boundaries of DEM array
    #
    # Check if current(new) XY from function GetNextSectionCell is outside DEM boundaries
    # if it is, set current elevation to 99999.0 and return to previous values of row,col;
    # if is not, get next cell elevation
    #
    # Returns:  X coordinate, Y coordinate, cell elevation
    # =====================================

    if cellx < wXmin or cellx > wXmax or celly < wYmin or celly > wYmax:
        cellx = cellbuffx
        celly = cellbuffy
        cellelev = 99999.0

    else: # get next row,col elevationzzz
        cellelev = A[cellx,celly]

    return cellx,celly,cellelev

def GetNextSectionCell(cellx,celly,cellelev,cellposneg,currFlowDir,wXmax,wXmin,wYmax,wYmin,A):
    # =====================================
    # Parameters:
    #   cellx:  X coordinate of the current cell
    #   celly:  Y coordinate of the current cell
    #   cellelev:  DEM elevation at current cell
    #   cellposneg:  negative or positive 1 indicating left or right direction
    #   currFlowDir:  current flow direction
    #   wXmax,wXmin,wYmax,wYmin:  boundaries of DEM array
    #
    # uses current flow direction to set the operator to get next cross section cell
    # stores the current XY in buffer variables, calls CheckForWindowBoundaries
    # to check if out of bounds
    #
    # Returns:  X coordinate, Y coordinate, cell elevation
    # =====================================

    if currFlowDir == 1:
        rowoper = -1
        coloper = 0
    elif currFlowDir == 2:
        rowoper = -1
        coloper = 1
    elif currFlowDir == 4:
        rowoper = 0
        coloper = 1
    elif currFlowDir == 8:
        rowoper = 1
        coloper = 1
    elif currFlowDir == 16:
        rowoper = 1
        coloper = 0
    elif currFlowDir == 32:
        rowoper = 1
        coloper = -1
    elif currFlowDir == 64:
        rowoper = 0
        coloper = -1
    elif currFlowDir == 128:
        rowoper = -1
        coloper = -1
    else:
        print("Bad flow direction ", currFlowDir)

    cellbuffx = cellx
    cellbuffy = celly
    cellx = cellx + cellposneg * rowoper
    celly = celly + cellposneg * coloper
    cellx,celly,cellelev = CheckForWindowBoundaries(cellx,celly,cellbuffx,cellbuffy,cellelev,wXmax,wXmin,wYmax,wYmin,A)

    return cellx,celly,cellelev

def Check4Pop(currxarea):
    # =====================================
    # Parameters:
    #   currxarea: copy of xsectAreaList and created in the CalcCrossSection function
    #              xsectAreaList is a list of the calculated cross section areas
    #
    # If currxarea list is longer than 1,
    # check each of the section areas to see if it is a negative value.
    # If so, delete item from list by popping
    #
    # Returns: currxarea 
    # =====================================

    negcount = 0
    currlength = len(currxarea)
    if len(currxarea) > 1:
        for i in range(len(currxarea)):
            if currxarea[i] < 0:
                negcount += 1
    while negcount > 0 and currlength > 1:
        currxarea.pop()
        negcount -= 1
        currlength -= 1
    return currxarea

def CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B):

    # =====================================
    # Parameters:
    #   currFlowDir:  current flow direction
    #   currRow:  row of the current cell
    #   currCol:  column of the current cell
    #   wXmax,wXmin,wYmax,wYmin:  boundaries of DEM array
    #   planvals:  starts as a list of 0's; one for each planimetric area
    #
    # Calculates cross sections for a single stream cell
    # sets variables including whether direction is ordinal or diagonal,
    # gets initial XY row column of left and right cells, gets elevations for
    # comparison, and sets fill level.
    #
    # Main Loop identifies which scenario applies to left and right cell comparison
    #   compare elevations equal to fill level
    #   compare elevations less than fill level
    #   compare equal elevations
    #   compare unequal elevations
    # calculates the cross section and subtracts planimetric cells from total,
    # sets new fill level, calls AppendCurrPointToPointArrays and GetNextSectionCell
    # store location and move to next cell
    # updates cell count as appropriate, if elevations are equal, moves both left and right
    # cells. If elevation is 99999 stops CalcCrossSection
    # If currxarea is a list longer than 1, check each of the section areas to see if it
    # is a negative value.  If so, delete (pop) item from list
    #
    # Returns:  planvals, B
    # =====================================

    # Get sectn dictionary values
    wXmax=sectn['wXmax']
    wXmin=sectn['wXmin']
    wYmax=sectn['wYmax']
    wYmin=sectn['wYmin']
    cellDiagonal=sectn['cellDiagonal']
    cellWidth=sectn['cellWidth']
    A=sectn['A']


    currxarea = []
    count = 0
    currxarea.extend(xsectAreaList) # make a copy"


    #=============================================
    # set cell dimension according to current
    # flow direction--use integer value currFlowDir
    #=============================================
    if currFlowDir == 8 or currFlowDir == 128 or currFlowDir == 2 or currFlowDir == 32:
        cellDimen = cellDiagonal
    else: # currFlowDir == 1 or currFlowDir == 16 or currFlowDir == 4 or currFlowDir == 64:
        cellDimen = cellWidth

    #=============================================
    # set X,Y coordinates of current stream cell
    # as right cell -- facing downstream (flow direstion)
    #=============================================

    cellrightx = currRow
    cellrighty = currCol

    #=============================================
    # calculate X,Y coordinates of left stream
    # cell -- facing downstream based upon current
    # flow direction
    #=============================================

    if currFlowDir == 1:
        cellleftx = currRow - 1
        celllefty = currCol
    elif currFlowDir == 2:
        cellleftx = currRow - 1
        celllefty = currCol + 1
    elif currFlowDir == 4:
        cellleftx = currRow
        celllefty = currCol + 1
    elif currFlowDir == 8:
        cellleftx = currRow + 1
        celllefty = currCol + 1
    elif currFlowDir == 16:
        cellleftx = currRow + 1
        celllefty = currCol
    elif currFlowDir == 32:
        cellleftx = currRow + 1
        celllefty = currCol - 1
    elif currFlowDir == 64:
        cellleftx = currRow
        celllefty = currCol - 1
    elif currFlowDir == 128:
        cellleftx = currRow - 1
        celllefty = currCol - 1
    else:
        print("Bad flow direction ", currFlowDir)


    #=============================================
    # get elevations of left and right cells
    #=============================================

    cellleftelev = A[cellleftx,celllefty]
    cellrightelev = A[cellrightx,cellrighty]

    #=============================================
    # set filllevel equal to the lower of
    # the left or right elevations
    #=============================================

    filllevel = cellrightelev
    cellcount = 0
    cellnorm = 1
    cellwneg = -1

    #=============================================
    #              Main Loop
    #=============================================

    while count < 1000000000:

        if currxarea[0] < 0:
            break
        #=============================================
        # compare elevations equal to fill level
        #=============================================

        if cellleftelev == filllevel or cellrightelev == filllevel:

            if cellleftelev == filllevel:

                planvals,B = AppendCurrPointToPointArrays(cellleftx,celllefty,currxarea,planvals,B)
                cellleftx,celllefty,cellleftelev = GetNextSectionCell(cellleftx,celllefty,cellleftelev,cellnorm,currFlowDir,wXmax,wXmin,wYmax,wYmin,A)
            else: #cellrightelev = filllevel

                planvals,B = AppendCurrPointToPointArrays(cellrightx,cellrighty,currxarea,planvals,B)
                cellrightx,cellrighty,cellrightelev = GetNextSectionCell(cellrightx,cellrighty,cellrightelev,cellwneg,currFlowDir,wXmax,wXmin,wYmax,wYmin,A)
            cellcount += 1

        #=============================================
        # compare elevations less than fill level
        #=============================================

        elif cellrightelev < filllevel or cellleftelev < filllevel:

            if cellrightelev < filllevel:

                for i in range(len(currxarea)):
                    currxarea[i] = currxarea[i] - ((filllevel - cellrightelev) * cellDimen)

                currxarea = Check4Pop(currxarea)
                if currxarea[0] > 0:
                    planvals,B = AppendCurrPointToPointArrays(cellrightx,cellrighty,currxarea,planvals,B)
                    cellrightx,cellrighty,cellrightelev = GetNextSectionCell(cellrightx,cellrighty,cellrightelev,cellwneg,currFlowDir,wXmax,wXmin,wYmax,wYmin,A)

            else: # cellleftelev < filllevel
                for i in range(len(currxarea)):
                    currxarea[i] = currxarea[i] - ((filllevel - cellleftelev) * cellDimen)

                currxarea = Check4Pop(currxarea)
                if currxarea[0] > 0:
                    planvals,B = AppendCurrPointToPointArrays(cellleftx,celllefty,currxarea,planvals,B)
                    cellleftx,celllefty,cellleftelev = GetNextSectionCell(cellleftx,celllefty,cellleftelev,cellnorm,currFlowDir,wXmax,wXmin,wYmax,wYmin,A)
            cellcount += 1

        #=============================================
        # compare equal elevations
        #=============================================

        elif cellrightelev == cellleftelev:
            for i in range(len(currxarea)):
                currxarea[i] = currxarea[i] - ((cellrightelev - filllevel) * (cellDimen * cellcount))

            currxarea = Check4Pop(currxarea)
            if currxarea[0] > 0:
                filllevel = cellrightelev
                #=============================================
                # move left and right
                #=============================================
                planvals,B = AppendCurrPointToPointArrays(cellleftx,celllefty,currxarea,planvals,B)
                cellleftx,celllefty,cellleftelev = GetNextSectionCell(cellleftx,celllefty,cellleftelev,cellnorm,currFlowDir,wXmax,wXmin,wYmax,wYmin,A)
                planvals,B = AppendCurrPointToPointArrays(cellrightx,cellrighty,currxarea,planvals,B)
                cellrightx,cellrighty,cellrightelev = GetNextSectionCell(cellrightx,cellrighty,cellrightelev,cellwneg,currFlowDir,wXmax,wXmin,wYmax,wYmin,A)
                cellcount = cellcount + 2

        #=============================================
        # compare unequal elevations
        #=============================================

        elif cellrightelev > cellleftelev or cellrightelev < cellleftelev:
            if cellrightelev > cellleftelev:

                for i in range(len(currxarea)):
                    currxarea[i] = currxarea[i] - ((cellleftelev - filllevel) * (cellDimen * cellcount))

                currxarea = Check4Pop(currxarea)
                if currxarea[0] > 0:
                    filllevel = cellleftelev
                    planvals,B = AppendCurrPointToPointArrays(cellleftx,celllefty,currxarea,planvals,B)
                    cellleftx,celllefty,cellleftelev = GetNextSectionCell(cellleftx,celllefty,cellleftelev,cellnorm,currFlowDir,wXmax,wXmin,wYmax,wYmin,A)
            else: # cellleftelev > cellrightelev
                for i in range(len(currxarea)):
                    currxarea[i] = currxarea[i] - ((cellrightelev - filllevel) * (cellDimen * cellcount))

                currxarea = Check4Pop(currxarea)

                if currxarea[0] > 0:
                    filllevel = cellrightelev
                    planvals,B = AppendCurrPointToPointArrays(cellrightx,cellrighty,currxarea,planvals,B)
                    cellrightx,cellrighty,cellrightelev = GetNextSectionCell(cellrightx,cellrighty,cellrightelev,cellwneg,currFlowDir,wXmax,wXmin,wYmax,wYmin,A)
            cellcount += 1

        #=============================================
        # hit an edge
        #=============================================
        if cellleftelev == 99999.0 or cellrightelev == 99999.0:
            for i in range(len(currxarea)):
                currxarea[i] = -99999

        #=============================================
        # update count of time through the MAIN LOOP
        # stops at 1000000000
        #=============================================
        count += 1

    return planvals,B

#=============================================
# End Local Functions
#=============================================


def main(workspace, Input_surface_raster, drainName, volumeTextFile, coordsTextFile, flowType):

    for i in [1]:
        #===========================================================================
        # Assign user inputs from menu to appropriate variables
        #===========================================================================
        starttimetot = time.process_time() # calculate time for program run
        tottime = 0.0
        arcpy.AddMessage("Parsing user inputs:")

        arcpy.env.workspace=workspace

        if flowType == 'Lahar' or flowType == 'Debris_Flow' or flowType == 'Rock_Avalanche':
            flowType = flowType          # lahar, debris flow, rock avalanche
            conflim = False
            arcpy.AddMessage("Running Laharz_py")
        else:
            confLimitChoice = flowType       # selected confidence limit
            conflim = True
            arcpy.AddMessage("Running Laharz_py with confidence limits")

        #=============================================
        # report dem selected back to user
        #=============================================
        arcpy.AddMessage( "_________ Input Values _________")
        arcpy.AddMessage( 'Input Surface Raster Is:' + Input_surface_raster)

        #=============================================
        # report inputs back to user
        #=============================================
        arcpy.AddMessage("Volume textfile   :" + volumeTextFile)
        arcpy.AddMessage("Starting coordinates file  :" + coordsTextFile)
        arcpy.AddMessage("Drainage identifier  :" + drainName)

        # =====================================
        # report flowType back to user
        # =====================================
        if conflim:
            # =====================================
            # fix flowType as Lahar
            # =====================================
            flowType = 'Lahar'
            arcpy.AddMessage("Flow Type is Lahar")
        else:
            if flowType == 'Lahar':
                arcpy.AddMessage("Lahar Selected")
            if flowType == 'Debris_Flow':
                arcpy.AddMessage("Debris Flow Selected")
            if flowType == 'Rock_Avalanche':
                arcpy.AddMessage("Rock Avalanche Selected")
        arcpy.AddMessage( "_________ Paths on Disk _________")

        #=============================================
        # Set the ArcGIS environment settings
        #=============================================
        env.scratchWorkspace = env.workspace
        env.extent = Input_surface_raster
        env.snapRaster = Input_surface_raster
        currentPath = env.workspace

        #=============================================
        # Set filenames and directories
        #=============================================
        BaseName = os.path.basename(Input_surface_raster)
        BaseNameNum= len(BaseName)
        PathName = env.workspace + "\\"

        # if the filename suffix is "fill", get prefix name
        if BaseName.endswith("fill"):
            PrefixName = BaseName.rstrip("fill")

        # assign complete names for supplementary files,
        # path and basename(prefix and suffix)
        fillname = PathName + PrefixName + "fill"
        dirname = PathName + PrefixName + "dir"
        flacname = PathName + PrefixName + "flac"
        strname = PathName + PrefixName + "str"

        # assign partial names, prefix and suffix without path
        pfillname = PrefixName + "fill"
        pdirname = PrefixName + "dir"
        pflacname = PrefixName + "flac"
        pstrname = PrefixName + "str"

        # report full names including path
        arcpy.AddMessage("full path fill  :" + fillname)
        arcpy.AddMessage("full path dir   :" + dirname)
        arcpy.AddMessage("full path flac  :" + flacname)
        arcpy.AddMessage("full path str   :" + strname)

        # assign the flow direction and flow accumulation grids to variables
        Input_direction_raster = dirname
        Input_flowaccumulation_raster = flacname

        # =====================================
        #    Set up List variables
        # =====================================

        volumeList = []       # list of input volumes
        xstartpoints = []     # coordinates of starting cell
        xsectAreaList = []    # list of cross section areas
        planAreaList = []     # list of planimetric areas
        checkPlanExtent = []  # copy of list of planimetric areas
        masterXsectList = []  # copy of list of cross section areas
        masterPlanList = []   # copy of list of planimetric areas
        masterVolumeList = [] # copy of list of input volumes

        # string lists for output text file
        str_volumeList = []
        str_xsectAreaList = []
        str_planAreaList = []
          

        # =====================================
        #  Convert DEM to NumPyArray and
        #  get row, column values for boundaries
        # =====================================
        arcpy.AddMessage("_________ Creating DEM Array _________")
        A = arcpy.RasterToNumPyArray(fillname)

        # =====================================
        #    Get NumPyArray Dimensions
        # =====================================
        arcpy.AddMessage("_________ Get NumPyArray Dimensions _________")

        arcpy.AddMessage('Shape is: ' + str(A.shape) + " (rows, colums)")
        number_rows = A.shape[0]
        number_cols = A.shape[1]
        arcpy.AddMessage('Number of rows is: ' + str(number_rows))
        arcpy.AddMessage('Number of columns is: ' + str(number_cols))

        #========================================================
        # Setthe Xmin, Xmax, Ymin, Ymax values for DEM boundaries
        #========================================================
        arcpy.AddMessage("_________ Set Window Boundaries _________")

        wXmin = 0
        wXmax = number_rows - 1
        wYmin = 0
        wYmax = number_cols - 1

        arcpy.AddMessage( "wXmin (TOP): " + str(wXmin))
        arcpy.AddMessage( "wXmax (BOTTOM): " + str(wXmax))
        arcpy.AddMessage( "wYmin (LEFT): " + str(wYmin))
        arcpy.AddMessage( "wYmax (RIGHT): " + str(wYmax))

        # =====================================
        # Call ConvertTxtToList function with volumes and
        # starting point locations
        # =====================================

        arcpy.AddMessage( "_________ Convert Textfiles to Arrays _________")

        volumeList = ConvertTxtToList(volumeTextFile, volumeList, 'volumes', conflim)
        numvolumes = len(volumeList)

        if conflim and numvolumes > 1:
            vList = []
            vList = append.volumeList[0]
            volumeList = []
            volumeList = append.vList[0]
            del vList
        arcpy.AddMessage("Volume List is: " + str(volumeList))

        xstartpoints = ConvertTxtToList(coordsTextFile, xstartpoints, 'points', conflim)
        numstartpts = len(xstartpoints)
        arcpy.AddMessage("Points entered: " + str(xstartpoints))

        # =====================================
        # call CalcArea function with parameters of list of volumes,
        # appropriate coefficents, and an empty list to store
        # calculated cross section or planimetric area values
        # =====================================

        if flowType == 'Lahar':
            xsectAreaList = CalcArea(volumeList,0.05,xsectAreaList)
            planAreaList = CalcArea(volumeList,200,planAreaList)
        if flowType == 'Debris_Flow':
            xsectAreaList = CalcArea(volumeList,0.1,xsectAreaList)
            planAreaList = CalcArea(volumeList,20,planAreaList)
        if flowType == 'Rock_Avalanche':
            xsectAreaList = CalcArea(volumeList,0.2,xsectAreaList)
            planAreaList = CalcArea(volumeList,20,planAreaList)

        if conflim:
            # =====================================
            # Calculate the max and min values for selected confidence limits
            # then add the cross section and planimetric areas to respective list
            # =====================================
            oneVolume = volumeList[0]
            XSArea1, XSArea3 = StdErrModMean('A',PathName,oneVolume,confLimitChoice)
            PlanArea1, PlanArea3 = StdErrModMean('B',PathName,oneVolume,confLimitChoice)

            xsectAreaList.append(round(XSArea1))
            xsectAreaList.append(round(XSArea3))
            planAreaList.append(round(PlanArea1))
            planAreaList.append(round(PlanArea3))
            xsectAreaList.sort() # sort
            planAreaList.sort()  # sort


        arcpy.AddMessage("Cross Section Area List is: " + str(xsectAreaList))
        arcpy.AddMessage("Planimetric Area List is: " + str(planAreaList))

        # =====================================
        # order volumes, cross section and planimetric areas (large to small)
        # make copy of the planimetric area called checkPlanExtent
        # to store calculated area
        # make master copies of planimetric and cross section areas and volumes
        # =====================================

        volumeList.reverse()                 # order volumes large to small
        xsectAreaList.reverse()              # order xsection areas list large to small
        planAreaList.reverse()               # order planimetric areas large to small
        checkPlanExtent.extend(planAreaList) # make copy of planAreaList
        masterPlanList.extend(planAreaList)  # master copy of planimetric areas
        masterXsectList.extend(xsectAreaList)# master copy of cross section areas
        masterVolumeList.extend(volumeList)  # master copy of volumes



        # =====================================
        # Call CalcCellDimensions function to get
        # cell width and diagonal cell length of DEM cells
        # get the lower left corner location for array output
        # =====================================

        cellWidth, cellDiagonal = CalcCellDimensions(pfillname)
        xxllx = arcpy.GetRasterProperties_management(pfillname,"LEFT")
        lowLeftX = float(xxllx.getOutput(0))
        xxlly = arcpy.GetRasterProperties_management(pfillname,"BOTTOM")
        lowLeftY = float(xxlly.getOutput(0))

        # initialize count and stop flag (boolean)
        cellTraverseCount = 0
        allStop = False

        # =====================================
        # Create starting point coordinate array
        # Convert current coordinates to Arcpy Point
        # and append to startCoordsList
        # =====================================

        startCoordsList = []
        for b in range(len(xstartpoints)):
            apoint = xstartpoints[b]    # get coordinates as list of first point
            currx = float(apoint[0])    # assign first value of coord list (X) of first point as float
            curry = float(apoint[1])    # assign second value of coord list (Y) of first point as float
            xonePoint = arcpy.Point(currx, curry)
            startCoordsList.append(xonePoint) # append current point to a list

        arcpy.AddMessage("_________ Creating startpts_g _________")

        if arcpy.Exists(currentPath + "\\" + "startpts_g"):
            arcpy.Delete_management(currentPath + "\\" + "startpts_g") # delete existing startpts_g

        # =====================================
        # Use cell locations of startCoordsList to create a
        # temporary grid with cells having a value
        # of 0 at starting points and all other cells
        # having values of NODATA; use isnull function
        # to create grid having 0's at start locations
        # and the other cells having values of 1
        # creates startpts_g grid that stores locations
        # will convert to array, search for 0's then
        # store row, column to start runs
        # =====================================

        tmpStartPoints = ExtractByPoints(Input_surface_raster,startCoordsList,"INSIDE")

        isnull_result = IsNull(tmpStartPoints)
        isnull_result.save(currentPath + "\\" + "startpts_g") # create startpts_g having values of 0 and 1


        # =====================================
        #    Convert startpts_g grid to NumPyArray
        # =====================================

        arcpy.AddMessage("_________ Creating Starting Points Array _________")
        B = arcpy.RasterToNumPyArray(currentPath + "\\" + "startpts_g")

        # =====================================
        #    Convert flow direction grid to NumPyArray
        # =====================================

        arcpy.AddMessage("_________ Creating Flow Direction Array _________")
        C = arcpy.RasterToNumPyArray(Input_direction_raster)

        # =====================================
        #    Get row, column of all starting cells
        # =====================================

        arcpy.AddMessage('Total rows : ' + str(number_rows))
        arcpy.AddMessage('Total columns : ' + str(number_cols))
        # set counters to zero
        i = 0
        j = 0
        zerosCoordsList = []
        foundPt = []
        while j < number_rows:
            for i in range(number_cols):
               if B[j,i] == 0:
                  arcpy.AddMessage('Found the zero : '+ str(A[j,i]))
                  FoundX = j
                  FoundY = i
                  foundPt.append(j)
                  foundPt.append(i)
                  zerosCoordsList.append(foundPt)
                  foundPt = []
            j = j + 1
        arcpy.AddMessage('found points: ' + str(zerosCoordsList))
        for r in range(len(zerosCoordsList)):
            aStartPoint = zerosCoordsList[r]
            currRow = aStartPoint[0] #startX
            currCol = aStartPoint[1] #startY
            B[currRow,currCol] = 1 # Remove the 0's, entire array completely 1's

        mergeList = []
        # =====================================
        #    Begin loop for list of rows, columns
        # =====================================

        blcount = 0
        for r in range(len(zerosCoordsList)):
            # =====================================
            #   Intialize variables and lists for new run
            # =====================================

            blcount = blcount + 1

            cellTraverseCount = 0
            allStop = False

            str_volumeList = []
            str_xsectAreaList = []
            str_planAreaList = []

            xsectAreaList = []
            xsectAreaList.extend(masterXsectList)

            planAreaList = []
            planAreaList.extend(masterPlanList)

            checkPlanExtent = []
            checkPlanExtent.extend(masterPlanList) # make copy of planAreaList

            volumeList = []
            volumeList.extend(masterVolumeList)

            planvals = []
            for m in range(len(checkPlanExtent)):
                planvals.append(0)

            # =====================================
            #  Load a row, column
            # =====================================

            aStartPoint = zerosCoordsList[r]

            currRow = aStartPoint[0] #startX
            currCol = aStartPoint[1] #startY

            currFlowDir = C[currRow,currCol]
            arcpy.AddMessage("Current flow direction:  " + str(currFlowDir))


            # =====================================
            #  call WriteHeader function for drainName.pts file
            # =====================================

            ptsfilename = currentPath+"\\"+str(drainName)+ str(blcount)+".pts"
            arcpy.AddMessage("Current name:  " + str(ptsfilename))
            if not os.path.exists(ptsfilename):
                outfile = open(ptsfilename, "w")
                arcpy.AddMessage( "Textfile Created: " + ptsfilename)
            else:
                outfile = open(ptsfilename, "a")
                arcpy.AddMessage( "Textfile Exists: " + ptsfilename)
            arcpy.AddMessage("Calling writeheader with:  " + str(drainName))

            # =====================================
            #    Set up Dictionaries
            # =====================================
            
            headr={}
            headr['drainName']=drainName
            headr['ptsfilename']= ptsfilename
            headr['volumeList']= volumeList
            headr['masterXsectList']=masterXsectList
            headr['masterPlanList']=masterPlanList 
        
            #WriteHeader(drainName,ptsfilename,volumeList,masterXsectList,masterPlanList)
            WriteHeader(headr)  

            sectn={}
            sectn['wXmax']=wXmax
            sectn['wXmin']=wXmin
            sectn['wYmax']=wYmax
            sectn['wYmin']=wYmin
            sectn['cellDiagonal']=cellDiagonal
            sectn['cellWidth']=cellWidth
            sectn['A']=A



            while not allStop:
                # =====================================
                #  just in case of problems
                # =====================================
                if cellTraverseCount > 90000000:
                    break
                
                # ===========================================
                #  Create cross sections in directions other
                #  than the direction of stream flow
                # ===========================================

                #arcpy.AddMessage("First cross section")
                planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)

                # ===========================================
                #  Store current flow direction,
                #  change flow direction to construct sections
                #  in other two possible directions
                # ===========================================

                savedir = currFlowDir  # store current flow direction
                # Calculate two cross sections for each flow direction
                if currFlowDir == 32:
                    currFlowDir = 16
                    # 1 of 2 Cardinal flow directions
                    #arcpy.AddMessage("Second cross section - ordinal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)
                    currFlowDir = 64
                    # 2 of 2 Cardinal flow directions
                    #arcpy.AddMessage("Third cross section - ordinal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)
                if currFlowDir == 128:
                    currFlowDir = 64
                    # 1 of 2 Cardinal flow directions
                    #arcpy.AddMessage("Second cross section - ordinal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)
                    currFlowDir = 1
                    # 2 of 2 Cardinal flow directions
                    #arcpy.AddMessage("Third cross section - ordinal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)
                if currFlowDir == 2:
                    currFlowDir = 1
                    # 1 of 2 Cardinal flow directions
                    #arcpy.AddMessage("Second cross section - ordinal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)
                    currFlowDir = 4
                    # 2 of 2 Cardinal flow directions
                    #arcpy.AddMessage("Third cross section - ordinal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)
                if currFlowDir == 8:
                    currFlowDir = 4
                    # 1 of 2 Cardinal flow directions
                    #arcpy.AddMessage("Second cross section - ordinal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)
                    currFlowDir = 16
                    # 2 of 2 Cardinal flow directions
                    #arcpy.AddMessage("Third cross section - ordinal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)

                
                if currFlowDir == 1: #  or currFlowDir == 4 or currFlowDir == 16 or currFlowDir == 64:
                    currFlowDir = 128
                    # 1 of 2 Diagonal flow directions
                    #arcpy.AddMessage("Second cross section - diagonal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)
                    currFlowDir = 2
                    # 2 of 2 Diagonal flow directions
                    #arcpy.AddMessage("Third cross section - diagonal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)
                if currFlowDir == 4: #  or currFlowDir == 4 or currFlowDir == 16 or currFlowDir == 64:
                    currFlowDir = 2
                    # 1 of 2 Diagonal flow directions
                    #arcpy.AddMessage("Second cross section - diagonal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)
                    currFlowDir = 8
                    # 2 of 2 Diagonal flow directions
                    #arcpy.AddMessage("Third cross section - diagonal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)
                if currFlowDir == 16: #  or currFlowDir == 4 or currFlowDir == 16 or currFlowDir == 64:
                    currFlowDir = 8
                    # 1 of 2 Diagonal flow directions
                    #arcpy.AddMessage("Second cross section - diagonal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)
                    currFlowDir = 32
                    # 2 of 2 Diagonal flow directions
                    #arcpy.AddMessage("Third cross section - diagonal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)
                if currFlowDir == 64: #  or currFlowDir == 4 or currFlowDir == 16 or currFlowDir == 64:
                    currFlowDir = 32
                    # 1 of 2 Diagonal flow directions
                    #arcpy.AddMessage("Second cross section - diagonal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)
                    currFlowDir = 128
                    # 2 of 2 Diagonal flow directions
                    #arcpy.AddMessage("Third cross section - diagonal")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)

                currFlowDir = savedir  # restore the saved flow direction
                
                # ===========================================
                # checkerboard on diagonal - move to new X,Y,
                # make section and restore to original X,Y
                # ===========================================

                if currFlowDir == 2 or currFlowDir == 8 or currFlowDir == 32 or currFlowDir == 128:
                    # Checkerboard flow direction
                    savex = currRow  # store current X coordinate
                    savey = currCol  # store current Y coordinate
                    if currFlowDir == 8:
                        # east
                        currRow = currRow + 1
                    elif currFlowDir == 32:
                        # southeast
                        currCol = currCol - 1
                    elif currFlowDir == 128:
                        # south
                        currRow = currRow - 1
                    elif currFlowDir == 2:
                        # southwest
                        currCol = currCol + 1
                    #arcpy.AddMessage("Fourth cross section ")
                    planvals,B = CalcCrossSection(sectn,currFlowDir,currRow,currCol,planvals,xsectAreaList,B)

                    currRow = savex   # restore X coordinate
                    currCol = savey   # restore Y coordinate
                
                # =====================================
                #  Check planimetric area to see if run
                #  should stop
                # =====================================

                planvals.reverse()
                numz = 0
                temp_plan = []
                
                for i in range(len(planvals)):
                    numz = planvals[i] + numz

                    temp_plan.append(numz * cellWidth * cellWidth)

                temp_plan.reverse()

                for i in range(len(checkPlanExtent)):
                    checkPlanExtent[i] = planAreaList[i] - temp_plan[i]


                planvals.reverse()
                
                # ===========================================
                # write the remaining planimetric areas to file
                # remaining area - checkPlanExtent[0] - [6] or
                # 7 simultaneous runs
                # ===========================================
                outfile = open(ptsfilename, "a")
                iwrite = len(checkPlanExtent)
                if iwrite == 1:
                    outfile.write(str(checkPlanExtent[0])+ "\n")
                elif iwrite == 2:
                    outfile.write(str(checkPlanExtent[0])+", "+str(checkPlanExtent[1])+ "\n")
                elif iwrite == 3:
                    outfile.write(str(checkPlanExtent[0])+", "+str(checkPlanExtent[1])+", "+str(checkPlanExtent[2])+ "\n")
                elif iwrite == 4:
                    outfile.write(str(checkPlanExtent[0])+", "+str(checkPlanExtent[1])+", "+str(checkPlanExtent[2])+", "+str(checkPlanExtent[3])+ "\n")
                elif iwrite == 5:
                    outfile.write(str(checkPlanExtent[0])+", "+str(checkPlanExtent[1])+", "+str(checkPlanExtent[2])+", "+str(checkPlanExtent[3])+", "+str(checkPlanExtent[4])+ "\n")
                elif iwrite == 6:
                    outfile.write(str(checkPlanExtent[0])+", "+str(checkPlanExtent[1])+", "+str(checkPlanExtent[2])+", "+str(checkPlanExtent[3])+", "+str(checkPlanExtent[4])+", "+str(checkPlanExtent[5])+ "\n")
                elif iwrite == 7:
                    outfile.write(str(checkPlanExtent[0])+", "+str(checkPlanExtent[1])+", "+str(checkPlanExtent[2])+", "+str(checkPlanExtent[3])+", "+str(checkPlanExtent[4])+", "+str(checkPlanExtent[5])+", "+str(checkPlanExtent[6])+ "\n")
                
               # ===========================================
                # check for negative planimetric values
                # if so, delete (pop) them
                # ===========================================

                pnegcount = 0
                plandiflength = len(checkPlanExtent)
                if plandiflength > 1:
                    for i in range(len(checkPlanExtent)):
                        if checkPlanExtent[i] < 0:
                            pnegcount += 1
                if pnegcount > 0 and plandiflength > 1:
                    #arcpy.AddMessage("Popping...")
                    planAreaList.pop()
                    xsectAreaList.pop()
                    checkPlanExtent.pop()
                    pnegcount -= 1
                    plandiflength -= 1

                # =====================================
                #  Stop if done
                # =====================================

                if checkPlanExtent[0] < 0:
                    endtimetot = time.process_time()
                    tottime = endtimetot - starttimetot


                    stringtime = CalcTime(tottime)

                    outfile.write("TOTAL TIME:  " + str(tottime)+ " seconds" + "\n")
                    outfile.write("TOTAL TIME:  " + stringtime + "\n")
                    outfile.write("TOTAL CELLS TRAVERSED:  " + str(cellTraverseCount)+ " cells" + "\n")
                    outfile.close()

                    allStop = True


                # ===========================================
                # This function changes coordinates to move
                # downstream to appropriate stream cell
                # ===========================================

                if cellTraverseCount < 9000000:

                    if currFlowDir == 1:
                        #  east
                        currCol = currCol + 1
                    elif currFlowDir == 2:
                        # southeast
                        currRow = currRow + 1
                        currCol = currCol + 1
                    elif currFlowDir == 4:
                        # south
                        currRow = currRow + 1
                    elif currFlowDir == 8:
                        # southwest
                        currRow = currRow +1
                        currCol = currCol - 1
                    elif currFlowDir == 16:
                        #  west
                        currCol = currCol - 1
                    elif currFlowDir == 32:
                        # northwest
                        currRow = currRow - 1
                        currCol = currCol - 1
                    elif currFlowDir == 64:
                        # north
                        currRow = currRow - 1
                    elif currFlowDir == 128:
                        # northeast
                        currRow = currRow - 1
                        currCol = currCol + 1
                    else:
                        #print("Bad flow direction ", currFlowDir)
                        arcpy.AddMessage("Bad flow direction")
                else:
                    # =====================================
                    #   Stop if infinite loop
                    # =====================================
                    endtimetot = time.process_time()
                    tottime = endtimetot - starttimetot

                    stringtime = CalcTime(tottime)

                    outfile.write("TOTAL TIME:  " + str(tottime)+ " seconds" + "\n")
                    outfile.write("TOTAL TIME:  " + stringtime + "\n")
                    outfile.write("TOTAL CELLS TRAVERSED:  " + str(cellTraverseCount)+ " cells" + "\n")
                    outfile.close()

                    allStop = True


                # ===========================================
                # Get new flow direction
                # ===========================================
                currFlowDir = C[currRow,currCol]
                arcpy.AddMessage("New Flow Direction is: " + str(currFlowDir))

                cellTraverseCount += 1

                arcpy.AddMessage("______________________________________")
                arcpy.AddMessage(" NUMBER OF STREAM CELLS TRAVERSED: " + str(cellTraverseCount))

                arcpy.AddMessage("")

            if allStop == True:
                arcpy.AddMessage("______________________________________")
                arcpy.AddMessage("_________ ALL STOP IS:" + str(allStop))

            arcpy.AddMessage("_________ Creating Grid " + str(drainName) + str(blcount) + " from Array _________")
            if arcpy.Exists(currentPath + "\\" + str(drainName) + str(blcount)):
                arcpy.Delete_management(currentPath + "\\" + str(drainName) + str(blcount)) # delete existing test_sect
            myRaster = arcpy.NumPyArrayToRaster(B,arcpy.Point(lowLeftX, lowLeftY),cellWidth,cellWidth)
            myRaster.save(env.workspace + "\\" + str(drainName) + str(blcount))

            mergeList.append(str(drainName)+str(blcount))

            # =====================================
            #   Restore B array to all 1's
            # =====================================

            i = 0
            j = 0
            while j < number_rows:
                for i in range(number_cols):
                   if B[j,i] > 1:
                       B[j,i] = 1
                j = j + 1

        arcpy.AddMessage("...Processing Complete...")
        arcpy.AddMessage("TOTAL TIME:  " + str(tottime) + " seconds")

        arcpy.AddMessage("List of the files created:  " + str(mergeList))
        arcpy.AddMessage("Volumes entered:  " + str(volumeList))

        arcpy.AddMessage("Number of volumes entered:  " + str(numvolumes))

        del A
        del B
        del C

if __name__ == "__main__":
    from sys import argv
    main(argv[1], argv[2], argv[3], argv[4], argv[5], argv[6])