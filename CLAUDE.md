# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **TDA (Thermal Desorption Analysis) System** for hydrogen analysis - a comprehensive PyQt5-based application for processing gas chromatograph data from raw files through calibration management to publication-ready plots.

## Project Status

This repository contains **detailed specification documents** but **no implemented code yet**. The project is in the design/specification phase with complete implementation guides for three integrated modules:

1. **Module 1: Calibration Management** - Process hydrogen calibration standard data
2. **Module 2: Data Processing** - Convert raw experimental TDA data to hydrogen concentrations  
3. **Module 3: Data Visualization** - Generate publication-ready plots with extensive customization

## Architecture Overview

### Technology Stack
- **GUI Framework**: PyQt5/PyQt6 with tabbed interface
- **Data Processing**: pandas, numpy, scipy for data manipulation
- **Plotting**: matplotlib with PyQt integration
- **File I/O**: openpyxl for Excel files, standard Python for text/CSV
- **Data Storage**: JSON for calibration database, CSV for processed data

### Intended Project Structure
```
tda_analysis_system/
├── main.py                      # Application entry point & main window
├── modules/
│   ├── __init__.py
│   ├── calibration_manager.py   # Module 1: Calibration processing
│   ├── data_processor.py        # Module 2: Experimental data processing  
│   ├── plot_manager.py          # Module 3: Data visualization
│   └── data_extraction.py       # SHARED: TDA file parsing utilities
├── data/
│   ├── calibrations/            # Calibration database & files
│   ├── processed_experiments/   # Output CSV files
│   └── config/                  # Application settings
├── ui/
│   ├── calibration_widget.py    # GUI for calibration management
│   ├── processing_widget.py     # GUI for data processing
│   └── plotting_widget.py       # GUI for visualization
└── requirements.txt             # All dependencies
```

### Dependencies (requirements.txt)
```
PyQt5>=5.15.0
pandas>=1.3.0
numpy>=1.21.0
matplotlib>=3.5.0
openpyxl>=3.0.9
scipy>=1.7.0
statsmodels>=0.13.0
```

## Development Commands

**Note**: No build/test commands are currently defined as the project is in specification phase.

When implementation begins:
- Run application: `python main.py`
- Install dependencies: `pip install -r requirements.txt`

## Core Data Structures

### TDADataSet
Standard structure for all TDA data across the system with validation methods.

### CalibrationData  
Complete calibration data structure used across all modules with quality assessment.

## Key Implementation Requirements

### Critical Success Factors
1. **data_extraction.py MUST be implemented first** - all modules depend on it
2. **Exact formula implementation** for hydrogen calculations:
   ```
   H_ppm_per_minute = (peak_area × H_standard_ppm × flow_rate × 0.8928) / (H_standard_peak_area × sample_weight)
   ```
3. **Complete metadata preservation** through CSV headers
4. **Proper missing run handling** (skip, don't zero)
5. **Timestamp standardization** to "MM/DD/YYYY HH:MM:SS" format

### Data Flow
1. **Calibration**: Raw TDA folder → data_extraction.py → Statistics → JSON database
2. **Processing**: Raw TDA folder → data_extraction.py → Calibration selection → Hydrogen calculation → Enhanced CSV  
3. **Visualization**: Enhanced CSV → Metadata parsing → Multi-dataset plotting → Professional export

### File Formats
- **Input**: .txt summary files (GLPrpt format preferred), .xls individual reports, .pdf fallback
- **Calibration Storage**: JSON database with individual calibration folders
- **Output**: Enhanced CSV with complete metadata headers for traceability

## Error Handling
Uses consistent exception hierarchy:
- `TDAError` (base)
- `TDAFileError` (file reading/parsing)  
- `TDAValidationError` (data validation)
- `TDACalculationError` (calculation/processing)

## Development Notes

- This is a **defensive security application** for scientific data analysis
- Focus on **data integrity** and **complete traceability**
- All GUI layouts have detailed ASCII art specifications in the module files
- **Quality validation** is critical - CV% limits, run count validation, outlier detection
- Professional export capabilities for publication-ready figures

## Implementation Sequence

1. **Phase 1**: Core infrastructure (data_extraction.py, shared structures, error handling)
2. **Phase 2**: Module implementation (calibration → processing → visualization)  
3. **Phase 3**: Main application integration and testing

Refer to the individual module specification files for detailed implementation requirements.