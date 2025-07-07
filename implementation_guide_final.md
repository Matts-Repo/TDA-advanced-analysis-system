# COMPLETE IMPLEMENTATION GUIDE - TDA Analysis System

## **IMPLEMENTATION INSTRUCTIONS FOR CLAUDE CODE**

**OBJECTIVE**: Build a complete Thermal Desorption Analysis (TDA) system with three integrated modules for hydrogen analysis, following the exact specifications provided.

## **IMPLEMENTATION SEQUENCE**

### **Phase 1: Core Infrastructure (Implement First)**

#### **1.1 Project Setup**
```bash
# Create project structure exactly as specified
tda_analysis_system/
├── main.py                      # Main application entry point
├── modules/
│   ├── __init__.py
│   ├── data_extraction.py       # CRITICAL: Implement first - shared by all modules
│   ├── calibration_manager.py   # Module 1
│   ├── data_processor.py        # Module 2  
│   ├── plot_manager.py          # Module 3
├── ui/
│   ├── __init__.py
│   ├── calibration_widget.py
│   ├── processing_widget.py
│   └── plotting_widget.py
├── data/
│   ├── calibrations/            # Separate calibration storage
│   ├── processed_experiments/   # CSV outputs
│   └── config/
└── requirements.txt
```

#### **1.2 Generate requirements.txt**
```
PyQt5>=5.15.0
pandas>=1.3.0
numpy>=1.21.0
matplotlib>=3.5.0
openpyxl>=3.0.9
scipy>=1.7.0
statsmodels>=0.13.0
```

#### **1.3 Implement Shared Data Structures**
- Create **exactly** the `TDADataSet` and `CalibrationData` classes from the master specification
- Include **all** methods: `validate_data_consistency()`, `calculate_quality_score()`, `to_dict()`, `from_dict()`
- Use **exact** field names and types as specified

#### **1.4 Implement Error Handling Framework**
```python
class TDAError(Exception): pass
class TDAFileError(TDAError): pass  
class TDAValidationError(TDAError): pass
class TDACalculationError(TDAError): pass

def handle_error_with_user_feedback(parent_widget, operation_name, error):
    # Implement exactly as specified in master document
```

#### **1.5 Implement data_extraction.py (CRITICAL - Required by all modules)**
**This is the most important shared component. Implement:**
- `TDAFileExtractor` class with **all** specified methods
- `TimestampProcessor` class for **standardized** timestamp handling  
- Support for **.txt summary files** (GLPrpt format) - **PREFERRED**
- Support for **.xls individual reports** as fallback
- **Exact** timestamp format: "MM/DD/YYYY HH:MM:SS"
- **Proper** handling of missing runs (skip entirely, don't set to zero)

### **Phase 2: Module Implementation**

#### **2.1 Module 1: Calibration Management**
**Requirements:**
- Store calibrations in **separate folder** (`./data/calibrations/`)
- Implement **complete** `CalibrationManager` class with all specified methods
- Generate **unique calibration IDs**: "cal_YYYY-MM-DD_XXX" format
- Calculate **comprehensive statistics**: mean, std dev, CV%, outliers
- Implement **quality validation** with specific CV% and run count rules
- Create **CalibrationWidget** with **exact** three-section layout from ASCII art
- Save **individual calibration folders** with JSON reports and CSV data

#### **2.2 Module 2: Data Processing**  
**Requirements:**
- Implement **complete** `DataProcessor` class with all specified methods
- Implement **HydrogenCalculator** with **exact formula**: 
  ```
  H_ppm_per_minute = (peak_area × H_standard_ppm × flow_rate × 0.8928) / (H_standard_peak_area × sample_weight)
  ```
- Generate **enhanced CSV** with **complete metadata header** as specified
- Use `TimestampProcessor.calculate_minutes_from_start()` for time series
- Implement **ProcessingWidget** with **exact** four-section layout
- **Interactive calibration selection** with date-based suggestions
- **Comprehensive validation** at all processing stages

#### **2.3 Module 3: Data Visualization**
**Requirements:**
- Implement **complete** `PlotManager` class  
- Parse **enhanced CSV files** from Module 2 using `ProcessedCSVParser`
- Support **two plot types**: "h_ppm_per_min" vs time, "cumulative_h_ppm" vs time
- Implement **data filtering**: outlier removal, smoothing, time range filtering
- Create **PlottingWidget** with **exact** split-panel layout from ASCII art
- **Per-dataset styling**: color picker, line style, custom labels
- **Professional export**: PNG, PDF, SVG with publication settings

### **Phase 3: Main Application Integration**

#### **3.1 Main Application Window**
- Implement **TDAAnalysisApp** class as specified
- Create **tabbed interface** with three tabs
- Connect all modules through shared managers
- Implement **menu bar** and **status bar**

#### **3.2 GUI Implementation Requirements**
- Use **PyQt5/PyQt6** as specified
- Implement **exact layouts** from ASCII art diagrams
- Use **consistent error handling** across all widgets
- Implement **progress dialogs** for long operations
- Add **keyboard shortcuts**: Ctrl+O, Ctrl+S, Ctrl+E

## **CRITICAL IMPLEMENTATION DETAILS**

### **Data Flow Requirements**
1. **Calibration Processing**: Raw TDA folder → `data_extraction.py` → Statistics → JSON database in `./data/calibrations/`
2. **Experimental Processing**: Raw TDA folder → `data_extraction.py` → Calibration selection → Hydrogen calculation → Enhanced CSV in `./data/processed_experiments/`  
3. **Visualization**: Enhanced CSV → Metadata parsing → Multi-dataset plotting → Professional export

### **File Format Specifications**

#### **Enhanced CSV Header (Module 2 Output)**
Must include **exactly** these sections:
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

#### **Calibration Database JSON Structure**
```json
{
  "database_version": "1.0",
  "last_updated": "[ISO timestamp]", 
  "calibrations": {
    "cal_YYYY-MM-DD_XXX": { /* CalibrationData.to_dict() */ }
  }
}
```

### **Timestamp Processing Standard**
- **Input formats**: Handle "MM/DD/YYYY HH:MM:SS" and "YYYY-MM-DD HH:MM:SS"
- **Standard format**: Convert all to "MM/DD/YYYY HH:MM:SS"
- **Time calculations**: Use `TimestampProcessor.calculate_minutes_from_start()` 
- **Missing runs**: Skip entirely in time calculations (don't set to zero)

### **Quality Assurance Checklist**

#### **Data Integrity**
- [ ] All data arrays have consistent lengths
- [ ] Missing runs properly tracked and excluded
- [ ] Timestamps in chronological order
- [ ] Peak areas are positive numbers

#### **Calibration Quality**
- [ ] CV% validation rules implemented (>10% = error, >5% = warning)
- [ ] Run count validation (< 3 = error, < 5 = warning)  
- [ ] Outlier detection using Z-score method
- [ ] Quality score calculation (0-100 scale)

#### **User Experience**
- [ ] Consistent error messaging across modules
- [ ] Progress indicators for operations > 2 seconds
- [ ] Real-time validation in forms
- [ ] ASCII art layouts implemented exactly

#### **Integration Points**
- [ ] Calibration manager accessible from processing module
- [ ] Enhanced CSV format consumable by plotting module
- [ ] Shared data structures used consistently
- [ ] Error handling consistent across modules

## **TESTING REQUIREMENTS**

### **Module 1 Testing**
- [ ] Process calibration folder with summary .txt file
- [ ] Process calibration folder with individual .xls files  
- [ ] Calculate statistics correctly
- [ ] Validate quality assessment
- [ ] Save/load calibration database

### **Module 2 Testing**  
- [ ] Load experimental data from folder
- [ ] Select and apply calibration
- [ ] Calculate hydrogen concentrations with exact formula
- [ ] Generate enhanced CSV with complete metadata
- [ ] Handle missing runs correctly

### **Module 3 Testing**
- [ ] Load enhanced CSV files  
- [ ] Parse metadata correctly
- [ ] Generate both plot types
- [ ] Apply data filtering  
- [ ] Export to multiple formats

### **Integration Testing**
- [ ] Complete workflow: Calibration → Processing → Plotting
- [ ] Data consistency across all modules
- [ ] GUI responsiveness and error handling
- [ ] File format compatibility

## **IMPLEMENTATION NOTES**

### **Critical Success Factors**
1. **data_extraction.py MUST be implemented first** - all modules depend on it
2. **Exact formula implementation** for hydrogen calculations
3. **Complete metadata preservation** through CSV headers  
4. **Proper missing run handling** (skip, don't zero)
5. **ASCII art layouts** must be implemented exactly as shown

### **Error Prevention**
- **Validate all inputs** before processing
- **Handle file format errors** gracefully  
- **Provide clear user feedback** for all errors
- **Use consistent exception types** across modules

### **Performance Considerations**  
- **Background processing** for operations > 2 seconds
- **Memory efficient** handling of large datasets
- **Responsive UI** during processing
- **Efficient file I/O** with proper error handling

## **FINAL DELIVERABLE STRUCTURE**
The completed system should provide:
1. **Complete calibration management** with quality assessment
2. **Accurate hydrogen concentration calculations** with full traceability  
3. **Professional data visualization** with publication-ready export
4. **Seamless integration** between all three modules
5. **Robust error handling** and user feedback
6. **Professional GUI** matching all layout specifications

**SUCCESS CRITERIA**: User can process calibration data, convert experimental TDA data to hydrogen concentrations using selected calibrations, and generate publication-ready plots comparing multiple experiments - all with complete data traceability and quality validation.