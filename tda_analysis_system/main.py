#!/usr/bin/env python3
"""
TDA (Thermal Desorption Analysis) System - Main Application Entry Point

This is the main entry point for the TDA Analysis System, providing a comprehensive
PyQt5-based application for processing gas chromatograph data from raw files through
calibration management to publication-ready plots.

The application integrates three main modules:
1. Calibration Management - Process hydrogen calibration standard data
2. Data Processing - Convert raw experimental TDA data to hydrogen concentrations  
3. Data Visualization - Generate publication-ready plots with extensive customization

Usage:
    python main.py

Author: TDA Analysis System
"""

import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.calibration_manager import CalibrationManager
from modules.data_processor import DataProcessor
from modules.plot_manager import PlotManager
from modules.error_handling import handle_error_with_user_feedback

from ui.calibration_widget import CalibrationWidget
from ui.processing_widget import ProcessingWidget
from ui.plotting_widget import PlottingWidget


class TDAMainWindow(QMainWindow):
    """Main application window with tabbed interface for TDA analysis"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TDA Analysis System v1.0")
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        # Initialize core managers
        self.calibration_manager = None
        self.data_processor = None
        self.plot_manager = None
        
        # Initialize UI components
        self.central_widget = None
        self.tab_widget = None
        self.status_bar = None
        
        # Initialize application
        self.init_status_bar()  # Initialize status bar first
        self.init_managers()
        self.init_ui()
        self.init_menu_bar()
        
        # Show welcome message
        self.show_welcome_message()
    
    def init_managers(self):
        """Initialize core data management components"""
        try:
            # Create data directories if they don't exist
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_dir, "data")
            
            calibration_dir = os.path.join(data_dir, "calibrations")
            processed_dir = os.path.join(data_dir, "processed_experiments")
            config_dir = os.path.join(data_dir, "config")
            
            for directory in [calibration_dir, processed_dir, config_dir]:
                os.makedirs(directory, exist_ok=True)
            
            # Initialize managers
            self.calibration_manager = CalibrationManager(calibration_folder=calibration_dir)
            self.data_processor = DataProcessor(
                calibration_manager=self.calibration_manager,
                output_folder=processed_dir
            )
            self.plot_manager = PlotManager(processed_data_folder=processed_dir)
            
            if self.status_bar:
                self.status_bar.showMessage("Core managers initialized successfully", 3000)
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Initialization Error", 
                f"Failed to initialize core managers:\n{str(e)}\n\nThe application may not function properly."
            )
    
    def init_ui(self):
        """Initialize the main user interface with tabbed layout"""
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setMovable(False)
        self.tab_widget.setTabsClosable(False)
        
        # Create and add tabs
        self.create_tabs()
        
        layout.addWidget(self.tab_widget)
        
        # Set window properties
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        self.center_window()
    
    def create_tabs(self):
        """Create the three main application tabs"""
        try:
            # Tab 1: Calibration Management
            self.calibration_widget = CalibrationWidget(self.calibration_manager)
            self.tab_widget.addTab(self.calibration_widget, "📊 Calibration Management")
            
            # Tab 2: Data Processing
            self.processing_widget = ProcessingWidget(self.calibration_manager, self.data_processor)
            self.tab_widget.addTab(self.processing_widget, "⚗️ Data Processing")
            
            # Tab 3: Data Visualization
            self.plotting_widget = PlottingWidget(self.plot_manager)
            self.tab_widget.addTab(self.plotting_widget, "📈 Data Visualization")
            
            # Connect tab change signal for status updates
            self.tab_widget.currentChanged.connect(self.on_tab_changed)
            
        except Exception as e:
            handle_error_with_user_feedback(self, "UI Initialization", e)
    
    def init_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu('&File')
        
        # Import/Export actions
        import_action = QAction('&Import Calibration...', self)
        import_action.setShortcut('Ctrl+I')
        import_action.setStatusTip('Import calibration from file')
        import_action.triggered.connect(self.import_calibration)
        file_menu.addAction(import_action)
        
        export_action = QAction('&Export Data...', self)
        export_action.setShortcut('Ctrl+E')
        export_action.setStatusTip('Export processed data')
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Settings action
        settings_action = QAction('&Settings...', self)
        settings_action.setStatusTip('Application settings')
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools Menu
        tools_menu = menubar.addMenu('&Tools')
        
        refresh_action = QAction('&Refresh Data', self)
        refresh_action.setShortcut('F5')
        refresh_action.setStatusTip('Refresh all data views')
        refresh_action.triggered.connect(self.refresh_all_data)
        tools_menu.addAction(refresh_action)
        
        validate_action = QAction('&Validate System', self)
        validate_action.setStatusTip('Run system validation checks')
        validate_action.triggered.connect(self.validate_system)
        tools_menu.addAction(validate_action)
        
        # Help Menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About TDA System...', self)
        about_action.setStatusTip('About this application')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        help_action = QAction('&User Guide', self)
        help_action.setShortcut('F1')
        help_action.setStatusTip('Open user documentation')
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
    
    def init_status_bar(self):
        """Initialize status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("TDA Analysis System Ready", 2000)
        
        # Add permanent widgets to status bar
        self.calibration_status = QLabel("Calibrations: 0")
        self.status_bar.addPermanentWidget(self.calibration_status)
        
        self.data_status = QLabel("Processed: 0")
        self.status_bar.addPermanentWidget(self.data_status)
        
        # Update status on startup
        self.update_status_counts()
    
    def center_window(self):
        """Center the window on screen"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def show_welcome_message(self):
        """Show welcome message on startup"""
        self.status_bar.showMessage(
            "Welcome to TDA Analysis System - Use tabs to navigate between Calibration, Processing, and Visualization", 
            5000
        )
    
    def on_tab_changed(self, index):
        """Handle tab change events"""
        tab_names = ["Calibration Management", "Data Processing", "Data Visualization"]
        if 0 <= index < len(tab_names):
            self.status_bar.showMessage(f"Switched to {tab_names[index]}", 2000)
            
            # Update data when switching to certain tabs
            if index == 1:  # Processing tab
                try:
                    self.processing_widget.refresh_calibration_list()
                except:
                    pass
            elif index == 2:  # Visualization tab
                try:
                    self.plotting_widget.scan_datasets()
                except:
                    pass
    
    def update_status_counts(self):
        """Update status bar with current data counts"""
        try:
            # Count calibrations
            cal_count = len(self.calibration_manager.calibrations) if self.calibration_manager else 0
            self.calibration_status.setText(f"Calibrations: {cal_count}")
            
            # Count processed files
            processed_count = 0
            if self.plot_manager:
                datasets = self.plot_manager.scan_for_datasets()
                processed_count = len(datasets)
            self.data_status.setText(f"Processed: {processed_count}")
            
        except Exception as e:
            pass  # Silently handle status update errors
    
    # Menu action handlers
    def import_calibration(self):
        """Import calibration from file"""
        QMessageBox.information(
            self, 
            "Import Calibration", 
            "Import calibration functionality would be implemented here.\n\n"
            "For now, use the Calibration Management tab to process new calibrations."
        )
    
    def export_data(self):
        """Export processed data"""
        current_tab = self.tab_widget.currentIndex()
        if current_tab == 2:  # Visualization tab
            QMessageBox.information(
                self,
                "Export Data",
                "Use the Export controls in the Data Visualization tab to export plots.\n\n"
                "Use the Data Processing tab to export enhanced CSV files."
            )
        else:
            QMessageBox.information(
                self,
                "Export Data", 
                "Switch to the Data Processing or Visualization tabs to export data."
            )
    
    def show_settings(self):
        """Show application settings dialog"""
        QMessageBox.information(
            self,
            "Settings",
            "Application settings functionality would be implemented here.\n\n"
            "Future versions will include:\n"
            "• Default calibration selection\n"
            "• Plot styling preferences\n"
            "• Data validation thresholds\n"
            "• Export format defaults"
        )
    
    def refresh_all_data(self):
        """Refresh all data views"""
        try:
            # Refresh calibration list
            if hasattr(self, 'calibration_widget'):
                self.calibration_widget.refresh_calibration_list()
            
            # Refresh processing calibrations
            if hasattr(self, 'processing_widget'):
                self.processing_widget.refresh_calibration_list()
            
            # Refresh visualization datasets
            if hasattr(self, 'plotting_widget'):
                self.plotting_widget.scan_datasets()
            
            # Update status counts
            self.update_status_counts()
            
            self.status_bar.showMessage("All data refreshed", 2000)
            
        except Exception as e:
            handle_error_with_user_feedback(self, "Data Refresh", e)
    
    def validate_system(self):
        """Run system validation checks"""
        validation_results = []
        
        try:
            # Check data directories
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_dir, "data")
            
            required_dirs = [
                os.path.join(data_dir, "calibrations"),
                os.path.join(data_dir, "processed_experiments"),
                os.path.join(data_dir, "config")
            ]
            
            for directory in required_dirs:
                if os.path.exists(directory):
                    validation_results.append(f"✅ Directory exists: {os.path.basename(directory)}")
                else:
                    validation_results.append(f"❌ Directory missing: {os.path.basename(directory)}")
            
            # Check managers
            if self.calibration_manager:
                validation_results.append("✅ Calibration Manager initialized")
                cal_count = len(self.calibration_manager.calibrations)
                validation_results.append(f"📊 {cal_count} calibrations loaded")
            else:
                validation_results.append("❌ Calibration Manager not initialized")
            
            if self.data_processor:
                validation_results.append("✅ Data Processor initialized")
            else:
                validation_results.append("❌ Data Processor not initialized")
            
            if self.plot_manager:
                validation_results.append("✅ Plot Manager initialized")
                try:
                    datasets = self.plot_manager.scan_for_datasets()
                    validation_results.append(f"📈 {len(datasets)} processed datasets found")
                except:
                    validation_results.append("⚠️ Could not scan for datasets")
            else:
                validation_results.append("❌ Plot Manager not initialized")
            
            # Show results
            result_text = "System Validation Results:\n\n" + "\n".join(validation_results)
            QMessageBox.information(self, "System Validation", result_text)
            
        except Exception as e:
            handle_error_with_user_feedback(self, "System Validation", e)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h3>TDA Analysis System v1.0</h3>
        
        <p><b>Thermal Desorption Analysis System</b></p>
        
        <p>A comprehensive PyQt5-based application for processing gas chromatograph data 
        from raw files through calibration management to publication-ready plots.</p>
        
        <p><b>Features:</b></p>
        <ul>
        <li>📊 Calibration Management - Process hydrogen calibration standard data</li>
        <li>⚗️ Data Processing - Convert raw experimental TDA data to hydrogen concentrations</li>
        <li>📈 Data Visualization - Generate publication-ready plots with extensive customization</li>
        </ul>
        
        <p><b>Technology Stack:</b></p>
        <ul>
        <li>GUI Framework: PyQt5</li>
        <li>Data Processing: pandas, numpy, scipy</li>
        <li>Plotting: matplotlib</li>
        <li>File I/O: openpyxl, standard Python libraries</li>
        </ul>
        
        <p><i>Generated with Claude Code assistance</i></p>
        """
        
        QMessageBox.about(self, "About TDA Analysis System", about_text)
    
    def show_help(self):
        """Show help documentation"""
        help_text = """
        TDA Analysis System User Guide

        GETTING STARTED:
        1. Start with the Calibration Management tab to process calibration standards
        2. Move to Data Processing to analyze experimental data
        3. Use Data Visualization to create publication-ready plots

        CALIBRATION MANAGEMENT:
        • Select a folder containing TDA calibration files
        • Set the gas concentration (default: 61.0 ppm)
        • Click "Process Calibration" to analyze
        • View results in the database table

        DATA PROCESSING:
        • Load experimental TDA data folder
        • Set processing parameters (sample weight, flow rate, cycle time)
        • Select appropriate calibration
        • Process data and export enhanced CSV

        DATA VISUALIZATION:
        • Scan for processed CSV files
        • Select datasets to plot
        • Customize plot appearance and filtering
        • Export publication-ready figures

        KEYBOARD SHORTCUTS:
        • Ctrl+I - Import calibration
        • Ctrl+E - Export data
        • Ctrl+Q - Exit application
        • F5 - Refresh all data
        • F1 - Show this help

        For technical support, check the implementation documentation.
        """
        
        dialog = QDialog(self)
        dialog.setWindowTitle("TDA System User Guide")
        dialog.setModal(True)
        dialog.resize(600, 500)
        
        layout = QVBoxLayout()
        
        text_edit = QTextEdit()
        text_edit.setPlainText(help_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def closeEvent(self, event):
        """Handle application close event"""
        reply = QMessageBox.question(
            self,
            'Exit Application',
            'Are you sure you want to exit the TDA Analysis System?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.status_bar.showMessage("Shutting down TDA Analysis System...")
            event.accept()
        else:
            event.ignore()


def main():
    """Main application entry point"""
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("TDA Analysis System")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("TDA Analysis")
    
    # Set application style
    app.setStyle('Fusion')  # Modern, cross-platform appearance
    
    # Create and show main window
    try:
        window = TDAMainWindow()
        window.show()
        
        # Run application event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        QMessageBox.critical(
            None,
            "Fatal Error",
            f"Failed to start TDA Analysis System:\n\n{str(e)}\n\n"
            "Please check the installation and try again."
        )
        sys.exit(1)


if __name__ == '__main__':
    main()