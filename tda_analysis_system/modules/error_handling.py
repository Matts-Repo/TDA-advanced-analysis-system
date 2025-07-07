"""
Error Handling Framework for TDA Analysis System

This module provides consistent error handling patterns across all modules.
"""

try:
    from PyQt5.QtWidgets import QMessageBox
    HAS_QT = True
except ImportError:
    HAS_QT = False


class TDAError(Exception):
    """Base exception for TDA system"""
    pass


class TDAFileError(TDAError):
    """File reading/parsing errors"""
    pass


class TDAValidationError(TDAError):
    """Data validation errors"""
    pass


class TDACalculationError(TDAError):
    """Calculation/processing errors"""
    pass


def handle_error_with_user_feedback(parent_widget, operation_name, error):
    """Standardized error handling with user feedback"""
    if not HAS_QT:
        # Fallback for non-GUI environments
        print(f"ERROR in {operation_name}: {str(error)}")
        return
    
    if isinstance(error, TDAFileError):
        QMessageBox.critical(parent_widget, "File Error", 
                           f"{operation_name} failed: {str(error)}\n\nPlease check the file format and try again.")
    elif isinstance(error, TDAValidationError):
        QMessageBox.warning(parent_widget, "Data Validation", 
                          f"{operation_name} completed with warnings: {str(error)}")
    elif isinstance(error, TDACalculationError):
        QMessageBox.critical(parent_widget, "Calculation Error", 
                           f"{operation_name} failed: {str(error)}\n\nPlease check your parameters and try again.")
    else:
        QMessageBox.critical(parent_widget, "Unexpected Error", 
                           f"{operation_name} failed with unexpected error: {str(error)}")