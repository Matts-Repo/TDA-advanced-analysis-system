================================================================================
TDA ANALYSIS SYSTEM v1.0 - README
================================================================================

OVERVIEW
--------
The TDA (Thermal Desorption Analysis) Analysis System is a comprehensive PyQt5-based
application for processing gas chromatograph data from raw files through calibration
management to publication-ready plots. This system enables accurate hydrogen analysis
with complete data traceability and quality validation.

The system integrates three main modules:
1. Calibration Management - Process hydrogen calibration standard data
2. Data Processing - Convert raw experimental TDA data to hydrogen concentrations  
3. Data Visualization - Generate publication-ready plots with extensive customization

INSTALLATION
------------
1. Ensure Python 3.8+ is installed on your system
2. Navigate to the tda_analysis_system directory
3. Install required dependencies:
   
   pip install -r requirements.txt

   Dependencies include:
   - PyQt5>=5.15.0 (GUI framework)
   - pandas>=1.3.0 (data processing)
   - numpy>=1.21.0 (numerical calculations)
   - matplotlib>=3.5.0 (plotting)
   - openpyxl>=3.0.9 (Excel file support)
   - scipy>=1.7.0 (statistical analysis)
   - statsmodels>=0.13.0 (advanced statistics)

LAUNCHING THE APPLICATION
-------------------------
Run the main application:

python main.py

The application will open with a tabbed interface containing three main sections:
- Calibration Management
- Data Processing  
- Data Visualization

USING THE SYSTEM
================

MODULE 1: CALIBRATION MANAGEMENT
---------------------------------
This module processes hydrogen calibration standard data to create a calibration database.

STEP 1: Process New Calibration
1. Click "Browse" to select a folder containing TDA calibration files
2. Enter gas concentration (default: 61.0 ppm)
3. Optionally provide a custom calibration name
4. Click "Preview Data" to verify the data looks correct
5. Click "Process Calibration" to add to database

Supported file formats (in order of preference):
- .txt summary files (GLPrpt format) - PREFERRED
- Multiple .xls files (individual run reports)
- .pdf files (fallback option)

STEP 2: Manage Calibration Database
1. Use search/filter controls to find specific calibrations
2. Filter by quality: "Valid Only", "High Quality (>80)", "Needs Review"
3. View calibration details including statistics and quality flags
4. Export calibration data or set as default for processing

Quality indicators:
- Green: CV% ≤ 5% (excellent)
- Yellow: CV% > 5% but ≤ 10% (acceptable)
- Red: CV% > 10% (poor quality - review needed)

MODULE 2: DATA PROCESSING
-------------------------
This module converts raw experimental TDA data to hydrogen concentrations using calibrations.

STEP 1: Load Experimental Data
1. Click "Browse" to select folder containing experimental TDA files
2. Click "Preview Data" to verify data extraction
3. Review data summary (total runs, missing runs, date range)

STEP 2: Set Processing Parameters
1. Enter sample weight (grams)
2. Enter flow rate (ml/min)
3. Enter cycle time (minutes)
4. System provides real-time validation warnings

STEP 3: Select Calibration
1. Choose calibration from dropdown menu
2. Use "Suggest Best" for automatic date-based selection
3. Review calibration details (CV%, quality score, date)

STEP 4: Process and Export
1. Click "Process Data" to calculate hydrogen concentrations
2. Review results summary
3. Click "Export Enhanced CSV" to save results

The enhanced CSV includes:
- Complete metadata headers for traceability
- Hydrogen evolution rates (ppm/min)
- Hydrogen per cycle (ppm)
- Cumulative hydrogen totals
- Quality flags and processing information

MODULE 3: DATA VISUALIZATION
----------------------------
This module generates publication-ready plots from processed data.

STEP 1: Load Datasets
1. System automatically scans for enhanced CSV files
2. Select datasets to plot using checkboxes
3. Review dataset information (sample parameters, calibration used)

STEP 2: Configure Plot
1. Choose plot type:
   - "H Evolution Rate" - hydrogen evolution rate vs time
   - "Cumulative H" - cumulative hydrogen vs time
   - "Peak Areas" - raw peak areas vs time
2. Customize dataset styling (colors, line styles, labels)
3. Apply data filtering (outlier removal, smoothing, time ranges)

STEP 3: Format and Export
1. Set plot title and axis labels
2. Configure grid, legend, and formatting options
3. Export to publication formats:
   - PNG (high resolution)
   - PDF (vector graphics)
   - SVG (scalable vector)
   - EPS (publication standard)

WORKFLOW EXAMPLE
================

Complete analysis workflow:

1. CALIBRATION SETUP
   - Process calibration standard data (e.g., 61 ppm H2)
   - Verify CV% < 10% for acceptable quality
   - Add to calibration database

2. EXPERIMENTAL PROCESSING
   - Load experimental TDA data folder
   - Set sample weight (e.g., 0.1234 g)
   - Set flow rate (e.g., 20 ml/min)
   - Set cycle time (e.g., 10 minutes)
   - Select appropriate calibration
   - Process data and export enhanced CSV

3. VISUALIZATION
   - Load processed CSV files
   - Create hydrogen evolution rate plot
   - Compare multiple experiments
   - Export publication-ready figures

DATA REQUIREMENTS
=================

Input Data Format:
- TDA files should be in folders containing either:
  * Summary .txt files (GLPrpt format preferred)
  * Individual .xls run reports
  * .pdf files as fallback

Critical Success Factors:
- Calibration CV% should be < 10% (preferably < 5%)
- Minimum 3 calibration runs (5+ recommended)
- Consistent sample weights and flow rates
- Proper timestamp formatting

HYDROGEN CALCULATION FORMULA
============================

The system uses the exact formula:

H_ppm_per_minute = (peak_area × H_standard_ppm × flow_rate × 0.8928) / (H_standard_peak_area × sample_weight)

Where:
- peak_area: Measured peak area (µV*s)
- H_standard_ppm: Calibration gas concentration (typically 61.0 ppm)
- flow_rate: Gas flow rate (ml/min)
- sample_weight: Sample weight (g)
- H_standard_peak_area: Mean peak area from calibration
- 0.8928: Conversion factor (pre-calculated physical constants)

TROUBLESHOOTING
===============

Common Issues:

1. "Could not load Qt platform plugin"
   - This occurs in headless environments without display
   - Install X11 forwarding or run on system with display

2. "Import Error" on startup
   - Ensure all dependencies are installed: pip install -r requirements.txt
   - Check Python version is 3.8+

3. "High CV% warning" in calibration
   - Review calibration data for outliers
   - Check for instrumental issues
   - Consider removing outlier runs

4. "Missing runs" in experimental data
   - System automatically handles missing runs
   - Review data extraction log for failed runs
   - Check original TDA files for completeness

5. "Invalid peak area" errors
   - Verify peak areas are positive numbers
   - Check for corrupted data files
   - Review extraction log for parsing errors

QUALITY CONTROL
===============

The system implements comprehensive quality control:

Calibration Quality:
- CV% > 10%: ERROR (unacceptable)
- CV% > 5%: WARNING (review recommended)
- N < 3 runs: ERROR (inadequate)
- N < 5 runs: WARNING (insufficient)

Data Processing Quality:
- >50% missing runs: ERROR
- >20% missing runs: WARNING
- Unusual sample parameters: WARNING
- Calibration quality issues: ERROR/WARNING

TECHNICAL SPECIFICATIONS
========================

System Requirements:
- Python 3.8+
- 4GB RAM minimum (8GB recommended)
- 1GB disk space for application
- Display support for GUI (1024x768 minimum)

Performance:
- Handles datasets up to 1000 data points
- Processes calibrations in < 30 seconds
- Generates plots in < 10 seconds
- Exports high-resolution figures

File Structure:
tda_analysis_system/
├── main.py                    # Application entry point
├── requirements.txt           # Dependencies
├── modules/                   # Core processing modules
├── ui/                       # User interface components
├── data/
│   ├── calibrations/         # Calibration database
│   ├── processed_experiments/ # Output CSV files
│   └── config/               # Application settings
└── README.txt                # This file

SUPPORT
=======

For technical support:
1. Check this README for common solutions
2. Review the todo_list.md for detailed implementation notes
3. Examine the CLAUDE.md for development guidance
4. Run test_structure.py to verify system integrity

Version: 1.0
Release Date: 2025
System Type: Scientific data analysis tool for defensive security research

================================================================================