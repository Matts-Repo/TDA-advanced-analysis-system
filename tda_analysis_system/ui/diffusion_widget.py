"""
Diffusion Analysis Widget GUI for TDA Analysis System

This module provides the GUI interface for diffusion analysis with controls for:
- Tail region selection (manual or auto-detect)
- Plot type selection (1/√t, √t, log-log)
- Linear fit options and diffusion coefficient calculation
- Results display and export
"""

import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from modules.plot_manager import PlotManager, PlotDataset, PlotOptions, ExportOptions
from modules.calcs import DiffusionAnalysisResult
from modules.error_handling import handle_error_with_user_feedback


class DiffusionWidget(QWidget):
    """Diffusion analysis widget with controls and plot display"""
    
    def __init__(self, plot_manager: PlotManager):
        super().__init__()
        self.plot_manager = plot_manager
        self.loaded_datasets = {}  # filename -> PlotDataset
        self.current_figure = None
        self.current_analysis_result = None
        
        self.setup_ui()
        self.scan_datasets()
    
    def setup_ui(self):
        """Create split-panel layout for diffusion analysis interface"""
        layout = QHBoxLayout()
        
        # Left Panel: Controls
        controls_panel = self.create_controls_panel()
        layout.addWidget(controls_panel, 1)  # 1/3 of space
        
        # Right Panel: Plot Display
        plot_panel = self.create_plot_panel()
        layout.addWidget(plot_panel, 2)  # 2/3 of space
        
        self.setLayout(layout)
    
    def create_controls_panel(self):
        """Create left panel with diffusion analysis controls"""
        panel = QWidget()
        panel.setMaximumWidth(400)
        layout = QVBoxLayout()
        
        # Dataset Selection Section
        dataset_group = self.create_dataset_section()
        layout.addWidget(dataset_group)
        
        # Tail Region Selection Section
        tail_group = self.create_tail_region_section()
        layout.addWidget(tail_group)
        
        # Plot Options Section
        plot_options_group = self.create_plot_options_section()
        layout.addWidget(plot_options_group)
        
        # Analysis Settings Section
        analysis_group = self.create_analysis_section()
        layout.addWidget(analysis_group)
        
        # Results Display Section
        results_group = self.create_results_section()
        layout.addWidget(results_group)
        
        # Action Buttons
        buttons_group = self.create_buttons_section()
        layout.addWidget(buttons_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        
        # Add scroll area for long control panel
        scroll = QScrollArea()
        scroll.setWidget(panel)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        return scroll
    
    def create_dataset_section(self):
        """Dataset selection for diffusion analysis"""
        group = QGroupBox("Dataset Selection")
        layout = QVBoxLayout()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Available Datasets")
        refresh_btn.clicked.connect(self.scan_datasets)
        layout.addWidget(refresh_btn)
        
        # Dataset dropdown (single selection for diffusion analysis)
        layout.addWidget(QLabel("Select Dataset:"))
        self.dataset_combo = QComboBox()
        self.dataset_combo.currentTextChanged.connect(self.load_selected_dataset)
        layout.addWidget(self.dataset_combo)
        
        # Dataset info display
        self.dataset_info_label = QLabel("No dataset selected")
        self.dataset_info_label.setWordWrap(True)
        self.dataset_info_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; }")
        layout.addWidget(self.dataset_info_label)
        
        group.setLayout(layout)
        return group
    
    def create_tail_region_section(self):
        """Tail region selection controls"""
        group = QGroupBox("Tail Region Selection")
        layout = QVBoxLayout()
        
        # Auto-detect checkbox
        self.auto_detect_check = QCheckBox("Auto-detect tail start")
        self.auto_detect_check.setChecked(True)
        self.auto_detect_check.stateChanged.connect(self.on_auto_detect_changed)
        layout.addWidget(self.auto_detect_check)
        
        # Manual tail start time
        tail_layout = QHBoxLayout()
        tail_layout.addWidget(QLabel("Tail Start Time:"))
        self.tail_start_spin = QDoubleSpinBox()
        self.tail_start_spin.setRange(0, 10000)
        self.tail_start_spin.setValue(120)
        self.tail_start_spin.setSuffix(" min")
        self.tail_start_spin.setEnabled(False)  # Disabled when auto-detect is on
        self.tail_start_spin.valueChanged.connect(self.update_analysis)
        tail_layout.addWidget(self.tail_start_spin)
        layout.addLayout(tail_layout)
        
        # Help text
        help_text = QLabel("Select time after initial peak has decayed. Auto-detect finds when desorption rate drops below 10% of maximum.")
        help_text.setWordWrap(True)
        help_text.setStyleSheet("QLabel { font-size: 9px; color: #666; }")
        layout.addWidget(help_text)
        
        group.setLayout(layout)
        return group
    
    def create_plot_options_section(self):
        """Plot type and display options"""
        group = QGroupBox("Plot Options")
        layout = QVBoxLayout()
        
        # Plot type radio buttons
        layout.addWidget(QLabel("Plot Type:"))
        
        self.plot_type_group = QButtonGroup()
        
        self.plot_1_sqrt_t = QRadioButton("Desorption Rate vs 1/√t")
        self.plot_1_sqrt_t.setChecked(True)
        self.plot_1_sqrt_t.toggled.connect(self.update_analysis)
        self.plot_type_group.addButton(self.plot_1_sqrt_t, 0)
        layout.addWidget(self.plot_1_sqrt_t)
        
        self.plot_sqrt_t = QRadioButton("Cumulative H vs √t")
        self.plot_sqrt_t.toggled.connect(self.update_analysis)
        self.plot_type_group.addButton(self.plot_sqrt_t, 1)
        layout.addWidget(self.plot_sqrt_t)
        
        self.plot_log_log = QRadioButton("Log-Log Plot (log J vs log t)")
        self.plot_log_log.toggled.connect(self.update_analysis)
        self.plot_type_group.addButton(self.plot_log_log, 2)
        layout.addWidget(self.plot_log_log)
        
        # Display options
        self.show_fit_check = QCheckBox("Show linear fit")
        self.show_fit_check.setChecked(True)
        self.show_fit_check.stateChanged.connect(self.update_analysis)
        layout.addWidget(self.show_fit_check)
        
        # Unit selection for diffusion analysis
        units_layout = QVBoxLayout()
        units_layout.addWidget(QLabel("Y-axis Units:"))
        
        units_radio_layout = QHBoxLayout()
        self.units_mol_radio = QRadioButton("mol/cm²")
        self.units_mol_radio.setChecked(True)
        self.units_mol_radio.toggled.connect(self.update_analysis)
        units_radio_layout.addWidget(self.units_mol_radio)
        
        self.units_ppm_radio = QRadioButton("ppm")
        self.units_ppm_radio.toggled.connect(self.update_analysis)
        units_radio_layout.addWidget(self.units_ppm_radio)
        
        units_layout.addLayout(units_radio_layout)
        
        # Note about surface area
        note_label = QLabel("Note: mol/cm² requires surface area data")
        note_label.setStyleSheet("QLabel { font-size: 9px; color: #666; }")
        note_label.setWordWrap(True)
        units_layout.addWidget(note_label)
        
        layout.addLayout(units_layout)
        
        # Manual label controls
        labels_layout = QVBoxLayout()
        labels_layout.addWidget(QLabel("Custom Labels (optional):"))
        
        xlabel_layout = QHBoxLayout()
        xlabel_layout.addWidget(QLabel("X-axis:"))
        self.custom_xlabel_edit = QLineEdit()
        self.custom_xlabel_edit.setPlaceholderText("Auto (1/√t, √t, etc.)")
        self.custom_xlabel_edit.textChanged.connect(self.update_analysis)
        xlabel_layout.addWidget(self.custom_xlabel_edit)
        
        # Auto-fill button
        auto_fill_btn = QPushButton("Auto-fill")
        auto_fill_btn.setMaximumWidth(80)
        auto_fill_btn.clicked.connect(self.auto_fill_labels)
        xlabel_layout.addWidget(auto_fill_btn)
        
        labels_layout.addLayout(xlabel_layout)
        
        ylabel_layout = QHBoxLayout()
        ylabel_layout.addWidget(QLabel("Y-axis:"))
        self.custom_ylabel_edit = QLineEdit()
        self.custom_ylabel_edit.setPlaceholderText("Auto")
        self.custom_ylabel_edit.textChanged.connect(self.update_analysis)
        ylabel_layout.addWidget(self.custom_ylabel_edit)
        labels_layout.addLayout(ylabel_layout)
        
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.custom_title_edit = QLineEdit()
        self.custom_title_edit.setPlaceholderText("Auto")
        self.custom_title_edit.textChanged.connect(self.update_analysis)
        title_layout.addWidget(self.custom_title_edit)
        labels_layout.addLayout(title_layout)
        
        layout.addLayout(labels_layout)
        
        group.setLayout(layout)
        return group
    
    def create_analysis_section(self):
        """Analysis calculation settings"""
        group = QGroupBox("Analysis Settings")
        layout = QVBoxLayout()
        
        # Temperature inputs
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Test Temperature:"))
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0, 1200)
        self.temperature_spin.setValue(25)
        self.temperature_spin.setSuffix(" °C")
        self.temperature_spin.valueChanged.connect(self.update_analysis)
        temp_layout.addWidget(self.temperature_spin)
        layout.addLayout(temp_layout)
        
        # Optional D override
        d_override_layout = QHBoxLayout()
        d_override_layout.addWidget(QLabel("Known D (optional):"))
        self.d_override_spin = QDoubleSpinBox()
        self.d_override_spin.setRange(0, 1e-2)
        self.d_override_spin.setDecimals(10)
        self.d_override_spin.setValue(0.0)
        self.d_override_spin.setSuffix(" cm²/s")
        self.d_override_spin.setSpecialValueText("Auto-calculate")
        self.d_override_spin.valueChanged.connect(self.update_analysis)
        d_override_layout.addWidget(self.d_override_spin)
        layout.addLayout(d_override_layout)
        
        # GC detection limit
        gc_limit_layout = QHBoxLayout()
        gc_limit_layout.addWidget(QLabel("GC Detection Limit:"))
        self.gc_limit_spin = QDoubleSpinBox()
        self.gc_limit_spin.setRange(0.000001, 10.0)
        self.gc_limit_spin.setValue(0.001)  # Lower default for typical TDA data
        self.gc_limit_spin.setDecimals(6)
        self.gc_limit_spin.setSuffix(" ppm")
        self.gc_limit_spin.setSpecialValueText("Auto-adjust")
        self.gc_limit_spin.valueChanged.connect(self.update_analysis)
        gc_limit_layout.addWidget(self.gc_limit_spin)
        layout.addLayout(gc_limit_layout)
        
        # Filter noise/zeros checkbox
        self.filter_noise_check = QCheckBox("Filter noise/zeros")
        self.filter_noise_check.stateChanged.connect(self.update_analysis)
        layout.addWidget(self.filter_noise_check)
        
        # Calculate diffusion coefficient
        self.calc_d_check = QCheckBox("Calculate diffusion coefficient")
        self.calc_d_check.setChecked(True)
        self.calc_d_check.stateChanged.connect(self.update_analysis)
        layout.addWidget(self.calc_d_check)
        
        # Sample thickness
        thickness_layout = QHBoxLayout()
        thickness_layout.addWidget(QLabel("Sample Thickness:"))
        self.thickness_spin = QDoubleSpinBox()
        self.thickness_spin.setRange(0.001, 10.0)
        self.thickness_spin.setValue(0.1)
        self.thickness_spin.setDecimals(3)
        self.thickness_spin.setSuffix(" cm")
        self.thickness_spin.valueChanged.connect(self.update_analysis)
        thickness_layout.addWidget(self.thickness_spin)
        layout.addLayout(thickness_layout)
        
        group.setLayout(layout)
        return group
    
    def create_results_section(self):
        """Analysis results display"""
        group = QGroupBox("Analysis Results")
        layout = QVBoxLayout()
        
        # Results text area
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(150)
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("QTextEdit { font-family: monospace; font-size: 10px; }")
        layout.addWidget(self.results_text)
        
        group.setLayout(layout)
        return group
    
    def create_buttons_section(self):
        """Action buttons"""
        group = QGroupBox("Actions")
        layout = QHBoxLayout()
        
        # Analyze button
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self.update_analysis)
        self.analyze_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        layout.addWidget(self.analyze_btn)
        
        # Clear plot button
        self.clear_btn = QPushButton("Clear Plot")
        self.clear_btn.clicked.connect(self.clear_plot)
        layout.addWidget(self.clear_btn)
        
        # Export button
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_plot)
        layout.addWidget(self.export_btn)
        
        group.setLayout(layout)
        return group
    
    def create_plot_panel(self):
        """Create right panel with matplotlib canvas"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Add navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        
        panel.setLayout(layout)
        return panel
    
    def scan_datasets(self):
        """Scan for available datasets and populate dropdown"""
        try:
            datasets = self.plot_manager.scan_for_datasets()
            
            self.dataset_combo.clear()
            self.dataset_combo.addItem("Select a dataset...")
            
            for dataset_info in datasets:
                display_name = f"{dataset_info['name']} ({dataset_info['modification_date']})"
                self.dataset_combo.addItem(display_name)
                self.dataset_combo.setItemData(self.dataset_combo.count() - 1, dataset_info['path'])
            
        except Exception as e:
            handle_error_with_user_feedback(self, "Dataset Scan", e)
    
    def load_selected_dataset(self):
        """Load the selected dataset"""
        try:
            current_index = self.dataset_combo.currentIndex()
            if current_index <= 0:  # "Select a dataset..." is at index 0
                self.dataset_info_label.setText("No dataset selected")
                self.loaded_datasets.clear()
                return
            
            dataset_path = self.dataset_combo.itemData(current_index)
            if dataset_path:
                filename = os.path.basename(dataset_path)
                
                # Load the dataset
                dataset = self.plot_manager.load_dataset(dataset_path)
                self.loaded_datasets = {filename: dataset}
                
                # Update dataset info display
                info_text = f"""Dataset: {dataset.experiment_name}
Processing Date: {dataset.processing_date}
Sample Weight: {dataset.sample_weight} g
Duration: {dataset.duration_hours:.1f} hours
Total H: {dataset.total_hydrogen:.2f} ppm
Max Rate: {dataset.max_rate:.2f} ppm/min
Data Points: {len(dataset.time_minutes)}"""
                
                if dataset.calculation_mode == "surface_normalized":
                    info_text += f"\nSurface Area: {dataset.surface_area:.2f} cm²"
                
                self.dataset_info_label.setText(info_text)
                
                # Trigger analysis update if auto-detect is enabled
                if self.auto_detect_check.isChecked():
                    self.auto_detect_tail_start()
                
                self.update_analysis()
            
        except Exception as e:
            handle_error_with_user_feedback(self, "Dataset Loading", e)
    
    def on_auto_detect_changed(self):
        """Handle auto-detect checkbox change"""
        is_auto = self.auto_detect_check.isChecked()
        self.tail_start_spin.setEnabled(not is_auto)
        
        if is_auto and self.loaded_datasets:
            self.auto_detect_tail_start()
        
        self.update_analysis()
    
    def auto_detect_tail_start(self):
        """Auto-detect tail start time"""
        if not self.loaded_datasets:
            return
        
        try:
            dataset = list(self.loaded_datasets.values())[0]
            
            # Use the calculation module to find tail start
            from modules.calcs import TailRegionAnalyzer
            analyzer = TailRegionAnalyzer()
            
            desorption_rate = (dataset.h_ppm_per_min if dataset.calculation_mode == "mass_normalized" 
                             else dataset.h_mol_cm2_per_min)
            
            tail_start = analyzer.find_tail_start(dataset.time_minutes, desorption_rate)
            self.tail_start_spin.setValue(tail_start)
            
        except Exception as e:
            print(f"Auto-detect failed: {e}")
            # Fall back to default value
            self.tail_start_spin.setValue(120)
    
    def get_selected_plot_type(self):
        """Get the selected plot type"""
        if self.plot_1_sqrt_t.isChecked():
            return "1_sqrt_t"
        elif self.plot_sqrt_t.isChecked():
            return "sqrt_t"
        elif self.plot_log_log.isChecked():
            return "log_log"
        else:
            return "1_sqrt_t"
    
    def auto_fill_labels(self):
        """Auto-fill the custom label fields with appropriate defaults"""
        plot_type = self.get_selected_plot_type()
        use_mol_units = self.units_mol_radio.isChecked()
        
        # Determine default labels based on plot type and units
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
            xlabel = "Time"
            ylabel = "Value"
            title = "Diffusion Analysis"
        
        # Fill the fields
        self.custom_xlabel_edit.setText(xlabel)
        self.custom_ylabel_edit.setText(ylabel)
        self.custom_title_edit.setText(title)
    
    def update_analysis(self):
        """Update the diffusion analysis plot and results"""
        if not self.loaded_datasets:
            self.clear_plot()
            self.results_text.clear()
            return
        
        try:
            dataset = list(self.loaded_datasets.values())[0]
            
            # Get analysis parameters
            plot_type = self.get_selected_plot_type()
            tail_start = self.tail_start_spin.value()
            show_fit = self.show_fit_check.isChecked()
            calc_d = self.calc_d_check.isChecked()
            thickness = self.thickness_spin.value()
            
            # Create plot options
            options = PlotOptions()
            options.figure_size = (10, 6)
            options.show_legend = True
            options.show_grid = True
            
            # Set custom labels if provided
            options.xlabel = self.custom_xlabel_edit.text().strip()
            options.ylabel = self.custom_ylabel_edit.text().strip()
            options.title = self.custom_title_edit.text().strip()
            
            # Get analysis settings
            temperature = self.temperature_spin.value()
            filter_noise = self.filter_noise_check.isChecked()
            detection_limit = self.gc_limit_spin.value()
            use_mol_units = self.units_mol_radio.isChecked()
            
            # Add unit preference to options
            options.use_mol_units = use_mol_units
            
            # Generate diffusion plot
            self.current_figure, self.current_analysis_result = self.plot_manager.generate_diffusion_plot(
                dataset=dataset,
                plot_type=plot_type,
                tail_start_time=tail_start,
                show_linear_fit=show_fit,
                calculate_D=calc_d,
                sample_thickness=thickness,
                temperature=temperature,
                filter_noise=filter_noise,
                detection_limit=detection_limit,
                options=options
            )
            
            # Update canvas
            self.figure.clear()
            self.figure = self.current_figure
            self.canvas.figure = self.figure
            self.canvas.draw()
            
            # Update results display
            self.update_results_display()
            
        except Exception as e:
            handle_error_with_user_feedback(self, "Diffusion Analysis", e)
    
    def update_results_display(self):
        """Update the results text display"""
        if not self.current_analysis_result:
            self.results_text.clear()
            return
        
        result = self.current_analysis_result
        
        # Add filtering information if available
        filtering_info = ""
        if self.filter_noise_check.isChecked():
            detection_limit = self.gc_limit_spin.value()
            filtering_info = f"""
Noise Filtering Applied:
  Detection Limit: {detection_limit:.6f} ppm
  (Check console for detailed filtering results)
"""

        # Determine slope units based on analysis
        units_used = getattr(result, 'units_used', 'ppm')
        if result.analysis_type == "1_sqrt_t":
            if units_used == "mol/cm²":
                slope_units = "mol/(cm²·min⁻⁰·⁵)"
            else:
                slope_units = "ppm·min⁻⁰·⁵"
        elif result.analysis_type == "sqrt_t":
            if units_used == "mol/cm²":
                slope_units = "mol/(cm²·min⁰·⁵)"
            else:
                slope_units = "ppm/min⁰·⁵"
        else:
            slope_units = "log units"

        results_text = f"""DIFFUSION ANALYSIS RESULTS
{'='*40}
{filtering_info}
Tail Region Analysis:
  Start Time: {result.tail_start_time:.1f} minutes
  Data Points: {result.num_points}
  Analysis Type: {result.analysis_type}
  Units Used: {units_used}

Linear Regression:
  Slope: {result.slope:.4e} {slope_units}
  Intercept: {result.intercept:.4e}
  R² Value: {result.r_squared:.4f}
  P-value: {result.p_value:.4e}
  Std Error: {result.std_error:.4e}
  Fit Quality: {result.goodness_of_fit}

"""
        
        if result.diffusion_coefficient > 0:
            results_text += f"""Diffusion Coefficient:
  D = {result.diffusion_coefficient:.4e} cm²/s
  Sample Thickness: {result.thickness:.3f} cm
"""
            
            # Add temperature information if available
            if hasattr(result, 'measurement_temperature'):
                results_text += f"  Test Temperature: {result.measurement_temperature:.0f}°C\n"
                
                if hasattr(result, 'literature_D_at_temp'):
                    lit_d = result.literature_D_at_temp
                    ratio = result.diffusion_coefficient / lit_d
                    results_text += f"""  
Literature Comparison at {result.measurement_temperature:.0f}°C:
  Expected D: {lit_d:.4e} cm²/s
  Your value: {ratio:.2f}x expected
  Activation Energy: {result.activation_energy:.1f} kJ/mol
"""
            else:
                results_text += f"""  
Literature Comparison:
  Typical for steel: ~1.0e-7 cm²/s at 25°C
  Your value: {result.diffusion_coefficient/1e-7:.2f}x typical
"""
        
        # Add interpretation
        if result.r_squared >= 0.95:
            interpretation = "Excellent linear fit - strong evidence of diffusion control"
        elif result.r_squared >= 0.90:
            interpretation = "Good linear fit - likely diffusion controlled"
        elif result.r_squared >= 0.80:
            interpretation = "Fair linear fit - possible diffusion control"
        else:
            interpretation = "Poor linear fit - may not be diffusion controlled"
        
        results_text += f"\nInterpretation:\n  {interpretation}"
        
        self.results_text.setPlainText(results_text)
    
    def clear_plot(self):
        """Clear the current plot"""
        self.figure.clear()
        self.canvas.draw()
        self.current_figure = None
        self.current_analysis_result = None
        self.results_text.clear()
    
    def export_plot(self):
        """Export the current plot"""
        if not self.current_figure:
            QMessageBox.information(self, "Info", "No plot to export")
            return
        
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Diffusion Plot",
                "diffusion_analysis.png",
                "PNG files (*.png);;PDF files (*.pdf);;SVG files (*.svg)"
            )
            
            if filename:
                # Determine format from extension
                if filename.lower().endswith('.pdf'):
                    format_type = "PDF"
                elif filename.lower().endswith('.svg'):
                    format_type = "SVG"
                else:
                    format_type = "PNG"
                
                export_options = ExportOptions()
                export_options.filename = filename
                export_options.format = format_type
                export_options.dpi = 300
                
                self.plot_manager.export_plot(self.current_figure, export_options)
                QMessageBox.information(self, "Success", f"Plot exported to {filename}")
            
        except Exception as e:
            handle_error_with_user_feedback(self, "Plot Export", e)