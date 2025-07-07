"""
Calibration Management Module for TDA Analysis System

This module handles processing of hydrogen calibration standard data from raw TDA files,
calculates comprehensive statistics, and manages a calibration database.
"""

import os
import json
import csv
import shutil
from datetime import datetime
from typing import List, Dict, Optional
import numpy as np
from scipy import stats as scipy_stats

from .data_extraction import TDAFileExtractor
from .shared_data_structures import CalibrationData, TDADataSet
from .error_handling import TDAFileError, TDAValidationError


class CalibrationManager:
    """Manages calibration data processing and database operations"""
    
    def __init__(self, calibration_folder="./data/calibrations/"):
        self.calibration_folder = calibration_folder
        self.database_file = os.path.join(calibration_folder, "calibration_database.json")
        
        # Ensure folders exist
        os.makedirs(calibration_folder, exist_ok=True)
        
        # Load existing calibrations
        self.calibrations = self.load_database()
    
    def load_database(self) -> Dict[str, CalibrationData]:
        """Load calibrations from JSON database file"""
        if not os.path.exists(self.database_file):
            return {}
            
        try:
            with open(self.database_file, 'r') as f:
                data = json.load(f)
                calibrations = {}
                for cal_id, cal_dict in data.get('calibrations', {}).items():
                    calibrations[cal_id] = CalibrationData.from_dict(cal_dict)
                return calibrations
        except Exception as e:
            print(f"Warning: Could not load calibration database: {e}")
            return {}
    
    def save_database(self):
        """Save current calibrations to JSON database file"""
        database_data = {
            "database_version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "calibrations": {
                cal_id: cal_data.to_dict() 
                for cal_id, cal_data in self.calibrations.items()
            }
        }
        
        with open(self.database_file, 'w') as f:
            json.dump(database_data, f, indent=2)
    
    def process_calibration_folder(self, folder_path: str, gas_ppm: float = 61.0, 
                                 cal_name: Optional[str] = None) -> CalibrationData:
        """
        Process TDA calibration files and add to database
        
        Args:
            folder_path: Path to folder containing calibration TDA files
            gas_ppm: Hydrogen gas concentration in ppm (default 61.0)
            cal_name: Optional custom calibration name
            
        Returns:
            CalibrationData object with processing results
        """
        # Extract raw data using shared extraction utility
        raw_data = TDAFileExtractor.extract_from_folder(folder_path)
        
        # Generate calibration ID
        if cal_name:
            cal_id = cal_name
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            existing_count = len([cal for cal in self.calibrations.keys() 
                                if cal.startswith(f"cal_{date_str}")])
            cal_id = f"cal_{date_str}_{existing_count + 1:03d}"
        
        # Calculate statistics
        stats = self.calculate_calibration_stats(raw_data.peak_areas)
        
        # Create calibration data object
        cal_data = CalibrationData(
            calibration_id=cal_id,
            date=datetime.now().strftime("%Y-%m-%d"),
            processing_timestamp=datetime.now().isoformat(),
            gas_concentration_ppm=gas_ppm,
            mean_peak_area=stats['mean'],
            std_deviation=stats['std_dev'],
            cv_percent=stats['cv_percent'],
            num_runs=stats['n_points'],
            min_peak_area=stats['min_value'],
            max_peak_area=stats['max_value'],
            median_peak_area=stats['median'],
            raw_peak_areas=raw_data.peak_areas,
            raw_timestamps=raw_data.timestamps,
            outlier_indices=stats['outlier_indices'],
            source_folder=folder_path
        )
        
        # Validate quality and set flags
        cal_data.quality_flags = self.validate_calibration_quality(cal_data)
        cal_data.quality_score = cal_data.calculate_quality_score()
        cal_data.is_valid = len([flag for flag in cal_data.quality_flags if flag.startswith("ERROR")]) == 0
        
        # Save individual calibration folder
        self._save_individual_calibration(cal_data, raw_data)
        
        # Add to database
        self.calibrations[cal_id] = cal_data
        self.save_database()
        
        return cal_data
    
    def calculate_calibration_stats(self, peak_areas: List[float]) -> Dict:
        """
        Calculate comprehensive statistics for calibration data
        
        Returns:
            Dictionary with mean, std_dev, cv_percent, min_value, max_value,
            median, n_points, outlier_indices, quality_score
        """
        if not peak_areas:
            raise TDAValidationError("No peak areas provided for statistics calculation")
        
        areas = np.array(peak_areas)
        
        # Basic statistics
        mean_area = np.mean(areas)
        std_dev = np.std(areas, ddof=1)  # Sample standard deviation
        cv_percent = (std_dev / mean_area) * 100 if mean_area > 0 else 100
        
        # Outlier detection using Z-score method
        z_scores = np.abs(scipy_stats.zscore(areas))
        outlier_indices = np.where(z_scores > 3.0)[0].tolist()
        
        return {
            'mean': float(mean_area),
            'std_dev': float(std_dev),
            'cv_percent': float(cv_percent),
            'min_value': float(np.min(areas)),
            'max_value': float(np.max(areas)),
            'median': float(np.median(areas)),
            'n_points': len(areas),
            'outlier_indices': outlier_indices,
            'outliers': [float(areas[i]) for i in outlier_indices]
        }
    
    def validate_calibration_quality(self, cal_data: CalibrationData) -> List[str]:
        """
        Check calibration quality and return warnings/errors
        
        Quality checks:
        - CV% > 10%: Error (unacceptable calibration)
        - CV% > 5%: Warning (unstable calibration) 
        - N < 3 runs: Error (inadequate calibration)
        - N < 5 runs: Warning (insufficient data)
        - >20% outliers: Warning
        - Mean outside reasonable range: Warning
        """
        warnings = []
        
        # CV% checks
        if cal_data.cv_percent > 10:
            warnings.append("ERROR: CV% > 10% - Calibration too unstable for reliable use")
        elif cal_data.cv_percent > 5:
            warnings.append("WARNING: CV% > 5% - Check calibration stability")
            
        # Run count checks
        if cal_data.num_runs < 3:
            warnings.append("ERROR: < 3 runs - Inadequate calibration data")
        elif cal_data.num_runs < 5:
            warnings.append("WARNING: < 5 runs - Limited calibration data")
            
        # Outlier checks
        outlier_percent = (len(cal_data.outlier_indices) / cal_data.num_runs) * 100
        if outlier_percent > 20:
            warnings.append(f"WARNING: {outlier_percent:.1f}% outliers detected")
            
        # Range checks (typical peak areas 1000-100000)
        if cal_data.mean_peak_area < 1000:
            warnings.append("WARNING: Very low peak areas - check instrument sensitivity")
        elif cal_data.mean_peak_area > 100000:
            warnings.append("WARNING: Very high peak areas - check for overload")
            
        return warnings
    
    def _save_individual_calibration(self, cal_data: CalibrationData, raw_data: TDADataSet):
        """Save individual calibration data to dedicated folder"""
        cal_folder = os.path.join(self.calibration_folder, cal_data.calibration_id)
        os.makedirs(cal_folder, exist_ok=True)
        
        # Save detailed calibration report
        report_path = os.path.join(cal_folder, "calibration_report.json")
        with open(report_path, 'w') as f:
            json.dump(cal_data.to_dict(), f, indent=2)
        
        # Save processed data as CSV
        csv_path = os.path.join(cal_folder, "processed_data.csv")
        self._save_calibration_csv(cal_data, raw_data, csv_path)
    
    def _save_calibration_csv(self, cal_data: CalibrationData, raw_data: TDADataSet, csv_path: str):
        """Save calibration data as CSV with metadata"""
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header with metadata
            writer.writerow(['# Calibration Data Export'])
            writer.writerow([f'# Calibration ID: {cal_data.calibration_id}'])
            writer.writerow([f'# Date: {cal_data.date}'])
            writer.writerow([f'# Gas Concentration: {cal_data.gas_concentration_ppm} ppm'])
            writer.writerow([f'# Mean Peak Area: {cal_data.mean_peak_area:.1f} µV*s'])
            writer.writerow([f'# Standard Deviation: {cal_data.std_deviation:.1f} µV*s'])
            writer.writerow([f'# CV%: {cal_data.cv_percent:.2f}%'])
            writer.writerow([f'# Quality Score: {cal_data.quality_score:.1f}/100'])
            writer.writerow(['#'])
            
            # Column headers
            writer.writerow(['Run', 'Timestamp', 'Peak_Area_µVs', 'Peak_Height_µV', 'Outlier_Flag'])
            
            # Data rows
            for i in range(len(raw_data.run_numbers)):
                outlier_flag = "outlier" if i in cal_data.outlier_indices else ""
                writer.writerow([
                    raw_data.run_numbers[i],
                    raw_data.timestamps[i],
                    f"{raw_data.peak_areas[i]:.5f}",
                    f"{raw_data.peak_heights[i]:.5f}",
                    outlier_flag
                ])
    
    def get_calibrations_by_date_range(self, start_date: str, end_date: str) -> List[CalibrationData]:
        """Retrieve calibrations within date range (YYYY-MM-DD format)"""
        calibrations = []
        for cal_data in self.calibrations.values():
            if start_date <= cal_data.date <= end_date:
                calibrations.append(cal_data)
        return sorted(calibrations, key=lambda x: x.date)
    
    def suggest_calibration_for_date(self, target_date: str) -> Optional[str]:
        """
        Find closest valid calibration by date
        
        Args:
            target_date: Target date in YYYY-MM-DD format
            
        Returns:
            Calibration ID of best match, or None if no valid calibrations
        """
        valid_calibrations = [cal for cal in self.calibrations.values() if cal.is_valid]
        
        if not valid_calibrations:
            return None
        
        # Find closest by date
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        
        closest_cal = min(valid_calibrations, 
                         key=lambda cal: abs((datetime.strptime(cal.date, "%Y-%m-%d") - target_dt).days))
        
        return closest_cal.calibration_id
    
    def get_calibration(self, calibration_id: str) -> Optional[CalibrationData]:
        """Get specific calibration by ID"""
        return self.calibrations.get(calibration_id)
    
    def get_recent_calibrations(self, limit: int = 10) -> List[CalibrationData]:
        """Get most recent calibrations, sorted by date"""
        all_cals = list(self.calibrations.values())
        all_cals.sort(key=lambda x: x.date, reverse=True)
        return all_cals[:limit]
    
    def delete_calibration(self, calibration_id: str) -> bool:
        """Delete calibration from database and file system"""
        if calibration_id not in self.calibrations:
            return False
        
        # Remove from database
        del self.calibrations[calibration_id]
        self.save_database()
        
        # Remove individual calibration folder
        cal_folder = os.path.join(self.calibration_folder, calibration_id)
        if os.path.exists(cal_folder):
            shutil.rmtree(cal_folder)
        
        return True