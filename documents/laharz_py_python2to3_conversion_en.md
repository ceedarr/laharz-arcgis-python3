2025-08-29 Kazuki Sugimura

# Purpose of this document

Resolve errors encountered when using LAHARZ_py by porting Python 2 code to run in a Python 3 (ArcGIS Pro) environment.

Note:
These fixes address errors observed when running the following LAHARZ_py tools within ArcGIS: "Create Surface Hydrology Rasters", "Generate New Stream Network", "Hazard Zone Proximal", and "LaharZ Distal Zones". The other tools—"LaharZ Distal Zones with Conf Levels", "Merge Rasters by Volume", and "Raster to Shapefile"—were not exercised, so issues (if any) are unknown. Please apply similar fixes as needed.

# Assumptions / Environment

- Platform:
  - Windows 11
  - ArcGIS Pro 3.4
  - (VS Code or other code editor)

# Code changes (Python 2 → 3 and other fixing issues)

USGS website: https://pubs.usgs.gov/of/2014/1073/
Download and extract LAHARZ_py ("LAHARZ_py_example.zip") from the USGS site above.

LAHARZ_py was written for Python 2, while current ArcGIS Pro versions use Python 3. This causes version-related errors. Apply the changes below.
Tip: To avoid missing any occurrences, use your editor’s multi-file search/replace.

1. Print statement syntax

Change all Python 2 print statements to Python 3 function calls.
Target files: "distal_inundation.py", "new_stream_network.py", "surface_hydro.py"

Example:
- Python 2 (incorrect):
print "Bad flow direction ", currFlowDir
- Python 3 (correct):
print("Bad flow direction ", currFlowDir)

- regular expression (VS Code)
    search: "print (.+)"
    replace: "print($1)"


2. Not-equal operator

Replace the Python 2 operator `<>` with `!=`.
Target files: "distal_inundation.py", "merge_runs.py", "proximal_zone.py"

Example:
- Python 2 (incorrect):
if aline.find(',') <> -1:  # if it does have a ','
- Python 3 (correct):
if aline.find(',') != -1:  # if it does have a ','

- regular expression (VS Code)
    search: "<>"
    replace: "!="


3. Time functions

Replace `time.clock()` with `time.process_time()` (Python 3 removed `clock`).
Target files: "distal_inundation.py", "merge_runs.py", "raster_to_shapefile.py"

Example:
- Python 2 (incorrect):
starttimetot = time.clock()  # calculate time for program run
- Python 3 (correct):
starttimetot = time.process_time()  # calculate time for program run

- regular expression (VS Code)
    search: "time\.clock"
    replace: "time.process_time"


4. File opening function

Replace Python 2 `file()` with Python 3 `open()`.
Target files: "distal_inundation.py"

Example:
- Python 2 (incorrect):
outfile = file(ptsfilename, "a")
- Python 3 (correct):
outfile = open(ptsfilename, "a")

- regular expression (VS Code)
    search: "file\("
    replace: "open("


5. BOM-safe text file handling for open()

Observed in this project: reading or writing text files created or edited on Japanese Windows 11 systems caused UnicodeError. The cause was a UTF-8 BOM at the start of the file. Adding encoding="utf_8_sig" to open() calls resolved these errors by handling the BOM automatically.

Target files:
- "distal_inundation.py"
- "merge_runs.py"
- "proximal_zone.py"

Examples:
- Before (incorrect):
    outfile = open(ptsfilename, "a")
- After (correct):
    outfile = open(ptsfilename, "a", encoding="utf_8_sig")


- regular expression (VS Code)
    search: "open\((.+[r|a|w]["|'])\)"
    replace: "open($1, encoding="utf_8_sig")"


6?. Path concatenation / encoding robustness (if needed)

On some Japanese Windows environments (mix of UTF-8 and Shift-JIS in project or directory names), string concatenation with backslashes can trigger encoding/path handling issues when saving rasters. Use `os.path.join()` instead of manual concatenation with `+ "\\" +`.
Note: This fix is not necessary in environments that contain only English characters (ASCII letters, numbers, etc.).

Target file: "distal_inundation.py" (original occurrence line 1591)

Example:
- Original (problematic when mixed encodings):
myRaster.save(env.workspace + "\\" + str(drainName) + str(blcount))
- Revised (encoding-safe):
# ======== fixing for encode flexibility 2025-09-09 Kazuki
# myRaster.save(env.workspace + "\\" + str(drainName) + str(blcount))       # this is original code, which cause error when mixing utf-8 and shift-jis (japanese encode)

myRaster.save(os.path.join(env.workspace, (str(drainName) + str(blcount)))) # no error even if mixing

# Alternative using pathlib (optional):
# import pathlib
# myRaster.save(str(pathlib.Path(env.workspace) / (str(drainName) + str(blcount)))) # also no error even if mixing but you need to use "pathlib" library additionally
# ======== end of fixing


End of required changes.
