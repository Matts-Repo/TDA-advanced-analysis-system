# MASTER: TDA Analysis System - Complete Specification

## **System Overview**
Create a comprehensive Thermal Desorption Analysis (TDA) system with three integrated modules for hydrogen analysis. The system processes gas chromatograph data from raw files through calibration management to publication-ready plots.

## **Application Architecture**

### **Technology Stack**
- **GUI Framework**: PyQt5/PyQt6 with tabbed interface
- **Data Processing**: pandas, numpy, scipy for data manipulation
- **Plotting**: matplotlib with PyQt integration  
- **File I/O**: openpyxl for Excel files, standard Python for text/CSV
- **Data Storage**: JSON for calibration database, CSV for processed data

### **Project Structure**
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

### **Requirements.txt Generation**
Create requirements.txt with these dependencies:
```
PyQt5>=5.15.0
pandas>=1.3.0
numpy>=1.21.0
matplotlib>=3.5.0
openpyxl>=3.0.9
scipy>=1.7.0
statsmodels>=0.13.0
```

### **Main Application Class**
```python
class TDAAnalysisApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TDA Hydrogen Analysis System")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize managers
        self.calibration_manager = CalibrationManager()
        self.data_processor = DataProcessor(self.calibration_manager)
        self.plot_manager = PlotManager()
        
        # Create tabbed interface
        self.tabs = QTabWidget()
        self.tabs.addTab(CalibrationWidget(self.calibration_manager), "Calibration Management")
        self.tabs.addTab(ProcessingWidget(self.calibration_manager, self.data_processor), "Data Processing") 
        self.tabs.addTab(PlottingWidget(self.plot_manager), "Data Visualization")
        
        self.setCentralWidget(self.tabs)
        
        # Setup menu bar and status bar
        self.setup_menu_bar()
        self.statusBar().showMessage("Ready")
```

## **SHARED DATA STRUCTURES** (Definitive Specifications)

### **Core TDA Data Structure**
```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class TDADataSet:
    """Standard structure for all TDA data across the system"""
    # Identification
    experiment_name: str = ""
    source_file: str = ""
    extraction_timestamp: str = ""
    
    # Raw data arrays (parallel lists - same length)
    run_numbers: List[int] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)      # Format: "MM/DD/YYYY HH:MM:SS"
    peak_areas: List[float] = field(default_factory=list)    # Units: µV*s
    peak_heights: List[float] = field(default_factory=list)  # Units: µV
    
    # Metadata from file parsing
    metadata: Dict = field(default_factory=dict)
    missing_runs: List[int] = field(default_factory=list)    # Run numbers that failed
    
    def validate_data_consistency(self) -> List[str]:
        """Validate that all data arrays have consistent lengths"""
        errors = []
        expected_length = len(self.run_numbers)
        
        if len(self.timestamps) != expected_length:
            errors.append("Timestamp count mismatch")
        if len(self.peak_areas) != expected_length:
            errors.append("Peak area count mismatch") 
        if len(self.peak_heights) != expected_length:
            errors.append("Peak height count mismatch")
            
        return errors
```

### **Calibration Data Structure**
```python
@dataclass
class CalibrationData:
    """Complete calibration data structure used across all modules"""
    # Identification
    calibration_id: str = ""                    # Format: "cal_YYYY-MM-DD_XXX"
    date: str = ""                              # Format: "YYYY-MM-DD"
    processing_timestamp: str = ""              # ISO format when processed
    
    # Gas parameters
    gas_concentration_ppm: float = 61.0         # Standard gas concentration
    
    # Statistical results
    mean_peak_area: float = 0.0
    std_deviation: float = 0.0
    cv_percent: float = 0.0                     # Coefficient of variation
    num_runs: int = 0
    min_peak_area: float = 0.0
    max_peak_area: float = 0.0
    median_peak_area: float = 0.0
    
    # Raw calibration data
    raw_peak_areas: List[float] = field(default_factory=list)
    raw_timestamps: List[str] = field(default_factory=list)
    outlier_indices: List[int] = field(default_factory=list)
    
    # Quality assessment
    quality_flags: List[str] = field(default_factory=list)  # ["high_cv", "low_n", "outliers"]
    quality_score: float = 0.0                              # 0-100 overall quality rating
    is_valid: bool = True
    
    # Metadata
    source_folder: str = ""
    operator: str = "SYSTEM"
    notes: str = ""
    
    def calculate_quality_score(self) -> float:
        """Calculate overall quality score based on CV% and run count"""
        score = 100.0
        
        # Penalize high CV%
        if self.cv_percent > 10:
            score -= 50
        elif self.cv_percent > 5:
            score -= 20
        elif self.cv_percent > 2:
            score -= 10
            
        # Penalize low run count
        if self.num_runs < 5:
            score -= 30
        elif self.num_runs < 8:
            score -= 15
            
        return max(0.0, score)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage"""
        return {
            'calibration_id': self.calibration_id,
            'date': self.date,
            'processing_timestamp': self.processing_timestamp,
            'gas_concentration_ppm': self.gas_concentration_ppm,
            'mean_peak_area': self.mean_peak_area,
            'std_deviation': self.std_deviation,
            'cv_percent': self.cv_percent,
            'num_runs': self.num_runs,
            'min_peak_area': self.min_peak_area,
            'max_peak_area': self.max_peak_area,
            'median_peak_area': self.median_peak_area,
            'raw_peak_areas': self.raw_peak_areas,
            'raw_timestamps': self.raw_timestamps,
            'outlier_indices': self.outlier_indices,
            'quality_flags': self.quality_flags,
            'quality_score': self.quality_score,
            'is_valid': self.is_valid,
            'source_folder': self.source_folder,
            'operator': self.operator,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CalibrationData':
        """Create from dictionary (JSON loading)"""
        return cls(**data)
```

## **SHARED UTILITY: data_extraction.py Specification**

### **Purpose and Scope**
The data_extraction.py module provides unified TDA file parsing for both calibration and experimental data. It handles multiple file formats and returns standardized TDADataSet objects.

### **Supported File Formats**
1. **Summary Files** (.txt format from GLPrpt): Contains all runs in single file
2. **Individual Reports** (.xls format): Separate file per run in folder
3. **PDF Files** (.pdf): As fallback, but prefer .txt when available

### **TDAFileExtractor Class**
```python
class TDAFileExtractor:
    """Unified extractor for all TDA file formats"""
    
    @staticmethod
    def extract_from_folder(folder_path: str) -> TDADataSet:
        """
        Main entry point - auto-detect file type and extract data
        
        Detection Priority:
        1. Look for .txt summary files (GLPrpt format) - PREFERRED
        2. Look for multiple .xls files (individual reports)
        3. Look for .pdf files as fallback
        
        Returns: TDADataSet with all extracted data
        """
        
    @staticmethod
    def extract_from_txt_summary(file_path: str) -> TDADataSet:
        """
        Extract from GLPrpt .txt summary file
        
        Expected format:
        - File contains run table with timestamps
        - Contains "Compound: hydrogen" section  
        - Contains peak area table with run numbers and values
        - May contain missing runs (gaps in run numbers)
        """
        
    @staticmethod
    def extract_from_xls_reports(folder_path: str) -> TDADataSet:
        """
        Extract from multiple .xls individual report files
        
        Expected format:
        - Multiple .xls files in folder (Report01.xls, Report02.xls, etc.)
        - Each file contains single run data
        - Peak area in "Peak" sheet or "IntResults1" sheet
        - Extract run number from filename or file content
        """
        
    @staticmethod
    def parse_timestamp(timestamp_str: str) -> str:
        """
        Standardize timestamp format to "MM/DD/YYYY HH:MM:SS"
        
        Input formats handled:
        - "07/06/2025 15:34:21" (preferred format)
        - "2025-06-07 15:34:21" (ISO format)
        - Other common variations
        
        Returns: Standardized timestamp string
        """
        
    @staticmethod
    def extract_experiment_name(folder_path: str) -> str:
        """
        Extract experiment name from folder path or file names
        
        Priority:
        1. Use folder name if descriptive
        2. Extract from file metadata if available
        3. Generate from timestamp if needed
        """
        
    @staticmethod
    def validate_extracted_data(data: TDADataSet) -> List[str]:
        """
        Validate extracted data quality
        
        Checks:
        - At least some data was extracted
        - Peak areas are positive numbers
        - Timestamps are valid
        - Run numbers are sequential (allowing gaps)
        """
```

### **Timestamp Handling Standard**
```python
class TimestampProcessor:
    """Standardized timestamp handling across all modules"""
    
    STANDARD_FORMAT = "%m/%d/%Y %H:%M:%S"  # "MM/DD/YYYY HH:MM:SS"
    
    @staticmethod
    def parse_to_standard(timestamp_str: str) -> str:
        """Convert any timestamp format to standard format"""
        
    @staticmethod
    def calculate_minutes_from_start(timestamps: List[str]) -> List[float]:
        """
        Convert timestamps to minutes elapsed from first timestamp
        
        Input: List of standardized timestamp strings
        Output: List of float minutes (e.g. [0.0, 5.3, 10.7, ...])
        """
        
    @staticmethod
    def validate_timestamp_sequence(timestamps: List[str]) -> List[str]:
        """Validate timestamp sequence for anomalies"""
```

## **Error Handling Standards**

### **Consistent Error Patterns**
```python
class TDAError(Exception):
    """Base exception for TDA system"""
    pass

class TDAFileError(TDAError):
    """File reading/parsing errors"""
    pass

class TDAValidationError(TDAError):
    """Data validation errors"""
    pass

class TDACalculationError(TDAError):
    """Calculation/processing errors"""
    pass

# Standard error handling pattern for all GUI components
def handle_error_with_user_feedback(parent_widget, operation_name, error):
    """Standardized error handling with user feedback"""
    if isinstance(error, TDAFileError):
        QMessageBox.critical(parent_widget, "File Error", 
                           f"{operation_name} failed: {str(error)}\n\nPlease check the file format and try again.")
    elif isinstance(error, TDAValidationError):
        QMessageBox.warning(parent_widget, "Data Validation", 
                          f"{operation_name} completed with warnings: {str(error)}")
    elif isinstance(error, TDACalculationError):
        QMessageBox.critical(parent_widget, "Calculation Error", 
                           f"{operation_name} failed: {str(error)}\n\nPlease check your parameters and try again.")
    else:
        QMessageBox.critical(parent_widget, "Unexpected Error", 
                           f"{operation_name} failed with unexpected error: {str(error)}")
```

## **Enhanced CSV Format Specification**

### **Complete Enhanced CSV Structure**
```python
def generate_enhanced_csv_header(experiment_data, calibration_data, processing_params):
    """
    Generate standardized CSV header with complete metadata
    
    Example output:
    ```
    # TDA Hydrogen Analysis Results - Generated by TDA Analysis System
    # Generated: 2025-07-07T14:30:15
    # 
    # === EXPERIMENT INFORMATION ===
    # Experiment Name: SS316L_sample_700C_18hours
    # Source Folder: /path/to/experiment/folder
    # Processing Date: 2025-07-07T14:30:15
    # Operator: SYSTEM
    # 
    # === SAMPLE PARAMETERS ===
    # Sample Weight: 5.0 g
    # Flow Rate: 20 ml/min
    # Cycle Time: 5 minutes
    # 
    # === CALIBRATION INFORMATION ===
    # Calibration ID: cal_2025-06-07_001
    # Calibration Date: 2025-06-07
    # Gas Concentration: 61.0 ppm
    # Mean Peak Area: 51250.5 µV*s
    # Standard Deviation: 1075.2 µV*s
    # CV Percentage: 2.1%
    # Quality Score: 95.0/100
    # 
    # === DATA QUALITY SUMMARY ===
    # Total Runs Attempted: 244
    # Successful Runs: 225
    # Failed Runs: 19
    # Missing Run Numbers: 94,98,105,141,148,153,169,183,186,188,200,205,210,211,220,229,235,242
    # Data Quality Score: Good (92% success rate)
    # 
    # === CALCULATED RESULTS SUMMARY ===
    # Total Hydrogen Released: 4.329 ppm
    # Maximum Evolution Rate: 0.1157 ppm/min
    # Average Evolution Rate: 0.0192 ppm/min
    # Experiment Duration: 1329.0 minutes (22.15 hours)
    # 
    # === COLUMN DEFINITIONS ===
    # Run: Sequential run number from GC analysis
    # Timestamp: Date and time of measurement (MM/DD/YYYY HH:MM:SS)
    # Time_minutes: Minutes elapsed from start of experiment
    # Peak_Area_µVs: Raw peak area from chromatograph (µV*s)
    # Peak_Height_µV: Raw peak height from chromatograph (µV)
    # H_ppm_per_min: Calculated hydrogen evolution rate (ppm/min)
    # H_ppm_over_cycle: Hydrogen evolved during this cycle (ppm)
    # Cumulative_H_ppm: Total cumulative hydrogen evolved (ppm)
    # Quality_Flags: Data quality indicators (outlier, low_signal, etc.)
    # 
    Run,Timestamp,Time_minutes,Peak_Area_µVs,Peak_Height_µV,H_ppm_per_min,H_ppm_over_cycle,Cumulative_H_ppm,Quality_Flags
    ```
    """
```

## **Module Development Sequence**

### **Phase 1: Core Infrastructure**
1. **data_extraction.py** - Implement shared TDA file parsing
2. **Shared data structures** - Create TDADataSet and CalibrationData classes
3. **Error handling framework** - Implement consistent error patterns

### **Phase 2: Module Implementation**
4. **Module 1: Calibration Management** - Build calibration processing and GUI
5. **Module 3: Data Processing** - Create experimental data processing with calibration integration  
6. **Module 3: Data Visualization** - Implement plotting GUI with processed data consumption

### **Phase 3: Integration & Testing**
7. **Main application** - Connect all modules with tabbed interface
8. **Cross-module integration** - Ensure seamless data flow
9. **Comprehensive testing** - Validate complete workflow

## **Quality Assurance Requirements**

### **Data Integrity Checks**
- All data arrays must have consistent lengths
- Timestamps must be in chronological order (allowing gaps)
- Peak areas must be positive numbers
- Missing runs must be properly tracked and excluded from calculations

### **User Experience Standards**
- Consistent error messaging across all modules
- Progress indicators for long operations (>2 seconds)
- Real-time validation feedback in forms
- Keyboard shortcuts: Ctrl+O (open), Ctrl+S (save), Ctrl+E (export)

### **Performance Requirements**
- Handle datasets up to 1000 data points efficiently
- Responsive UI during data processing
- Memory-efficient handling of multiple datasets
- Background processing where appropriate

This master specification provides the complete architectural foundation with all shared components, data structures, and standards needed for implementing a robust TDA analysis system. Each module specification builds upon this foundation while maintaining complete consistency and integration.