"""
Plotting Widget GUI for TDA Analysis System

This module provides the GUI interface for data visualization with split-panel layout:
- Left Panel: Controls for dataset selection, styling, filtering, and export
- Right Panel: Matplotlib canvas for plot display
"""

import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from modules.plot_manager import PlotManager, PlotDataset, PlotOptions, ExportOptions, DatasetStyle, FilterOptions
from modules.error_handling import handle_error_with_user_feedback


class PlottingWidget(QWidget):
    """Main plotting widget with split-panel layout"""
    
    def __init__(self, plot_manager: PlotManager):
        super().__init__()
        self.plot_manager = plot_manager
        self.loaded_datasets = {}  # filename -> PlotDataset
        self.current_figure = None
        
        self.setup_ui()
        self.scan_datasets()
    
    def setup_ui(self):
        """Create split-panel layout for plotting interface"""
        layout = QHBoxLayout()
        
        # Left Panel: Controls
        controls_panel = self.create_controls_panel()
        layout.addWidget(controls_panel, 1)  # 1/3 of space
        
        # Right Panel: Plot Display
        plot_panel = self.create_plot_panel()
        layout.addWidget(plot_panel, 2)  # 2/3 of space
        
        self.setLayout(layout)
    
    def create_controls_panel(self):
        """Create left panel with all controls"""
        panel = QWidget()
        panel.setMaximumWidth(400)
        layout = QVBoxLayout()
        
        # Dataset Selection Section
        dataset_group = self.create_dataset_section()
        layout.addWidget(dataset_group)
        
        # Plot Type Section
        plot_type_group = self.create_plot_type_section()
        layout.addWidget(plot_type_group)
        
        # Dataset Styling Section
        styling_group = self.create_styling_section()
        layout.addWidget(styling_group)
        
        # Plot Type Options Section  
        plot_options_group = self.create_plot_options_section()
        layout.addWidget(plot_options_group)
        
        # Data Filtering Section
        filtering_group = self.create_filtering_section()
        layout.addWidget(filtering_group)
        
        # Plot Options Section
        options_group = self.create_options_section()
        layout.addWidget(options_group)
        
        # Export Section
        export_group = self.create_export_section()
        layout.addWidget(export_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        
        # Add scroll area for long control panel
        scroll = QScrollArea()
        scroll.setWidget(panel)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        return scroll
    
    def create_dataset_section(self):
        """Dataset selection area with checkboxes"""
        group = QGroupBox("Dataset Selection")
        layout = QVBoxLayout()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Available Datasets")
        refresh_btn.clicked.connect(self.scan_datasets)
        layout.addWidget(refresh_btn)
        
        # Dataset list with checkboxes
        self.dataset_list_widget = QListWidget()
        self.dataset_list_widget.setSelectionMode(QAbstractItemView.NoSelection)
        layout.addWidget(self.dataset_list_widget)
        
        # Load selected button
        load_btn = QPushButton("Load Selected Datasets")
        load_btn.clicked.connect(self.load_selected_datasets)
        layout.addWidget(load_btn)
        
        group.setLayout(layout)
        return group
    
    def create_plot_type_section(self):
        """Plot type dropdown"""
        group = QGroupBox("Plot Type")
        layout = QVBoxLayout()
        
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems([
            "H Evolution Rate (ppm/min)",
            "Cumulative H Content (ppm)", 
            "Peak Areas (µV*s)"
        ])
        self.plot_type_combo.currentTextChanged.connect(self.update_plot)
        layout.addWidget(self.plot_type_combo)
        
        group.setLayout(layout)
        return group
    
    def create_styling_section(self):
        """Dataset styling controls"""
        group = QGroupBox("Dataset Styling")
        layout = QVBoxLayout()
        
        # Active dataset selector
        layout.addWidget(QLabel("Select Dataset to Style:"))
        self.style_dataset_combo = QComboBox()
        self.style_dataset_combo.currentTextChanged.connect(self.update_style_controls)
        layout.addWidget(self.style_dataset_combo)
        
        # Styling controls
        style_grid = QGridLayout()
        
        # Color picker
        style_grid.addWidget(QLabel("Color:"), 0, 0)
        self.color_btn = QPushButton()
        self.color_btn.setMaximumWidth(50)
        self.color_btn.clicked.connect(self.pick_color)
        style_grid.addWidget(self.color_btn, 0, 1)
        
        # Line style
        style_grid.addWidget(QLabel("Line Style:"), 1, 0)
        self.linestyle_combo = QComboBox()
        self.linestyle_combo.addItems(["-", "--", "-.", ":"])
        self.linestyle_combo.currentTextChanged.connect(self.update_dataset_style)
        style_grid.addWidget(self.linestyle_combo, 1, 1)
        
        # Line width
        style_grid.addWidget(QLabel("Line Width:"), 2, 0)
        self.linewidth_spin = QDoubleSpinBox()
        self.linewidth_spin.setRange(0.5, 5.0)
        self.linewidth_spin.setSingleStep(0.5)
        self.linewidth_spin.setValue(2.0)
        self.linewidth_spin.valueChanged.connect(self.update_dataset_style)
        style_grid.addWidget(self.linewidth_spin, 2, 1)
        
        # Custom label
        style_grid.addWidget(QLabel("Custom Label:"), 3, 0)
        self.custom_label_edit = QLineEdit()
        self.custom_label_edit.textChanged.connect(self.update_dataset_style)
        style_grid.addWidget(self.custom_label_edit, 3, 1)
        
        layout.addLayout(style_grid)
        
        group.setLayout(layout)
        return group
    
    def create_plot_options_section(self):
        """Plot type and display options"""
        group = QGroupBox("Plot Options")
        layout = QVBoxLayout()
        
        # Axis mode selection
        axis_layout = QVBoxLayout()
        axis_layout.addWidget(QLabel("Axis Mode:"))
        
        axis_radio_layout = QHBoxLayout()
        self.dual_axis_radio = QRadioButton("Dual Axis (mol + ppm)")
        self.dual_axis_radio.setChecked(True)
        self.dual_axis_radio.toggled.connect(self.on_axis_mode_changed)
        axis_radio_layout.addWidget(self.dual_axis_radio)
        
        self.single_axis_radio = QRadioButton("Single Axis")
        self.single_axis_radio.toggled.connect(self.on_axis_mode_changed)
        axis_radio_layout.addWidget(self.single_axis_radio)
        
        axis_layout.addLayout(axis_radio_layout)
        
        # Single axis unit selection (only visible when single axis is selected)
        self.single_axis_unit_layout = QHBoxLayout()
        self.single_axis_unit_layout.addWidget(QLabel("Units:"))
        
        self.units_mol_radio = QRadioButton("mol/cm²")
        self.units_mol_radio.setChecked(True)
        self.units_mol_radio.toggled.connect(self.update_plot)
        self.single_axis_unit_layout.addWidget(self.units_mol_radio)
        
        self.units_ppm_radio = QRadioButton("ppm")
        self.units_ppm_radio.toggled.connect(self.update_plot)
        self.single_axis_unit_layout.addWidget(self.units_ppm_radio)
        
        # Create widget to hold the unit selection layout
        self.single_axis_unit_widget = QWidget()
        self.single_axis_unit_widget.setLayout(self.single_axis_unit_layout)
        self.single_axis_unit_widget.setVisible(False)  # Hidden by default
        
        axis_layout.addWidget(self.single_axis_unit_widget)
        layout.addLayout(axis_layout)
        
        # Dual axis display options (only visible when dual axis is selected)
        dual_axis_options_layout = QVBoxLayout()
        dual_axis_options_layout.addWidget(QLabel("Dual Axis Display:"))
        
        self.primary_only_check = QCheckBox("Show only primary data (mol/cm²)")
        self.primary_only_check.stateChanged.connect(self.update_plot)
        dual_axis_options_layout.addWidget(self.primary_only_check)
        
        self.clean_legend_check = QCheckBox("Clean legend (no unit labels)")
        self.clean_legend_check.setChecked(True)
        self.clean_legend_check.stateChanged.connect(self.update_plot)
        dual_axis_options_layout.addWidget(self.clean_legend_check)
        
        # Create widget to hold dual axis options
        self.dual_axis_options_widget = QWidget()
        self.dual_axis_options_widget.setLayout(dual_axis_options_layout)
        self.dual_axis_options_widget.setVisible(True)  # Visible by default
        
        layout.addWidget(self.dual_axis_options_widget)
        
        # Zero filtering checkbox
        self.exclude_zeros_check = QCheckBox("Exclude zero values")
        self.exclude_zeros_check.stateChanged.connect(self.update_plot)
        layout.addWidget(self.exclude_zeros_check)
        
        group.setLayout(layout)
        return group
    
    def on_axis_mode_changed(self):
        """Handle axis mode change to show/hide relevant controls"""
        is_dual_axis = self.dual_axis_radio.isChecked()
        
        # Show/hide controls based on mode
        self.single_axis_unit_widget.setVisible(not is_dual_axis)
        self.dual_axis_options_widget.setVisible(is_dual_axis)
        
        # Update the plot
        self.update_plot()
    
    def create_filtering_section(self):
        """Data filtering options"""
        group = QGroupBox("Data Filtering")
        layout = QVBoxLayout()
        
        # Outlier removal
        self.outlier_check = QCheckBox("Remove Outliers")
        self.outlier_check.stateChanged.connect(self.update_plot)
        layout.addWidget(self.outlier_check)
        
        outlier_layout = QHBoxLayout()
        outlier_layout.addWidget(QLabel("Method:"))
        self.outlier_method_combo = QComboBox()
        self.outlier_method_combo.addItems(["zscore", "iqr"])
        self.outlier_method_combo.currentTextChanged.connect(self.update_plot)
        outlier_layout.addWidget(self.outlier_method_combo)
        
        outlier_layout.addWidget(QLabel("Threshold:"))
        self.outlier_threshold_spin = QDoubleSpinBox()
        self.outlier_threshold_spin.setRange(1.0, 5.0)
        self.outlier_threshold_spin.setValue(3.0)
        self.outlier_threshold_spin.valueChanged.connect(self.update_plot)
        outlier_layout.addWidget(self.outlier_threshold_spin)
        
        layout.addLayout(outlier_layout)
        
        # Data smoothing
        self.smoothing_check = QCheckBox("Apply Smoothing")
        self.smoothing_check.stateChanged.connect(self.update_plot)
        layout.addWidget(self.smoothing_check)
        
        smoothing_layout = QHBoxLayout()
        smoothing_layout.addWidget(QLabel("Method:"))
        self.smoothing_method_combo = QComboBox()
        self.smoothing_method_combo.addItems(["moving_avg", "savgol", "lowess"])
        self.smoothing_method_combo.currentTextChanged.connect(self.update_plot)
        smoothing_layout.addWidget(self.smoothing_method_combo)
        
        smoothing_layout.addWidget(QLabel("Window:"))
        self.smoothing_window_spin = QSpinBox()
        self.smoothing_window_spin.setRange(3, 21)
        self.smoothing_window_spin.setValue(5)
        self.smoothing_window_spin.valueChanged.connect(self.update_plot)
        smoothing_layout.addWidget(self.smoothing_window_spin)
        
        layout.addLayout(smoothing_layout)
        
        # Time range filtering
        self.time_range_check = QCheckBox("Filter Time Range")
        self.time_range_check.stateChanged.connect(self.update_plot)
        layout.addWidget(self.time_range_check)
        
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Start:"))
        self.time_start_spin = QDoubleSpinBox()
        self.time_start_spin.setRange(0, 10000)
        self.time_start_spin.setValue(0)
        self.time_start_spin.valueChanged.connect(self.update_plot)
        time_layout.addWidget(self.time_start_spin)
        
        time_layout.addWidget(QLabel("End:"))
        self.time_end_spin = QDoubleSpinBox()
        self.time_end_spin.setRange(0, 10000)
        self.time_end_spin.setValue(1000)
        self.time_end_spin.valueChanged.connect(self.update_plot)
        time_layout.addWidget(self.time_end_spin)
        
        layout.addLayout(time_layout)
        
        group.setLayout(layout)
        return group
    
    def create_options_section(self):
        """Plot formatting options"""
        group = QGroupBox("Plot Options")
        layout = QVBoxLayout()
        
        # Title and labels
        layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit()
        self.title_edit.textChanged.connect(self.update_plot)
        layout.addWidget(self.title_edit)
        
        layout.addWidget(QLabel("Y-axis Label:"))
        self.ylabel_edit = QLineEdit()
        self.ylabel_edit.textChanged.connect(self.update_plot)
        layout.addWidget(self.ylabel_edit)
        
        # Grid and legend
        self.grid_check = QCheckBox("Show Grid")
        self.grid_check.setChecked(True)
        self.grid_check.stateChanged.connect(self.update_plot)
        layout.addWidget(self.grid_check)
        
        self.legend_check = QCheckBox("Show Legend")
        self.legend_check.setChecked(True)
        self.legend_check.stateChanged.connect(self.update_plot)
        layout.addWidget(self.legend_check)
        
        # Log scale
        self.log_y_check = QCheckBox("Log Y Scale")
        self.log_y_check.stateChanged.connect(self.update_plot)
        layout.addWidget(self.log_y_check)
        
        group.setLayout(layout)
        return group
    
    def create_export_section(self):
        """Export settings and buttons"""
        group = QGroupBox("Export")
        layout = QVBoxLayout()
        
        # Export format
        layout.addWidget(QLabel("Format:"))
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["PNG", "PDF", "SVG", "EPS"])
        layout.addWidget(self.export_format_combo)
        
        # DPI setting
        dpi_layout = QHBoxLayout()
        dpi_layout.addWidget(QLabel("DPI:"))
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(300)
        dpi_layout.addWidget(self.dpi_spin)
        layout.addLayout(dpi_layout)
        
        # Action buttons layout
        button_layout = QHBoxLayout()
        
        # Clear plot button
        clear_btn = QPushButton("Clear Plot")
        clear_btn.clicked.connect(self.clear_plot)
        button_layout.addWidget(clear_btn)
        
        # Export button
        export_btn = QPushButton("Export Plot")
        export_btn.clicked.connect(self.export_plot)
        button_layout.addWidget(export_btn)
        
        layout.addLayout(button_layout)
        
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
        """Scan for available datasets and populate list"""
        try:
            datasets = self.plot_manager.scan_for_datasets()
            
            self.dataset_list_widget.clear()
            
            for dataset_info in datasets:
                item = QListWidgetItem()
                
                # Create checkbox widget
                checkbox = QCheckBox(f"{dataset_info['name']} ({dataset_info['modification_date']})")
                checkbox.setProperty('dataset_path', dataset_info['path'])
                
                self.dataset_list_widget.addItem(item)
                self.dataset_list_widget.setItemWidget(item, checkbox)
            
        except Exception as e:
            handle_error_with_user_feedback(self, "Dataset Scan", e)
    
    def load_selected_datasets(self):
        """Load datasets selected by checkboxes"""
        try:
            selected_paths = []
            
            for i in range(self.dataset_list_widget.count()):
                item = self.dataset_list_widget.item(i)
                checkbox = self.dataset_list_widget.itemWidget(item)
                
                if checkbox.isChecked():
                    dataset_path = checkbox.property('dataset_path')
                    selected_paths.append(dataset_path)
            
            if not selected_paths:
                QMessageBox.information(self, "Info", "Please select at least one dataset")
                return
            
            # Load selected datasets
            for path in selected_paths:
                filename = os.path.basename(path)
                if filename not in self.loaded_datasets:
                    dataset = self.plot_manager.load_dataset(path)
                    self.loaded_datasets[filename] = dataset
            
            # Update style dataset combo
            self.update_style_dataset_combo()
            
            # Update plot
            self.update_plot()
            
            QMessageBox.information(self, "Success", f"Loaded {len(selected_paths)} dataset(s)")
            
        except Exception as e:
            handle_error_with_user_feedback(self, "Dataset Loading", e)
    
    def update_style_dataset_combo(self):
        """Update the dataset combo for styling"""
        self.style_dataset_combo.clear()
        
        for filename in self.loaded_datasets.keys():
            self.style_dataset_combo.addItem(filename)
    
    def update_style_controls(self):
        """Update style controls based on selected dataset"""
        filename = self.style_dataset_combo.currentText()
        if filename in self.loaded_datasets:
            dataset = self.loaded_datasets[filename]
            style = dataset.style
            
            # Update color button
            color = QColor(style.color)
            self.color_btn.setStyleSheet(f"background-color: {style.color};")
            
            # Update other controls
            self.linestyle_combo.setCurrentText(style.linestyle)
            self.linewidth_spin.setValue(style.linewidth)
            self.custom_label_edit.setText(style.label)
    
    def pick_color(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_btn.setStyleSheet(f"background-color: {color.name()};")
            self.update_dataset_style()
    
    def update_dataset_style(self):
        """Update the style of the selected dataset"""
        filename = self.style_dataset_combo.currentText()
        if filename in self.loaded_datasets:
            dataset = self.loaded_datasets[filename]
            
            # Get color from button
            color = self.color_btn.palette().button().color().name()
            
            # Update dataset style
            dataset.style.color = color
            dataset.style.linestyle = self.linestyle_combo.currentText()
            dataset.style.linewidth = self.linewidth_spin.value()
            dataset.style.label = self.custom_label_edit.text()
            
            # Update plot
            self.update_plot()
    
    def update_plot(self):
        """Update the plot with current settings"""
        if not self.loaded_datasets:
            return
        
        try:
            # Update filter options for all datasets
            for dataset in self.loaded_datasets.values():
                # Update zero filtering options
                dataset.filter_options.exclude_zeros = self.exclude_zeros_check.isChecked()
                dataset.filter_options.detection_limit = 0.001  # Lower default for TDA data
                
                # Update other filter options
                dataset.filter_options.remove_outliers = self.outlier_check.isChecked()
                dataset.filter_options.outlier_method = self.outlier_method_combo.currentText()
                dataset.filter_options.outlier_threshold = self.outlier_threshold_spin.value()
                
                dataset.filter_options.apply_smoothing = self.smoothing_check.isChecked()
                dataset.filter_options.smoothing_method = self.smoothing_method_combo.currentText()
                dataset.filter_options.smoothing_window = self.smoothing_window_spin.value()
                
                dataset.filter_options.time_range_filter = self.time_range_check.isChecked()
                dataset.filter_options.time_start = self.time_start_spin.value()
                dataset.filter_options.time_end = self.time_end_spin.value()
            
            # Get plot type
            plot_type_text = self.plot_type_combo.currentText()
            if "Evolution Rate" in plot_type_text:
                plot_type = "h_ppm_per_min"
            elif "Cumulative" in plot_type_text:
                plot_type = "cumulative_h_ppm"
            else:
                plot_type = "peak_areas"
            
            # Create plot options
            options = PlotOptions()
            options.dual_axis = self.dual_axis_radio.isChecked()
            options.title = self.title_edit.text()
            options.ylabel = self.ylabel_edit.text()
            options.show_grid = self.grid_check.isChecked()
            options.show_legend = self.legend_check.isChecked()
            options.log_y = self.log_y_check.isChecked()
            
            # Set plotting preferences with safe defaults
            options.primary_only = getattr(self, 'primary_only_check', None) and self.primary_only_check.isChecked()
            options.clean_legend = getattr(self, 'clean_legend_check', None) and self.clean_legend_check.isChecked()
            if hasattr(self, 'units_mol_radio') and hasattr(self, 'units_ppm_radio'):
                options.single_axis_units = "mol" if self.units_mol_radio.isChecked() else "ppm"
            else:
                options.single_axis_units = "mol"  # Default
            
            # Generate plot
            datasets_list = list(self.loaded_datasets.values())
            self.current_figure = self.plot_manager.generate_plot(datasets_list, plot_type, options)
            
            # Update canvas
            self.figure.clear()
            self.figure = self.current_figure
            self.canvas.figure = self.figure
            self.canvas.draw()
            
        except Exception as e:
            handle_error_with_user_feedback(self, "Plot Update", e)
    
    def clear_plot(self):
        """Clear the current plot"""
        self.figure.clear()
        self.canvas.draw()
        self.current_figure = None
    
    def export_plot(self):
        """Export the current plot"""
        if not self.current_figure:
            QMessageBox.information(self, "Info", "No plot to export")
            return
        
        try:
            # Get export settings
            format_ext = self.export_format_combo.currentText().lower()
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Plot",
                f"tda_plot.{format_ext}",
                f"{format_ext.upper()} files (*.{format_ext})"
            )
            
            if filename:
                export_options = ExportOptions()
                export_options.filename = filename
                export_options.format = self.export_format_combo.currentText()
                export_options.dpi = self.dpi_spin.value()
                
                self.plot_manager.export_plot(self.current_figure, export_options)
                QMessageBox.information(self, "Success", f"Plot exported to {filename}")
            
        except Exception as e:
            handle_error_with_user_feedback(self, "Plot Export", e)