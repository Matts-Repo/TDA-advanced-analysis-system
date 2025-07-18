"""
Plot Manager Module for TDA Analysis System

This module provides comprehensive plotting capabilities for processed TDA data with extensive 
customization options, data filtering, and professional export features.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy import signal, stats
from typing import List, Dict, Optional, Tuple
import json
from dataclasses import dataclass, field

from .error_handling import TDAFileError, TDAError
from .calcs import DiffusionAnalysisEngine, DiffusionAnalysisResult, DataFilteringUtils


@dataclass
class PlotDataset:
    """Complete dataset structure for plotting with all metadata"""
    # File information
    name: str = ""
    csv_path: str = ""
    
    # Experiment metadata (from CSV header)
    experiment_name: str = ""
    processing_date: str = ""
    
    # Sample parameters
    sample_weight: float = 0.0
    flow_rate: float = 0.0
    cycle_time: float = 0.0
    
    # Calibration information
    calibration_id: str = ""
    calibration_date: str = ""
    calibration_quality: float = 0.0
    
    # Summary statistics
    total_hydrogen: float = 0.0
    max_rate: float = 0.0
    avg_rate: float = 0.0
    duration_hours: float = 0.0
    
    # Data arrays (parallel lists)
    run_numbers: List[int] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)
    time_minutes: List[float] = field(default_factory=list)
    peak_areas: List[float] = field(default_factory=list)
    peak_heights: List[float] = field(default_factory=list)
    h_ppm_per_min: List[float] = field(default_factory=list)
    h_ppm_over_cycle: List[float] = field(default_factory=list)
    cumulative_h_ppm: List[float] = field(default_factory=list)
    h_mol_cm2_per_min: List[float] = field(default_factory=list)      # For surface normalized data
    h_mol_cm2_over_cycle: List[float] = field(default_factory=list)   # For surface normalized data
    cumulative_h_mol_cm2: List[float] = field(default_factory=list)   # For surface normalized data
    quality_flags: List[str] = field(default_factory=list)
    
    # Calculation mode detection
    calculation_mode: str = "mass_normalized"  # "mass_normalized" or "surface_normalized"
    surface_area: float = 0.0                  # cm² for surface normalized mode
    
    # Plotting configuration
    style: 'DatasetStyle' = field(default_factory=lambda: DatasetStyle())
    filter_options: 'FilterOptions' = field(default_factory=lambda: FilterOptions())
    
    def get_plot_data(self, plot_type: str) -> Tuple[List[float], List[float]]:
        """Get X,Y data for specified plot type"""
        x_data = self.time_minutes
        
        if plot_type == "h_ppm_per_min":
            if self.calculation_mode == "surface_normalized" and self.h_mol_cm2_per_min:
                y_data = self.h_mol_cm2_per_min
            else:
                y_data = self.h_ppm_per_min
        elif plot_type == "cumulative_h_ppm":
            if self.calculation_mode == "surface_normalized" and self.cumulative_h_mol_cm2:
                y_data = self.cumulative_h_mol_cm2
            else:
                y_data = self.cumulative_h_ppm
        elif plot_type == "peak_areas":
            y_data = self.peak_areas
        else:
            raise ValueError(f"Unknown plot type: {plot_type}")
        
        return x_data, y_data
    
    def get_display_label(self) -> str:
        """Get formatted label for display"""
        if self.style.label:
            return self.style.label
        return self.experiment_name or self.name


@dataclass
class DatasetStyle:
    """Complete styling options for datasets"""
    color: str = '#1f77b4'              # Hex color
    linestyle: str = '-'                # '-', '--', '-.', ':'
    linewidth: float = 2.0              # Line thickness
    marker: str = 'None'                # 'o', 's', '^', 'v', 'd', 'None'
    markersize: float = 6.0             # Marker size
    alpha: float = 1.0                  # Transparency (0-1)
    label: str = ""                     # Custom legend label
    zorder: int = 1                     # Plot order (higher = on top)


@dataclass
class FilterOptions:
    """Data filtering and processing options"""
    # Zero and noise filtering
    exclude_zeros: bool = False
    keep_origin: bool = True            # Keep (0, 0) point even if excluding zeros
    threshold_percent: float = 2.0      # Remove values below this % of rolling average
    detection_limit: float = 0.1        # Minimum detectable value (ppm)
    
    # Outlier removal
    remove_outliers: bool = False
    outlier_method: str = "zscore"      # "zscore", "iqr", "manual"
    outlier_threshold: float = 3.0      # Z-score threshold or IQR multiplier
    
    # Data smoothing
    apply_smoothing: bool = False
    smoothing_method: str = "moving_avg"  # "moving_avg", "savgol", "lowess"
    smoothing_window: int = 5           # Window size
    
    # Time range filtering
    time_range_filter: bool = False
    time_start: float = 0.0             # Start time (minutes)
    time_end: float = 1000.0            # End time (minutes)
    
    # Value range filtering
    value_range_filter: bool = False
    value_min: float = 0.0              # Minimum Y value
    value_max: float = 1000.0           # Maximum Y value


@dataclass
class PlotOptions:
    """Complete plot formatting options"""
    # Figure settings
    figure_size: Tuple[float, float] = (10, 6)
    dpi: int = 100
    
    # Axis settings
    xlabel: str = "Time (minutes)"
    ylabel: str = ""
    title: str = ""
    
    # Dual axis settings
    dual_axis: bool = False
    ylabel_right: str = ""              # Right Y-axis label for dual axis mode
    primary_only: bool = False          # Show only primary data in dual axis mode
    clean_legend: bool = True           # Don't add unit labels to legend entries
    single_axis_units: str = "mol"      # "mol" or "ppm" for single axis mode
    
    # Diffusion analysis settings
    use_mol_units: bool = True          # Use mol/cm² units for diffusion analysis
    
    # Axis limits
    xlim_auto: bool = True
    xlim_min: float = 0
    xlim_max: float = 100
    ylim_auto: bool = True
    ylim_min: float = 0
    ylim_max: float = 1
    
    # Scale
    log_x: bool = False
    log_y: bool = False
    
    # Grid and styling
    show_grid: bool = True
    grid_alpha: float = 0.3
    
    # Legend
    show_legend: bool = True
    legend_location: str = "best"       # "best", "upper right", "upper left", etc.
    legend_fontsize: int = 10
    legend_frame: bool = True
    legend_outside: bool = False
    
    # Professional formatting
    despine: bool = True                # Remove top and right spines
    tight_layout: bool = True


@dataclass
class ExportOptions:
    """Export configuration options"""
    filename: str = "tda_plot.png"
    format: str = "PNG"                 # "PNG", "PDF", "SVG", "EPS"
    dpi: int = 300
    transparent: bool = False
    bbox_inches: str = 'tight'
    pad_inches: float = 0.1
    facecolor: str = 'white'


class ProcessedCSVParser:
    """Parse enhanced CSV files from Module 2 with complete metadata extraction"""
    
    @staticmethod
    def parse_csv_file(csv_path: str) -> PlotDataset:
        """
        Parse enhanced CSV with metadata header from Module 2
        Returns PlotDataset with all data and metadata
        """
        dataset = PlotDataset(
            name=os.path.basename(csv_path).replace('.csv', ''),
            csv_path=csv_path
        )
        
        try:
            # Parse metadata from header comments
            metadata = ProcessedCSVParser.parse_metadata_header(csv_path)
            
            # Extract experiment information
            dataset.experiment_name = metadata.get('experiment_name', dataset.name)
            dataset.processing_date = metadata.get('generated', '')
            
            # Extract sample parameters
            dataset.sample_weight = float(metadata.get('sample_weight', 0))
            dataset.flow_rate = float(metadata.get('flow_rate', 0))
            dataset.cycle_time = float(metadata.get('cycle_time', 0))
            
            # Extract calibration information
            dataset.calibration_id = metadata.get('calibration_id', '')
            dataset.calibration_date = metadata.get('calibration_date', '')
            dataset.calibration_quality = float(metadata.get('quality_score', 0))
            
            # Extract summary statistics
            dataset.total_hydrogen = float(metadata.get('total_hydrogen_released', 0))
            dataset.max_rate = float(metadata.get('maximum_evolution_rate', 0))
            dataset.avg_rate = float(metadata.get('average_evolution_rate', 0))
            dataset.duration_hours = float(metadata.get('experiment_duration', 0)) / 60
            
            # Parse data columns (skip comment lines)
            df = pd.read_csv(csv_path, comment='#')
            
            # Detect calculation mode based on column presence
            surface_area_columns = ['H_mol_cm2_per_min', 'H_mol_cm2_over_cycle', 'Cumulative_H_mol_cm2']
            has_surface_columns = all(col in df.columns for col in surface_area_columns)
            
            if has_surface_columns:
                dataset.calculation_mode = "surface_normalized"
                # Extract surface area from metadata if available
                dataset.surface_area = float(metadata.get('surface_area', 0))
            else:
                dataset.calculation_mode = "mass_normalized"
            
            # Validate core required columns
            required_columns = [
                'Run', 'Timestamp', 'Time_minutes', 'Peak_Area_µVs', 
                'Peak_Height_µV'
            ]
            
            # Add calculation-specific required columns
            if dataset.calculation_mode == "surface_normalized":
                required_columns.extend(surface_area_columns)
                required_columns.extend(['H_ppm_per_min', 'H_ppm_over_cycle', 'Cumulative_H_ppm'])  # Also included for reference
            else:
                required_columns.extend(['H_ppm_per_min', 'H_ppm_over_cycle', 'Cumulative_H_ppm'])
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Extract basic data arrays
            dataset.run_numbers = df['Run'].tolist()
            dataset.timestamps = df['Timestamp'].tolist()
            dataset.time_minutes = df['Time_minutes'].tolist()
            dataset.peak_areas = df['Peak_Area_µVs'].tolist()
            dataset.peak_heights = df['Peak_Height_µV'].tolist()
            
            # Extract calculation-specific data
            if dataset.calculation_mode == "surface_normalized":
                dataset.h_mol_cm2_per_min = df['H_mol_cm2_per_min'].tolist()
                dataset.h_mol_cm2_over_cycle = df['H_mol_cm2_over_cycle'].tolist()
                dataset.cumulative_h_mol_cm2 = df['Cumulative_H_mol_cm2'].tolist()
                # Also extract mass-normalized for reference
                dataset.h_ppm_per_min = df['H_ppm_per_min'].tolist()
                dataset.h_ppm_over_cycle = df['H_ppm_over_cycle'].tolist()
                dataset.cumulative_h_ppm = df['Cumulative_H_ppm'].tolist()
            else:
                dataset.h_ppm_per_min = df['H_ppm_per_min'].tolist()
                dataset.h_ppm_over_cycle = df['H_ppm_over_cycle'].tolist()
                dataset.cumulative_h_ppm = df['Cumulative_H_ppm'].tolist()
            
            # Extract quality flags if present
            if 'Quality_Flags' in df.columns:
                dataset.quality_flags = df['Quality_Flags'].tolist()
            
            # Set default styling
            dataset.style = DatasetStyle()
            
            return dataset
            
        except Exception as e:
            raise TDAFileError(f"Failed to parse CSV file {csv_path}: {str(e)}")
    
    @staticmethod
    def parse_metadata_header(csv_path: str) -> Dict[str, str]:
        """Extract metadata from CSV header comments"""
        metadata = {}
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                
                # Stop at data section
                if not line.startswith('#'):
                    break
                
                # Parse metadata lines
                if ':' in line:
                    # Remove leading # and split on first colon
                    content = line[1:].strip()
                    if ':' in content:
                        key, value = content.split(':', 1)
                        key = key.strip().lower().replace(' ', '_').replace('=', '')
                        value = value.strip()
                        
                        # Parse numeric values
                        if key in ['sample_weight', 'flow_rate', 'cycle_time', 'quality_score', 
                                 'total_hydrogen_released', 'maximum_evolution_rate', 
                                 'average_evolution_rate', 'experiment_duration', 'surface_area']:
                            try:
                                # Extract numeric part (remove units)
                                numeric_part = value.split()[0]
                                metadata[key] = numeric_part
                            except:
                                metadata[key] = value
                        else:
                            metadata[key] = value
        
        return metadata


class DataFilter:
    """Apply various filtering and smoothing operations to dataset"""
    
    @staticmethod
    def apply_all_filters(dataset: PlotDataset, plot_type: str) -> Tuple[List[float], List[float]]:
        """Apply all enabled filters to dataset and return filtered X,Y data"""
        x_data, y_data = dataset.get_plot_data(plot_type)
        
        # Convert to numpy arrays for processing
        x_array = np.array(x_data)
        y_array = np.array(y_data)
        
        # Apply zero filtering first (if enabled)
        if dataset.filter_options.exclude_zeros:
            # Create DataFrame for filtering
            temp_df = pd.DataFrame({
                'Time_min': x_array,
                'Value': y_array
            })
            
            filtered_df = DataFilteringUtils.filter_zeros(
                temp_df, 
                value_column='Value',
                time_column='Time_min',
                keep_origin=dataset.filter_options.keep_origin,
                threshold_percent=dataset.filter_options.threshold_percent,
                detection_limit=dataset.filter_options.detection_limit
            )
            
            if not filtered_df.empty:
                x_array = filtered_df['Time_min'].values
                y_array = filtered_df['Value'].values
        
        # Apply filters in sequence
        if dataset.filter_options.time_range_filter:
            x_array, y_array = DataFilter.filter_time_range(
                x_array, y_array, 
                dataset.filter_options.time_start, 
                dataset.filter_options.time_end
            )
        
        if dataset.filter_options.value_range_filter:
            x_array, y_array = DataFilter.filter_value_range(
                x_array, y_array,
                dataset.filter_options.value_min,
                dataset.filter_options.value_max
            )
        
        if dataset.filter_options.remove_outliers:
            x_array, y_array = DataFilter.remove_outliers(
                x_array, y_array,
                dataset.filter_options.outlier_method,
                dataset.filter_options.outlier_threshold
            )
        
        if dataset.filter_options.apply_smoothing:
            y_array = DataFilter.apply_smoothing(
                y_array,
                dataset.filter_options.smoothing_method,
                dataset.filter_options.smoothing_window
            )
        
        return x_array.tolist(), y_array.tolist()
    
    @staticmethod
    def remove_outliers(x_data: np.ndarray, y_data: np.ndarray, 
                       method: str = "zscore", threshold: float = 3.0) -> Tuple[np.ndarray, np.ndarray]:
        """Remove outliers using specified method"""
        if len(y_data) < 3:
            return x_data, y_data
        
        if method == "zscore":
            z_scores = np.abs(stats.zscore(y_data))
            mask = z_scores < threshold
        elif method == "iqr":
            Q1, Q3 = np.percentile(y_data, [25, 75])
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR  # threshold used as IQR multiplier
            upper_bound = Q3 + threshold * IQR
            mask = (y_data >= lower_bound) & (y_data <= upper_bound)
        else:
            return x_data, y_data  # Unknown method, return unchanged
        
        return x_data[mask], y_data[mask]
    
    @staticmethod
    def apply_smoothing(y_data: np.ndarray, method: str = "moving_avg", 
                       window: int = 5) -> np.ndarray:
        """Apply smoothing to data"""
        if len(y_data) < window:
            return y_data
        
        if method == "moving_avg":
            return DataFilter._moving_average(y_data, window)
        elif method == "savgol":
            try:
                from scipy.signal import savgol_filter
                # Ensure window is odd and <= data length
                window = min(window, len(y_data))
                if window % 2 == 0:
                    window -= 1
                window = max(3, window)  # Minimum window size
                polyorder = min(3, window - 1)
                return savgol_filter(y_data, window, polyorder)
            except ImportError:
                return DataFilter._moving_average(y_data, window)
        elif method == "lowess":
            try:
                from statsmodels.nonparametric.lowess import lowess
                frac = min(window / len(y_data), 0.3)  # Convert window to fraction
                smoothed = lowess(y_data, range(len(y_data)), frac=frac)
                return smoothed[:, 1]
            except ImportError:
                return DataFilter._moving_average(y_data, window)
        
        return y_data  # Unknown method, return unchanged
    
    @staticmethod
    def _moving_average(data: np.ndarray, window: int) -> np.ndarray:
        """Calculate moving average"""
        if window <= 1:
            return data
        
        # Pad data to handle edges
        padded = np.pad(data, (window//2, window//2), mode='edge')
        return np.convolve(padded, np.ones(window)/window, mode='valid')
    
    @staticmethod
    def filter_time_range(x_data: np.ndarray, y_data: np.ndarray, 
                         start_time: float, end_time: float) -> Tuple[np.ndarray, np.ndarray]:
        """Filter data to specified time range"""
        mask = (x_data >= start_time) & (x_data <= end_time)
        return x_data[mask], y_data[mask]
    
    @staticmethod
    def filter_value_range(x_data: np.ndarray, y_data: np.ndarray,
                          min_value: float, max_value: float) -> Tuple[np.ndarray, np.ndarray]:
        """Filter data to specified value range"""
        mask = (y_data >= min_value) & (y_data <= max_value)
        return x_data[mask], y_data[mask]


class PlotGenerator:
    """Core plotting functionality using matplotlib"""
    
    def __init__(self):
        self.figure = None
        self.axes = None
        
        # Set matplotlib style
        plt.style.use('default')
        
        # Professional color palette
        self.default_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        self.default_linestyles = ['-', '--', '-.', ':']
    
    def create_time_series_plot(self, datasets: List[PlotDataset], 
                               plot_type: str = "h_ppm_per_min", 
                               options: PlotOptions = None) -> Figure:
        """
        Generate time-series plot for multiple datasets
        
        Args:
            datasets: List of PlotDataset objects to plot
            plot_type: "h_ppm_per_min", "cumulative_h_ppm", or "peak_areas"
            options: PlotOptions for formatting
        """
        if options is None:
            options = PlotOptions()
        
        # Create figure and axes
        self.figure = Figure(figsize=options.figure_size, dpi=options.dpi)
        self.axes = self.figure.add_subplot(111)
        
        # Check for dual axis mode
        if options.dual_axis and plot_type in ["h_ppm_per_min", "cumulative_h_ppm"]:
            return self._create_dual_axis_plot(datasets, plot_type, options)
        
        # Set Y-axis label based on plot type, calculation mode, and unit preference
        has_surface_normalized = any(dataset.calculation_mode == "surface_normalized" for dataset in datasets)
        
        # Determine units based on user preference for single axis mode
        if options.single_axis_units == "mol":
            use_mol_units = True
        elif options.single_axis_units == "ppm":
            use_mol_units = False
        else:
            # Default behavior - use mol if surface normalized, otherwise ppm
            use_mol_units = has_surface_normalized
        
        if plot_type == "h_ppm_per_min":
            if use_mol_units:
                default_ylabel = "Hydrogen Evolution Rate (mol/cm²/min)"
            else:
                default_ylabel = "Hydrogen Evolution Rate (ppm/min)"
        elif plot_type == "cumulative_h_ppm":
            if use_mol_units:
                default_ylabel = "Cumulative Hydrogen (mol/cm²)"
            else:
                default_ylabel = "Cumulative Hydrogen Content (ppm)"
        elif plot_type == "peak_areas":
            default_ylabel = "Peak Area (µV*s)"
        else:
            default_ylabel = "Value"
        
        # Plot each dataset
        for i, dataset in enumerate(datasets):
            try:
                # Apply filters and get plot data
                x_data, y_data = DataFilter.apply_all_filters(dataset, plot_type)
                
                if not x_data or not y_data:
                    print(f"Warning: No data to plot for dataset {dataset.name}")
                    continue
                
                # Convert units if needed for single axis mode
                if use_mol_units and plot_type in ["h_ppm_per_min", "cumulative_h_ppm"]:
                    # Convert ppm data to mol units
                    ppm_array = np.array(y_data)
                    mol_data = DataFilteringUtils.ppm_to_mol_conversion(
                        ppm_array,
                        dataset.sample_weight,
                        dataset.surface_area if dataset.calculation_mode == "surface_normalized" else None
                    )
                    y_data = mol_data.tolist()
                elif not use_mol_units and plot_type in ["h_ppm_per_min", "cumulative_h_ppm"]:
                    # If dataset has mol data but we want ppm, convert back
                    if dataset.calculation_mode == "surface_normalized":
                        mol_array = np.array(y_data)
                        ppm_data = DataFilteringUtils.mol_to_ppm_conversion(
                            mol_array,
                            dataset.sample_weight,
                            dataset.surface_area
                        )
                        y_data = ppm_data.tolist()
                
                # Use dataset style or assign defaults
                style = dataset.style
                if not style.color or style.color == '#1f77b4':
                    style.color = self.default_colors[i % len(self.default_colors)]
                # Only auto-assign line styles if not explicitly set and there are multiple datasets
                if not style.linestyle:
                    style.linestyle = self.default_linestyles[i % len(self.default_linestyles)]
                
                # Plot the data with consistent styling
                line = self.axes.plot(
                    x_data, y_data,
                    color=style.color,
                    linestyle=style.linestyle,
                    linewidth=style.linewidth,
                    marker=style.marker if style.marker != 'None' else None,
                    markersize=max(style.markersize * 0.8, 3),  # Slightly smaller markers
                    alpha=style.alpha,
                    label=dataset.get_display_label(),
                    zorder=style.zorder
                )[0]
                
                # Store reference for potential updates
                dataset._plot_line = line
                
            except Exception as e:
                print(f"Warning: Failed to plot dataset {dataset.name}: {e}")
                continue
        
        # Apply formatting
        self._apply_plot_formatting(options, default_ylabel)
        
        return self.figure
    
    def _create_dual_axis_plot(self, datasets: List[PlotDataset], 
                              plot_type: str, options: PlotOptions) -> Figure:
        """Create dual axis plot with mol units on left and ppm units on right"""
        
        # Create figure and main axis
        self.figure = Figure(figsize=options.figure_size, dpi=options.dpi)
        self.axes = self.figure.add_subplot(111)
        
        # Create secondary axis
        ax_right = self.axes.twinx()
        
        # Set labels for dual axis
        if plot_type == "h_ppm_per_min":
            left_label = "H₂ Evolution Rate (mol/cm²/min)"
            right_label = "H₂ Evolution Rate (ppm/min)"
        elif plot_type == "cumulative_h_ppm":
            left_label = "Cumulative H₂ (mol/cm²)"
            right_label = "Cumulative H₂ (ppm)"
        
        # Plot each dataset on both axes
        for i, dataset in enumerate(datasets):
            try:
                # Apply filters and get plot data
                x_data, y_data = DataFilter.apply_all_filters(dataset, plot_type)
                
                if not x_data or not y_data:
                    print(f"Warning: No data to plot for dataset {dataset.name}")
                    continue
                
                # Convert ppm data to mol data for left axis
                if plot_type == "h_ppm_per_min":
                    ppm_data = dataset.h_ppm_per_min if len(dataset.h_ppm_per_min) > 0 else y_data
                elif plot_type == "cumulative_h_ppm":
                    ppm_data = dataset.cumulative_h_ppm if len(dataset.cumulative_h_ppm) > 0 else y_data
                
                # Apply same filtering to ppm data
                x_array = np.array(x_data)
                ppm_array = np.array(ppm_data[:len(x_array)])
                
                # Convert to mol units for left axis
                mol_data = DataFilteringUtils.ppm_to_mol_conversion(
                    ppm_array, 
                    dataset.sample_weight,
                    dataset.surface_area if dataset.calculation_mode == "surface_normalized" else None
                )
                
                # Use dataset style or assign defaults
                style = dataset.style
                if not style.color or style.color == '#1f77b4':
                    style.color = self.default_colors[i % len(self.default_colors)]
                
                # Determine legend labels based on options
                if options.clean_legend:
                    mol_label = dataset.get_display_label()
                    ppm_label = f"{dataset.get_display_label()} (ppm ref)"
                else:
                    mol_label = f"{dataset.get_display_label()} (mol)"
                    ppm_label = f"{dataset.get_display_label()} (ppm)"
                
                # Plot on left axis (mol units)
                line_left = self.axes.plot(
                    x_data, mol_data[:len(x_data)],
                    color=style.color,
                    linestyle=style.linestyle,
                    linewidth=style.linewidth,
                    alpha=style.alpha,
                    label=mol_label,
                    zorder=style.zorder
                )[0]
                
                # Plot on right axis (ppm units) - only if not primary_only mode
                if not options.primary_only:
                    line_right = ax_right.plot(
                        x_data, y_data,
                        color=style.color,
                        linestyle='--',  # Always dashed for reference
                        linewidth=style.linewidth * 0.7,
                        alpha=style.alpha * 0.5,
                        label=ppm_label,
                        zorder=style.zorder - 0.1
                    )[0]
                
            except Exception as e:
                print(f"Warning: Failed to plot dataset {dataset.name}: {e}")
                continue
        
        # Apply formatting to both axes
        self.axes.set_xlabel(options.xlabel, fontsize=12)
        self.axes.set_ylabel(left_label, fontsize=12, color='black')
        
        # Only show right axis label if we're plotting secondary data
        if not options.primary_only:
            ax_right.set_ylabel(right_label, fontsize=12, color='gray')
        else:
            ax_right.set_ylabel("")  # Hide right axis label
            ax_right.tick_params(right=False, labelright=False)  # Hide right ticks
        
        if options.title:
            self.axes.set_title(options.title, fontsize=14, fontweight='bold')
        
        # Grid and styling
        if options.show_grid:
            self.axes.grid(True, alpha=options.grid_alpha, linestyle='-', linewidth=0.5)
        
        # Combined legend
        if options.show_legend:
            lines1, labels1 = self.axes.get_legend_handles_labels()
            
            if options.primary_only:
                # Only show primary axis legend
                self.axes.legend(lines1, labels1, 
                               loc=options.legend_location, fontsize=options.legend_fontsize)
            else:
                # Show combined legend
                lines2, labels2 = ax_right.get_legend_handles_labels()
                self.axes.legend(lines1 + lines2, labels1 + labels2, 
                               loc=options.legend_location, fontsize=options.legend_fontsize)
        
        # Professional styling
        if options.despine:
            self.axes.spines['top'].set_visible(False)
            ax_right.spines['top'].set_visible(False)
        
        # Improve tick appearance
        self.axes.tick_params(direction='out', length=4, width=1)
        ax_right.tick_params(direction='out', length=4, width=1)
        
        # Tight layout
        if options.tight_layout:
            self.figure.tight_layout()
        
        return self.figure
    
    def _apply_plot_formatting(self, options: PlotOptions, default_ylabel: str):
        """Apply professional formatting to plot"""
        
        # Set labels and title
        self.axes.set_xlabel(options.xlabel, fontsize=12)
        self.axes.set_ylabel(options.ylabel or default_ylabel, fontsize=12)
        
        if options.title:
            self.axes.set_title(options.title, fontsize=14, fontweight='bold')
        
        # Set axis limits
        if not options.xlim_auto:
            self.axes.set_xlim(options.xlim_min, options.xlim_max)
        if not options.ylim_auto:
            self.axes.set_ylim(options.ylim_min, options.ylim_max)
        
        # Set scale
        if options.log_x:
            self.axes.set_xscale('log')
        if options.log_y:
            self.axes.set_yscale('log')
        
        # Apply grid
        if options.show_grid:
            self.axes.grid(True, alpha=options.grid_alpha, linestyle='-', linewidth=0.5)
        
        # Configure legend
        if options.show_legend:
            legend = self.axes.legend(
                loc=options.legend_location,
                fontsize=options.legend_fontsize,
                frameon=options.legend_frame
            )
            
            if options.legend_outside:
                legend.set_bbox_to_anchor((1.05, 1), loc='upper left')
        
        # Professional styling
        if options.despine:
            self.axes.spines['top'].set_visible(False)
            self.axes.spines['right'].set_visible(False)
        
        # Improve tick appearance
        self.axes.tick_params(direction='out', length=4, width=1)
        
        # Tight layout
        if options.tight_layout:
            self.figure.tight_layout()
    
    def create_diffusion_plot(self, dataset: PlotDataset,
                             plot_type: str = "1_sqrt_t",
                             tail_start_time: float = 120.0,
                             show_linear_fit: bool = True,
                             calculate_D: bool = True,
                             sample_thickness: float = 0.1,
                             temperature: float = 25.0,
                             filter_noise: bool = False,
                             detection_limit: float = 0.1,
                             options: PlotOptions = None) -> Tuple[Figure, DiffusionAnalysisResult]:
        """
        Generate diffusion analysis plot with linear regression
        
        Args:
            dataset: PlotDataset with TDA data
            plot_type: "1_sqrt_t", "sqrt_t", or "log_log"
            tail_start_time: Start time for tail region (minutes)
            show_linear_fit: Whether to show linear regression line
            calculate_D: Whether to calculate diffusion coefficient
            sample_thickness: Sample thickness for D calculation (cm)
            options: PlotOptions for formatting
        
        Returns:
            (matplotlib Figure, DiffusionAnalysisResult)
        """
        if options is None:
            options = PlotOptions()
        
        try:
            # Initialize diffusion analysis engine
            diffusion_engine = DiffusionAnalysisEngine()
            
            # Determine if we should use mol units
            use_mol_units = getattr(options, 'use_mol_units', True)
            
            # Prepare data for analysis
            time_data = dataset.time_minutes
            desorption_rate = dataset.h_ppm_per_min if dataset.calculation_mode == "mass_normalized" else dataset.h_mol_cm2_per_min
            cumulative_hydrogen = dataset.cumulative_h_ppm if dataset.calculation_mode == "mass_normalized" else dataset.cumulative_h_mol_cm2
            
            # Apply noise filtering if requested (only for tail region analysis)
            if filter_noise:
                print(f"Applying noise filtering with detection limit: {detection_limit:.6f} ppm")
                
                # Create DataFrame for filtering (only use data after tail start)
                tail_mask = np.array(time_data) >= tail_start_time
                tail_time = np.array(time_data)[tail_mask]
                tail_rate = np.array(desorption_rate)[tail_mask]
                
                print(f"Tail region: {len(tail_time)} points from {tail_start_time:.1f} min onwards")
                print(f"Tail rate range: {np.min(tail_rate):.8f} to {np.max(tail_rate):.8f} ppm/min")
                
                if len(tail_time) > 0:
                    # Create DataFrame with quality flags if available from original dataset
                    temp_df = pd.DataFrame({
                        'Time_min': tail_time,
                        'H_ppm_per_min': tail_rate
                    })
                    
                    # Try to add quality flags if they exist in the original dataset
                    if hasattr(dataset, 'quality_flags') and len(dataset.quality_flags) > 0:
                        # Map quality flags to tail region
                        original_time = np.array(dataset.time_minutes)
                        original_flags = np.array(dataset.quality_flags)
                        
                        # Find quality flags for tail region
                        tail_flags = []
                        for t in tail_time:
                            # Find closest time match in original data
                            closest_idx = np.argmin(np.abs(original_time - t))
                            if closest_idx < len(original_flags):
                                tail_flags.append(original_flags[closest_idx])
                            else:
                                tail_flags.append('')
                        
                        temp_df['Quality_Flags'] = tail_flags
                        print(f"Added quality flags: {len([f for f in tail_flags if 'low_signal' in str(f)])} low_signal flags found")
                    
                    filtered_df = DataFilteringUtils.filter_zeros(
                        temp_df,
                        value_column='H_ppm_per_min',
                        time_column='Time_min',
                        keep_origin=False,  # Don't keep origin for tail region
                        threshold_percent=2.0,
                        detection_limit=detection_limit
                    )
                    
                    if not filtered_df.empty and len(filtered_df) < len(temp_df):
                        # Replace tail region data with filtered data
                        filtered_time = filtered_df['Time_min'].tolist()
                        filtered_rate = filtered_df['H_ppm_per_min'].tolist()
                        
                        print(f"Filtering reduced tail region from {len(tail_time)} to {len(filtered_time)} points")
                        
                        # Combine pre-tail and filtered tail data
                        pre_tail_mask = np.array(time_data) < tail_start_time
                        pre_tail_time = np.array(time_data)[pre_tail_mask].tolist()
                        pre_tail_rate = np.array(desorption_rate)[pre_tail_mask].tolist()
                        
                        time_data = pre_tail_time + filtered_time
                        desorption_rate = pre_tail_rate + filtered_rate
                        
                        print(f"Final dataset: {len(time_data)} points total")
                    else:
                        print(f"No filtering applied - would have removed too many points or no noise detected")
            
            # Convert data to mol units if requested
            if use_mol_units:
                # Convert desorption rate and cumulative hydrogen to mol units
                desorption_rate_mol = DataFilteringUtils.ppm_to_mol_conversion(
                    np.array(desorption_rate),
                    dataset.sample_weight,
                    dataset.surface_area if dataset.surface_area > 0 else 1.0  # Default surface area if not available
                )
                cumulative_hydrogen_mol = DataFilteringUtils.ppm_to_mol_conversion(
                    np.array(cumulative_hydrogen),
                    dataset.sample_weight,
                    dataset.surface_area if dataset.surface_area > 0 else 1.0
                )
                
                # Use mol data for analysis
                analysis_desorption_rate = desorption_rate_mol.tolist()
                analysis_cumulative_hydrogen = cumulative_hydrogen_mol.tolist()
            else:
                # Use original ppm data
                analysis_desorption_rate = desorption_rate
                analysis_cumulative_hydrogen = cumulative_hydrogen
            
            # Perform diffusion analysis
            analysis_result = diffusion_engine.analyze_diffusion_behavior(
                time_minutes=time_data,
                desorption_rate=analysis_desorption_rate,
                cumulative_hydrogen=analysis_cumulative_hydrogen,
                analysis_type=plot_type,
                tail_start=tail_start_time,
                sample_thickness=sample_thickness,
                calculate_D=calculate_D
            )
            
            # Store unit information in the analysis result
            analysis_result.units_used = "mol/cm²" if use_mol_units else "ppm"
            analysis_result.surface_area = dataset.surface_area if dataset.surface_area > 0 else 1.0
            analysis_result.sample_weight = dataset.sample_weight
            
            # Apply temperature correction if D was calculated and temperature != 25°C
            if (calculate_D and analysis_result.diffusion_coefficient > 0 and 
                abs(temperature - 25.0) > 0.1):
                
                from .calcs import TemperatureCorrectionUtils
                temp_utils = TemperatureCorrectionUtils()
                
                # Get literature value for comparison at this temperature
                lit_data = temp_utils.get_literature_D_at_temperature("steel", temperature)
                
                # Store original and temperature-corrected D
                analysis_result.original_diffusion_coefficient = analysis_result.diffusion_coefficient
                analysis_result.measurement_temperature = temperature
                analysis_result.literature_D_at_temp = lit_data["D_literature"]
                analysis_result.activation_energy = lit_data["activation_energy"]
            
            # Create figure and axes
            self.figure = Figure(figsize=options.figure_size, dpi=options.dpi)
            self.axes = self.figure.add_subplot(111)
            
            # Set labels based on plot type and unit preference
            
            if plot_type == "1_sqrt_t":
                xlabel = "1/√t (min⁻⁰·⁵)"
                if use_mol_units:
                    ylabel = "Hydrogen Evolution Rate (mol/cm²/min)"
                else:
                    ylabel = "Hydrogen Evolution Rate (ppm/min)"
                title = "Desorption Rate vs 1/√t - Diffusion Analysis"
            elif plot_type == "sqrt_t":
                xlabel = "√t (min⁰·⁵)"
                if use_mol_units:
                    ylabel = "Cumulative Hydrogen (mol/cm²)"
                else:
                    ylabel = "Cumulative Hydrogen (ppm)"
                title = "Cumulative Hydrogen vs √t - Diffusion Analysis"
            elif plot_type == "log_log":
                xlabel = "log(Time) (min)"
                if use_mol_units:
                    ylabel = "log(Evolution Rate) (mol/cm²/min)"
                else:
                    ylabel = "log(Evolution Rate) (ppm/min)"
                title = "Log-Log Plot - Diffusion Analysis"
            else:
                xlabel = "X"
                ylabel = "Y"
                title = "Diffusion Analysis"
            
            # Plot the data points with smaller, cleaner markers
            self.axes.scatter(
                analysis_result.x_data, 
                analysis_result.y_data,
                alpha=0.8,
                s=20,  # Smaller markers
                color='#1f77b4',
                edgecolors='white',
                linewidth=0.5,
                label=f'{dataset.get_display_label()} (tail region)',
                zorder=2
            )
            
            # Plot linear fit if requested
            if show_linear_fit and analysis_result.fit_x and analysis_result.fit_y:
                self.axes.plot(
                    analysis_result.fit_x,
                    analysis_result.fit_y,
                    color='red',
                    linestyle='--',
                    linewidth=2,
                    alpha=0.7,
                    label=f'Linear fit (R² = {analysis_result.r_squared:.3f})',
                    zorder=3
                )
                
                # Single clean text box with essential information
                if analysis_result.r_squared >= 0.8:  # Only show fit info if R² is decent
                    # Create concise information text
                    info_lines = [
                        f'R² = {analysis_result.r_squared:.3f}',
                        f'Slope = {analysis_result.slope:.2e}'
                    ]
                    
                    info_text = '\n'.join(info_lines)
                    
                    # Position text box in the clearest corner
                    # Check if data is mainly in upper left or lower right
                    x_data = np.array(analysis_result.x_data)
                    y_data = np.array(analysis_result.y_data)
                    
                    if len(x_data) > 0 and len(y_data) > 0:
                        x_mid = (np.max(x_data) + np.min(x_data)) / 2
                        y_mid = (np.max(y_data) + np.min(y_data)) / 2
                        
                        # Simple heuristic: place box opposite to data concentration
                        x_center = (np.max(x_data) - np.min(x_data)) / 2 + np.min(x_data)
                        y_center = (np.max(y_data) - np.min(y_data)) / 2 + np.min(y_data)
                        
                        # Count points in each quadrant to find best position
                        upper_right_count = np.sum((x_data > x_center) & (y_data > y_center))
                        lower_left_count = np.sum((x_data < x_center) & (y_data < y_center))
                        
                        if upper_right_count > lower_left_count:
                            # Place in lower left
                            text_x, text_y = 0.05, 0.25
                        else:
                            # Place in upper right
                            text_x, text_y = 0.65, 0.85
                    else:
                        # Default position
                        text_x, text_y = 0.05, 0.85
                    
                    self.axes.text(
                        text_x, text_y,
                        info_text,
                        transform=self.axes.transAxes,
                        fontsize=10,
                        verticalalignment='top',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                                alpha=0.8, edgecolor='gray', linewidth=0.5)
                    )
            
            # Set labels and title
            # Use custom labels if provided, otherwise use plot-type specific labels
            final_xlabel = options.xlabel if options.xlabel else xlabel
            final_ylabel = options.ylabel if options.ylabel else ylabel
            final_title = options.title if options.title else title
            
            self.axes.set_xlabel(final_xlabel, fontsize=12)
            self.axes.set_ylabel(final_ylabel, fontsize=12)
            self.axes.set_title(final_title, fontsize=14, fontweight='bold')
            
            # Apply formatting with improved aesthetics
            self._apply_plot_formatting(options, ylabel)
            
            # Use tight_layout to prevent label cutoff
            self.figure.tight_layout()
            
            return self.figure, analysis_result
            
        except Exception as e:
            raise TDAError(f"Diffusion plot generation failed: {str(e)}")

    def update_dataset_style(self, dataset: PlotDataset):
        """Update the appearance of a specific dataset"""
        if hasattr(dataset, '_plot_line') and dataset._plot_line:
            line = dataset._plot_line
            style = dataset.style
            
            line.set_color(style.color)
            line.set_linestyle(style.linestyle)
            line.set_linewidth(style.linewidth)
            line.set_alpha(style.alpha)
            line.set_label(dataset.get_display_label())
            
            if style.marker != 'None':
                line.set_marker(style.marker)
                line.set_markersize(style.markersize)
            else:
                line.set_marker(None)


class PlotManager:
    """Main plot manager for TDA visualization"""
    
    def __init__(self, processed_data_folder="./data/processed_experiments/"):
        self.processed_data_folder = processed_data_folder
        self.available_datasets = []
        self.selected_datasets = []
        self.current_plot_type = "h_ppm_per_min"
        self.plot_options = PlotOptions()
        
        # Template management
        self.template_folder = os.path.join(os.path.dirname(processed_data_folder), "config", "plot_templates")
        os.makedirs(self.template_folder, exist_ok=True)
        
    def scan_for_datasets(self) -> List[Dict]:
        """Scan folder for processed CSV files from Module 2"""
        datasets = []
        
        if not os.path.exists(self.processed_data_folder):
            return datasets
        
        for filename in os.listdir(self.processed_data_folder):
            if filename.endswith('.csv') and not filename.startswith('#'):
                csv_path = os.path.join(self.processed_data_folder, filename)
                
                try:
                    # Quick validation - check if it's a processed TDA file
                    if self._is_valid_tda_csv(csv_path):
                        dataset_info = {
                            'filename': filename,
                            'path': csv_path,
                            'name': filename.replace('.csv', ''),
                            'modification_date': self._get_file_date(csv_path),
                            'size_kb': os.path.getsize(csv_path) // 1024
                        }
                        datasets.append(dataset_info)
                except Exception as e:
                    print(f"Warning: Could not process {filename}: {e}")
        
        # Sort by modification date (newest first)
        datasets.sort(key=lambda x: x['modification_date'], reverse=True)
        self.available_datasets = datasets
        return datasets
    
    def _is_valid_tda_csv(self, csv_path: str) -> bool:
        """Check if CSV file is a valid processed TDA file"""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                # Check for TDA header signature
                return first_line.startswith('# TDA Hydrogen Analysis Results')
        except:
            return False
    
    def _get_file_date(self, file_path: str) -> str:
        """Get file modification date"""
        from datetime import datetime
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    def load_dataset(self, csv_path: str) -> PlotDataset:
        """Load and parse processed CSV file from Module 2"""
        try:
            dataset = ProcessedCSVParser.parse_csv_file(csv_path)
            return dataset
        except Exception as e:
            raise TDAFileError(f"Failed to load dataset {csv_path}: {str(e)}")
    
    def generate_plot(self, datasets: List[PlotDataset], plot_type: str, options: PlotOptions) -> Figure:
        """Create matplotlib figure with specified options"""
        try:
            plot_generator = PlotGenerator()
            figure = plot_generator.create_time_series_plot(datasets, plot_type, options)
            return figure
        except Exception as e:
            raise TDAError(f"Plot generation failed: {str(e)}")
    
    def generate_diffusion_plot(self, dataset: PlotDataset, 
                               plot_type: str = "1_sqrt_t",
                               tail_start_time: float = 120.0,
                               show_linear_fit: bool = True,
                               calculate_D: bool = True,
                               sample_thickness: float = 0.1,
                               temperature: float = 25.0,
                               filter_noise: bool = False,
                               detection_limit: float = 0.1,
                               options: PlotOptions = None) -> Tuple[Figure, DiffusionAnalysisResult]:
        """Create diffusion analysis plot with specified options"""
        try:
            plot_generator = PlotGenerator()
            figure, analysis_result = plot_generator.create_diffusion_plot(
                dataset=dataset,
                plot_type=plot_type,
                tail_start_time=tail_start_time,
                show_linear_fit=show_linear_fit,
                calculate_D=calculate_D,
                sample_thickness=sample_thickness,
                temperature=temperature,
                filter_noise=filter_noise,
                detection_limit=detection_limit,
                options=options
            )
            return figure, analysis_result
        except Exception as e:
            raise TDAError(f"Diffusion plot generation failed: {str(e)}")

    def export_plot(self, figure: Figure, export_options: ExportOptions) -> str:
        """Export plot to specified format"""
        try:
            figure.savefig(
                export_options.filename,
                format=export_options.format.lower(),
                dpi=export_options.dpi,
                transparent=export_options.transparent,
                bbox_inches=export_options.bbox_inches,
                pad_inches=export_options.pad_inches,
                facecolor=export_options.facecolor
            )
            return export_options.filename
        except Exception as e:
            raise TDAFileError(f"Export failed: {str(e)}")