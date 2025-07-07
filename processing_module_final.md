# Module 2: Data Processing - Complete Implementation Guide

## **Module Purpose**
Convert raw experimental TDA data to hydrogen concentrations using calibration standards, with interactive parameter input, complete time-series calculation, and comprehensive CSV output with full traceability.

## **Core Implementation**

### **DataProcessor Class (Complete)**
```python
from modules.data_extraction import TDAFileExtractor, TimestampProcessor
from modules.calibration_manager import CalibrationManager, CalibrationData
import pandas as pd
import numpy as np
from datetime import datetime
import csv
import os
from typing import List, Dict, Optional, Tuple

class DataProcessor:
    def __init__(self, calibration_manager: CalibrationManager, 
                 output_folder="./data/processed_experiments/"):
        self.calibration_manager = calibration_manager
        self.output_folder = output_folder
        self.current_experiment = None
        self.selected_calibration = None
        
        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Initialize calculation engine
        self.calculator = HydrogenCalculator()
        
    def load_experiment_data(self, folder_path: str) -> ExperimentData:
        """Extract TDA data from experimental folder using shared extraction utility"""
        try:
            # Use shared data extraction
            raw_data = TDAFileExtractor.extract_from_folder(folder_path)
            
            # Convert to ExperimentData structure
            experiment_data = ExperimentData(
                experiment_name=raw_data.experiment_name,
                source_folder=folder_path,
                extraction_timestamp=datetime.now().isoformat(),
                run_numbers=raw_data.run_numbers,
                timestamps=raw_data.timestamps,
                peak_areas=raw_data.peak_areas,
                peak_heights=raw_data.peak_heights,
                missing_runs=raw_data.missing_runs
            )
            
            # Calculate time series from timestamps
            experiment_data.time_minutes = TimestampProcessor.calculate_minutes_from_start(
                raw_data.timestamps
            )
            
            # Validate data consistency
            validation_errors = experiment_data.validate_data_consistency()
            if validation_errors:
                raise TDAValidationError(f"Data consistency errors: {', '.join(validation_errors)}")
            
            self.current_experiment = experiment_data
            return experiment_data
            
        except Exception as e:
            if isinstance(e, (TDAFileError, TDAValidationError)):
                raise
            else:
                raise TDAFileError(f"Failed to load experiment data: {str(e)}")
    
    def preview_experiment_data(self, folder_path: str, num_rows: int = 10) -> Dict:
        """Generate preview data for GUI display"""
        try:
            experiment_data = self.load_experiment_data(folder_path)
            
            # Create preview data
            preview_data = {
                'experiment_name': experiment_data.experiment_name,
                'total_runs': len(experiment_data.run_numbers),
                'missing_runs': len(experiment_data.missing_runs),
                'date_range': f"{experiment_data.timestamps[0]} to {experiment_data.timestamps[-1]}" if experiment_data.timestamps else "No data",
                'preview_rows': []
            }
            
            # Add preview rows
            for i in range(min(num_rows, len(experiment_data.run_numbers))):
                preview_data['preview_rows'].append({
                    'run': experiment_data.run_numbers[i],
                    'timestamp': experiment_data.timestamps[i],
                    'peak_area': f"{experiment_data.peak_areas[i]:,.1f}",
                    'peak_height': f"{experiment_data.peak_heights[i]:,.1f}",
                    'time_minutes': f"{experiment_data.time_minutes[i]:.1f}"
                })
            
            return preview_data
            
        except Exception as e:
            raise TDAFileError(f"Failed to preview data: {str(e)}")
    
    def select_calibration(self, calibration_id: str) -> CalibrationData:
        """Load calibration for processing"""
        calibration = self.calibration_manager.get_calibration(calibration_id)
        if not calibration:
            raise TDAValidationError(f"Calibration {calibration_id} not found")
        
        if not calibration.is_valid:
            raise TDAValidationError(f"Calibration {calibration_id} is marked as invalid")
        
        self.selected_calibration = calibration
        return calibration
    
    def calculate_hydrogen_concentrations(self, experiment_data: ExperimentData, 
                                        calibration: CalibrationData, 
                                        parameters: Dict) -> ExperimentData:
        """
        Apply hydrogen calculation formula to experimental data
        
        Parameters dict should contain:
        - sample_weight: float (grams)
        - flow_rate: float (ml/min)
        - cycle_time: float (minutes)
        """
        try:
            # Validate inputs
            errors, warnings = self.validate_processing_inputs(experiment_data, calibration, parameters)
            if errors:
                raise TDAValidationError(f"Processing validation failed: {'; '.join(errors)}")
            
            # Store processing parameters
            experiment_data.sample_weight = parameters['sample_weight']
            experiment_data.flow_rate = parameters['flow_rate']
            experiment_data.cycle_time = parameters['cycle_time']
            experiment_data.calibration_id = calibration.calibration_id
            
            # Calculate hydrogen concentrations for each run
            h_ppm_per_min = []
            h_ppm_over_cycle = []
            quality_flags = []
            
            for i, peak_area in enumerate(experiment_data.peak_areas):
                try:
                    # Calculate H ppm/min using calibration
                    h_rate = self.calculator.calculate_h_ppm_per_minute(
                        peak_area, calibration, parameters['flow_rate'], parameters['sample_weight']
                    )
                    
                    # Calculate H ppm over cycle
                    h_cycle = self.calculator.calculate_h_ppm_over_cycle(h_rate, parameters['cycle_time'])
                    
                    h_ppm_per_min.append(h_rate)
                    h_ppm_over_cycle.append(h_cycle)
                    
                    # Quality flags
                    flags = []
                    if h_rate < 0:
                        flags.append("negative_rate")
                    if peak_area < 100:
                        flags.append("low_signal")
                    quality_flags.append("; ".join(flags))
                    
                except Exception as calc_error:
                    # Handle individual calculation errors
                    h_ppm_per_min.append(0.0)
                    h_ppm_over_cycle.append(0.0)
                    quality_flags.append(f"calc_error: {str(calc_error)}")
            
            # Store calculated results
            experiment_data.h_ppm_per_min = h_ppm_per_min
            experiment_data.h_ppm_over_cycle = h_ppm_over_cycle
            experiment_data.quality_flags = quality_flags
            
            # Calculate cumulative hydrogen
            experiment_data.cumulative_h_ppm = self.calculator.calculate_cumulative_hydrogen(h_ppm_over_cycle)
            
            # Final validation of results
            result_warnings = self.validate_processing_results(experiment_data)
            if result_warnings:
                experiment_data.processing_warnings = result_warnings
            
            return experiment_data
            
        except Exception as e:
            if isinstance(e, TDAValidationError):
                raise
            else:
                raise TDACalculationError(f"Hydrogen calculation failed: {str(e)}")
    
    def generate_enhanced_csv(self, processed_data: ExperimentData, output_path: str) -> str:
        """
        Create comprehensive CSV with complete metadata header
        Returns: Path to generated CSV file
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Generate comprehensive metadata header
                self._write_csv_header(writer, processed_data)
                
                # Column headers
                headers = [
                    'Run',
                    'Timestamp', 
                    'Time_minutes',
                    'Peak_Area_µVs',
                    'Peak_Height_µV',
                    'H_ppm_per_min',
                    'H_ppm_over_cycle',
                    'Cumulative_H_ppm',
                    'Quality_Flags'
                ]
                writer.writerow(headers)
                
                # Data rows
                for i in range(len(processed_data.run_numbers)):
                    row = [
                        processed_data.run_numbers[i],
                        processed_data.timestamps[i],
                        f"{processed_data.time_minutes[i]:.2f}",
                        f"{processed_data.peak_areas[i]:.5f}",
                        f"{processed_data.peak_heights[i]:.5f}",
                        f"{processed_data.h_ppm_per_min[i]:.8f}",
                        f"{processed_data.h_ppm_over_cycle[i]:.8f}",
                        f"{processed_data.cumulative_h_ppm[i]:.8f}",
                        processed_data.quality_flags[i] if i < len(processed_data.quality_flags) else ""
                    ]
                    writer.writerow(row)
            
            return output_path
            
        except Exception as e:
            raise TDAFileError(f"Failed to generate CSV: {str(e)}")
    
    def _write_csv_header(self, writer, processed_data: ExperimentData):
        """Write comprehensive metadata header to CSV"""
        # Basic information
        writer.writerow(['# TDA Hydrogen Analysis Results - Generated by TDA Analysis System'])
        writer.writerow([f'# Generated: {datetime.now().isoformat()}'])
        writer.writerow(['#'])
        
        # Experiment information
        writer.writerow(['# === EXPERIMENT INFORMATION ==='])
        writer.writerow([f'# Experiment Name: {processed_data.experiment_name}'])
        writer.writerow([f'# Source Folder: {processed_data.source_folder}'])
        writer.writerow([f'# Extraction Date: {processed_data.extraction_timestamp}'])
        writer.writerow([f'# Operator: SYSTEM'])
        writer.writerow(['#'])
        
        # Sample parameters
        writer.writerow(['# === SAMPLE PARAMETERS ==='])
        writer.writerow([f'# Sample Weight: {processed_data.sample_weight} g'])
        writer.writerow([f'# Flow Rate: {processed_data.flow_rate} ml/min'])
        writer.writerow([f'# Cycle Time: {processed_data.cycle_time} minutes'])
        writer.writerow(['#'])
        
        # Calibration information
        if self.selected_calibration:
            cal = self.selected_calibration
            writer.writerow(['# === CALIBRATION INFORMATION ==='])
            writer.writerow([f'# Calibration ID: {cal.calibration_id}'])
            writer.writerow([f'# Calibration Date: {cal.date}'])
            writer.writerow([f'# Gas Concentration: {cal.gas_concentration_ppm} ppm'])
            writer.writerow([f'# Mean Peak Area: {cal.mean_peak_area:.1f} µV*s'])
            writer.writerow([f'# Standard Deviation: {cal.std_deviation:.1f} µV*s'])
            writer.writerow([f'# CV Percentage: {cal.cv_percent:.2f}%'])
            writer.writerow([f'# Quality Score: {cal.quality_score:.1f}/100'])
            writer.writerow(['#'])
        
        # Data quality summary
        writer.writerow(['# === DATA QUALITY SUMMARY ==='])
        total_attempted = len(processed_data.run_numbers) + len(processed_data.missing_runs)
        success_rate = (len(processed_data.run_numbers) / total_attempted * 100) if total_attempted > 0 else 0
        
        writer.writerow([f'# Total Runs Attempted: {total_attempted}'])
        writer.writerow([f'# Successful Runs: {len(processed_data.run_numbers)}'])
        writer.writerow([f'# Failed Runs: {len(processed_data.missing_runs)}'])
        if processed_data.missing_runs:
            missing_str = ",".join(map(str, processed_data.missing_runs[:20]))  # Limit to first 20
            if len(processed_data.missing_runs) > 20:
                missing_str += f"... (and {len(processed_data.missing_runs) - 20} more)"
            writer.writerow([f'# Missing Run Numbers: {missing_str}'])
        writer.writerow([f'# Data Quality Score: {self._assess_data_quality(success_rate)} ({success_rate:.1f}% success rate)'])
        writer.writerow(['#'])
        
        # Calculated results summary
        if processed_data.h_ppm_over_cycle:
            total_h = sum(processed_data.h_ppm_over_cycle)
            max_rate = max(processed_data.h_ppm_per_min) if processed_data.h_ppm_per_min else 0
            avg_rate = sum(processed_data.h_ppm_per_min) / len(processed_data.h_ppm_per_min) if processed_data.h_ppm_per_min else 0
            duration = max(processed_data.time_minutes) if processed_data.time_minutes else 0
            
            writer.writerow(['# === CALCULATED RESULTS SUMMARY ==='])
            writer.writerow([f'# Total Hydrogen Released: {total_h:.6f} ppm'])
            writer.writerow([f'# Maximum Evolution Rate: {max_rate:.8f} ppm/min'])
            writer.writerow([f'# Average Evolution Rate: {avg_rate:.8f} ppm/min'])
            writer.writerow([f'# Experiment Duration: {duration:.1f} minutes ({duration/60:.2f} hours)'])
            writer.writerow(['#'])
        
        # Column definitions
        writer.writerow(['# === COLUMN DEFINITIONS ==='])
        writer.writerow(['# Run: Sequential run number from GC analysis'])
        writer.writerow(['# Timestamp: Date and time of measurement (MM/DD/YYYY HH:MM:SS)'])
        writer.writerow(['# Time_minutes: Minutes elapsed from start of experiment'])
        writer.writerow(['# Peak_Area_µVs: Raw peak area from chromatograph (µV*s)'])
        writer.writerow(['# Peak_Height_µV: Raw peak height from chromatograph (µV)'])
        writer.writerow(['# H_ppm_per_min: Calculated hydrogen evolution rate (ppm/min)'])
        writer.writerow(['# H_ppm_over_cycle: Hydrogen evolved during this cycle (ppm)'])
        writer.writerow(['# Cumulative_H_ppm: Total cumulative hydrogen evolved (ppm)'])
        writer.writerow(['# Quality_Flags: Data quality indicators (outlier, low_signal, etc.)'])
        writer.writerow(['#'])
    
    def _assess_data_quality(self, success_rate: float) -> str:
        """Assess overall data quality based on success rate"""
        if success_rate >= 95:
            return "Excellent"
        elif success_rate >= 85:
            return "Good"
        elif success_rate >= 70:
            return "Fair"
        else:
            return "Poor"
    
    def validate_processing_inputs(self, experiment_data: ExperimentData, 
                                 calibration: CalibrationData, 
                                 parameters: Dict) -> Tuple[List[str], List[str]]:
        """Comprehensive validation before processing"""
        errors = []
        warnings = []
        
        # Validate experiment data
        if not experiment_data.peak_areas:
            errors.append("No peak area data found")
        
        if len(experiment_data.missing_runs) > len(experiment_data.run_numbers) * 0.5:
            errors.append("More than 50% of runs are missing - data quality too poor")
        elif len(experiment_data.missing_runs) > len(experiment_data.run_numbers) * 0.2:
            warnings.append("More than 20% of runs are missing - check data quality")
        
        # Validate calibration
        if not calibration:
            errors.append("No calibration selected")
        elif calibration.cv_percent > 15:
            errors.append("Calibration CV% too high (>15%) - results will be unreliable")
        elif calibration.cv_percent > 10:
            warnings.append("Calibration CV% high (>10%) - results may be less accurate")
        elif calibration.num_runs < 3:
            warnings.append("Calibration based on few runs (<3) - accuracy may be limited")
        
        # Validate parameters
        try:
            sample_weight = float(parameters.get('sample_weight', 0))
            if sample_weight <= 0:
                errors.append("Sample weight must be positive")
            elif sample_weight < 0.1 or sample_weight > 50:
                warnings.append(f"Unusual sample weight ({sample_weight} g) - verify value")
        except (ValueError, TypeError):
            errors.append("Invalid sample weight - must be a number")
        
        try:
            flow_rate = float(parameters.get('flow_rate', 0))
            if flow_rate <= 0:
                errors.append("Flow rate must be positive")
            elif flow_rate < 1 or flow_rate > 100:
                warnings.append(f"Unusual flow rate ({flow_rate} ml/min) - verify value")
        except (ValueError, TypeError):
            errors.append("Invalid flow rate - must be a number")
        
        try:
            cycle_time = float(parameters.get('cycle_time', 0))
            if cycle_time <= 0:
                errors.append("Cycle time must be positive")
            elif cycle_time < 1 or cycle_time > 60:
                warnings.append(f"Unusual cycle time ({cycle_time} min) - verify value")
        except (ValueError, TypeError):
            errors.append("Invalid cycle time - must be a number")
        
        return errors, warnings
    
    def validate_processing_results(self, processed_data: ExperimentData) -> List[str]:
        """Validate calculated results for potential issues"""
        warnings = []
        
        if not processed_data.h_ppm_per_min:
            warnings.append("No hydrogen concentrations calculated")
            return warnings
        
        # Check for negative concentrations
        negative_count = sum(1 for h in processed_data.h_ppm_per_min if h < 0)
        if negative_count > 0:
            warnings.append(f"{negative_count} negative hydrogen concentrations calculated")
        
        # Check for very high concentrations
        max_concentration = max(processed_data.h_ppm_per_min)
        if max_concentration > 1000:
            warnings.append(f"Very high hydrogen concentrations detected (max: {max_concentration:.2f} ppm)")
        
        # Check for very low concentrations (all below detection limit)
        if max_concentration < 0.001:
            warnings.append("All hydrogen concentrations very low - check sensitivity")
        
        # Check for calculation consistency
        total_calculated = sum(processed_data.h_ppm_over_cycle)
        final_cumulative = processed_data.cumulative_h_ppm[-1] if processed_data.cumulative_h_ppm else 0
        
        if abs(total_calculated - final_cumulative) > 0.001:
            warnings.append("Cumulative calculation inconsistency detected")
        
        return warnings
```

### **HydrogenCalculator Class (Complete)**
```python
class HydrogenCalculator:
    """Core calculation engine for hydrogen concentration conversion"""
    
    def __init__(self):
        # Physical constants (do not change)
        self.CARRIER_GAS_MOL_PER_SEC = 7.44e-6  # For Argon carrier gas
        self.MOLAR_WEIGHT_H2 = 2.0              # g/mol
        self.SECONDS_PER_MINUTE = 60
        self.CONVERSION_FACTOR = 0.8928          # Pre-calculated: 7.44e-6 × 1e6 × 2 × 60 / 10
        
    def calculate_h_ppm_per_minute(self, peak_area: float, calibration_data: CalibrationData, 
                                  flow_rate: float, sample_weight: float) -> float:
        """
        Apply the core hydrogen calculation formula:
        
        H_ppm_per_minute = (peak_area × H_standard_ppm × flow_rate × 0.8928) 
                          / (H_standard_peak_area × sample_weight)
        
        Args:
            peak_area: Measured peak area (µV*s)
            calibration_data: Calibration standard data
            flow_rate: Gas flow rate (ml/min)
            sample_weight: Sample weight (g)
            
        Returns:
            Hydrogen concentration rate (ppm/min)
        """
        # Validate inputs
        validation_warnings = self.validate_calculation_inputs(
            peak_area, calibration_data, flow_rate, sample_weight
        )
        if any("ERROR" in w for w in validation_warnings):
            raise TDACalculationError(f"Invalid inputs: {'; '.join(validation_warnings)}")
        
        # Extract calibration parameters
        h_standard_ppm = calibration_data.gas_concentration_ppm
        h_standard_peak_area = calibration_data.mean_peak_area
        
        # Apply the simplified formula
        h_ppm_per_min = (peak_area * h_standard_ppm * flow_rate * self.CONVERSION_FACTOR) / (h_standard_peak_area * sample_weight)
        
        return h_ppm_per_min
    
    def calculate_h_ppm_over_cycle(self, h_ppm_per_min: float, cycle_time: float) -> float:
        """
        Calculate hydrogen amount evolved over the cycle period
        
        Args:
            h_ppm_per_min: Hydrogen evolution rate (ppm/min)
            cycle_time: Cycle duration (minutes)
            
        Returns:
            Hydrogen evolved during cycle (ppm)
        """
        return h_ppm_per_min * cycle_time
    
    def calculate_cumulative_hydrogen(self, h_ppm_over_cycle_list: List[float]) -> List[float]:
        """
        Calculate running total of hydrogen evolution
        
        Args:
            h_ppm_over_cycle_list: List of hydrogen evolved per cycle
            
        Returns:
            List of cumulative hydrogen totals
        """
        cumulative = []
        running_total = 0.0
        
        for h_cycle in h_ppm_over_cycle_list:
            running_total += h_cycle
            cumulative.append(running_total)
            
        return cumulative
    
    def validate_calculation_inputs(self, peak_area: float, calibration_data: CalibrationData,
                                   flow_rate: float, sample_weight: float) -> List[str]:
        """Validate inputs and return warnings/errors"""
        warnings = []
        
        # Peak area validation
        if peak_area <= 0:
            warnings.append("ERROR: Peak area must be positive")
        elif peak_area < 100:
            warnings.append("WARNING: Very low peak area - check signal quality")
        elif peak_area > 1000000:
            warnings.append("WARNING: Very high peak area - check for overload")
        
        # Sample weight validation
        if sample_weight <= 0:
            warnings.append("ERROR: Sample weight must be positive")
        elif sample_weight < 0.1:
            warnings.append("WARNING: Very low sample weight - results may be imprecise")
        elif sample_weight > 50:
            warnings.append("WARNING: Very high sample weight - unusual for TDA")
        
        # Flow rate validation
        if flow_rate <= 0:
            warnings.append("ERROR: Flow rate must be positive")
        elif flow_rate < 1:
            warnings.append("WARNING: Very low flow rate")
        elif flow_rate > 100:
            warnings.append("WARNING: Very high flow rate")
        
        # Calibration validation
        if calibration_data.cv_percent > 10:
            warnings.append("WARNING: High calibration CV% - results may be unreliable")
        if calibration_data.mean_peak_area <= 0:
            warnings.append("ERROR: Invalid calibration peak area")
        
        return warnings
```

### **ExperimentData Class (Complete)**
```python
@dataclass
class ExperimentData:
    """Complete experimental data structure with processing results"""
    # Identification
    experiment_name: str = ""
    source_folder: str = ""
    extraction_timestamp: str = ""
    
    # Raw TDA data (parallel arrays - same length)
    run_numbers: List[int] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)      # Format: MM/DD/YYYY HH:MM:SS
    peak_areas: List[float] = field(default_factory=list)    # Units: µV*s
    peak_heights: List[float] = field(default_factory=list)  # Units: µV
    time_minutes: List[float] = field(default_factory=list)  # Minutes from start
    
    # Processing parameters
    sample_weight: float = 0.0                               # grams
    flow_rate: float = 0.0                                   # ml/min
    cycle_time: float = 0.0                                  # minutes
    calibration_id: str = ""
    
    # Calculated results (parallel arrays)
    h_ppm_per_min: List[float] = field(default_factory=list)
    h_ppm_over_cycle: List[float] = field(default_factory=list)
    cumulative_h_ppm: List[float] = field(default_factory=list)
    
    # Quality tracking
    missing_runs: List[int] = field(default_factory=list)    # Run numbers that failed
    quality_flags: List[str] = field(default_factory=list)   # Per-run quality indicators
    processing_warnings: List[str] = field(default_factory=list)
    
    def validate_data_consistency(self) -> List[str]:
        """Validate that all data arrays have consistent lengths"""
        errors = []
        expected_length = len(self.run_numbers)
        
        arrays_to_check = [
            ("timestamps", self.timestamps),
            ("peak_areas", self.peak_areas),
            ("peak_heights", self.peak_heights),
            ("time_minutes", self.time_minutes)
        ]
        
        for name, array in arrays_to_check:
            if len(array) != expected_length:
                errors.append(f"{name} length ({len(array)}) != run_numbers length ({expected_length})")
        
        # Check for reasonable time sequence
        if self.time_minutes and len(self.time_minutes) > 1:
            if not all(self.time_minutes[i] <= self.time_minutes[i+1] for i in range(len(self.time_minutes)-1)):
                errors.append("Time sequence is not monotonically increasing")
        
        return errors
    
    def get_summary_statistics(self) -> Dict:
        """Calculate summary statistics for the experiment"""
        if not self.h_ppm_over_cycle:
            return {"error": "No calculated data available"}
        
        return {
            "total_hydrogen_ppm": sum(self.h_ppm_over_cycle),
            "max_rate_ppm_per_min": max(self.h_ppm_per_min) if self.h_ppm_per_min else 0,
            "avg_rate_ppm_per_min": sum(self.h_ppm_per_min) / len(self.h_ppm_per_min) if self.h_ppm_per_min else 0,
            "duration_minutes": max(self.time_minutes) if self.time_minutes else 0,
            "successful_runs": len(self.run_numbers),
            "failed_runs": len(self.missing_runs),
            "success_rate_percent": len(self.run_numbers) / (len(self.run_numbers) + len(self.missing_runs)) * 100 if (len(self.run_numbers) + len(self.missing_runs)) > 0 else 0
        }
```

This complete Module 2 specification addresses all of Gemini's feedback by providing:

1. **Complete time_minutes calculation** using the shared TimestampProcessor
2. **Detailed enhanced CSV format** with comprehensive metadata headers
3. **Robust error handling** with specific exception types and validation
4. **Full integration** with shared data structures and calibration system
5. **Comprehensive validation** at all processing stages
6. **Complete calculation engine** with the exact hydrogen formula implementation

The module now provides complete traceability from raw TDA files through calibration application to final processed CSV output that Module 3 can consume for visualization.