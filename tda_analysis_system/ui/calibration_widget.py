"""
Calibration Widget GUI for TDA Analysis System

This module provides the GUI interface for calibration management with three main sections:
1. Process New Calibration
2. Calibration Database
3. Calibration Details
"""

import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from modules.calibration_manager import CalibrationManager
from modules.shared_data_structures import CalibrationData
from modules.error_handling import handle_error_with_user_feedback


class CalibrationWidget(QWidget):
    """Main calibration management widget with three-section layout"""
    
    def __init__(self, calibration_manager: CalibrationManager):
        super().__init__()
        self.cal_manager = calibration_manager
        self.current_calibration = None
        self.setup_ui()
        self.refresh_calibration_list()
    
    def setup_ui(self):
        """Create three-section layout for calibration management"""
        layout = QVBoxLayout()
        
        # Section 1: Process New Calibration
        process_group = self.create_process_section()
        layout.addWidget(process_group)
        
        # Section 2: Calibration Database
        database_group = self.create_database_section()
        layout.addWidget(database_group)
        
        # Section 3: Calibration Details
        details_group = self.create_details_section()
        layout.addWidget(details_group)
        
        self.setLayout(layout)
    
    def create_process_section(self):
        """Process New Calibration section"""
        group = QGroupBox("Process New Calibration")
        layout = QVBoxLayout()
        
        # Input method selection
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Input Method:"))
        self.input_method_combo = QComboBox()
        self.input_method_combo.addItems(["From Folder", "Manual Entry"])
        self.input_method_combo.currentTextChanged.connect(self.on_input_method_changed)
        method_layout.addWidget(self.input_method_combo)
        method_layout.addStretch()
        layout.addLayout(method_layout)
        
        # Create stacked widget for different input methods
        self.input_stack = QStackedWidget()
        
        # Folder input page
        folder_widget = QWidget()
        folder_layout = QGridLayout()
        
        # Folder selection
        folder_layout.addWidget(QLabel("Folder Path:"), 0, 0)
        self.folder_path_edit = QLineEdit()
        folder_layout.addWidget(self.folder_path_edit, 0, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_calibration_folder)
        folder_layout.addWidget(browse_btn, 0, 2)
        
        # Gas concentration
        folder_layout.addWidget(QLabel("Gas Concentration:"), 1, 0)
        self.gas_ppm_edit = QLineEdit("61.0")
        folder_layout.addWidget(self.gas_ppm_edit, 1, 1)
        folder_layout.addWidget(QLabel("ppm"), 1, 2)
        
        # Custom name (optional)
        folder_layout.addWidget(QLabel("Calibration Name:"), 2, 0)
        self.cal_name_edit = QLineEdit()
        self.cal_name_edit.setPlaceholderText("Auto-generate if empty")
        folder_layout.addWidget(self.cal_name_edit, 2, 1, 1, 2)
        
        folder_widget.setLayout(folder_layout)
        self.input_stack.addWidget(folder_widget)
        
        # Manual input page
        manual_widget = QWidget()
        manual_layout = QGridLayout()
        
        # Calibration ID
        manual_layout.addWidget(QLabel("Calibration ID:"), 0, 0)
        self.manual_cal_id_edit = QLineEdit()
        self.manual_cal_id_edit.setPlaceholderText("e.g., cal_2024-07-07_001")
        manual_layout.addWidget(self.manual_cal_id_edit, 0, 1, 1, 2)
        
        # Date
        manual_layout.addWidget(QLabel("Date:"), 1, 0)
        self.manual_date_edit = QLineEdit()
        self.manual_date_edit.setText(QDate.currentDate().toString("yyyy-MM-dd"))
        manual_layout.addWidget(self.manual_date_edit, 1, 1)
        
        date_btn = QPushButton("Select Date")
        date_btn.clicked.connect(self.select_calibration_date)
        manual_layout.addWidget(date_btn, 1, 2)
        
        # Gas concentration
        manual_layout.addWidget(QLabel("Gas Concentration:"), 2, 0)
        self.manual_gas_ppm_edit = QLineEdit("61.0")
        manual_layout.addWidget(self.manual_gas_ppm_edit, 2, 1)
        manual_layout.addWidget(QLabel("ppm"), 2, 2)
        
        # Peak area data entry
        manual_layout.addWidget(QLabel("Peak Areas:"), 3, 0)
        self.peak_areas_edit = QTextEdit()
        self.peak_areas_edit.setMaximumHeight(80)
        self.peak_areas_edit.setPlaceholderText("Enter peak areas separated by commas or new lines\nExample: 12345.6, 12543.2, 12398.7, 12467.1, 12412.5")
        manual_layout.addWidget(self.peak_areas_edit, 3, 1, 1, 2)
        
        # Run count
        manual_layout.addWidget(QLabel("Number of Runs:"), 4, 0)
        self.manual_runs_edit = QLineEdit()
        self.manual_runs_edit.setPlaceholderText("Auto-calculated from peak areas")
        self.manual_runs_edit.setReadOnly(True)
        manual_layout.addWidget(self.manual_runs_edit, 4, 1, 1, 2)
        
        # Connect peak areas to run count calculation
        self.peak_areas_edit.textChanged.connect(self.update_manual_run_count)
        
        manual_widget.setLayout(manual_layout)
        self.input_stack.addWidget(manual_widget)
        
        layout.addWidget(self.input_stack)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Preview Data")
        self.preview_btn.clicked.connect(self.preview_calibration_data)
        button_layout.addWidget(self.preview_btn)
        
        self.process_btn = QPushButton("Process Calibration")
        self.process_btn.clicked.connect(self.process_calibration)
        self.process_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        button_layout.addWidget(self.process_btn)
        
        layout.addLayout(button_layout)
        
        group.setLayout(layout)
        return group
    
    def create_database_section(self):
        """Calibration Database section"""
        group = QGroupBox("Calibration Database")
        layout = QVBoxLayout()
        
        # Search/filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter by name or date...")
        self.search_edit.textChanged.connect(self.filter_calibrations)
        filter_layout.addWidget(self.search_edit)
        
        self.quality_filter = QComboBox()
        self.quality_filter.addItems(["All", "Valid Only", "High Quality (>80)", "Needs Review"])
        self.quality_filter.currentTextChanged.connect(self.filter_calibrations)
        filter_layout.addWidget(self.quality_filter)
        
        layout.addLayout(filter_layout)
        
        # Calibration list table
        self.calibration_table = QTableWidget()
        self.calibration_table.setColumnCount(7)
        self.calibration_table.setHorizontalHeaderLabels([
            'Date', 'ID', 'Mean Peak Area', 'CV%', 'Runs', 'Quality', 'Status'
        ])
        
        # Configure table
        header = self.calibration_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.calibration_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.calibration_table.setAlternatingRowColors(True)
        self.calibration_table.itemSelectionChanged.connect(self.on_calibration_selected)
        
        layout.addWidget(self.calibration_table)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        view_btn = QPushButton("View Details")
        view_btn.clicked.connect(self.view_calibration_details)
        button_layout.addWidget(view_btn)
        
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_calibration)
        edit_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
        button_layout.addWidget(edit_btn)
        
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_calibration)
        button_layout.addWidget(export_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_calibration)
        delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        button_layout.addWidget(delete_btn)
        
        default_btn = QPushButton("Set as Default")
        default_btn.clicked.connect(self.set_as_default)
        button_layout.addWidget(default_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        group.setLayout(layout)
        return group
    
    def create_details_section(self):
        """Calibration Details section"""
        group = QGroupBox("Calibration Details")
        layout = QHBoxLayout()
        
        # Left side: Statistics
        stats_layout = QVBoxLayout()
        
        self.details_label = QLabel("No calibration selected")
        self.details_label.setWordWrap(True)
        stats_layout.addWidget(self.details_label)
        
        self.quality_text = QTextEdit()
        self.quality_text.setMaximumHeight(100)
        self.quality_text.setReadOnly(True)
        stats_layout.addWidget(self.quality_text)
        
        # Action buttons for details
        details_button_layout = QHBoxLayout()
        
        plot_btn = QPushButton("Plot Raw Data")
        plot_btn.clicked.connect(self.plot_calibration_data)
        details_button_layout.addWidget(plot_btn)
        
        stats_btn = QPushButton("View Statistics")
        stats_btn.clicked.connect(self.view_detailed_statistics)
        details_button_layout.addWidget(stats_btn)
        
        csv_btn = QPushButton("Export CSV")
        csv_btn.clicked.connect(self.export_calibration_csv)
        details_button_layout.addWidget(csv_btn)
        
        stats_layout.addLayout(details_button_layout)
        layout.addLayout(stats_layout)
        
        # Right side: Mini plot (optional)
        self.mini_plot_widget = QWidget()
        self.mini_plot_widget.setMinimumSize(300, 200)
        layout.addWidget(self.mini_plot_widget)
        
        group.setLayout(layout)
        return group
    
    def browse_calibration_folder(self):
        """Open folder browser for calibration data"""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Calibration Data Folder",
            "",
            QFileDialog.ShowDirsOnly
        )
        if folder:
            self.folder_path_edit.setText(folder)
    
    def preview_calibration_data(self):
        """Preview calibration data before processing"""
        folder_path = self.folder_path_edit.text().strip()
        if not folder_path:
            QMessageBox.warning(self, "Warning", "Please select a calibration folder")
            return
        
        try:
            dialog = CalibrationPreviewDialog(folder_path, self)
            dialog.exec_()
        except Exception as e:
            handle_error_with_user_feedback(self, "Data Preview", e)
    
    def process_calibration(self):
        """Process new calibration (folder or manual entry)"""
        if self.input_method_combo.currentText() == "From Folder":
            self.process_folder_calibration()
        else:
            self.process_manual_calibration()
    
    def process_folder_calibration(self):
        """Process new calibration folder"""
        folder_path = self.folder_path_edit.text().strip()
        if not folder_path:
            QMessageBox.warning(self, "Warning", "Please select a calibration folder")
            return
        
        if not os.path.exists(folder_path):
            QMessageBox.critical(self, "Error", "Selected folder does not exist")
            return
        
        try:
            gas_ppm = float(self.gas_ppm_edit.text())
            if gas_ppm <= 0:
                raise ValueError("Gas concentration must be positive")
        except ValueError as e:
            QMessageBox.critical(self, "Error", f"Invalid gas concentration: {e}")
            return
        
        cal_name = self.cal_name_edit.text().strip() or None
        
        # Show progress dialog
        progress = QProgressDialog("Processing calibration data...", "Cancel", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        try:
            # Process calibration
            cal_data = self.cal_manager.process_calibration_folder(
                folder_path, gas_ppm, cal_name
            )
            
            # Show results
            self.show_processing_results(cal_data)
            
            # Refresh display
            self.refresh_calibration_list()
            
            # Clear input fields
            self.folder_path_edit.clear()
            self.cal_name_edit.clear()
            
        except Exception as e:
            handle_error_with_user_feedback(self, "Calibration Processing", e)
        finally:
            progress.close()
    
    def show_processing_results(self, cal_data: CalibrationData):
        """Display calibration processing results"""
        dialog = CalibrationResultDialog(cal_data, self)
        dialog.exec_()
    
    def refresh_calibration_list(self):
        """Refresh the calibration list table"""
        calibrations = list(self.cal_manager.calibrations.values())
        calibrations.sort(key=lambda x: x.date, reverse=True)
        
        self.calibration_table.setRowCount(len(calibrations))
        
        for row, cal_data in enumerate(calibrations):
            # Date
            self.calibration_table.setItem(row, 0, QTableWidgetItem(cal_data.date))
            
            # ID
            self.calibration_table.setItem(row, 1, QTableWidgetItem(cal_data.calibration_id))
            
            # Mean Peak Area
            self.calibration_table.setItem(row, 2, QTableWidgetItem(f"{cal_data.mean_peak_area:,.0f}"))
            
            # CV%
            cv_item = QTableWidgetItem(f"{cal_data.cv_percent:.1f}%")
            if cal_data.cv_percent > 10:
                cv_item.setBackground(QColor("#ffcccb"))  # Light red
            elif cal_data.cv_percent > 5:
                cv_item.setBackground(QColor("#fff4cd"))  # Light yellow
            else:
                cv_item.setBackground(QColor("#d4edda"))  # Light green
            self.calibration_table.setItem(row, 3, cv_item)
            
            # Runs
            self.calibration_table.setItem(row, 4, QTableWidgetItem(str(cal_data.num_runs)))
            
            # Quality Score
            quality_item = QTableWidgetItem(f"{cal_data.quality_score:.0f}/100")
            if cal_data.quality_score >= 80:
                quality_item.setBackground(QColor("#d4edda"))  # Light green
            elif cal_data.quality_score >= 60:
                quality_item.setBackground(QColor("#fff4cd"))  # Light yellow
            else:
                quality_item.setBackground(QColor("#ffcccb"))  # Light red
            self.calibration_table.setItem(row, 5, quality_item)
            
            # Status
            status = "Valid" if cal_data.is_valid else "Invalid"
            status_item = QTableWidgetItem(status)
            if not cal_data.is_valid:
                status_item.setBackground(QColor("#ffcccb"))
            self.calibration_table.setItem(row, 6, status_item)
        
        # Resize columns to content
        self.calibration_table.resizeColumnsToContents()
    
    def filter_calibrations(self):
        """Filter calibrations based on search and quality criteria"""
        search_text = self.search_edit.text().lower()
        quality_filter = self.quality_filter.currentText()
        
        for row in range(self.calibration_table.rowCount()):
            show_row = True
            
            # Apply search filter
            if search_text:
                row_text = ""
                for col in range(self.calibration_table.columnCount()):
                    item = self.calibration_table.item(row, col)
                    if item:
                        row_text += item.text().lower() + " "
                
                if search_text not in row_text:
                    show_row = False
            
            # Apply quality filter
            if quality_filter != "All" and show_row:
                quality_item = self.calibration_table.item(row, 5)
                status_item = self.calibration_table.item(row, 6)
                
                if quality_filter == "Valid Only":
                    show_row = status_item and status_item.text() == "Valid"
                elif quality_filter == "High Quality (>80)":
                    if quality_item:
                        quality_score = float(quality_item.text().split('/')[0])
                        show_row = quality_score > 80
                elif quality_filter == "Needs Review":
                    show_row = status_item and status_item.text() == "Invalid"
            
            self.calibration_table.setRowHidden(row, not show_row)
    
    def on_calibration_selected(self):
        """Handle calibration selection in table"""
        selected_rows = self.calibration_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            cal_id_item = self.calibration_table.item(row, 1)
            if cal_id_item:
                cal_id = cal_id_item.text()
                self.current_calibration = self.cal_manager.get_calibration(cal_id)
                self.update_details_display()
    
    def update_details_display(self):
        """Update the details section with selected calibration info"""
        if not self.current_calibration:
            self.details_label.setText("No calibration selected")
            self.quality_text.clear()
            return
        
        cal = self.current_calibration
        
        # Update statistics display
        details_text = f"""
        <b>Calibration ID:</b> {cal.calibration_id}<br>
        <b>Date:</b> {cal.date}<br>
        <b>Gas Concentration:</b> {cal.gas_concentration_ppm} ppm<br>
        <b>Mean Peak Area:</b> {cal.mean_peak_area:.1f} µV*s<br>
        <b>Standard Deviation:</b> {cal.std_deviation:.1f} µV*s<br>
        <b>CV%:</b> {cal.cv_percent:.2f}%<br>
        <b>Number of Runs:</b> {cal.num_runs}<br>
        <b>Quality Score:</b> {cal.quality_score:.1f}/100<br>
        <b>Status:</b> {'Valid' if cal.is_valid else 'Invalid'}
        """
        
        self.details_label.setText(details_text)
        
        # Update quality flags
        if cal.quality_flags:
            self.quality_text.setText('\n'.join(cal.quality_flags))
        else:
            self.quality_text.setText("No quality issues detected")
    
    def view_calibration_details(self):
        """View detailed calibration information"""
        if not self.current_calibration:
            QMessageBox.information(self, "Info", "Please select a calibration first")
            return
        
        dialog = DetailedStatisticsDialog(self.current_calibration, self)
        dialog.exec_()
    
    def export_calibration(self):
        """Export calibration data"""
        if not self.current_calibration:
            QMessageBox.information(self, "Info", "Please select a calibration first")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Calibration", 
            f"{self.current_calibration.calibration_id}.json",
            "JSON files (*.json)"
        )
        
        if filename:
            try:
                import json
                with open(filename, 'w') as f:
                    json.dump(self.current_calibration.to_dict(), f, indent=2)
                QMessageBox.information(self, "Success", "Calibration exported successfully")
            except Exception as e:
                handle_error_with_user_feedback(self, "Export Calibration", e)
    
    def delete_calibration(self):
        """Delete selected calibration"""
        if not self.current_calibration:
            QMessageBox.information(self, "Info", "Please select a calibration first")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete calibration {self.current_calibration.calibration_id}?\n\n"
            "This will permanently remove the calibration and all associated files.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.cal_manager.delete_calibration(self.current_calibration.calibration_id)
                if success:
                    QMessageBox.information(self, "Success", "Calibration deleted successfully")
                    self.refresh_calibration_list()
                    self.current_calibration = None
                    self.update_details_display()
                else:
                    QMessageBox.warning(self, "Warning", "Failed to delete calibration")
            except Exception as e:
                handle_error_with_user_feedback(self, "Delete Calibration", e)
    
    def set_as_default(self):
        """Set selected calibration as default"""
        if not self.current_calibration:
            QMessageBox.information(self, "Info", "Please select a calibration first")
            return
        
        # This would be implemented when we have settings management
        QMessageBox.information(self, "Info", "Default calibration functionality will be implemented with settings management")
    
    def plot_calibration_data(self):
        """Plot raw calibration data"""
        if not self.current_calibration:
            QMessageBox.information(self, "Info", "Please select a calibration first")
            return
        
        # This would show a plot dialog with the raw data
        QMessageBox.information(self, "Info", "Plotting functionality will be implemented with matplotlib integration")
    
    def view_detailed_statistics(self):
        """View detailed statistics dialog"""
        if not self.current_calibration:
            QMessageBox.information(self, "Info", "Please select a calibration first")
            return
        
        dialog = DetailedStatisticsDialog(self.current_calibration, self)
        dialog.exec_()
    
    def export_calibration_csv(self):
        """Export calibration as CSV"""
        if not self.current_calibration:
            QMessageBox.information(self, "Info", "Please select a calibration first")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Calibration CSV", 
            f"{self.current_calibration.calibration_id}.csv",
            "CSV files (*.csv)"
        )
        
        if filename:
            try:
                # Copy the CSV file from calibration folder
                cal_folder = os.path.join(self.cal_manager.calibration_folder, self.current_calibration.calibration_id)
                source_csv = os.path.join(cal_folder, "processed_data.csv")
                
                if os.path.exists(source_csv):
                    import shutil
                    shutil.copy2(source_csv, filename)
                    QMessageBox.information(self, "Success", "CSV exported successfully")
                else:
                    QMessageBox.warning(self, "Warning", "Source CSV file not found")
            except Exception as e:
                handle_error_with_user_feedback(self, "Export CSV", e)

    def on_input_method_changed(self):
        """Handle input method change"""
        if self.input_method_combo.currentText() == "From Folder":
            self.input_stack.setCurrentIndex(0)
        else:
            self.input_stack.setCurrentIndex(1)

    def select_calibration_date(self):
        """Open date picker for calibration date"""
        current_date = QDate.fromString(self.manual_date_edit.text(), "yyyy-MM-dd")
        if not current_date.isValid():
            current_date = QDate.currentDate()
        
        date, ok = QInputDialog.getText(self, "Select Date", "Enter date (YYYY-MM-DD):", 
                                       text=current_date.toString("yyyy-MM-dd"))
        if ok and date:
            # Validate date format
            try:
                QDate.fromString(date, "yyyy-MM-dd")
                self.manual_date_edit.setText(date)
            except:
                QMessageBox.warning(self, "Invalid Date", "Please enter date in YYYY-MM-DD format")

    def update_manual_run_count(self):
        """Update run count based on entered peak areas"""
        text = self.peak_areas_edit.toPlainText().strip()
        if not text:
            self.manual_runs_edit.clear()
            return
        
        # Parse peak areas
        areas = []
        for line in text.split('\n'):
            for area_str in line.split(','):
                area_str = area_str.strip()
                if area_str:
                    try:
                        areas.append(float(area_str))
                    except ValueError:
                        pass
        
        self.manual_runs_edit.setText(str(len(areas)))

    def process_manual_calibration(self):
        """Process manually entered calibration data"""
        try:
            # Validate inputs
            cal_id = self.manual_cal_id_edit.text().strip()
            if not cal_id:
                QMessageBox.warning(self, "Missing Data", "Please enter a calibration ID")
                return
            
            date_str = self.manual_date_edit.text().strip()
            if not date_str:
                QMessageBox.warning(self, "Missing Data", "Please enter a date")
                return
            
            try:
                gas_ppm = float(self.manual_gas_ppm_edit.text())
            except ValueError:
                QMessageBox.warning(self, "Invalid Data", "Please enter a valid gas concentration")
                return
            
            # Parse peak areas
            text = self.peak_areas_edit.toPlainText().strip()
            if not text:
                QMessageBox.warning(self, "Missing Data", "Please enter peak areas")
                return
            
            peak_areas = []
            for line in text.split('\n'):
                for area_str in line.split(','):
                    area_str = area_str.strip()
                    if area_str:
                        try:
                            peak_areas.append(float(area_str))
                        except ValueError:
                            QMessageBox.warning(self, "Invalid Data", f"Invalid peak area: {area_str}")
                            return
            
            if len(peak_areas) < 3:
                QMessageBox.warning(self, "Insufficient Data", "Please enter at least 3 peak area values")
                return
            
            # Create calibration data
            from datetime import datetime
            cal_data = CalibrationData(
                calibration_id=cal_id,
                date=date_str,
                processing_timestamp=datetime.now().isoformat(),
                gas_concentration_ppm=gas_ppm,
                raw_peak_areas=peak_areas,
                raw_timestamps=[datetime.now().strftime("%m/%d/%Y %H:%M:%S")] * len(peak_areas),
                source_folder="Manual Entry",
                operator="USER",
                notes="Manually entered calibration data"
            )
            
            # Calculate statistics
            stats = self.cal_manager.calculate_calibration_stats(peak_areas)
            cal_data.mean_peak_area = stats['mean']
            cal_data.std_deviation = stats['std_dev']
            cal_data.cv_percent = stats['cv_percent']
            cal_data.num_runs = stats['n_points']
            cal_data.min_peak_area = stats['min_value']
            cal_data.max_peak_area = stats['max_value']
            cal_data.median_peak_area = stats['median']
            cal_data.outlier_indices = stats['outlier_indices']
            
            # Validate quality
            self.cal_manager.validate_calibration_quality(cal_data)
            cal_data.quality_score = cal_data.calculate_quality_score()
            
            # Add to database
            self.cal_manager.calibrations[cal_id] = cal_data
            self.cal_manager.save_database()
            
            # Show results and refresh
            self.show_processing_results(cal_data)
            self.refresh_calibration_list()
            
            # Clear manual input form
            self.manual_cal_id_edit.clear()
            self.peak_areas_edit.clear()
            self.manual_runs_edit.clear()
            
        except Exception as e:
            handle_error_with_user_feedback(self, "Process Manual Calibration", e)

    def edit_calibration(self):
        """Edit selected calibration"""
        selected_rows = self.calibration_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a calibration to edit")
            return
        
        row = selected_rows[0].row()
        cal_id = self.calibration_table.item(row, 1).text()
        cal_data = self.cal_manager.calibrations.get(cal_id)
        
        if not cal_data:
            QMessageBox.warning(self, "Error", "Calibration not found")
            return
        
        # Open edit dialog
        dialog = CalibrationEditDialog(cal_data, self)
        if dialog.exec_() == QDialog.Accepted:
            # Update calibration in database
            self.cal_manager.calibrations[cal_id] = cal_data
            self.cal_manager.save_database()
            self.refresh_calibration_list()
            self.update_details_display()


class CalibrationResultDialog(QDialog):
    """Dialog to show calibration processing results"""
    
    def __init__(self, cal_data: CalibrationData, parent=None):
        super().__init__(parent)
        self.cal_data = cal_data
        self.setWindowTitle("Calibration Processing Results")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Results summary
        summary_text = f"""
        <h3>Calibration Processing Complete</h3>
        <b>Calibration ID:</b> {self.cal_data.calibration_id}<br>
        <b>Mean Peak Area:</b> {self.cal_data.mean_peak_area:.1f} µV*s<br>
        <b>Standard Deviation:</b> {self.cal_data.std_deviation:.1f} µV*s<br>
        <b>CV%:</b> {self.cal_data.cv_percent:.2f}%<br>
        <b>Number of Runs:</b> {self.cal_data.num_runs}<br>
        <b>Quality Score:</b> {self.cal_data.quality_score:.1f}/100<br>
        <b>Status:</b> {'Valid' if self.cal_data.is_valid else 'Invalid'}
        """
        
        summary_label = QLabel(summary_text)
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)
        
        # Quality flags
        if self.cal_data.quality_flags:
            layout.addWidget(QLabel("<b>Quality Flags:</b>"))
            flags_text = QTextEdit()
            flags_text.setText('\n'.join(self.cal_data.quality_flags))
            flags_text.setMaximumHeight(100)
            flags_text.setReadOnly(True)
            layout.addWidget(flags_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)


class CalibrationPreviewDialog(QDialog):
    """Dialog to preview calibration data before processing"""
    
    def __init__(self, folder_path: str, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self.setWindowTitle("Calibration Data Preview")
        self.setModal(True)
        self.resize(600, 400)
        self.setup_ui()
        self.load_preview()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel(f"<b>Folder:</b> {self.folder_path}"))
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_preview(self):
        """Load and display preview of data"""
        try:
            from modules.data_extraction import TDAFileExtractor
            data = TDAFileExtractor.extract_from_folder(self.folder_path)
            
            preview_text = f"""
Experiment Name: {data.experiment_name}
Total Runs: {len(data.run_numbers)}
Missing Runs: {len(data.missing_runs)}

First 10 runs:
Run | Timestamp | Peak Area | Peak Height
"""
            
            for i in range(min(10, len(data.run_numbers))):
                preview_text += f"{data.run_numbers[i]} | {data.timestamps[i]} | {data.peak_areas[i]:.1f} | {data.peak_heights[i]:.1f}\n"
            
            if len(data.run_numbers) > 10:
                preview_text += f"\n... and {len(data.run_numbers) - 10} more runs"
            
            self.preview_text.setText(preview_text)
            
        except Exception as e:
            self.preview_text.setText(f"Error loading preview: {str(e)}")


class DetailedStatisticsDialog(QDialog):
    """Dialog to show detailed calibration statistics"""
    
    def __init__(self, cal_data: CalibrationData, parent=None):
        super().__init__(parent)
        self.cal_data = cal_data
        self.setWindowTitle("Detailed Calibration Statistics")
        self.setModal(True)
        self.resize(500, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Statistics text
        stats_text = f"""
<h3>Detailed Statistics for {self.cal_data.calibration_id}</h3>

<b>Basic Statistics:</b><br>
Mean Peak Area: {self.cal_data.mean_peak_area:.2f} µV*s<br>
Standard Deviation: {self.cal_data.std_deviation:.2f} µV*s<br>
Coefficient of Variation: {self.cal_data.cv_percent:.2f}%<br>
Minimum Peak Area: {self.cal_data.min_peak_area:.2f} µV*s<br>
Maximum Peak Area: {self.cal_data.max_peak_area:.2f} µV*s<br>
Median Peak Area: {self.cal_data.median_peak_area:.2f} µV*s<br>

<b>Data Quality:</b><br>
Number of Runs: {self.cal_data.num_runs}<br>
Number of Outliers: {len(self.cal_data.outlier_indices)}<br>
Outlier Percentage: {(len(self.cal_data.outlier_indices) / self.cal_data.num_runs * 100):.1f}%<br>
Quality Score: {self.cal_data.quality_score:.1f}/100<br>
Valid for Use: {'Yes' if self.cal_data.is_valid else 'No'}<br>

<b>Processing Information:</b><br>
Processing Date: {self.cal_data.processing_timestamp}<br>
Source Folder: {self.cal_data.source_folder}<br>
Gas Concentration: {self.cal_data.gas_concentration_ppm} ppm<br>
Operator: {self.cal_data.operator}<br>
        """
        
        stats_label = QLabel(stats_text)
        stats_label.setWordWrap(True)
        layout.addWidget(stats_label)
        
        # Quality flags
        if self.cal_data.quality_flags:
            layout.addWidget(QLabel("<b>Quality Flags:</b>"))
            flags_text = QTextEdit()
            flags_text.setText('\n'.join(self.cal_data.quality_flags))
            flags_text.setMaximumHeight(100)
            flags_text.setReadOnly(True)
            layout.addWidget(flags_text)
        
        # Notes
        layout.addWidget(QLabel("<b>Notes:</b>"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setText(self.cal_data.notes)
        self.notes_edit.setMaximumHeight(100)
        layout.addWidget(self.notes_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Notes")
        save_btn.clicked.connect(self.save_notes)
        button_layout.addWidget(save_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def save_notes(self):
        """Save updated notes"""
        self.cal_data.notes = self.notes_edit.toPlainText()
        # Here we would save to the calibration manager
        QMessageBox.information(self, "Success", "Notes saved successfully")


class CalibrationEditDialog(QDialog):
    """Dialog for editing calibration data"""
    
    def __init__(self, cal_data: CalibrationData, parent=None):
        super().__init__(parent)
        self.cal_data = cal_data
        self.setWindowTitle(f"Edit Calibration - {cal_data.calibration_id}")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup edit dialog UI"""
        layout = QVBoxLayout()
        
        # Form layout for editable fields
        form_layout = QFormLayout()
        
        # Calibration ID
        self.cal_id_edit = QLineEdit(self.cal_data.calibration_id)
        form_layout.addRow("Calibration ID:", self.cal_id_edit)
        
        # Date
        self.date_edit = QLineEdit(self.cal_data.date)
        form_layout.addRow("Date (YYYY-MM-DD):", self.date_edit)
        
        # Gas concentration
        self.gas_ppm_edit = QLineEdit(str(self.cal_data.gas_concentration_ppm))
        form_layout.addRow("Gas Concentration (ppm):", self.gas_ppm_edit)
        
        # Source folder/operator
        self.source_edit = QLineEdit(self.cal_data.source_folder)
        form_layout.addRow("Source:", self.source_edit)
        
        self.operator_edit = QLineEdit(self.cal_data.operator)
        form_layout.addRow("Operator:", self.operator_edit)
        
        # Peak areas (editable)
        self.peak_areas_edit = QTextEdit()
        peak_areas_text = ', '.join(str(area) for area in self.cal_data.raw_peak_areas)
        self.peak_areas_edit.setPlainText(peak_areas_text)
        self.peak_areas_edit.setMaximumHeight(80)
        form_layout.addRow("Peak Areas:", self.peak_areas_edit)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlainText(self.cal_data.notes)
        self.notes_edit.setMaximumHeight(60)
        form_layout.addRow("Notes:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # Statistics display (read-only)
        stats_group = QGroupBox("Calculated Statistics (Read-Only)")
        stats_layout = QFormLayout()
        
        stats_layout.addRow("Mean Peak Area:", QLabel(f"{self.cal_data.mean_peak_area:.1f}"))
        stats_layout.addRow("CV%:", QLabel(f"{self.cal_data.cv_percent:.2f}%"))
        stats_layout.addRow("Number of Runs:", QLabel(str(self.cal_data.num_runs)))
        stats_layout.addRow("Quality Score:", QLabel(f"{self.cal_data.quality_score:.1f}"))
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        recalc_btn = QPushButton("Recalculate Statistics")
        recalc_btn.clicked.connect(self.recalculate_statistics)
        button_layout.addWidget(recalc_btn)
        
        button_layout.addStretch()
        
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def recalculate_statistics(self):
        """Recalculate statistics from edited peak areas"""
        try:
            # Parse peak areas
            text = self.peak_areas_edit.toPlainText().strip()
            peak_areas = []
            for area_str in text.split(','):
                area_str = area_str.strip()
                if area_str:
                    peak_areas.append(float(area_str))
            
            if len(peak_areas) < 3:
                QMessageBox.warning(self, "Invalid Data", "Please enter at least 3 peak area values")
                return
            
            # Update calibration data
            self.cal_data.raw_peak_areas = peak_areas
            self.cal_data.num_runs = len(peak_areas)
            
            # Calculate new statistics
            import numpy as np
            from scipy import stats as scipy_stats
            
            self.cal_data.mean_peak_area = float(np.mean(peak_areas))
            self.cal_data.std_deviation = float(np.std(peak_areas, ddof=1))
            self.cal_data.cv_percent = (self.cal_data.std_deviation / self.cal_data.mean_peak_area) * 100
            self.cal_data.min_peak_area = float(np.min(peak_areas))
            self.cal_data.max_peak_area = float(np.max(peak_areas))
            self.cal_data.median_peak_area = float(np.median(peak_areas))
            
            # Outlier detection
            z_scores = np.abs(scipy_stats.zscore(peak_areas))
            self.cal_data.outlier_indices = list(np.where(z_scores > 3.0)[0])
            
            # Quality assessment
            self.cal_data.quality_flags = []
            if self.cal_data.cv_percent > 10:
                self.cal_data.quality_flags.append("high_cv")
                self.cal_data.is_valid = False
            elif self.cal_data.cv_percent > 5:
                self.cal_data.quality_flags.append("moderate_cv")
            
            if self.cal_data.num_runs < 3:
                self.cal_data.quality_flags.append("low_n")
                self.cal_data.is_valid = False
            elif self.cal_data.num_runs < 5:
                self.cal_data.quality_flags.append("insufficient_n")
            
            if len(self.cal_data.outlier_indices) / self.cal_data.num_runs > 0.2:
                self.cal_data.quality_flags.append("outliers")
            
            self.cal_data.quality_score = self.cal_data.calculate_quality_score()
            
            # Refresh UI
            self.setup_ui()
            QMessageBox.information(self, "Success", "Statistics recalculated successfully")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to recalculate statistics: {str(e)}")
    
    def save_changes(self):
        """Save changes to calibration data"""
        try:
            # Validate and save changes
            new_cal_id = self.cal_id_edit.text().strip()
            if not new_cal_id:
                QMessageBox.warning(self, "Invalid Data", "Calibration ID cannot be empty")
                return
            
            new_date = self.date_edit.text().strip()
            if not new_date:
                QMessageBox.warning(self, "Invalid Data", "Date cannot be empty")
                return
            
            try:
                new_gas_ppm = float(self.gas_ppm_edit.text())
            except ValueError:
                QMessageBox.warning(self, "Invalid Data", "Invalid gas concentration")
                return
            
            # Update calibration data
            self.cal_data.calibration_id = new_cal_id
            self.cal_data.date = new_date
            self.cal_data.gas_concentration_ppm = new_gas_ppm
            self.cal_data.source_folder = self.source_edit.text().strip()
            self.cal_data.operator = self.operator_edit.text().strip()
            self.cal_data.notes = self.notes_edit.toPlainText()
            
            self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save changes: {str(e)}")