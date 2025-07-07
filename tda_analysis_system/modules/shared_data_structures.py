"""
Shared Data Structures for TDA Analysis System

This module contains the core data structures used across all modules:
- TDADataSet: Standard structure for all TDA data
- CalibrationData: Complete calibration data structure
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class TDADataSet:
    """Standard structure for all TDA data across the system"""
    # Identification
    experiment_name: str = ""
    source_file: str = ""
    extraction_timestamp: str = ""
    
    # Raw data arrays (parallel lists - same length)
    run_numbers: List[int] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)      # Format: "MM/DD/YYYY HH:MM:SS"
    peak_areas: List[float] = field(default_factory=list)    # Units: µV*s
    peak_heights: List[float] = field(default_factory=list)  # Units: µV
    
    # Metadata from file parsing
    metadata: Dict = field(default_factory=dict)
    missing_runs: List[int] = field(default_factory=list)    # Run numbers that failed
    
    def validate_data_consistency(self) -> List[str]:
        """Validate that all data arrays have consistent lengths"""
        errors = []
        expected_length = len(self.run_numbers)
        
        if len(self.timestamps) != expected_length:
            errors.append("Timestamp count mismatch")
        if len(self.peak_areas) != expected_length:
            errors.append("Peak area count mismatch") 
        if len(self.peak_heights) != expected_length:
            errors.append("Peak height count mismatch")
            
        return errors


@dataclass
class CalibrationData:
    """Complete calibration data structure used across all modules"""
    # Identification
    calibration_id: str = ""                    # Format: "cal_YYYY-MM-DD_XXX"
    date: str = ""                              # Format: "YYYY-MM-DD"
    processing_timestamp: str = ""              # ISO format when processed
    
    # Gas parameters
    gas_concentration_ppm: float = 61.0         # Standard gas concentration
    
    # Statistical results
    mean_peak_area: float = 0.0
    std_deviation: float = 0.0
    cv_percent: float = 0.0                     # Coefficient of variation
    num_runs: int = 0
    min_peak_area: float = 0.0
    max_peak_area: float = 0.0
    median_peak_area: float = 0.0
    
    # Raw calibration data
    raw_peak_areas: List[float] = field(default_factory=list)
    raw_timestamps: List[str] = field(default_factory=list)
    outlier_indices: List[int] = field(default_factory=list)
    
    # Quality assessment
    quality_flags: List[str] = field(default_factory=list)  # ["high_cv", "low_n", "outliers"]
    quality_score: float = 0.0                              # 0-100 overall quality rating
    is_valid: bool = True
    
    # Metadata
    source_folder: str = ""
    operator: str = "SYSTEM"
    notes: str = ""
    
    def calculate_quality_score(self) -> float:
        """Calculate overall quality score based on CV% and run count"""
        score = 100.0
        
        # Penalize high CV%
        if self.cv_percent > 10:
            score -= 50
        elif self.cv_percent > 5:
            score -= 20
        elif self.cv_percent > 2:
            score -= 10
            
        # Penalize low run count
        if self.num_runs < 5:
            score -= 30
        elif self.num_runs < 8:
            score -= 15
            
        return max(0.0, score)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage"""
        return {
            'calibration_id': self.calibration_id,
            'date': self.date,
            'processing_timestamp': self.processing_timestamp,
            'gas_concentration_ppm': self.gas_concentration_ppm,
            'mean_peak_area': self.mean_peak_area,
            'std_deviation': self.std_deviation,
            'cv_percent': self.cv_percent,
            'num_runs': self.num_runs,
            'min_peak_area': self.min_peak_area,
            'max_peak_area': self.max_peak_area,
            'median_peak_area': self.median_peak_area,
            'raw_peak_areas': self.raw_peak_areas,
            'raw_timestamps': self.raw_timestamps,
            'outlier_indices': self.outlier_indices,
            'quality_flags': self.quality_flags,
            'quality_score': self.quality_score,
            'is_valid': self.is_valid,
            'source_folder': self.source_folder,
            'operator': self.operator,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CalibrationData':
        """Create from dictionary (JSON loading)"""
        return cls(**data)