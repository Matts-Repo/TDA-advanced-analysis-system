# TDA Analysis System - Complete Implementation TODO List

This file contains the complete implementation plan for the TDA (Thermal Desorption Analysis) system based on all specification documents. Use this as the single source of truth for implementation.

## PROJECT OVERVIEW

**Objective**: Build a comprehensive Thermal Desorption Analysis (TDA) system with three integrated modules for hydrogen analysis using PyQt5, processing gas chromatograph data from raw files through calibration management to publication-ready plots.

**Key Success Criteria**: User can process calibration data, convert experimental TDA data to hydrogen concentrations using selected calibrations, and generate publication-ready plots comparing multiple experiments - all with complete data traceability and quality validation.

## IMPLEMENTATION PHASES

### PHASE 1: CORE INFRASTRUCTURE (IMPLEMENT FIRST)

#### 1.1 Project Structure Setup
- [ ] Create main project directory: `tda_analysis_system/`
- [ ] Create `main.py` (application entry point)
- [ ] Create `modules/` directory with `__init__.py`
- [ ] Create `ui/` directory with `__init__.py`
- [ ] Create `data/` directory structure:
  - [ ] `data/calibrations/` (calibration database & files)
  - [ ] `data/processed_experiments/` (CSV outputs)
  - [ ] `data/config/` (application settings)
- [ ] Create `requirements.txt` with exact dependencies:
  ```
  PyQt5>=5.15.0
  pandas>=1.3.0
  numpy>=1.21.0
  matplotlib>=3.5.0
  openpyxl>=3.0.9
  scipy>=1.7.0
  statsmodels>=0.13.0
  ```

#### 1.2 Shared Data Structures (CRITICAL - Required by all modules)
- [ ] Create `TDADataSet` dataclass with EXACT fields:
  - [ ] experiment_name: str
  - [ ] source_file: str  
  - [ ] extraction_timestamp: str
  - [ ] run_numbers: List[int]
  - [ ] timestamps: List[str] (format: "MM/DD/YYYY HH:MM:SS")
  - [ ] peak_areas: List[float] (units: µV*s)
  - [ ] peak_heights: List[float] (units: µV)
  - [ ] metadata: Dict
  - [ ] missing_runs: List[int]
- [ ] Implement `validate_data_consistency()` method for TDADataSet
- [ ] Create `CalibrationData` dataclass with EXACT fields:
  - [ ] calibration_id: str (format: "cal_YYYY-MM-DD_XXX")
  - [ ] date: str (format: "YYYY-MM-DD")
  - [ ] processing_timestamp: str (ISO format)
  - [ ] gas_concentration_ppm: float (default: 61.0)
  - [ ] mean_peak_area, std_deviation, cv_percent: float
  - [ ] num_runs, min_peak_area, max_peak_area, median_peak_area: float/int
  - [ ] raw_peak_areas, raw_timestamps: List[float/str]
  - [ ] outlier_indices: List[int]
  - [ ] quality_flags: List[str]
  - [ ] quality_score: float (0-100)
  - [ ] is_valid: bool
  - [ ] source_folder, operator, notes: str
- [ ] Implement `calculate_quality_score()` method for CalibrationData
- [ ] Implement `to_dict()` and `from_dict()` methods for CalibrationData

#### 1.3 Error Handling Framework
- [ ] Create base exception class: `TDAError(Exception)`
- [ ] Create specific exceptions:
  - [ ] `TDAFileError(TDAError)` - file reading/parsing errors
  - [ ] `TDAValidationError(TDAError)` - data validation errors  
  - [ ] `TDACalculationError(TDAError)` - calculation/processing errors
- [ ] Implement `handle_error_with_user_feedback(parent_widget, operation_name, error)` function
- [ ] Ensure consistent error handling patterns across all GUI components

#### 1.4 Data Extraction Module (CRITICAL - Must implement first)
- [ ] Create `modules/data_extraction.py`
- [ ] Implement `TDAFileExtractor` class with methods:
  - [ ] `extract_from_folder(folder_path)` - main entry point with auto-detection
  - [ ] `extract_from_txt_summary(file_path)` - GLPrpt .txt format (PREFERRED)
  - [ ] `extract_from_xls_reports(folder_path)` - individual .xls files
  - [ ] `parse_timestamp(timestamp_str)` - standardize to "MM/DD/YYYY HH:MM:SS"
  - [ ] `extract_experiment_name(folder_path)` - generate experiment name
  - [ ] `validate_extracted_data(data)` - quality validation
- [ ] File format support priorities:
  - [ ] 1st priority: .txt summary files (GLPrpt format)
  - [ ] 2nd priority: Multiple .xls files (individual reports)
  - [ ] 3rd priority: .pdf files (fallback)
- [ ] Implement `TimestampProcessor` class with methods:
  - [ ] `parse_to_standard(timestamp_str)` - convert any format to standard
  - [ ] `calculate_minutes_from_start(timestamps)` - time series calculation
  - [ ] `validate_timestamp_sequence(timestamps)` - check for anomalies
- [ ] Ensure proper handling of missing runs (skip entirely, don't set to zero)
- [ ] Standard timestamp format: "MM/DD/YYYY HH:MM:SS"

### PHASE 2: MODULE IMPLEMENTATION

#### 2.1 Module 1: Calibration Management
- [ ] Create `modules/calibration_manager.py`
- [ ] Implement `CalibrationManager` class with methods:
  - [ ] `__init__(calibration_folder="./data/calibrations/")`
  - [ ] `load_database()` - load calibrations from JSON
  - [ ] `save_database()` - save calibrations to JSON  
  - [ ] `process_calibration_folder(folder_path, gas_ppm, cal_name)` - main processing
  - [ ] `calculate_calibration_stats(peak_areas)` - comprehensive statistics
  - [ ] `validate_calibration_quality(cal_data)` - quality checks
  - [ ] `get_calibrations_by_date_range(start_date, end_date)`
  - [ ] `suggest_calibration_for_date(target_date)` - smart suggestions
  - [ ] `get_calibration(calibration_id)`, `get_recent_calibrations(limit)`
  - [ ] `delete_calibration(calibration_id)`
- [ ] Statistics calculations:
  - [ ] Mean, standard deviation, CV% (coefficient of variation)
  - [ ] Min, max, median peak areas
  - [ ] Outlier detection using Z-score method (threshold: 3.0)
- [ ] Quality validation rules:
  - [ ] CV% > 10%: ERROR (unacceptable calibration)
  - [ ] CV% > 5%: WARNING (unstable calibration)
  - [ ] N < 3 runs: ERROR (inadequate calibration)
  - [ ] N < 5 runs: WARNING (insufficient data)
  - [ ] >20% outliers: WARNING
- [ ] Calibration ID format: "cal_YYYY-MM-DD_XXX" (auto-generate)
- [ ] Individual calibration storage:
  - [ ] Create folder per calibration: `./data/calibrations/{cal_id}/`
  - [ ] Save detailed JSON report: `calibration_report.json`
  - [ ] Save processed CSV: `processed_data.csv`
- [ ] JSON database structure:
  ```json
  {
    "database_version": "1.0",
    "last_updated": "[ISO timestamp]",
    "calibrations": {
      "cal_YYYY-MM-DD_XXX": { /* CalibrationData.to_dict() */ }
    }
  }
  ```

#### 2.2 Module 1: Calibration GUI
- [ ] Create `ui/calibration_widget.py`
- [ ] Implement `CalibrationWidget(QWidget)` with three-section layout:
  - [ ] **Section 1: Process New Calibration**
    - [ ] Folder path selection with browse button
    - [ ] Gas concentration input (default: 61.0 ppm)
    - [ ] Optional custom calibration name
    - [ ] Preview data button
    - [ ] Process calibration button (green, bold)
  - [ ] **Section 2: Calibration Database**
    - [ ] Search/filter controls (by name, date, quality)
    - [ ] Quality filter dropdown: "All", "Valid Only", "High Quality (>80)", "Needs Review"
    - [ ] Calibration table with columns: Date, ID, Mean Peak Area, CV%, Runs, Quality, Status
    - [ ] Color-coded cells (CV%: red >10%, yellow >5%, green ≤5%)
    - [ ] Action buttons: View Details, Export, Delete, Set as Default
  - [ ] **Section 3: Calibration Details**
    - [ ] Statistics display area
    - [ ] Quality flags text area
    - [ ] Action buttons: Plot Raw Data, View Statistics, Export CSV
    - [ ] Mini plot widget (optional)
- [ ] Implement dialog classes:
  - [ ] `CalibrationResultDialog` - show processing results
  - [ ] `CalibrationPreviewDialog` - preview data before processing
  - [ ] `DetailedStatisticsDialog` - comprehensive statistics view

#### 2.3 Module 2: Data Processing Core
- [ ] Create `modules/data_processor.py`
- [ ] Implement `ExperimentData` dataclass with fields:
  - [ ] experiment_name, source_folder, extraction_timestamp: str
  - [ ] run_numbers: List[int], timestamps: List[str]
  - [ ] peak_areas, peak_heights, time_minutes: List[float]
  - [ ] sample_weight, flow_rate, cycle_time: float
  - [ ] calibration_id: str
  - [ ] h_ppm_per_min, h_ppm_over_cycle, cumulative_h_ppm: List[float]
  - [ ] missing_runs, quality_flags, processing_warnings: List
- [ ] Implement `validate_data_consistency()` method for ExperimentData
- [ ] Implement `get_summary_statistics()` method for ExperimentData

#### 2.4 Module 2: Hydrogen Calculator
- [ ] Implement `HydrogenCalculator` class with methods:
  - [ ] `__init__()` - set physical constants
  - [ ] `calculate_h_ppm_per_minute(peak_area, calibration_data, flow_rate, sample_weight)`
  - [ ] `calculate_h_ppm_over_cycle(h_ppm_per_min, cycle_time)`
  - [ ] `calculate_cumulative_hydrogen(h_ppm_over_cycle_list)`
  - [ ] `validate_calculation_inputs()` - input validation
- [ ] **EXACT FORMULA IMPLEMENTATION**:
  ```
  H_ppm_per_minute = (peak_area × H_standard_ppm × flow_rate × 0.8928) / (H_standard_peak_area × sample_weight)
  ```
- [ ] Physical constants:
  - [ ] CARRIER_GAS_MOL_PER_SEC = 7.44e-6 (for Argon)
  - [ ] MOLAR_WEIGHT_H2 = 2.0 (g/mol)
  - [ ] CONVERSION_FACTOR = 0.8928 (pre-calculated)
- [ ] Input validation warnings/errors:
  - [ ] Peak area ≤ 0: ERROR
  - [ ] Sample weight ≤ 0: ERROR  
  - [ ] Flow rate ≤ 0: ERROR
  - [ ] Very low peak area < 100: WARNING
  - [ ] Very high peak area > 1000000: WARNING

#### 2.5 Module 2: Data Processor
- [ ] Implement `DataProcessor` class with methods:
  - [ ] `__init__(calibration_manager, output_folder="./data/processed_experiments/")`
  - [ ] `load_experiment_data(folder_path)` - use shared extraction
  - [ ] `preview_experiment_data(folder_path, num_rows)` - GUI preview
  - [ ] `select_calibration(calibration_id)` - load calibration
  - [ ] `calculate_hydrogen_concentrations(experiment_data, calibration, parameters)`
  - [ ] `generate_enhanced_csv(processed_data, output_path)` - with metadata
  - [ ] `validate_processing_inputs()` - comprehensive validation
  - [ ] `validate_processing_results()` - result validation
- [ ] Enhanced CSV format with EXACT header sections:
  ```
  # TDA Hydrogen Analysis Results - Generated by TDA Analysis System
  # Generated: [ISO timestamp]
  # === EXPERIMENT INFORMATION ===
  # === SAMPLE PARAMETERS ===
  # === CALIBRATION INFORMATION ===
  # === DATA QUALITY SUMMARY ===
  # === CALCULATED RESULTS SUMMARY ===
  # === COLUMN DEFINITIONS ===
  Run,Timestamp,Time_minutes,Peak_Area_µVs,Peak_Height_µV,H_ppm_per_min,H_ppm_over_cycle,Cumulative_H_ppm,Quality_Flags
  ```
- [ ] Validation rules:
  - [ ] >50% missing runs: ERROR
  - [ ] >20% missing runs: WARNING
  - [ ] Calibration CV% > 15%: ERROR
  - [ ] Calibration CV% > 10%: WARNING
  - [ ] Unusual sample weights, flow rates, cycle times: WARNING

#### 2.6 Module 2: Processing GUI
- [ ] Create `ui/processing_widget.py`
- [ ] Implement `ProcessingWidget(QWidget)` with four-section layout:
  - [ ] **Section 1: Load Experiment Data**
    - [ ] Folder selection with browse button
    - [ ] Preview data button and display area
    - [ ] Data summary (total runs, missing runs, date range)
  - [ ] **Section 2: Processing Parameters**
    - [ ] Sample weight input (grams)
    - [ ] Flow rate input (ml/min)
    - [ ] Cycle time input (minutes)
    - [ ] Real-time validation with warning/error indicators
  - [ ] **Section 3: Calibration Selection**
    - [ ] Interactive calibration dropdown
    - [ ] Date-based suggestions
    - [ ] Calibration details display (CV%, quality score, date)
    - [ ] "Suggest Best" button for automatic selection
  - [ ] **Section 4: Processing and Export**
    - [ ] Process data button (green, bold)
    - [ ] Progress indicator
    - [ ] Results summary display
    - [ ] Export enhanced CSV button

#### 2.7 Module 3: Plot Data Structures
- [ ] Create `modules/plot_manager.py`
- [ ] Implement data classes:
  - [ ] `PlotDataset` - complete dataset with metadata
  - [ ] `DatasetStyle` - styling options (color, linestyle, etc.)
  - [ ] `FilterOptions` - data filtering settings
  - [ ] `PlotOptions` - plot formatting options
  - [ ] `ExportOptions` - export configuration
- [ ] `PlotDataset` fields:
  - [ ] File info: name, csv_path
  - [ ] Experiment metadata: experiment_name, processing_date
  - [ ] Sample parameters: sample_weight, flow_rate, cycle_time
  - [ ] Calibration info: calibration_id, calibration_date, calibration_quality
  - [ ] Summary stats: total_hydrogen, max_rate, avg_rate, duration_hours
  - [ ] Data arrays: all parallel lists from enhanced CSV
  - [ ] Plotting config: style, filter_options

#### 2.8 Module 3: CSV Parser
- [ ] Implement `ProcessedCSVParser` class with methods:
  - [ ] `parse_csv_file(csv_path)` - main parsing method
  - [ ] `parse_metadata_header(csv_path)` - extract metadata from comments
- [ ] Parse enhanced CSV metadata sections:
  - [ ] Extract experiment information
  - [ ] Extract sample parameters  
  - [ ] Extract calibration information
  - [ ] Extract summary statistics
- [ ] Validate CSV format:
  - [ ] Check for TDA header signature
  - [ ] Validate required columns
  - [ ] Handle missing optional columns
- [ ] Return complete `PlotDataset` object

#### 2.9 Module 3: Data Filtering
- [ ] Implement `DataFilter` class with methods:
  - [ ] `apply_all_filters(dataset, plot_type)` - main filter pipeline
  - [ ] `remove_outliers(x_data, y_data, method, threshold)` - outlier removal
  - [ ] `apply_smoothing(y_data, method, window)` - data smoothing
  - [ ] `filter_time_range(x_data, y_data, start, end)` - time filtering
  - [ ] `filter_value_range(x_data, y_data, min_val, max_val)` - value filtering
- [ ] Outlier removal methods:
  - [ ] Z-score method (threshold: 3.0)
  - [ ] IQR method with multiplier
- [ ] Smoothing methods:
  - [ ] Moving average
  - [ ] Savitzky-Golay filter (if scipy available)
  - [ ] LOWESS smoothing (if statsmodels available)

#### 2.10 Module 3: Plot Generation
- [ ] Implement `PlotGenerator` class with methods:
  - [ ] `create_time_series_plot(datasets, plot_type, options)` - main plotting
  - [ ] `_apply_plot_formatting(options, default_ylabel)` - professional formatting
  - [ ] `update_dataset_style(dataset)` - real-time style updates
- [ ] Support plot types:
  - [ ] "h_ppm_per_min" vs time (hydrogen evolution rate)
  - [ ] "cumulative_h_ppm" vs time (cumulative hydrogen)
  - [ ] "peak_areas" vs time (raw peak areas)
- [ ] Professional styling:
  - [ ] Color palette with 10 distinct colors
  - [ ] Multiple line styles: '-', '--', '-.', ':'
  - [ ] Grid, legend, axis labels
  - [ ] Remove top/right spines (despine)
  - [ ] Proper axis limits and scaling
- [ ] Multi-dataset support with automatic styling

#### 2.11 Module 3: Plot Manager
- [ ] Implement `PlotManager` class with methods:
  - [ ] `__init__(processed_data_folder="./data/processed_experiments/")`
  - [ ] `scan_for_datasets()` - find processed CSV files
  - [ ] `load_dataset(csv_path)` - load and parse dataset
  - [ ] `generate_plot(datasets, plot_type, options)` - create figure
  - [ ] `export_plot(figure, export_options)` - save to file
- [ ] Dataset management:
  - [ ] Auto-scan for valid TDA CSV files
  - [ ] Validate CSV format before loading
  - [ ] Sort by modification date
  - [ ] Track available and selected datasets
- [ ] Export formats: PNG, PDF, SVG, EPS with publication settings

#### 2.12 Module 3: Plotting GUI
- [ ] Create `ui/plotting_widget.py`
- [ ] Implement `PlottingWidget(QWidget)` with split-panel layout:
  - [ ] **Left Panel: Controls**
    - [ ] Dataset selection area with checkboxes
    - [ ] Plot type dropdown ("H Evolution Rate", "Cumulative H", "Peak Areas")
    - [ ] Dataset styling controls (color picker, line style, labels)
    - [ ] Data filtering options (outliers, smoothing, range filters)
    - [ ] Plot formatting options (title, axis labels, grid, legend)
    - [ ] Export settings and buttons
  - [ ] **Right Panel: Plot Display**
    - [ ] Matplotlib canvas with zoom/pan tools
    - [ ] Real-time plot updates
    - [ ] Professional formatting
- [ ] Interactive features:
  - [ ] Real-time style updates
  - [ ] Dataset enable/disable
  - [ ] Filter preview
  - [ ] Export preview

### PHASE 3: MAIN APPLICATION INTEGRATION

#### 3.1 Main Application Window
- [ ] Create `main.py` application entry point
- [ ] Implement `TDAAnalysisApp(QMainWindow)` class:
  - [ ] `__init__()` - window setup (1400x900)
  - [ ] Initialize managers: CalibrationManager, DataProcessor, PlotManager
  - [ ] Create tabbed interface with three tabs:
    - [ ] "Calibration Management" - CalibrationWidget
    - [ ] "Data Processing" - ProcessingWidget  
    - [ ] "Data Visualization" - PlottingWidget
  - [ ] `setup_menu_bar()` - File, Edit, View, Help menus
  - [ ] Status bar with ready message
- [ ] Cross-module integration:
  - [ ] Pass calibration_manager to data_processor
  - [ ] Ensure seamless data flow between modules
  - [ ] Shared error handling

#### 3.2 Application Features
- [ ] Menu bar implementation:
  - [ ] File: New, Open, Save, Export, Exit
  - [ ] Edit: Preferences, Clear Cache
  - [ ] View: Toggle sections, Refresh
  - [ ] Help: About, Documentation
- [ ] Keyboard shortcuts:
  - [ ] Ctrl+O: Open folder
  - [ ] Ctrl+S: Save/Export
  - [ ] Ctrl+E: Export data
- [ ] Status bar updates for long operations
- [ ] Progress dialogs for operations > 2 seconds
- [ ] Application icon and window title

#### 3.3 Final Integration Testing
- [ ] Complete workflow testing:
  - [ ] Process calibration data → Calibration database
  - [ ] Load experimental data → Select calibration → Process → Enhanced CSV
  - [ ] Load enhanced CSV → Generate plots → Export figures
- [ ] Data consistency validation across all modules
- [ ] Error handling consistency
- [ ] GUI responsiveness during processing
- [ ] File format compatibility verification

## CRITICAL IMPLEMENTATION REQUIREMENTS

### Data Flow Validation
- [ ] **Calibration Processing**: Raw TDA folder → data_extraction.py → Statistics → JSON database in ./data/calibrations/
- [ ] **Experimental Processing**: Raw TDA folder → data_extraction.py → Calibration selection → Hydrogen calculation → Enhanced CSV in ./data/processed_experiments/
- [ ] **Visualization**: Enhanced CSV → Metadata parsing → Multi-dataset plotting → Professional export

### Quality Assurance Checklist
- [ ] All data arrays have consistent lengths
- [ ] Missing runs properly tracked and excluded (not set to zero)
- [ ] Timestamps in chronological order  
- [ ] Peak areas are positive numbers
- [ ] CV% validation rules implemented correctly
- [ ] Run count validation implemented
- [ ] Outlier detection using Z-score method
- [ ] Quality score calculation (0-100 scale)
- [ ] Consistent error messaging across modules
- [ ] Progress indicators for operations > 2 seconds
- [ ] Real-time validation feedback in forms

### File Format Compliance
- [ ] TDA file extraction supports .txt (preferred), .xls, .pdf formats
- [ ] Timestamp standardization to "MM/DD/YYYY HH:MM:SS"
- [ ] Enhanced CSV header with all required sections
- [ ] JSON calibration database with correct structure
- [ ] Export formats: PNG, PDF, SVG, EPS with proper settings

### Integration Points
- [ ] Calibration manager accessible from processing module
- [ ] Enhanced CSV format consumable by plotting module  
- [ ] Shared data structures used consistently
- [ ] Error handling consistent across modules
- [ ] Progress feedback consistent across modules

## TESTING STRATEGY

### Module 1 Testing
- [ ] Process calibration folder with summary .txt file
- [ ] Process calibration folder with individual .xls files
- [ ] Calculate statistics correctly (mean, std dev, CV%, outliers)
- [ ] Validate quality assessment rules
- [ ] Save/load calibration database integrity
- [ ] Test GUI interactions and error handling

### Module 2 Testing  
- [ ] Load experimental data from folder
- [ ] Select and apply calibration correctly
- [ ] Calculate hydrogen concentrations with exact formula
- [ ] Generate enhanced CSV with complete metadata
- [ ] Handle missing runs correctly (skip, don't zero)
- [ ] Validate input parameters and show appropriate errors
- [ ] Test GUI workflow and progress indicators

### Module 3 Testing
- [ ] Load enhanced CSV files from Module 2
- [ ] Parse metadata correctly from CSV headers
- [ ] Generate both plot types (rate and cumulative)
- [ ] Apply data filtering (outliers, smoothing, ranges)
- [ ] Export to multiple formats with correct settings
- [ ] Test multi-dataset plotting and styling
- [ ] Validate GUI controls and real-time updates

### Integration Testing
- [ ] Complete end-to-end workflow
- [ ] Data consistency across all modules
- [ ] Error propagation and handling
- [ ] GUI responsiveness and user feedback
- [ ] File format compatibility
- [ ] Performance with large datasets (up to 1000 data points)

## PERFORMANCE REQUIREMENTS
- [ ] Handle datasets up to 1000 data points efficiently
- [ ] Responsive UI during data processing
- [ ] Memory-efficient handling of multiple datasets
- [ ] Background processing for operations > 2 seconds
- [ ] Efficient file I/O with proper error handling

## SUCCESS CRITERIA
✅ **Final System Capabilities**:
1. Complete calibration management with quality assessment
2. Accurate hydrogen concentration calculations with full traceability
3. Professional data visualization with publication-ready export  
4. Seamless integration between all three modules
5. Robust error handling and user feedback
6. Professional GUI matching layout specifications

The system should enable users to process calibration data, convert experimental TDA data to hydrogen concentrations using selected calibrations, and generate publication-ready plots comparing multiple experiments - all with complete data traceability and quality validation.