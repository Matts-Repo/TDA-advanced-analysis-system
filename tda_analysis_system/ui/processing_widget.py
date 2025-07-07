"""
Processing Widget GUI for TDA Analysis System

This module provides the GUI interface for data processing with four main sections:
1. Load Experiment Data
2. Processing Parameters
3. Calibration Selection
4. Processing and Export
"""

import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from modules.calibration_manager import CalibrationManager
from modules.data_processor import DataProcessor, ExperimentData, BatchResults, BatchProcessingResult
from modules.error_handling import handle_error_with_user_feedback


class ProcessingWidget(QWidget):
    """Main data processing widget with four-section layout"""
    
    def __init__(self, calibration_manager: CalibrationManager, data_processor: DataProcessor):
        super().__init__()
        self.cal_manager = calibration_manager
        self.data_processor = data_processor
        self.current_experiment = None
        self.selected_calibration = None
        self.processed_data = None
        
        # Batch processing attributes
        self.batch_mode = False
        self.selected_folders = []
        self.batch_results = None
        self.processing_cancelled = False
        
        self.setup_ui()
        self.refresh_calibration_list()
    
    def setup_ui(self):
        """Create four-section layout for data processing"""
        layout = QVBoxLayout()
        
        # Section 1: Load Experiment Data
        data_group = self.create_data_section()
        layout.addWidget(data_group)
        
        # Section 2: Processing Parameters
        params_group = self.create_parameters_section()
        layout.addWidget(params_group)
        
        # Section 3: Calibration Selection
        cal_group = self.create_calibration_section()
        layout.addWidget(cal_group)
        
        # Section 4: Processing and Export
        process_group = self.create_processing_section()
        layout.addWidget(process_group)
        
        self.setLayout(layout)
    
    def create_data_section(self):
        """Section 1: Load Experiment Data"""
        group = QGroupBox("Load Experiment Data")
        layout = QVBoxLayout()
        
        # Processing mode selection
        mode_layout = QHBoxLayout()
        self.single_mode_radio = QRadioButton("Single Folder")
        self.single_mode_radio.setChecked(True)
        self.single_mode_radio.toggled.connect(self.on_mode_changed)
        mode_layout.addWidget(self.single_mode_radio)
        
        self.batch_mode_radio = QRadioButton("Batch Processing")
        self.batch_mode_radio.toggled.connect(self.on_mode_changed)
        mode_layout.addWidget(self.batch_mode_radio)
        
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # Single folder selection (original functionality)
        self.single_folder_widget = QWidget()
        single_layout = QVBoxLayout()
        
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Folder Path:"))
        
        self.data_folder_edit = QLineEdit()
        folder_layout.addWidget(self.data_folder_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_data_folder)
        folder_layout.addWidget(browse_btn)
        
        preview_btn = QPushButton("Preview Data")
        preview_btn.clicked.connect(self.preview_data)
        folder_layout.addWidget(preview_btn)
        
        single_layout.addLayout(folder_layout)
        self.single_folder_widget.setLayout(single_layout)
        layout.addWidget(self.single_folder_widget)
        
        # Batch folder selection
        self.batch_folder_widget = QWidget()
        batch_layout = QVBoxLayout()
        
        batch_controls_layout = QHBoxLayout()
        batch_controls_layout.addWidget(QLabel(f"Selected Folders ({len(self.selected_folders)}):"))
        
        add_folders_btn = QPushButton("Add Folders...")
        add_folders_btn.clicked.connect(self.add_batch_folders)
        batch_controls_layout.addWidget(add_folders_btn)
        
        clear_folders_btn = QPushButton("Clear All")
        clear_folders_btn.clicked.connect(self.clear_batch_folders)
        batch_controls_layout.addWidget(clear_folders_btn)
        
        preview_batch_btn = QPushButton("Preview Batch")
        preview_batch_btn.clicked.connect(self.preview_batch)
        batch_controls_layout.addWidget(preview_batch_btn)
        
        batch_controls_layout.addStretch()
        batch_layout.addLayout(batch_controls_layout)
        
        # Batch folder list
        self.batch_folder_list = QListWidget()
        self.batch_folder_list.setMaximumHeight(120)
        self.batch_folder_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.batch_folder_list.customContextMenuRequested.connect(self.show_batch_context_menu)
        batch_layout.addWidget(self.batch_folder_list)
        
        self.batch_folder_widget.setLayout(batch_layout)
        self.batch_folder_widget.setVisible(False)
        layout.addWidget(self.batch_folder_widget)
        
        # Data summary and preview area (shared)
        self.data_summary_label = QLabel("No data loaded")
        layout.addWidget(self.data_summary_label)
        
        self.data_preview_table = QTableWidget()
        self.data_preview_table.setMaximumHeight(150)
        layout.addWidget(self.data_preview_table)
        
        group.setLayout(layout)
        return group
    
    def create_parameters_section(self):
        """Section 2: Processing Parameters"""
        group = QGroupBox("Processing Parameters")
        layout = QGridLayout()
        
        # Sample weight
        layout.addWidget(QLabel("Sample Weight:"), 0, 0)
        self.sample_weight_edit = QLineEdit()
        self.sample_weight_edit.setPlaceholderText("e.g., 5.0")
        self.sample_weight_edit.textChanged.connect(self.validate_parameters)
        layout.addWidget(self.sample_weight_edit, 0, 1)
        layout.addWidget(QLabel("grams"), 0, 2)
        
        self.weight_status_label = QLabel("")
        layout.addWidget(self.weight_status_label, 0, 3)
        
        # Flow rate
        layout.addWidget(QLabel("Flow Rate:"), 1, 0)
        self.flow_rate_edit = QLineEdit()
        self.flow_rate_edit.setPlaceholderText("e.g., 20.0")
        self.flow_rate_edit.textChanged.connect(self.validate_parameters)
        layout.addWidget(self.flow_rate_edit, 1, 1)
        layout.addWidget(QLabel("ml/min"), 1, 2)
        
        self.flow_status_label = QLabel("")
        layout.addWidget(self.flow_status_label, 1, 3)
        
        # Cycle time
        layout.addWidget(QLabel("Cycle Time:"), 2, 0)
        self.cycle_time_edit = QLineEdit()
        self.cycle_time_edit.setPlaceholderText("e.g., 5.0")
        self.cycle_time_edit.textChanged.connect(self.validate_parameters)
        layout.addWidget(self.cycle_time_edit, 2, 1)
        layout.addWidget(QLabel("minutes"), 2, 2)
        
        self.cycle_status_label = QLabel("")
        layout.addWidget(self.cycle_status_label, 2, 3)
        
        group.setLayout(layout)
        return group
    
    def create_calibration_section(self):
        """Section 3: Calibration Selection"""
        group = QGroupBox("Calibration Selection")
        layout = QVBoxLayout()
        
        # Calibration selection controls
        selection_layout = QHBoxLayout()
        
        selection_layout.addWidget(QLabel("Select Calibration:"))
        
        self.calibration_combo = QComboBox()
        self.calibration_combo.currentTextChanged.connect(self.on_calibration_selected)
        selection_layout.addWidget(self.calibration_combo)
        
        suggest_btn = QPushButton("Suggest Best")
        suggest_btn.clicked.connect(self.suggest_best_calibration)
        selection_layout.addWidget(suggest_btn)
        
        layout.addLayout(selection_layout)
        
        # Calibration details display
        self.calibration_details_label = QLabel("No calibration selected")
        self.calibration_details_label.setWordWrap(True)
        layout.addWidget(self.calibration_details_label)
        
        group.setLayout(layout)
        return group
    
    def create_processing_section(self):
        """Section 4: Processing and Export"""
        group = QGroupBox("Processing and Export")
        layout = QVBoxLayout()
        
        # Processing controls
        process_layout = QHBoxLayout()
        
        self.process_btn = QPushButton("Process Data")
        self.process_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        self.process_btn.clicked.connect(self.process_data)
        self.process_btn.setEnabled(False)
        process_layout.addWidget(self.process_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self.cancel_processing)
        process_layout.addWidget(self.cancel_btn)
        
        process_layout.addStretch()
        layout.addLayout(process_layout)
        
        # Progress tracking
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_status_label = QLabel("")
        self.progress_status_label.setVisible(False)
        progress_layout.addWidget(self.progress_status_label)
        
        layout.addLayout(progress_layout)
        
        # Results summary
        self.results_summary_label = QLabel("No processing results yet")
        self.results_summary_label.setWordWrap(True)
        layout.addWidget(self.results_summary_label)
        
        # Export controls
        export_layout = QHBoxLayout()
        
        self.export_csv_btn = QPushButton("Export Enhanced CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_csv_btn.setEnabled(False)
        export_layout.addWidget(self.export_csv_btn)
        
        self.view_results_btn = QPushButton("View Results")
        self.view_results_btn.clicked.connect(self.view_results)
        self.view_results_btn.setEnabled(False)
        export_layout.addWidget(self.view_results_btn)
        
        export_layout.addStretch()
        layout.addLayout(export_layout)
        
        group.setLayout(layout)
        return group
    
    def browse_data_folder(self):
        """Open folder browser for experiment data"""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Experiment Data Folder",
            "",
            QFileDialog.ShowDirsOnly
        )
        if folder:
            self.data_folder_edit.setText(folder)
    
    def preview_data(self):
        """Preview experiment data"""
        folder_path = self.data_folder_edit.text().strip()
        if not folder_path:
            QMessageBox.warning(self, "Warning", "Please select an experiment folder")
            return
        
        try:
            # Get preview data
            preview_data = self.data_processor.preview_experiment_data(folder_path, num_rows=10)
            
            # Update summary
            summary_text = f"""
            <b>Experiment:</b> {preview_data['experiment_name']}<br>
            <b>Total Runs:</b> {preview_data['total_runs']}<br>
            <b>Missing Runs:</b> {preview_data['missing_runs']}<br>
            <b>Date Range:</b> {preview_data['date_range']}
            """
            self.data_summary_label.setText(summary_text)
            
            # Update preview table
            if preview_data['preview_rows']:
                self.data_preview_table.setColumnCount(5)
                self.data_preview_table.setHorizontalHeaderLabels([
                    'Run', 'Timestamp', 'Peak Area', 'Peak Height', 'Time (min)'
                ])
                self.data_preview_table.setRowCount(len(preview_data['preview_rows']))
                
                for row, data in enumerate(preview_data['preview_rows']):
                    self.data_preview_table.setItem(row, 0, QTableWidgetItem(str(data['run'])))
                    self.data_preview_table.setItem(row, 1, QTableWidgetItem(data['timestamp']))
                    self.data_preview_table.setItem(row, 2, QTableWidgetItem(data['peak_area']))
                    self.data_preview_table.setItem(row, 3, QTableWidgetItem(data['peak_height']))
                    self.data_preview_table.setItem(row, 4, QTableWidgetItem(data['time_minutes']))
                
                self.data_preview_table.resizeColumnsToContents()
            
            # Store current experiment data
            self.current_experiment = self.data_processor.current_experiment
            self.update_process_button_state()
            
        except Exception as e:
            handle_error_with_user_feedback(self, "Data Preview", e)
    
    def validate_parameters(self):
        """Real-time validation of processing parameters"""
        # Validate sample weight
        try:
            weight = float(self.sample_weight_edit.text()) if self.sample_weight_edit.text() else 0
            if weight <= 0:
                self.weight_status_label.setText("❌ Must be positive")
                self.weight_status_label.setStyleSheet("color: red;")
            elif weight < 0.1 or weight > 50:
                self.weight_status_label.setText("⚠️ Unusual value")
                self.weight_status_label.setStyleSheet("color: orange;")
            else:
                self.weight_status_label.setText("✅ Valid")
                self.weight_status_label.setStyleSheet("color: green;")
        except ValueError:
            self.weight_status_label.setText("❌ Invalid number")
            self.weight_status_label.setStyleSheet("color: red;")
        
        # Validate flow rate
        try:
            flow = float(self.flow_rate_edit.text()) if self.flow_rate_edit.text() else 0
            if flow <= 0:
                self.flow_status_label.setText("❌ Must be positive")
                self.flow_status_label.setStyleSheet("color: red;")
            elif flow < 1 or flow > 100:
                self.flow_status_label.setText("⚠️ Unusual value")
                self.flow_status_label.setStyleSheet("color: orange;")
            else:
                self.flow_status_label.setText("✅ Valid")
                self.flow_status_label.setStyleSheet("color: green;")
        except ValueError:
            self.flow_status_label.setText("❌ Invalid number")
            self.flow_status_label.setStyleSheet("color: red;")
        
        # Validate cycle time
        try:
            cycle = float(self.cycle_time_edit.text()) if self.cycle_time_edit.text() else 0
            if cycle <= 0:
                self.cycle_status_label.setText("❌ Must be positive")
                self.cycle_status_label.setStyleSheet("color: red;")
            elif cycle < 1 or cycle > 60:
                self.cycle_status_label.setText("⚠️ Unusual value")
                self.cycle_status_label.setStyleSheet("color: orange;")
            else:
                self.cycle_status_label.setText("✅ Valid")
                self.cycle_status_label.setStyleSheet("color: green;")
        except ValueError:
            self.cycle_status_label.setText("❌ Invalid number")
            self.cycle_status_label.setStyleSheet("color: red;")
        
        self.update_process_button_state()
    
    def refresh_calibration_list(self):
        """Refresh the calibration dropdown"""
        self.calibration_combo.clear()
        self.calibration_combo.addItem("Select calibration...")
        
        # Add valid calibrations
        valid_calibrations = [cal for cal in self.cal_manager.calibrations.values() if cal.is_valid]
        valid_calibrations.sort(key=lambda x: x.date, reverse=True)
        
        for cal in valid_calibrations:
            display_text = f"{cal.calibration_id} ({cal.date}) - CV: {cal.cv_percent:.1f}%"
            self.calibration_combo.addItem(display_text, cal.calibration_id)
    
    def suggest_best_calibration(self):
        """Suggest the best calibration based on experiment date"""
        if not self.current_experiment:
            QMessageBox.information(self, "Info", "Please load experiment data first")
            return
        
        # Use current date for suggestion
        from datetime import datetime
        target_date = datetime.now().strftime("%Y-%m-%d")
        
        suggested_id = self.cal_manager.suggest_calibration_for_date(target_date)
        if suggested_id:
            # Find and select the suggested calibration
            for i in range(self.calibration_combo.count()):
                if self.calibration_combo.itemData(i) == suggested_id:
                    self.calibration_combo.setCurrentIndex(i)
                    break
            
            QMessageBox.information(self, "Suggestion", f"Suggested calibration: {suggested_id}")
        else:
            QMessageBox.information(self, "No Suggestion", "No valid calibrations available")
    
    def on_calibration_selected(self):
        """Handle calibration selection"""
        current_index = self.calibration_combo.currentIndex()
        if current_index > 0:  # Skip "Select calibration..." item
            cal_id = self.calibration_combo.itemData(current_index)
            self.selected_calibration = self.cal_manager.get_calibration(cal_id)
            self.update_calibration_details()
        else:
            self.selected_calibration = None
            self.calibration_details_label.setText("No calibration selected")
        
        self.update_process_button_state()
    
    def update_calibration_details(self):
        """Update calibration details display"""
        if not self.selected_calibration:
            return
        
        cal = self.selected_calibration
        
        details_text = f"""
        <b>Calibration ID:</b> {cal.calibration_id}<br>
        <b>Date:</b> {cal.date}<br>
        <b>Gas Concentration:</b> {cal.gas_concentration_ppm} ppm<br>
        <b>Mean Peak Area:</b> {cal.mean_peak_area:.1f} µV*s<br>
        <b>CV%:</b> {cal.cv_percent:.2f}% {'✅' if cal.cv_percent <= 5 else '⚠️' if cal.cv_percent <= 10 else '❌'}<br>
        <b>Runs:</b> {cal.num_runs} {'✅' if cal.num_runs >= 5 else '⚠️'}<br>
        <b>Quality Score:</b> {cal.quality_score:.1f}/100
        """
        
        self.calibration_details_label.setText(details_text)
    
    def update_process_button_state(self):
        """Update the process button enable state based on readiness"""
        if self.batch_mode:
            # Batch mode requirements
            ready = (
                len(self.selected_folders) > 0 and
                self.selected_calibration is not None and
                self.parameters_valid()
            )
        else:
            # Single mode requirements  
            ready = (
                self.current_experiment is not None and
                self.selected_calibration is not None and
                self.parameters_valid()
            )
        self.process_btn.setEnabled(ready)
    
    def parameters_valid(self) -> bool:
        """Check if all parameters are valid"""
        try:
            weight = float(self.sample_weight_edit.text()) if self.sample_weight_edit.text() else 0
            flow = float(self.flow_rate_edit.text()) if self.flow_rate_edit.text() else 0
            cycle = float(self.cycle_time_edit.text()) if self.cycle_time_edit.text() else 0
            
            return weight > 0 and flow > 0 and cycle > 0
        except ValueError:
            return False
    
    def process_data(self):
        """Process the experimental data - handles both single and batch modes"""
        if self.batch_mode:
            self.process_batch_data()
        else:
            self.process_single_data()
    
    def process_single_data(self):
        """Process single experiment data (original functionality)"""
        if not self.current_experiment or not self.selected_calibration:
            QMessageBox.warning(self, "Warning", "Please load data and select calibration first")
            return
        
        try:
            # Collect parameters
            parameters = {
                'sample_weight': float(self.sample_weight_edit.text()),
                'flow_rate': float(self.flow_rate_edit.text()),
                'cycle_time': float(self.cycle_time_edit.text())
            }
            
            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
            self.process_btn.setEnabled(False)
            
            QApplication.processEvents()
            
            # Process data
            self.processed_data = self.data_processor.calculate_hydrogen_concentrations(
                self.current_experiment, self.selected_calibration, parameters
            )
            
            # Update results summary
            stats = self.processed_data.get_summary_statistics()
            summary_text = f"""
            <b>Processing Complete!</b><br>
            <b>Total Hydrogen Released:</b> {stats['total_hydrogen_ppm']:.6f} ppm<br>
            <b>Maximum Evolution Rate:</b> {stats['max_rate_ppm_per_min']:.8f} ppm/min<br>
            <b>Average Evolution Rate:</b> {stats['avg_rate_ppm_per_min']:.8f} ppm/min<br>
            <b>Experiment Duration:</b> {stats['duration_minutes']:.1f} minutes<br>
            <b>Success Rate:</b> {stats['success_rate_percent']:.1f}%
            """
            
            self.results_summary_label.setText(summary_text)
            
            # Enable export buttons
            self.export_csv_btn.setEnabled(True)
            self.view_results_btn.setEnabled(True)
            
            # Show warnings if any
            if self.processed_data.processing_warnings:
                warning_text = "Processing completed with warnings:\n" + "\n".join(self.processed_data.processing_warnings)
                QMessageBox.warning(self, "Processing Warnings", warning_text)
            else:
                QMessageBox.information(self, "Success", "Data processing completed successfully!")
            
        except Exception as e:
            handle_error_with_user_feedback(self, "Data Processing", e)
        finally:
            self.progress_bar.setVisible(False)
            self.process_btn.setEnabled(True)
    
    def export_csv(self):
        """Export processed data as enhanced CSV"""
        if not self.processed_data:
            QMessageBox.information(self, "Info", "No processed data to export")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Enhanced CSV",
            f"{self.processed_data.experiment_name}_processed.csv",
            "CSV files (*.csv)"
        )
        
        if filename:
            try:
                self.data_processor.generate_enhanced_csv(self.processed_data, filename)
                QMessageBox.information(self, "Success", f"Data exported to {filename}")
            except Exception as e:
                handle_error_with_user_feedback(self, "CSV Export", e)
    
    def view_results(self):
        """View detailed processing results"""
        if not self.processed_data:
            QMessageBox.information(self, "Info", "No processed data to view")
            return
        
        dialog = ProcessingResultsDialog(self.processed_data, self)
        dialog.exec_()
    
    # Batch processing methods
    def on_mode_changed(self):
        """Handle mode change between single and batch processing"""
        self.batch_mode = self.batch_mode_radio.isChecked()
        
        # Show/hide appropriate widgets
        self.single_folder_widget.setVisible(not self.batch_mode)
        self.batch_folder_widget.setVisible(self.batch_mode)
        
        # Update process button text
        if self.batch_mode:
            self.process_btn.setText("Start Batch Processing")
        else:
            self.process_btn.setText("Process Data")
        
        # Reset state
        self.reset_processing_state()
        self.update_process_button_state()
    
    def add_batch_folders(self):
        """Add folders to batch processing list"""
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        
        # Enable multiple selection
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setViewMode(QFileDialog.List)
        
        # Custom dialog for multiple folder selection
        folders = QFileDialog.getExistingDirectory(
            self, "Select folders for batch processing (hold Ctrl to select multiple)", 
            "", QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folders:
            # Simple single folder selection for now - can be enhanced for multi-select
            folder_path = folders
            if folder_path not in self.selected_folders:
                self.selected_folders.append(folder_path)
                self.update_batch_folder_list()
                self.update_process_button_state()
    
    def clear_batch_folders(self):
        """Clear all selected batch folders"""
        self.selected_folders.clear()
        self.update_batch_folder_list()
        self.update_process_button_state()
    
    def update_batch_folder_list(self):
        """Update the batch folder list widget"""
        self.batch_folder_list.clear()
        
        for folder_path in self.selected_folders:
            folder_name = os.path.basename(folder_path)
            item = QListWidgetItem(f"📁 {folder_name}")
            item.setToolTip(folder_path)
            item.setData(Qt.UserRole, folder_path)
            self.batch_folder_list.addItem(item)
        
        # Update label count
        if hasattr(self, 'batch_folder_widget'):
            # Find and update the label
            for child in self.batch_folder_widget.findChildren(QLabel):
                if "Selected Folders" in child.text():
                    child.setText(f"Selected Folders ({len(self.selected_folders)}):")
                    break
    
    def show_batch_context_menu(self, position):
        """Show context menu for batch folder list"""
        item = self.batch_folder_list.itemAt(position)
        if item:
            menu = QMenu()
            
            remove_action = menu.addAction("Remove")
            remove_action.triggered.connect(lambda: self.remove_batch_folder(item))
            
            open_action = menu.addAction("Open in Explorer")
            open_action.triggered.connect(lambda: self.open_folder_in_explorer(item))
            
            menu.exec_(self.batch_folder_list.mapToGlobal(position))
    
    def remove_batch_folder(self, item):
        """Remove a folder from batch list"""
        folder_path = item.data(Qt.UserRole)
        if folder_path in self.selected_folders:
            self.selected_folders.remove(folder_path)
            self.update_batch_folder_list()
            self.update_process_button_state()
    
    def open_folder_in_explorer(self, item):
        """Open folder in system file explorer"""
        folder_path = item.data(Qt.UserRole)
        if os.path.exists(folder_path):
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                subprocess.run(["explorer", folder_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
    
    def preview_batch(self):
        """Preview batch processing details"""
        if not self.selected_folders:
            QMessageBox.information(self, "Preview Batch", "No folders selected for batch processing.")
            return
        
        try:
            preview = self.data_processor.get_batch_processing_preview(self.selected_folders)
            
            # Show preview dialog
            dialog = BatchPreviewDialog(preview, self)
            dialog.exec_()
            
        except Exception as e:
            handle_error_with_user_feedback(e, "Failed to preview batch processing", self)
    
    def cancel_processing(self):
        """Cancel ongoing processing"""
        # This would need to be implemented with threading for proper cancellation
        self.processing_cancelled = True
        self.reset_processing_state()
    
    def reset_processing_state(self):
        """Reset processing UI state"""
        self.progress_bar.setVisible(False)
        self.progress_status_label.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.process_btn.setEnabled(True)
        self.processing_cancelled = False
        
        # Clear results
        self.processed_data = None
        self.batch_results = None
        self.results_summary_label.setText("No processing results yet")
        self.export_csv_btn.setEnabled(False)
        self.view_results_btn.setEnabled(False)
    
    
    def process_batch_data(self):
        """Process multiple folders in batch mode"""
        # Validate inputs
        if not self.selected_folders:
            QMessageBox.warning(self, "Batch Processing", "No folders selected for batch processing.")
            return
        
        if not self.selected_calibration:
            QMessageBox.warning(self, "Batch Processing", "Please select a calibration.")
            return
        
        # Get parameters
        try:
            parameters = {
                'sample_weight': float(self.sample_weight_edit.text()),
                'flow_rate': float(self.flow_rate_edit.text()),
                'cycle_time': float(self.cycle_time_edit.text())
            }
        except ValueError:
            QMessageBox.warning(self, "Batch Processing", "Please enter valid numeric parameters.")
            return
        
        # Setup UI for processing
        self.processing_cancelled = False
        self.process_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.selected_folders))
        self.progress_bar.setValue(0)
        self.progress_status_label.setVisible(True)
        self.progress_status_label.setText("Starting batch processing...")
        
        try:
            # Process batch with progress callback
            self.batch_results = self.data_processor.process_batch(
                self.selected_folders,
                self.selected_calibration,
                parameters,
                progress_callback=self.update_batch_progress
            )
            
            # Show results
            self.show_batch_results()
            
        except Exception as e:
            handle_error_with_user_feedback(e, "Batch processing failed", self)
        finally:
            self.reset_processing_state()
    
    
    def update_batch_progress(self, current: int, total: int, status: str):
        """Update batch processing progress"""
        if self.processing_cancelled:
            return
        
        self.progress_bar.setValue(current)
        self.progress_status_label.setText(status)
        QApplication.processEvents()  # Keep UI responsive
    
    def show_batch_results(self):
        """Show batch processing results"""
        if not self.batch_results:
            return
        
        # Update results summary
        summary = f"""
        <b>Batch Processing Complete</b><br>
        Total Folders: {self.batch_results.total_folders}<br>
        Successful: {self.batch_results.successful}<br>
        Failed: {self.batch_results.failed}<br>
        Success Rate: {self.batch_results.get_success_rate():.1f}%<br>
        Processing Time: {self.batch_results.total_processing_time:.1f} seconds<br>
        Output Folder: {self.batch_results.output_folder}
        """
        
        self.results_summary_label.setText(summary)
        
        # Enable viewing results
        self.view_results_btn.setEnabled(True)
        
        # Show detailed results dialog
        dialog = BatchResultsDialog(self.batch_results, self)
        dialog.exec_()


class BatchPreviewDialog(QDialog):
    """Dialog to preview batch processing details"""
    
    def __init__(self, preview_data: dict, parent=None):
        super().__init__(parent)
        self.preview_data = preview_data
        self.setWindowTitle("Batch Processing Preview")
        self.setModal(True)
        self.resize(600, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Summary
        summary_text = f"""
        <b>Batch Processing Preview</b><br>
        Total Folders: {self.preview_data['total_folders']}<br>
        Valid Folders: {self.preview_data['valid_folders']}<br>
        Invalid Folders: {self.preview_data['invalid_folders']}<br>
        """
        
        summary_label = QLabel(summary_text)
        layout.addWidget(summary_label)
        
        # Folder details
        self.folder_table = QTableWidget()
        self.folder_table.setColumnCount(3)
        self.folder_table.setHorizontalHeaderLabels(["Folder Name", "Status", "Path"])
        
        details = self.preview_data['folder_details']
        self.folder_table.setRowCount(len(details))
        
        for i, detail in enumerate(details):
            self.folder_table.setItem(i, 0, QTableWidgetItem(detail['name']))
            self.folder_table.setItem(i, 1, QTableWidgetItem(detail['status']))
            self.folder_table.setItem(i, 2, QTableWidgetItem(detail['path']))
            
            # Color code based on status
            if detail['valid']:
                color = QColor(200, 255, 200)  # Light green
            else:
                color = QColor(255, 200, 200)  # Light red
            
            for j in range(3):
                self.folder_table.item(i, j).setBackground(color)
        
        self.folder_table.resizeColumnsToContents()
        layout.addWidget(self.folder_table)
        
        # Expected outputs
        if self.preview_data['estimated_outputs']:
            layout.addWidget(QLabel(f"<b>Expected CSV Output Files ({len(self.preview_data['estimated_outputs'])}):</b>"))
            
            outputs_text = QTextEdit()
            outputs_text.setText('\n'.join(self.preview_data['estimated_outputs']))
            outputs_text.setMaximumHeight(100)
            outputs_text.setReadOnly(True)
            layout.addWidget(outputs_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)


class BatchResultsDialog(QDialog):
    """Dialog to view detailed batch processing results"""
    
    def __init__(self, batch_results: BatchResults, parent=None):
        super().__init__(parent)
        self.batch_results = batch_results
        self.setWindowTitle("Batch Processing Results")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Summary
        summary_text = f"""
        <b>Batch Processing Results</b><br>
        Total Folders: {self.batch_results.total_folders}<br>
        Successful: {self.batch_results.successful}<br>
        Failed: {self.batch_results.failed}<br>
        Success Rate: {self.batch_results.get_success_rate():.1f}%<br>
        Total Processing Time: {self.batch_results.total_processing_time:.1f} seconds<br>
        Output Folder: {self.batch_results.output_folder}
        """
        
        summary_label = QLabel(summary_text)
        layout.addWidget(summary_label)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "Folder", "Status", "Processing Time", "CSV Output", "Error Message"
        ])
        
        results = self.batch_results.results
        self.results_table.setRowCount(len(results))
        
        for i, result in enumerate(results):
            self.results_table.setItem(i, 0, QTableWidgetItem(result.experiment_name))
            self.results_table.setItem(i, 1, QTableWidgetItem("Success" if result.success else "Failed"))
            self.results_table.setItem(i, 2, QTableWidgetItem(f"{result.processing_time:.1f}s"))
            
            if result.success and result.csv_output_path:
                csv_name = os.path.basename(result.csv_output_path)
                self.results_table.setItem(i, 3, QTableWidgetItem(csv_name))
            else:
                self.results_table.setItem(i, 3, QTableWidgetItem("N/A"))
            
            error_msg = result.error_message or ""
            if len(error_msg) > 100:
                error_msg = error_msg[:97] + "..."
            self.results_table.setItem(i, 4, QTableWidgetItem(error_msg))
            
            # Color code based on success
            if result.success:
                color = QColor(200, 255, 200)  # Light green
            else:
                color = QColor(255, 200, 200)  # Light red
            
            for j in range(5):
                self.results_table.item(i, j).setBackground(color)
        
        self.results_table.resizeColumnsToContents()
        layout.addWidget(self.results_table)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        if self.batch_results.get_successful_csvs():
            open_folder_btn = QPushButton("Open Output Folder")
            open_folder_btn.clicked.connect(self.open_output_folder)
            button_layout.addWidget(open_folder_btn)
        
        export_report_btn = QPushButton("Export Report")
        export_report_btn.clicked.connect(self.export_report)
        button_layout.addWidget(export_report_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def open_output_folder(self):
        """Open the output folder in system file explorer"""
        if os.path.exists(self.batch_results.output_folder):
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                subprocess.run(["explorer", self.batch_results.output_folder])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", self.batch_results.output_folder])
            else:  # Linux
                subprocess.run(["xdg-open", self.batch_results.output_folder])
    
    def export_report(self):
        """Export batch processing report to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Batch Report", "batch_report.txt", "Text Files (*.txt)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("TDA Batch Processing Report\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Total Folders: {self.batch_results.total_folders}\n")
                    f.write(f"Successful: {self.batch_results.successful}\n")
                    f.write(f"Failed: {self.batch_results.failed}\n")
                    f.write(f"Success Rate: {self.batch_results.get_success_rate():.1f}%\n")
                    f.write(f"Total Processing Time: {self.batch_results.total_processing_time:.1f} seconds\n")
                    f.write(f"Output Folder: {self.batch_results.output_folder}\n\n")
                    
                    f.write("Detailed Results:\n")
                    f.write("-" * 30 + "\n")
                    
                    for result in self.batch_results.results:
                        f.write(f"\nFolder: {result.experiment_name}\n")
                        f.write(f"Status: {'Success' if result.success else 'Failed'}\n")
                        f.write(f"Processing Time: {result.processing_time:.1f}s\n")
                        
                        if result.success and result.csv_output_path:
                            f.write(f"CSV Output: {os.path.basename(result.csv_output_path)}\n")
                        
                        if result.error_message:
                            f.write(f"Error: {result.error_message}\n")
                        
                        if result.data_summary:
                            f.write(f"Total Hydrogen: {result.data_summary.get('total_hydrogen_ppm', 'N/A')} ppm\n")
                            f.write(f"Duration: {result.data_summary.get('duration_minutes', 'N/A')} minutes\n")
                
                QMessageBox.information(self, "Export Complete", f"Report exported to:\n{filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export report:\n{str(e)}")


class ProcessingResultsDialog(QDialog):
    """Dialog to view detailed processing results"""
    
    def __init__(self, processed_data: ExperimentData, parent=None):
        super().__init__(parent)
        self.processed_data = processed_data
        self.setWindowTitle("Processing Results")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Summary information
        stats = self.processed_data.get_summary_statistics()
        summary_text = f"""
        <h3>Processing Results for {self.processed_data.experiment_name}</h3>
        <b>Total Hydrogen Released:</b> {stats['total_hydrogen_ppm']:.6f} ppm<br>
        <b>Maximum Evolution Rate:</b> {stats['max_rate_ppm_per_min']:.8f} ppm/min<br>
        <b>Average Evolution Rate:</b> {stats['avg_rate_ppm_per_min']:.8f} ppm/min<br>
        <b>Experiment Duration:</b> {stats['duration_minutes']:.1f} minutes ({stats['duration_minutes']/60:.2f} hours)<br>
        <b>Successful Runs:</b> {stats['successful_runs']}<br>
        <b>Failed Runs:</b> {stats['failed_runs']}<br>
        <b>Success Rate:</b> {stats['success_rate_percent']:.1f}%
        """
        
        summary_label = QLabel(summary_text)
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)
        
        # Data table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            'Run', 'Time (min)', 'Peak Area', 'H ppm/min', 'H ppm/cycle', 'Cumulative H', 'Quality Flags', 'Timestamp'
        ])
        
        # Fill table with first 50 rows (for performance)
        num_rows = min(50, len(self.processed_data.run_numbers))
        self.results_table.setRowCount(num_rows)
        
        for i in range(num_rows):
            self.results_table.setItem(i, 0, QTableWidgetItem(str(self.processed_data.run_numbers[i])))
            self.results_table.setItem(i, 1, QTableWidgetItem(f"{self.processed_data.time_minutes[i]:.2f}"))
            self.results_table.setItem(i, 2, QTableWidgetItem(f"{self.processed_data.peak_areas[i]:.1f}"))
            self.results_table.setItem(i, 3, QTableWidgetItem(f"{self.processed_data.h_ppm_per_min[i]:.8f}"))
            self.results_table.setItem(i, 4, QTableWidgetItem(f"{self.processed_data.h_ppm_over_cycle[i]:.8f}"))
            self.results_table.setItem(i, 5, QTableWidgetItem(f"{self.processed_data.cumulative_h_ppm[i]:.8f}"))
            
            flags = self.processed_data.quality_flags[i] if i < len(self.processed_data.quality_flags) else ""
            self.results_table.setItem(i, 6, QTableWidgetItem(flags))
            self.results_table.setItem(i, 7, QTableWidgetItem(self.processed_data.timestamps[i]))
        
        if len(self.processed_data.run_numbers) > 50:
            layout.addWidget(QLabel(f"Showing first 50 of {len(self.processed_data.run_numbers)} rows"))
        
        layout.addWidget(self.results_table)
        
        # Processing warnings
        if self.processed_data.processing_warnings:
            layout.addWidget(QLabel("<b>Processing Warnings:</b>"))
            warnings_text = QTextEdit()
            warnings_text.setText('\n'.join(self.processed_data.processing_warnings))
            warnings_text.setMaximumHeight(100)
            warnings_text.setReadOnly(True)
            layout.addWidget(warnings_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)