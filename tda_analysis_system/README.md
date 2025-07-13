# TDA Analysis System

A comprehensive PyQt5-based application for processing and analyzing Thermal Desorption Analysis (TDA) data from gas chromatograph experiments, with advanced diffusion analysis capabilities.

## Features

### 🔬 **Core Analysis Capabilities**
- **TDA Data Processing**: Convert raw gas chromatograph data to hydrogen concentrations
- **Calibration Management**: Process hydrogen calibration standard data with quality assessment
- **Diffusion Analysis**: Advanced diffusion-controlled behavior analysis with multiple plot types

### 📊 **Advanced Plotting & Visualization**
- **Dual-Axis Plotting**: Display both mol/cm² and ppm units simultaneously
- **Professional Export**: High-quality plots in PNG, PDF, SVG, and EPS formats
- **Interactive Controls**: Comprehensive styling and filtering options
- **Multi-Dataset Support**: Compare multiple experiments on the same plot

### 🧮 **Diffusion Analysis Features**
- **Multiple Plot Types**: 
  - Desorption Rate vs 1/√t (diffusion analysis)
  - Cumulative Hydrogen vs √t 
  - Log-log plots (log J vs log t)
- **Temperature Correction**: Arrhenius temperature-dependent diffusion coefficients
- **Unit Flexibility**: Switch between ppm and mol/cm² units for analysis
- **Linear Regression**: Automatic fit quality assessment and diffusion coefficient calculation

### 🔧 **Data Quality & Filtering**
- **Intelligent Noise Filtering**: Auto-detection and removal of low-signal data
- **Quality Flag System**: Automatic flagging of outliers and low-signal measurements
- **Zero-Value Filtering**: Configurable filtering of zero and near-zero values
- **Data Validation**: Comprehensive quality checks and validation

## Technology Stack

- **GUI Framework**: PyQt5 with tabbed interface
- **Data Processing**: pandas, numpy, scipy
- **Plotting**: matplotlib with PyQt integration
- **File I/O**: openpyxl for Excel files, standard Python for text/CSV
- **Data Storage**: JSON for calibration database, CSV for processed data

## Installation

### Requirements
```bash
pip install -r requirements.txt
```

### Dependencies
- PyQt5 >= 5.15.0
- pandas >= 1.3.0
- numpy >= 1.21.0
- matplotlib >= 3.5.0
- openpyxl >= 3.0.9
- scipy >= 1.7.0
- statsmodels >= 0.13.0

## Usage

### Running the Application
```bash
python main.py
```

### Basic Workflow
1. **Calibration Management**: Process hydrogen calibration standards
2. **Data Processing**: Convert raw TDA experimental data
3. **Data Visualization**: Create publication-ready plots
4. **Diffusion Analysis**: Analyze diffusion-controlled desorption behavior

## Project Structure

```
tda_analysis_system/
├── main.py                      # Application entry point & main window
├── modules/
│   ├── calibration_manager.py   # Calibration processing
│   ├── data_processor.py        # Experimental data processing  
│   ├── plot_manager.py          # Data visualization
│   ├── calcs.py                 # Diffusion analysis calculations
│   └── data_extraction.py       # TDA file parsing utilities
├── ui/
│   ├── calibration_widget.py    # GUI for calibration management
│   ├── processing_widget.py     # GUI for data processing
│   ├── plotting_widget.py       # GUI for visualization
│   └── diffusion_widget.py      # GUI for diffusion analysis
├── data/
│   ├── calibrations/            # Calibration database & files
│   └── processed_experiments/   # Output CSV files
└── requirements.txt             # All dependencies
```

## Key Formulas

### Hydrogen Concentration Calculation
```
H_ppm_per_minute = (peak_area × H_standard_ppm × flow_rate × 0.8928) / (H_standard_peak_area × sample_weight)
```

### Diffusion Coefficient Calculation
For 1/√t plots: `D = π × (slope × L)² / (4 × ΔC²)`

### Temperature Correction (Arrhenius)
```
D(T) = D₀ × exp(-Q/RT)
```

## Data Formats

### Input Formats
- **.txt files**: GLPrpt format (preferred)
- **.xls files**: Individual chromatograph reports
- **.pdf files**: Fallback parsing option

### Output Formats
- **Enhanced CSV**: Complete metadata headers for full traceability
- **JSON**: Calibration database with quality metrics
- **Plots**: PNG, PDF, SVG, EPS for publication

## Quality Control

- **CV% Validation**: Automatic coefficient of variation checking
- **Outlier Detection**: Statistical outlier identification and flagging
- **Run Count Validation**: Ensure sufficient data points for reliable analysis
- **Temperature Monitoring**: Track and correct for temperature variations

## Scientific Applications

This tool is designed for:
- **Hydrogen Desorption Studies**: Analysis of hydrogen evolution from materials
- **Diffusion Research**: Determination of hydrogen diffusion coefficients
- **Materials Characterization**: Quality assessment of hydrogen storage materials
- **Publication Preparation**: High-quality plots for scientific publications

## Contributing

This is a scientific analysis tool focused on TDA data processing and diffusion analysis. Contributions should maintain the defensive security approach and focus on data integrity.

## License

This project is designed for scientific research and analysis. Please ensure appropriate attribution when using in publications.

---

**🤖 Generated with [Claude Code](https://claude.ai/code)**