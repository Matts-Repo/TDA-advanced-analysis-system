"""
Diffusion Analysis Calculations for TDA Analysis System

This module provides calculations for analyzing hydrogen desorption tails using 
1/√t plots to confirm diffusion-controlled behavior and calculate diffusion coefficients.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from .error_handling import TDACalculationError


@dataclass
class DiffusionAnalysisResult:
    """Results from diffusion analysis calculations"""
    # Input parameters
    tail_start_time: float = 0.0
    analysis_type: str = ""  # "1_sqrt_t", "sqrt_t", "log_log"
    
    # Regression results
    slope: float = 0.0
    intercept: float = 0.0
    r_squared: float = 0.0
    std_error: float = 0.0
    p_value: float = 0.0
    
    # Diffusion coefficient (if calculated)
    diffusion_coefficient: float = 0.0
    thickness: float = 0.0  # Sample thickness (cm)
    
    # Data used in analysis
    x_data: List[float] = None
    y_data: List[float] = None
    fit_x: List[float] = None
    fit_y: List[float] = None
    
    # Quality metrics
    num_points: int = 0
    goodness_of_fit: str = ""
    
    def __post_init__(self):
        if self.x_data is None:
            self.x_data = []
        if self.y_data is None:
            self.y_data = []
        if self.fit_x is None:
            self.fit_x = []
        if self.fit_y is None:
            self.fit_y = []


class TailRegionAnalyzer:
    """Analyze TDA data to identify the diffusion-controlled tail region"""
    
    @staticmethod
    def find_tail_start(time_minutes: List[float], 
                       desorption_rate: List[float],
                       min_time: float = 60.0,
                       peak_fraction: float = 0.1) -> float:
        """
        Automatically identify the start of the diffusion tail region
        
        Args:
            time_minutes: Time data in minutes
            desorption_rate: Hydrogen desorption rate (ppm/min or mol/cm²/min)
            min_time: Minimum time after start to consider (minutes)
            peak_fraction: Fraction of peak maximum to use as threshold
        
        Returns:
            Suggested tail start time (minutes)
        """
        try:
            if len(time_minutes) != len(desorption_rate) or len(time_minutes) < 10:
                raise TDACalculationError("Insufficient data for tail analysis")
            
            # Convert to numpy arrays
            time_array = np.array(time_minutes)
            rate_array = np.array(desorption_rate)
            
            # Remove any negative values or NaN
            valid_mask = (rate_array > 0) & np.isfinite(rate_array) & np.isfinite(time_array)
            time_array = time_array[valid_mask]
            rate_array = rate_array[valid_mask]
            
            if len(time_array) < 5:
                raise TDACalculationError("Insufficient valid data points")
            
            # Find the maximum desorption rate
            max_rate = np.max(rate_array)
            threshold = max_rate * peak_fraction
            
            # Find where rate drops below threshold and time > min_time
            tail_candidates = time_array[(rate_array < threshold) & (time_array > min_time)]
            
            if len(tail_candidates) == 0:
                # If no points below threshold, use min_time
                return max(min_time, time_array[len(time_array)//3])
            
            # Return the first time point that meets criteria
            return float(tail_candidates[0])
            
        except Exception as e:
            raise TDACalculationError(f"Failed to find tail start: {str(e)}")
    
    @staticmethod
    def validate_tail_region(time_minutes: List[float],
                           desorption_rate: List[float],
                           tail_start: float) -> Dict[str, any]:
        """
        Validate that the tail region has sufficient data for analysis
        
        Returns:
            Dictionary with validation results
        """
        try:
            time_array = np.array(time_minutes)
            rate_array = np.array(desorption_rate)
            
            # Filter to tail region
            tail_mask = time_array >= tail_start
            tail_time = time_array[tail_mask]
            tail_rate = rate_array[tail_mask]
            
            # Remove invalid values
            valid_mask = (tail_rate > 0) & np.isfinite(tail_rate) & np.isfinite(tail_time)
            tail_time = tail_time[valid_mask]
            tail_rate = tail_rate[valid_mask]
            
            num_points = len(tail_time)
            duration = tail_time[-1] - tail_time[0] if num_points > 1 else 0
            
            validation = {
                'is_valid': num_points >= 10,
                'num_points': num_points,
                'duration_hours': duration / 60,
                'min_time': float(tail_time[0]) if num_points > 0 else 0,
                'max_time': float(tail_time[-1]) if num_points > 0 else 0,
                'warnings': []
            }
            
            if num_points < 10:
                validation['warnings'].append("Insufficient data points for reliable analysis (minimum 10 recommended)")
            
            if duration < 60:  # Less than 1 hour
                validation['warnings'].append("Short tail duration may affect analysis quality")
            
            return validation
            
        except Exception as e:
            raise TDACalculationError(f"Tail validation failed: {str(e)}")


class DiffusionPlotCalculator:
    """Calculate data transformations for diffusion analysis plots"""
    
    @staticmethod
    def calculate_1_sqrt_t_plot(time_minutes: List[float],
                               desorption_rate: List[float],
                               tail_start: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate data for desorption rate vs 1/√t plot
        
        Args:
            time_minutes: Time data in minutes
            desorption_rate: Hydrogen desorption rate
            tail_start: Start time for tail region
        
        Returns:
            (1/√t values, desorption rate values) for tail region
        """
        try:
            time_array = np.array(time_minutes)
            rate_array = np.array(desorption_rate)
            
            # Filter to tail region
            tail_mask = time_array >= tail_start
            tail_time = time_array[tail_mask]
            tail_rate = rate_array[tail_mask]
            
            # Remove invalid values
            valid_mask = (tail_rate > 0) & np.isfinite(tail_rate) & (tail_time > 0)
            tail_time = tail_time[valid_mask]
            tail_rate = tail_rate[valid_mask]
            
            if len(tail_time) < 3:
                raise TDACalculationError("Insufficient valid data points in tail region")
            
            # Convert time to seconds for calculation
            time_seconds = tail_time * 60
            
            # Calculate 1/√t
            sqrt_t = np.sqrt(time_seconds)
            inv_sqrt_t = 1.0 / sqrt_t
            
            return inv_sqrt_t, tail_rate
            
        except Exception as e:
            raise TDACalculationError(f"1/√t calculation failed: {str(e)}")
    
    @staticmethod
    def calculate_sqrt_t_plot(time_minutes: List[float],
                             cumulative_hydrogen: List[float],
                             tail_start: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate data for cumulative hydrogen vs √t plot
        
        Args:
            time_minutes: Time data in minutes
            cumulative_hydrogen: Cumulative hydrogen content
            tail_start: Start time for tail region
        
        Returns:
            (√t values, cumulative hydrogen values) for tail region
        """
        try:
            time_array = np.array(time_minutes)
            cumul_array = np.array(cumulative_hydrogen)
            
            # Filter to tail region
            tail_mask = time_array >= tail_start
            tail_time = time_array[tail_mask]
            tail_cumul = cumul_array[tail_mask]
            
            # Remove invalid values
            valid_mask = np.isfinite(tail_cumul) & np.isfinite(tail_time) & (tail_time > 0)
            tail_time = tail_time[valid_mask]
            tail_cumul = tail_cumul[valid_mask]
            
            if len(tail_time) < 3:
                raise TDACalculationError("Insufficient valid data points in tail region")
            
            # Convert time to seconds for calculation
            time_seconds = tail_time * 60
            
            # Calculate √t
            sqrt_t = np.sqrt(time_seconds)
            
            return sqrt_t, tail_cumul
            
        except Exception as e:
            raise TDACalculationError(f"√t calculation failed: {str(e)}")
    
    @staticmethod
    def calculate_log_log_plot(time_minutes: List[float],
                              desorption_rate: List[float],
                              tail_start: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate data for log-log plot (log J vs log t)
        
        Args:
            time_minutes: Time data in minutes
            desorption_rate: Hydrogen desorption rate
            tail_start: Start time for tail region
        
        Returns:
            (log(t) values, log(desorption rate) values) for tail region
        """
        try:
            time_array = np.array(time_minutes)
            rate_array = np.array(desorption_rate)
            
            # Filter to tail region
            tail_mask = time_array >= tail_start
            tail_time = time_array[tail_mask]
            tail_rate = rate_array[tail_mask]
            
            # Remove invalid values (must be positive for log)
            valid_mask = (tail_rate > 0) & np.isfinite(tail_rate) & (tail_time > 0) & np.isfinite(tail_time)
            tail_time = tail_time[valid_mask]
            tail_rate = tail_rate[valid_mask]
            
            if len(tail_time) < 3:
                raise TDACalculationError("Insufficient valid data points in tail region")
            
            # Calculate logarithms
            log_time = np.log10(tail_time)
            log_rate = np.log10(tail_rate)
            
            return log_time, log_rate
            
        except Exception as e:
            raise TDACalculationError(f"Log-log calculation failed: {str(e)}")


class LinearRegressionAnalyzer:
    """Perform linear regression analysis on diffusion data"""
    
    @staticmethod
    def perform_linear_regression(x_data: np.ndarray, 
                                y_data: np.ndarray,
                                noise_threshold: float = 1e-12) -> Dict[str, float]:
        """
        Perform linear regression with quality metrics
        
        Args:
            x_data: Independent variable data
            y_data: Dependent variable data
            noise_threshold: Minimum value threshold to avoid noise
        
        Returns:
            Dictionary with regression results
        """
        try:
            if len(x_data) != len(y_data) or len(x_data) < 3:
                raise TDACalculationError("Insufficient data for regression analysis")
            
            # Remove points below noise threshold
            valid_mask = np.abs(y_data) > noise_threshold
            x_filtered = x_data[valid_mask]
            y_filtered = y_data[valid_mask]
            
            if len(x_filtered) < 3:
                raise TDACalculationError("Insufficient data above noise threshold")
            
            # Perform linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_filtered, y_filtered)
            
            # Calculate additional metrics
            r_squared = r_value ** 2
            
            # Generate fit line
            fit_x = np.linspace(np.min(x_filtered), np.max(x_filtered), 100)
            fit_y = slope * fit_x + intercept
            
            return {
                'slope': float(slope),
                'intercept': float(intercept),
                'r_squared': float(r_squared),
                'r_value': float(r_value),
                'p_value': float(p_value),
                'std_error': float(std_err),
                'num_points': len(x_filtered),
                'fit_x': fit_x.tolist(),
                'fit_y': fit_y.tolist()
            }
            
        except Exception as e:
            raise TDACalculationError(f"Linear regression failed: {str(e)}")
    
    @staticmethod
    def assess_fit_quality(r_squared: float, p_value: float, num_points: int) -> str:
        """
        Assess the quality of the linear fit
        
        Args:
            r_squared: R² value from regression
            p_value: P-value from regression
            num_points: Number of data points used
        
        Returns:
            String describing fit quality
        """
        if r_squared >= 0.95 and p_value < 0.01 and num_points >= 10:
            return "Excellent"
        elif r_squared >= 0.90 and p_value < 0.05 and num_points >= 8:
            return "Good"
        elif r_squared >= 0.80 and p_value < 0.10 and num_points >= 5:
            return "Fair"
        else:
            return "Poor"


class DiffusionCoefficientCalculator:
    """Calculate diffusion coefficients from regression slopes"""
    
    @staticmethod
    def calculate_diffusion_coefficient(slope: float,
                                      sample_thickness: float = 0.1,
                                      surface_concentration_ratio: float = 1.0) -> float:
        """
        Calculate diffusion coefficient from 1/√t plot slope
        
        The relationship for semi-infinite solid with surface concentration = 0:
        J(t) = (D * ΔC) / (√(π * D * t))
        
        For 1/√t plot: J = slope * (1/√t) + intercept
        Therefore: D = π * (slope * L)² / (4 * ΔC²)
        
        Args:
            slope: Slope from J vs 1/√t plot
            sample_thickness: Sample thickness in cm (for semi-infinite approximation)
            surface_concentration_ratio: Ratio of surface to bulk concentration
        
        Returns:
            Diffusion coefficient in cm²/s
        """
        try:
            if slope == 0:
                return 0.0
            
            # For typical TDA analysis, assume semi-infinite geometry
            # D = π * (slope * L)² / (4 * ΔC²)
            # Simplified calculation assuming ΔC ~ 1 (normalized)
            
            # Convert slope units appropriately
            # Slope is typically in (ppm/min) / (1/√s) = (ppm/min) * √s
            # Need to convert to proper units for D calculation
            
            delta_c = 1.0  # Normalized concentration difference
            
            # Basic diffusion coefficient calculation
            # This is a simplified form - in practice would need proper unit conversion
            D = np.pi * (slope * sample_thickness) ** 2 / (4 * delta_c ** 2)
            
            # Ensure positive value
            D = abs(D)
            
            return float(D)
            
        except Exception as e:
            raise TDACalculationError(f"Diffusion coefficient calculation failed: {str(e)}")
    
    @staticmethod
    def compare_with_literature(calculated_D: float, 
                              material: str = "steel",
                              temperature: float = 298.15) -> Dict[str, any]:
        """
        Compare calculated D with literature values
        
        Args:
            calculated_D: Calculated diffusion coefficient (cm²/s)
            material: Material type
            temperature: Temperature in Kelvin
        
        Returns:
            Dictionary with comparison results
        """
        try:
            # Literature values for hydrogen diffusion in steel at room temperature
            # These are typical ranges - actual values depend on specific alloy
            literature_values = {
                "steel": {
                    "range": (1e-8, 1e-6),  # cm²/s at room temperature
                    "typical": 1e-7,
                    "source": "Typical for austenitic stainless steel at RT"
                },
                "iron": {
                    "range": (1e-9, 1e-7),
                    "typical": 1e-8,
                    "source": "Pure iron at room temperature"
                }
            }
            
            material_lower = material.lower()
            
            if material_lower in literature_values:
                lit_data = literature_values[material_lower]
                min_lit, max_lit = lit_data["range"]
                typical_lit = lit_data["typical"]
                
                # Calculate ratio
                ratio = calculated_D / typical_lit
                
                # Determine agreement
                if min_lit <= calculated_D <= max_lit:
                    agreement = "Good agreement"
                elif calculated_D < min_lit:
                    agreement = "Lower than expected"
                else:
                    agreement = "Higher than expected"
                
                return {
                    "literature_range": lit_data["range"],
                    "literature_typical": typical_lit,
                    "calculated_value": calculated_D,
                    "ratio": ratio,
                    "agreement": agreement,
                    "source": lit_data["source"]
                }
            else:
                return {
                    "literature_range": None,
                    "literature_typical": None,
                    "calculated_value": calculated_D,
                    "ratio": None,
                    "agreement": "No literature data available",
                    "source": f"Unknown material: {material}"
                }
            
        except Exception as e:
            return {
                "error": f"Literature comparison failed: {str(e)}",
                "calculated_value": calculated_D
            }


class DataFilteringUtils:
    """Utility functions for filtering and cleaning TDA data"""
    
    @staticmethod
    def filter_zeros(df: pd.DataFrame, 
                    value_column: str,
                    time_column: str = 'Time_min',
                    keep_origin: bool = True,
                    threshold_percent: float = 2.0,
                    detection_limit: float = 0.1) -> pd.DataFrame:
        """
        Filter out zero values and noise from TDA data
        
        Args:
            df: DataFrame with TDA data
            value_column: Name of column containing values to filter
            time_column: Name of time column
            keep_origin: Always keep the (0, 0) point
            threshold_percent: Remove values below this % of rolling average
            detection_limit: Minimum detectable value (ppm)
        
        Returns:
            Filtered DataFrame
        """
        try:
            if df.empty or value_column not in df.columns:
                return df.copy()
            
            filtered_df = df.copy()
            
            # Create mask for valid data
            valid_mask = pd.Series(True, index=filtered_df.index)
            
            # Remove exact zeros (except origin if keep_origin=True)
            if keep_origin:
                # Keep first point if it's at time 0
                origin_mask = (filtered_df[time_column] == 0) & (filtered_df[value_column] == 0)
                zero_mask = (filtered_df[value_column] == 0) & ~origin_mask
            else:
                zero_mask = filtered_df[value_column] == 0
            
            valid_mask &= ~zero_mask
            
            # Auto-adjust detection limit if it's too high for the data
            data_values = filtered_df[value_column].values
            data_max = np.max(data_values)
            data_median = np.median(data_values[data_values > 0])
            
            # If detection limit is higher than 10% of median value, auto-adjust
            auto_detection_limit = detection_limit
            if detection_limit > data_median * 0.1:
                auto_detection_limit = data_median * 0.01  # 1% of median
                print(f"Auto-adjusting detection limit from {detection_limit:.6f} to {auto_detection_limit:.6f} based on data scale")
            
            # Remove values below detection limit
            valid_mask &= filtered_df[value_column] >= auto_detection_limit
            
            # Remove quality-flagged data (if Quality_Flags column exists)
            if 'Quality_Flags' in filtered_df.columns:
                # Remove rows with low_signal flags
                quality_mask = ~filtered_df['Quality_Flags'].str.contains('low_signal', na=False)
                valid_mask &= quality_mask
                print(f"Removed {(~quality_mask).sum()} low_signal flagged points")
            
            # Remove suspiciously regular small values (likely detection limit artifacts)
            # Look for repeated very small values (e.g., 0.00000073)
            if len(data_values) > 10:
                # Find the most common small values
                small_values = data_values[data_values < data_median * 0.1]
                if len(small_values) > 3:
                    from collections import Counter
                    value_counts = Counter(np.round(small_values, 8))  # Round to avoid floating point issues
                    
                    # If any value appears more than 3 times and is very small, it's likely noise
                    for value, count in value_counts.items():
                        if count >= 3 and value < data_median * 0.05:
                            noise_mask = np.abs(filtered_df[value_column] - value) < 1e-8
                            valid_mask &= ~noise_mask
                            print(f"Removed {noise_mask.sum()} repeated noise values around {value:.8f}")
            
            # Remove values below threshold of rolling average
            if threshold_percent > 0:
                rolling_avg = filtered_df[value_column].rolling(window=5, min_periods=1).mean()
                threshold_values = rolling_avg * (threshold_percent / 100.0)
                rolling_mask = (filtered_df[value_column] >= threshold_values) | (filtered_df[time_column] == 0)
                valid_mask &= rolling_mask
            
            # Apply filter
            original_count = len(filtered_df)
            filtered_df = filtered_df[valid_mask].reset_index(drop=True)
            filtered_count = len(filtered_df)
            
            print(f"Noise filtering: Removed {original_count - filtered_count} points ({original_count - filtered_count}/{original_count} = {100*(original_count - filtered_count)/original_count:.1f}%)")
            
            return filtered_df
            
        except Exception as e:
            raise TDACalculationError(f"Data filtering failed: {str(e)}")
    
    @staticmethod
    def ppm_to_mol_conversion(ppm_values: np.ndarray, 
                             sample_mass_g: float,
                             surface_area_cm2: float = None) -> np.ndarray:
        """
        Convert hydrogen concentrations from ppm to mol units
        
        Args:
            ppm_values: Array of H concentrations in ppm
            sample_mass_g: Sample mass in grams
            surface_area_cm2: Surface area for surface normalization (optional)
        
        Returns:
            Array of H content in mol (or mol/cm² if surface_area provided)
        """
        try:
            # H2 molecular weight = 2.016 g/mol
            H2_MW = 2.016
            
            # Convert ppm to mol
            # ppm = mg H2 / kg sample = (mg H2 / 1000 g sample)
            # mol H2 = (ppm × sample_mass_g × 1e-6) / H2_MW
            mol_values = (ppm_values * sample_mass_g * 1e-6) / H2_MW
            
            # Surface normalize if area provided
            if surface_area_cm2 is not None and surface_area_cm2 > 0:
                mol_values = mol_values / surface_area_cm2
            
            return mol_values
            
        except Exception as e:
            raise TDACalculationError(f"Unit conversion failed: {str(e)}")
    
    @staticmethod
    def mol_to_ppm_conversion(mol_values: np.ndarray,
                             sample_mass_g: float,
                             surface_area_cm2: float = None) -> np.ndarray:
        """
        Convert hydrogen concentrations from mol to ppm units
        
        Args:
            mol_values: Array of H content in mol (or mol/cm²)
            sample_mass_g: Sample mass in grams
            surface_area_cm2: Surface area if mol_values are surface normalized
        
        Returns:
            Array of H concentrations in ppm
        """
        try:
            # H2 molecular weight = 2.016 g/mol
            H2_MW = 2.016
            
            mol_total = mol_values.copy()
            
            # Convert from surface normalized if needed
            if surface_area_cm2 is not None and surface_area_cm2 > 0:
                mol_total = mol_values * surface_area_cm2
            
            # Convert mol to ppm
            # ppm = (mol H2 × H2_MW × 1e6) / sample_mass_g
            ppm_values = (mol_total * H2_MW * 1e6) / sample_mass_g
            
            return ppm_values
            
        except Exception as e:
            raise TDACalculationError(f"Unit conversion failed: {str(e)}")


class TemperatureCorrectionUtils:
    """Utility functions for temperature-dependent diffusion analysis"""
    
    @staticmethod
    def arrhenius_temperature_correction(D_measured: float,
                                       T_measured: float,
                                       T_target: float,
                                       activation_energy_kJ_mol: float = 7.5) -> float:
        """
        Apply Arrhenius temperature correction to diffusion coefficient
        
        D(T) = D₀ × exp(-Q/RT)
        
        Args:
            D_measured: Measured diffusion coefficient (cm²/s)
            T_measured: Temperature of measurement (°C)
            T_target: Target temperature for correction (°C)
            activation_energy_kJ_mol: Activation energy in kJ/mol
        
        Returns:
            Temperature-corrected diffusion coefficient (cm²/s)
        """
        try:
            # Convert temperatures to Kelvin
            T_meas_K = T_measured + 273.15
            T_targ_K = T_target + 273.15
            
            # Gas constant R = 8.314 J/(mol·K) = 0.008314 kJ/(mol·K)
            R = 0.008314
            
            # Apply Arrhenius equation
            # D_target = D_measured × exp(Q/R × (1/T_measured - 1/T_target))
            exponent = (activation_energy_kJ_mol / R) * (1/T_meas_K - 1/T_targ_K)
            D_corrected = D_measured * np.exp(exponent)
            
            return float(D_corrected)
            
        except Exception as e:
            raise TDACalculationError(f"Temperature correction failed: {str(e)}")
    
    @staticmethod
    def get_literature_D_at_temperature(material: str = "steel",
                                      temperature_C: float = 25) -> Dict[str, float]:
        """
        Get literature diffusion coefficient values at specified temperature
        
        Args:
            material: Material type
            temperature_C: Temperature in Celsius
        
        Returns:
            Dictionary with literature D values
        """
        try:
            # Base values at room temperature (25°C)
            base_values = {
                "steel": 1.0e-7,  # cm²/s
                "iron": 1.0e-8,
                "austenitic_steel": 1.0e-7,
                "ferritic_steel": 5.0e-8
            }
            
            # Default activation energy (kJ/mol)
            activation_energies = {
                "steel": 7.5,
                "iron": 8.0,
                "austenitic_steel": 7.5,
                "ferritic_steel": 10.0
            }
            
            material_key = material.lower()
            if material_key not in base_values:
                material_key = "steel"  # Default fallback
            
            base_D = base_values[material_key]
            Q = activation_energies[material_key]
            
            # Apply temperature correction
            D_at_temp = TemperatureCorrectionUtils.arrhenius_temperature_correction(
                base_D, 25.0, temperature_C, Q
            )
            
            return {
                "D_literature": D_at_temp,
                "base_D_25C": base_D,
                "activation_energy": Q,
                "temperature": temperature_C,
                "material": material_key
            }
            
        except Exception as e:
            return {
                "D_literature": 1.0e-7,
                "base_D_25C": 1.0e-7,
                "activation_energy": 7.5,
                "temperature": temperature_C,
                "material": "steel",
                "error": str(e)
            }


class DiffusionAnalysisEngine:
    """Main engine for performing complete diffusion analysis"""
    
    def __init__(self):
        self.tail_analyzer = TailRegionAnalyzer()
        self.plot_calculator = DiffusionPlotCalculator()
        self.regression_analyzer = LinearRegressionAnalyzer()
        self.diffusion_calculator = DiffusionCoefficientCalculator()
        self.filter_utils = DataFilteringUtils()
        self.temp_utils = TemperatureCorrectionUtils()
    
    def analyze_diffusion_behavior(self,
                                 time_minutes: List[float],
                                 desorption_rate: List[float],
                                 cumulative_hydrogen: List[float],
                                 analysis_type: str = "1_sqrt_t",
                                 tail_start: Optional[float] = None,
                                 sample_thickness: float = 0.1,
                                 calculate_D: bool = True) -> DiffusionAnalysisResult:
        """
        Perform complete diffusion analysis
        
        Args:
            time_minutes: Time data in minutes
            desorption_rate: Hydrogen desorption rate
            cumulative_hydrogen: Cumulative hydrogen content
            analysis_type: "1_sqrt_t", "sqrt_t", or "log_log"
            tail_start: Manual tail start time (auto-detect if None)
            sample_thickness: Sample thickness for D calculation
            calculate_D: Whether to calculate diffusion coefficient
        
        Returns:
            DiffusionAnalysisResult with complete analysis
        """
        try:
            # Auto-detect tail start if not provided
            if tail_start is None:
                tail_start = self.tail_analyzer.find_tail_start(time_minutes, desorption_rate)
            
            # Validate tail region
            validation = self.tail_analyzer.validate_tail_region(
                time_minutes, desorption_rate, tail_start
            )
            
            if not validation['is_valid']:
                raise TDACalculationError(f"Invalid tail region: {validation['warnings']}")
            
            # Calculate plot data based on analysis type
            if analysis_type == "1_sqrt_t":
                x_data, y_data = self.plot_calculator.calculate_1_sqrt_t_plot(
                    time_minutes, desorption_rate, tail_start
                )
            elif analysis_type == "sqrt_t":
                x_data, y_data = self.plot_calculator.calculate_sqrt_t_plot(
                    time_minutes, cumulative_hydrogen, tail_start
                )
            elif analysis_type == "log_log":
                x_data, y_data = self.plot_calculator.calculate_log_log_plot(
                    time_minutes, desorption_rate, tail_start
                )
            else:
                raise TDACalculationError(f"Unknown analysis type: {analysis_type}")
            
            # Perform linear regression
            regression_results = self.regression_analyzer.perform_linear_regression(x_data, y_data)
            
            # Create result object
            result = DiffusionAnalysisResult()
            result.tail_start_time = tail_start
            result.analysis_type = analysis_type
            result.slope = regression_results['slope']
            result.intercept = regression_results['intercept']
            result.r_squared = regression_results['r_squared']
            result.std_error = regression_results['std_error']
            result.p_value = regression_results['p_value']
            result.num_points = regression_results['num_points']
            result.x_data = x_data.tolist()
            result.y_data = y_data.tolist()
            result.fit_x = regression_results['fit_x']
            result.fit_y = regression_results['fit_y']
            
            # Assess fit quality
            result.goodness_of_fit = self.regression_analyzer.assess_fit_quality(
                result.r_squared, result.p_value, result.num_points
            )
            
            # Calculate diffusion coefficient if requested and appropriate
            if calculate_D and analysis_type == "1_sqrt_t":
                result.diffusion_coefficient = self.diffusion_calculator.calculate_diffusion_coefficient(
                    result.slope, sample_thickness
                )
                result.thickness = sample_thickness
            
            return result
            
        except Exception as e:
            raise TDACalculationError(f"Diffusion analysis failed: {str(e)}")