"""
Data Processing Module for TDA Analysis System

This module converts raw experimental TDA data to hydrogen concentrations using calibration standards,
with interactive parameter input, complete time-series calculation, and comprehensive CSV output.
"""

import os
import csv
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass, field

from .data_extraction import TDAFileExtractor, TimestampProcessor
from .calibration_manager import CalibrationManager
from .shared_data_structures import CalibrationData
from .error_handling import TDAFileError, TDAValidationError, TDACalculationError


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


@dataclass
class BatchProcessingResult:
    """Result of processing a single folder in batch mode"""
    folder_path: str
    experiment_name: str
    success: bool
    csv_output_path: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    data_summary: Optional[Dict] = None


@dataclass
class BatchResults:
    """Complete results of batch processing operation"""
    total_folders: int
    successful: int
    failed: int
    results: List[BatchProcessingResult] = field(default_factory=list)
    total_processing_time: float = 0.0
    output_folder: str = ""
    
    def get_success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_folders == 0:
            return 0.0
        return (self.successful / self.total_folders) * 100
    
    def get_failed_folders(self) -> List[str]:
        """Get list of folder paths that failed processing"""
        return [r.folder_path for r in self.results if not r.success]
    
    def get_successful_csvs(self) -> List[str]:
        """Get list of successfully generated CSV paths"""
        return [r.csv_output_path for r in self.results if r.success and r.csv_output_path]


class HydrogenCalculator:
    """Core calculation engine for hydrogen concentration conversion"""
    
    def __init__(self):
        # Physical constants (do not change)
        self.CARRIER_GAS_MOL_PER_SEC = 7.44e-6  # For Argon carrier gas
        self.MOLAR_WEIGHT_H2 = 2.0              # g/mol
        self.SECONDS_PER_MINUTE = 60
        self.CONVERSION_FACTOR = 0.00008928          # Pre-calculated: 7.44e-6 × 1e6 × 2 × 60 / 10
        
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


class DataProcessor:
    """Main data processing class for experimental TDA data"""
    
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
            
            # Calculate time series - use sequential timing based on cycle time
            # Time will be properly calculated later when cycle_time is known
            experiment_data.time_minutes = [0.0] * len(raw_data.run_numbers)
            
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
            
            # Calculate proper time sequence: run_index × cycle_time
            experiment_data.time_minutes = [i * parameters['cycle_time'] for i in range(len(experiment_data.run_numbers))]
            
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
                # Write metadata header directly as text (not through CSV writer)
                self._write_csv_header_text(csvfile, processed_data)
                
                # Now use CSV writer for the actual data
                writer = csv.writer(csvfile)
                
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
    
    def _write_csv_header_text(self, file, processed_data: ExperimentData):
        """Write comprehensive metadata header directly to file"""
        # Basic information
        file.write('# TDA Hydrogen Analysis Results - Generated by TDA Analysis System\n')
        file.write(f'# Generated: {datetime.now().isoformat()}\n')
        file.write('#\n')
        
        # Experiment information
        file.write('# === EXPERIMENT INFORMATION ===\n')
        file.write(f'# Experiment Name: {processed_data.experiment_name}\n')
        file.write(f'# Source Folder: {processed_data.source_folder}\n')
        file.write(f'# Extraction Date: {processed_data.extraction_timestamp}\n')
        file.write(f'# Operator: SYSTEM\n')
        file.write('#\n')
        
        # Sample parameters
        file.write('# === SAMPLE PARAMETERS ===\n')
        file.write(f'# Sample Weight: {processed_data.sample_weight} g\n')
        file.write(f'# Flow Rate: {processed_data.flow_rate} ml/min\n')
        file.write(f'# Cycle Time: {processed_data.cycle_time} minutes\n')
        file.write('#\n')
        
        # Calibration information
        if self.selected_calibration:
            cal = self.selected_calibration
            file.write('# === CALIBRATION INFORMATION ===\n')
            file.write(f'# Calibration ID: {cal.calibration_id}\n')
            file.write(f'# Calibration Date: {cal.date}\n')
            file.write(f'# Gas Concentration: {cal.gas_concentration_ppm} ppm\n')
            file.write(f'# Mean Peak Area: {cal.mean_peak_area:.1f} µV*s\n')
            file.write(f'# Standard Deviation: {cal.std_deviation:.1f} µV*s\n')
            file.write(f'# CV Percentage: {cal.cv_percent:.2f}%\n')
            file.write(f'# Quality Score: {cal.quality_score:.1f}/100\n')
            file.write('#\n')
        
        # Data quality summary
        file.write('# === DATA QUALITY SUMMARY ===\n')
        total_attempted = len(processed_data.run_numbers) + len(processed_data.missing_runs)
        success_rate = (len(processed_data.run_numbers) / total_attempted * 100) if total_attempted > 0 else 0
        
        file.write(f'# Total Runs Attempted: {total_attempted}\n')
        file.write(f'# Successful Runs: {len(processed_data.run_numbers)}\n')
        file.write(f'# Failed Runs: {len(processed_data.missing_runs)}\n')
        if processed_data.missing_runs:
            missing_str = ",".join(map(str, processed_data.missing_runs[:20]))  # Limit to first 20
            if len(processed_data.missing_runs) > 20:
                missing_str += f"... (and {len(processed_data.missing_runs) - 20} more)"
            file.write(f'# Missing Run Numbers: {missing_str}\n')
        file.write(f'# Data Quality Score: {self._assess_data_quality(success_rate)} ({success_rate:.1f}% success rate)\n')
        file.write('#\n')
        
        # Calculated results summary
        if processed_data.h_ppm_over_cycle:
            total_h = sum(processed_data.h_ppm_over_cycle)
            max_rate = max(processed_data.h_ppm_per_min) if processed_data.h_ppm_per_min else 0
            avg_rate = sum(processed_data.h_ppm_per_min) / len(processed_data.h_ppm_per_min) if processed_data.h_ppm_per_min else 0
            duration = max(processed_data.time_minutes) if processed_data.time_minutes else 0
            
            file.write('# === CALCULATED RESULTS SUMMARY ===\n')
            file.write(f'# Total Hydrogen Released: {total_h:.6f} ppm\n')
            file.write(f'# Maximum Evolution Rate: {max_rate:.8f} ppm/min\n')
            file.write(f'# Average Evolution Rate: {avg_rate:.8f} ppm/min\n')
            file.write(f'# Experiment Duration: {duration:.1f} minutes ({duration/60:.2f} hours)\n')
            file.write('#\n')
        
        # Column definitions
        file.write('# === COLUMN DEFINITIONS ===\n')
        file.write('# Run: Sequential run number from GC analysis\n')
        file.write('# Timestamp: Date and time of measurement (MM/DD/YYYY HH:MM:SS)\n')
        file.write('# Time_minutes: Minutes elapsed from start of experiment\n')
        file.write('# Peak_Area_µVs: Raw peak area from chromatograph (µV*s)\n')
        file.write('# Peak_Height_µV: Raw peak height from chromatograph (µV)\n')
        file.write('# H_ppm_per_min: Calculated hydrogen evolution rate (ppm/min)\n')
        file.write('# H_ppm_over_cycle: Hydrogen evolved during this cycle (ppm)\n')
        file.write('# Cumulative_H_ppm: Total cumulative hydrogen evolved (ppm)\n')
        file.write('# Quality_Flags: Data quality indicators (outlier, low_signal, etc.)\n')
        file.write('#\n')
    
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
    
    def process_batch(self, folder_paths: List[str], 
                     calibration: CalibrationData, 
                     parameters: Dict,
                     progress_callback: Optional[Callable[[int, int, str], None]] = None) -> BatchResults:
        """
        Process multiple experiment folders in batch mode
        
        Args:
            folder_paths: List of folder paths to process
            calibration: Calibration data to use for all folders
            parameters: Processing parameters (sample_weight, flow_rate, cycle_time)
            progress_callback: Optional callback function(current, total, status_msg)
            
        Returns:
            BatchResults with complete processing summary
        """
        batch_start_time = time.time()
        
        # Initialize batch results
        batch_results = BatchResults(
            total_folders=len(folder_paths),
            successful=0,
            failed=0,
            output_folder=self.output_folder
        )
        
        # Validate inputs before starting
        validation_errors = self._validate_batch_inputs(folder_paths, calibration, parameters)
        if validation_errors:
            # Create failed results for all folders
            for folder_path in folder_paths:
                result = BatchProcessingResult(
                    folder_path=folder_path,
                    experiment_name=os.path.basename(folder_path),
                    success=False,
                    error_message=f"Batch validation failed: {'; '.join(validation_errors)}"
                )
                batch_results.results.append(result)
            batch_results.failed = len(folder_paths)
            return batch_results
        
        # Process each folder
        for i, folder_path in enumerate(folder_paths):
            if progress_callback:
                experiment_name = os.path.basename(folder_path)
                progress_callback(i, len(folder_paths), f"Processing {experiment_name}...")
            
            result = self._process_single_folder_batch(folder_path, calibration, parameters)
            batch_results.results.append(result)
            
            if result.success:
                batch_results.successful += 1
            else:
                batch_results.failed += 1
        
        # Final progress update
        if progress_callback:
            progress_callback(len(folder_paths), len(folder_paths), "Batch processing complete")
        
        batch_results.total_processing_time = time.time() - batch_start_time
        return batch_results
    
    def _process_single_folder_batch(self, folder_path: str, 
                                   calibration: CalibrationData, 
                                   parameters: Dict) -> BatchProcessingResult:
        """Process a single folder in batch mode"""
        start_time = time.time()
        experiment_name = os.path.basename(folder_path)
        
        try:
            # Load experiment data
            experiment_data = self.load_experiment_data(folder_path)
            
            # Apply processing
            processed_data = self.calculate_hydrogen_concentrations(
                experiment_data, calibration, parameters
            )
            
            # Generate CSV with unique name
            csv_filename = self._generate_unique_csv_name(experiment_name)
            csv_path = os.path.join(self.output_folder, csv_filename)
            
            self.generate_enhanced_csv(processed_data, csv_path)
            
            # Get summary statistics
            summary = processed_data.get_summary_statistics()
            
            return BatchProcessingResult(
                folder_path=folder_path,
                experiment_name=experiment_name,
                success=True,
                csv_output_path=csv_path,
                processing_time=time.time() - start_time,
                data_summary=summary
            )
            
        except Exception as e:
            return BatchProcessingResult(
                folder_path=folder_path,
                experiment_name=experiment_name,
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _validate_batch_inputs(self, folder_paths: List[str], 
                             calibration: CalibrationData, 
                             parameters: Dict) -> List[str]:
        """Validate batch processing inputs"""
        errors = []
        
        # Check folder paths
        if not folder_paths:
            errors.append("No folders selected for processing")
            return errors
        
        # Check if folders exist and contain data
        invalid_folders = []
        for folder_path in folder_paths:
            if not os.path.exists(folder_path):
                invalid_folders.append(f"{folder_path} (does not exist)")
            elif not os.path.isdir(folder_path):
                invalid_folders.append(f"{folder_path} (not a directory)")
            else:
                # Quick check for TDA files
                try:
                    files = os.listdir(folder_path)
                    has_d_folders = any(f.endswith('.D') for f in files if os.path.isdir(os.path.join(folder_path, f)))
                    has_data_files = any(f.lower().endswith(('.xls', '.xlsx', '.txt')) for f in files)
                    
                    if not (has_d_folders or has_data_files):
                        invalid_folders.append(f"{folder_path} (no TDA data files found)")
                except OSError:
                    invalid_folders.append(f"{folder_path} (cannot access directory)")
        
        if invalid_folders:
            errors.append(f"Invalid folders: {'; '.join(invalid_folders[:5])}")  # Limit to first 5
            if len(invalid_folders) > 5:
                errors.append(f"... and {len(invalid_folders) - 5} more folders with issues")
        
        # Validate calibration
        if not calibration:
            errors.append("No calibration selected")
        elif not calibration.is_valid:
            errors.append(f"Selected calibration ({calibration.calibration_id}) is invalid")
        elif calibration.cv_percent > 15:
            errors.append(f"Calibration CV% too high ({calibration.cv_percent:.1f}%) - results will be unreliable")
        
        # Validate parameters (basic checks)
        try:
            sample_weight = float(parameters.get('sample_weight', 0))
            if sample_weight <= 0:
                errors.append("Sample weight must be positive")
        except (ValueError, TypeError):
            errors.append("Invalid sample weight")
        
        try:
            flow_rate = float(parameters.get('flow_rate', 0))
            if flow_rate <= 0:
                errors.append("Flow rate must be positive")
        except (ValueError, TypeError):
            errors.append("Invalid flow rate")
        
        try:
            cycle_time = float(parameters.get('cycle_time', 0))
            if cycle_time <= 0:
                errors.append("Cycle time must be positive")
        except (ValueError, TypeError):
            errors.append("Invalid cycle time")
        
        return errors
    
    def _generate_unique_csv_name(self, experiment_name: str) -> str:
        """Generate unique CSV filename, handling conflicts"""
        base_name = f"{experiment_name}_processed"
        csv_name = f"{base_name}.csv"
        
        # Check for conflicts and add numbering if needed
        counter = 1
        while os.path.exists(os.path.join(self.output_folder, csv_name)):
            counter += 1
            csv_name = f"{base_name}_{counter}.csv"
        
        return csv_name
    
    def get_batch_processing_preview(self, folder_paths: List[str]) -> Dict:
        """Generate preview information for batch processing"""
        preview = {
            "total_folders": len(folder_paths),
            "valid_folders": 0,
            "invalid_folders": 0,
            "folder_details": [],
            "estimated_outputs": []
        }
        
        for folder_path in folder_paths:
            folder_name = os.path.basename(folder_path)
            is_valid = os.path.exists(folder_path) and os.path.isdir(folder_path)
            
            if is_valid:
                try:
                    # Quick data check
                    files = os.listdir(folder_path)
                    has_data = any(f.endswith('.D') for f in files if os.path.isdir(os.path.join(folder_path, f))) or \
                              any(f.lower().endswith(('.xls', '.xlsx', '.txt')) for f in files)
                    
                    if has_data:
                        preview["valid_folders"] += 1
                        status = "Ready"
                        # Predict CSV name
                        csv_name = self._generate_unique_csv_name(folder_name)
                        preview["estimated_outputs"].append(csv_name)
                    else:
                        preview["invalid_folders"] += 1
                        status = "No data files found"
                except OSError:
                    preview["invalid_folders"] += 1
                    status = "Cannot access"
            else:
                preview["invalid_folders"] += 1
                status = "Does not exist"
            
            preview["folder_details"].append({
                "name": folder_name,
                "path": folder_path,
                "status": status,
                "valid": is_valid and status == "Ready"
            })
        
        return preview