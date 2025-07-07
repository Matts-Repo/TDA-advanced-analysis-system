"""
Data Extraction Module for TDA Analysis System

This module provides unified TDA file parsing for both calibration and experimental data.
Handles multiple file formats and returns standardized TDADataSet objects.
"""

import os
import re
from datetime import datetime
from typing import List, Optional
import pandas as pd
from .shared_data_structures import TDADataSet
from .error_handling import TDAFileError, TDAValidationError


class TDAFileExtractor:
    """Unified extractor for all TDA file formats"""
    
    @staticmethod
    def extract_from_folder(folder_path: str) -> TDADataSet:
        """
        Main entry point - auto-detect file type and extract data
        
        Detection Priority:
        1. Look for .txt summary files (GLPrpt format) - PREFERRED
        2. Look for multiple .xls files (individual reports)
        3. Look for .pdf files as fallback
        
        Returns: TDADataSet with all extracted data
        """
        if not os.path.exists(folder_path):
            raise TDAFileError(f"Folder does not exist: {folder_path}")
        
        files = os.listdir(folder_path)
        
        # Priority 1: Look for .xls files in .D subdirectories (preferred for peak data)
        d_folders = [f for f in files if os.path.isdir(os.path.join(folder_path, f)) and f.endswith('.D')]
        if d_folders:
            # Check if any .D folders contain Report01.xls
            for d_folder in d_folders:
                xls_path = os.path.join(folder_path, d_folder, 'Report01.xls')
                if os.path.exists(xls_path):
                    return TDAFileExtractor.extract_from_xls_reports(folder_path)
        
        # Priority 2: Look for multiple .xls files in root folder
        xls_files = [f for f in files if f.lower().endswith(('.xls', '.xlsx'))]
        if len(xls_files) > 1:
            return TDAFileExtractor.extract_from_xls_reports(folder_path)
        
        # Priority 3: Look for .txt summary files (for metadata, not peak data)
        txt_files = [f for f in files if f.lower().endswith('.txt')]
        if txt_files:
            # Use the first .txt file found
            txt_path = os.path.join(folder_path, txt_files[0])
            return TDAFileExtractor.extract_from_txt_summary(txt_path)
        
        # Priority 3: Look for .pdf files (placeholder implementation)
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        if pdf_files:
            raise TDAFileError("PDF file parsing not yet implemented. Please use .txt or .xls files.")
        
        raise TDAFileError(f"No supported file formats found in {folder_path}")
    
    @staticmethod
    def extract_from_txt_summary(file_path: str) -> TDADataSet:
        """
        Extract from GLPrpt .txt summary file
        
        Expected format:
        - File contains run table with timestamps
        - Contains "Compound: hydrogen" section  
        - Contains peak area table with run numbers and values
        - May contain missing runs (gaps in run numbers)
        """
        # Try different encodings to handle various file formats
        content = None
        for encoding in ['utf-16', 'utf-8', 'latin-1']:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
                    content = file.read()
                    if content and len(content.strip()) > 0:
                        break
            except Exception:
                continue
        
        if content is None:
            raise TDAFileError(f"Could not read file with any supported encoding: {file_path}")
        
        try:
            
            dataset = TDADataSet()
            dataset.source_file = file_path
            dataset.extraction_timestamp = datetime.now().isoformat()
            dataset.experiment_name = TDAFileExtractor.extract_experiment_name(os.path.dirname(file_path))
            
            # Extract run table with timestamps
            run_timestamps = TDAFileExtractor._parse_run_timestamps(content)
            
            # Extract peak areas for hydrogen
            peak_data = TDAFileExtractor._parse_peak_areas(content)
            
            # Merge data and handle missing runs
            TDAFileExtractor._merge_run_data(dataset, run_timestamps, peak_data)
            
            # Validate extracted data
            errors = TDAFileExtractor.validate_extracted_data(dataset)
            if errors:
                raise TDAValidationError(f"Data validation failed: {'; '.join(errors)}")
            
            return dataset
            
        except Exception as e:
            if isinstance(e, (TDAFileError, TDAValidationError)):
                raise
            else:
                raise TDAFileError(f"Failed to parse .txt file {file_path}: {str(e)}")
    
    @staticmethod
    def extract_from_xls_reports(folder_path: str) -> TDADataSet:
        """
        Extract from multiple .xls individual report files
        
        Expected format:
        - Multiple .xls files in folder (Report01.xls, Report02.xls, etc.)
        - Each file contains single run data
        - Peak area in "Peak" sheet or "IntResults1" sheet
        - Extract run number from filename or file content
        """
        try:
            # Find all .D directories with Report01.xls files
            xls_files = []
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isdir(item_path) and item.endswith('.D'):
                    xls_path = os.path.join(item_path, 'Report01.xls')
                    if os.path.exists(xls_path):
                        xls_files.append((xls_path, item))  # (file_path, folder_name)
            
            # Also check for direct .xls files in root folder (fallback)
            for f in os.listdir(folder_path):
                if f.lower().endswith(('.xls', '.xlsx')):
                    file_path = os.path.join(folder_path, f)
                    if os.path.isfile(file_path):
                        xls_files.append((file_path, f))
            
            if not xls_files:
                raise TDAFileError("No .xls files found in .D folders or root directory")
            
            dataset = TDADataSet()
            dataset.source_file = folder_path
            dataset.extraction_timestamp = datetime.now().isoformat()
            dataset.experiment_name = TDAFileExtractor.extract_experiment_name(folder_path)
            
            run_data = []
            
            for file_path, folder_name in xls_files:
                try:
                    # Extract run number from folder name or filename
                    run_number = None
                    
                    # Try to extract from .D folder name (e.g., "--002F.D" → run 2)
                    if folder_name.endswith('.D'):
                        run_match = re.search(r'--(\d+)', folder_name)
                        if run_match:
                            run_number = int(run_match.group(1))
                    
                    # Fallback: extract from filename
                    if run_number is None:
                        run_match = re.search(r'(\d+)', folder_name)
                        if run_match:
                            run_number = int(run_match.group(1))
                    
                    if run_number is None:
                        print(f"Warning: Could not extract run number from {folder_name}")
                        continue
                    
                    # Try to read the Excel file - start with Peak sheet directly
                    try:
                        # Try "Peak" sheet first (preferred)
                        df = pd.read_excel(file_path, sheet_name='Peak', engine='xlrd')
                    except:
                        try:
                            # Try "IntResults1" sheet
                            df = pd.read_excel(file_path, sheet_name='IntResults1', engine='xlrd')
                        except:
                            # Use first sheet
                            df = pd.read_excel(file_path, engine='xlrd')
                    
                    # Find hydrogen peak area and height
                    peak_area, peak_height, timestamp = TDAFileExtractor._extract_from_excel_sheet(df, file_path)
                    
                    if peak_area is not None:
                        run_data.append({
                            'run': run_number,
                            'timestamp': timestamp or "",
                            'peak_area': peak_area,
                            'peak_height': peak_height or 0.0
                        })
                        print(f"✅ Extracted run {run_number}: peak_area={peak_area}")
                    else:
                        print(f"⚠️ No peak area found for run {run_number} in {folder_name}")
                    
                except Exception as e:
                    print(f"Warning: Could not process {folder_name}: {e}")
                    continue
            
            if not run_data:
                raise TDAFileError("No valid data extracted from .xls files")
            
            # Sort by run number
            run_data.sort(key=lambda x: x['run'])
            
            # Fill dataset
            for data in run_data:
                dataset.run_numbers.append(data['run'])
                dataset.timestamps.append(data['timestamp'])
                dataset.peak_areas.append(data['peak_area'])
                dataset.peak_heights.append(data['peak_height'])
            
            # Detect missing runs
            if dataset.run_numbers:
                all_runs = range(min(dataset.run_numbers), max(dataset.run_numbers) + 1)
                dataset.missing_runs = [r for r in all_runs if r not in dataset.run_numbers]
            
            # Validate extracted data
            errors = TDAFileExtractor.validate_extracted_data(dataset)
            if errors:
                raise TDAValidationError(f"Data validation failed: {'; '.join(errors)}")
            
            return dataset
            
        except Exception as e:
            if isinstance(e, (TDAFileError, TDAValidationError)):
                raise
            else:
                raise TDAFileError(f"Failed to parse .xls files in {folder_path}: {str(e)}")
    
    @staticmethod
    def _parse_run_timestamps(content: str) -> dict:
        """Parse run timestamps from text content"""
        timestamps = {}
        
        # Look for run table patterns
        lines = content.split('\n')
        in_run_table = False
        
        for line in lines:
            line = line.strip()
            
            # Detect start of run table
            if 'run' in line.lower() and 'time' in line.lower():
                in_run_table = True
                continue
            
            # End of table detection
            if in_run_table and (line == '' or line.startswith('=')):
                break
            
            if in_run_table:
                # Parse run number and timestamp
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        run_num = int(parts[0])
                        # Combine date and time parts
                        if len(parts) >= 4:
                            timestamp = f"{parts[1]} {parts[2]}"
                        else:
                            timestamp = parts[1]
                        
                        # Standardize timestamp
                        timestamp = TimestampProcessor.parse_to_standard(timestamp)
                        timestamps[run_num] = timestamp
                    except (ValueError, IndexError):
                        continue
        
        return timestamps
    
    @staticmethod
    def _parse_peak_areas(content: str) -> dict:
        """Parse peak areas for hydrogen from text content"""
        peak_data = {}
        
        lines = content.split('\n')
        in_hydrogen_section = False
        in_peak_table = False
        
        for line in lines:
            line = line.strip()
            
            # Look for hydrogen compound section
            if 'compound' in line.lower() and 'hydrogen' in line.lower():
                in_hydrogen_section = True
                continue
            
            # End of section
            if in_hydrogen_section and line.startswith('='):
                break
            
            # Look for peak table
            if in_hydrogen_section and ('run' in line.lower() and 'area' in line.lower()):
                in_peak_table = True
                continue
            
            if in_peak_table and line:
                # Parse run number and peak area
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        run_num = int(parts[0])
                        peak_area = float(parts[1])
                        peak_height = float(parts[2]) if len(parts) > 2 else 0.0
                        
                        peak_data[run_num] = {
                            'area': peak_area,
                            'height': peak_height
                        }
                    except (ValueError, IndexError):
                        continue
        
        return peak_data
    
    @staticmethod
    def _merge_run_data(dataset: TDADataSet, timestamps: dict, peak_data: dict):
        """Merge timestamp and peak data, handling missing runs"""
        all_runs = set(timestamps.keys()) | set(peak_data.keys())
        
        for run_num in sorted(all_runs):
            if run_num in timestamps and run_num in peak_data:
                dataset.run_numbers.append(run_num)
                dataset.timestamps.append(timestamps[run_num])
                dataset.peak_areas.append(peak_data[run_num]['area'])
                dataset.peak_heights.append(peak_data[run_num]['height'])
            else:
                # Missing run - add to missing list
                dataset.missing_runs.append(run_num)
    
    @staticmethod
    def _extract_from_excel_sheet(df: pd.DataFrame, file_path: str = None) -> tuple:
        """Extract peak area, height, and timestamp from Excel sheet
        
        For TDA data, peak area is specifically located in 'Peak' sheet, cell N2
        """
        peak_area = None
        peak_height = None
        timestamp = None
        
        # If we have the file path, try to read 'Peak' sheet directly
        if file_path:
            try:
                # Read 'Peak' sheet and get cell N2 (row 2, column N = 14th column, 0-indexed = 13)
                # Use header=None to ensure we get raw data without pandas trying to interpret headers
                peak_df = pd.read_excel(file_path, sheet_name='Peak', engine='xlrd', header=None)
                if len(peak_df) >= 2 and len(peak_df.columns) >= 14:
                    # Get value from N2 (Excel row 2, col N) = pandas iloc[1, 13]
                    peak_area_raw = peak_df.iloc[1, 13]
                    print(f"DEBUG: Extracting from cell N2 (row 2, col N): {peak_area_raw}")
                    try:
                        peak_area = float(peak_area_raw)
                        if peak_area <= 0:
                            peak_area = None
                        else:
                            print(f"✅ Successfully extracted peak area from N2: {peak_area}")
                    except (ValueError, TypeError):
                        print(f"⚠️ Could not convert N2 value to float: {peak_area_raw}")
                        peak_area = None
                
                # Try to get peak height from nearby cell (e.g., M2 or O2)
                if len(peak_df) >= 2:
                    for col_idx in [12, 14]:  # M2 or O2
                        if col_idx < len(peak_df.columns):
                            try:
                                height_raw = peak_df.iloc[1, col_idx]
                                peak_height = float(height_raw)
                                if peak_height > 0:
                                    break
                            except (ValueError, TypeError):
                                continue
                
                # Try to extract timestamp from the main sheet
                try:
                    main_df = pd.read_excel(file_path, engine='xlrd')
                    timestamp = TDAFileExtractor._extract_timestamp_from_excel(main_df)
                except:
                    pass
                    
            except Exception as e:
                # Fallback to original search method if direct access fails
                pass
        
        # If direct access failed, fall back to search method
        if peak_area is None:
            peak_area, peak_height, timestamp = TDAFileExtractor._search_excel_for_data(df)
        
        return peak_area, peak_height, timestamp
    
    @staticmethod
    def _search_excel_for_data(df: pd.DataFrame) -> tuple:
        """Fallback method to search Excel sheet for hydrogen data"""
        peak_area = None
        peak_height = None
        timestamp = None
        
        # Convert to string for searching
        df_str = df.astype(str).apply(lambda x: x.str.lower())
        
        # Look for hydrogen-related data
        hydrogen_patterns = ['hydrogen', 'h2', 'h_2']
        area_patterns = ['area', 'peak area']
        height_patterns = ['height', 'peak height']
        
        # Search for hydrogen peak area
        for h_pattern in hydrogen_patterns:
            for a_pattern in area_patterns:
                mask = df_str.apply(lambda x: x.str.contains(h_pattern)).any(axis=1) & \
                       df_str.apply(lambda x: x.str.contains(a_pattern)).any(axis=1)
                if mask.any():
                    row_idx = mask.idxmax()
                    # Find numeric value in that row
                    for col in df.columns:
                        try:
                            value = float(df.iloc[row_idx, col])
                            if value > 0:  # Valid peak area
                                peak_area = value
                                break
                        except:
                            continue
                    if peak_area:
                        break
            if peak_area:
                break
        
        # If no labeled data found, look for numeric data in likely columns
        if peak_area is None:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                # Use first positive numeric value as peak area
                for col in numeric_cols:
                    values = df[col].dropna()
                    positive_values = values[values > 0]
                    if len(positive_values) > 0:
                        peak_area = float(positive_values.iloc[0])
                        break
        
        return peak_area, peak_height, timestamp
    
    @staticmethod
    def _extract_timestamp_from_excel(df: pd.DataFrame) -> str:
        """Extract timestamp from Excel data"""
        timestamp = None
        df_str = df.astype(str).apply(lambda x: x.str.lower())
        time_patterns = ['time', 'timestamp', 'date', 'injtime']
        
        for t_pattern in time_patterns:
            mask = df_str.apply(lambda x: x.str.contains(t_pattern)).any(axis=1)
            if mask.any():
                row_idx = mask.idxmax()
                for col in df.columns:
                    try:
                        # Try to parse as timestamp
                        value = str(df.iloc[row_idx, col])
                        if len(value) > 8:  # Reasonable timestamp length
                            timestamp = TimestampProcessor.parse_to_standard(value)
                            break
                    except:
                        continue
                break
        
        return timestamp
    
    @staticmethod
    def parse_timestamp(timestamp_str: str) -> str:
        """
        Standardize timestamp format to "MM/DD/YYYY HH:MM:SS"
        
        Input formats handled:
        - "07/06/2025 15:34:21" (preferred format)
        - "2025-06-07 15:34:21" (ISO format)
        - Other common variations
        
        Returns: Standardized timestamp string
        """
        return TimestampProcessor.parse_to_standard(timestamp_str)
    
    @staticmethod
    def extract_experiment_name(folder_path: str) -> str:
        """
        Extract experiment name from folder path or file names
        
        Priority:
        1. Use folder name if descriptive
        2. Extract from file metadata if available
        3. Generate from timestamp if needed
        """
        folder_name = os.path.basename(folder_path)
        
        # Clean up folder name
        if folder_name and folder_name != '.' and not folder_name.startswith('Temp'):
            return folder_name
        
        # Generate from timestamp
        return f"TDA_Experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    @staticmethod
    def validate_extracted_data(data: TDADataSet) -> List[str]:
        """
        Validate extracted data quality
        
        Checks:
        - At least some data was extracted
        - Peak areas are positive numbers
        - Timestamps are valid
        - Run numbers are sequential (allowing gaps)
        """
        errors = []
        
        # Check if any data was extracted
        if not data.run_numbers:
            errors.append("No data was extracted")
            return errors
        
        # Check data consistency
        consistency_errors = data.validate_data_consistency()
        errors.extend(consistency_errors)
        
        # Check peak areas are positive
        if data.peak_areas:
            negative_areas = [area for area in data.peak_areas if area <= 0]
            if negative_areas:
                errors.append(f"Found {len(negative_areas)} non-positive peak areas")
        
        # Check run number sequence
        if data.run_numbers:
            if not all(isinstance(run, int) for run in data.run_numbers):
                errors.append("Run numbers must be integers")
            
            sorted_runs = sorted(data.run_numbers)
            if sorted_runs != data.run_numbers:
                errors.append("Run numbers are not in sequential order")
        
        return errors


class TimestampProcessor:
    """Standardized timestamp handling across all modules"""
    
    STANDARD_FORMAT = "%m/%d/%Y %H:%M:%S"  # "MM/DD/YYYY HH:MM:SS"
    
    @staticmethod
    def parse_to_standard(timestamp_str: str) -> str:
        """Convert any timestamp format to standard format"""
        if not timestamp_str or timestamp_str.strip() == "":
            return ""
        
        # Common timestamp formats to try
        formats = [
            "%m/%d/%Y %H:%M:%S",    # MM/DD/YYYY HH:MM:SS (target format)
            "%Y-%m-%d %H:%M:%S",    # YYYY-MM-DD HH:MM:SS (ISO format)
            "%m/%d/%Y",             # MM/DD/YYYY (date only)
            "%Y-%m-%d",             # YYYY-MM-DD (date only)
            "%m-%d-%Y %H:%M:%S",    # MM-DD-YYYY HH:MM:SS
            "%d/%m/%Y %H:%M:%S",    # DD/MM/YYYY HH:MM:SS (European)
        ]
        
        timestamp_str = timestamp_str.strip()
        
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                return dt.strftime(TimestampProcessor.STANDARD_FORMAT)
            except ValueError:
                continue
        
        # If no format matched, return original string
        return timestamp_str
    
    @staticmethod
    def calculate_minutes_from_start(timestamps: List[str]) -> List[float]:
        """
        Convert timestamps to minutes elapsed from first timestamp
        
        Input: List of standardized timestamp strings
        Output: List of float minutes (e.g. [0.0, 5.3, 10.7, ...])
        """
        if not timestamps:
            return []
        
        minutes = []
        start_time = None
        
        for timestamp_str in timestamps:
            try:
                dt = datetime.strptime(timestamp_str, TimestampProcessor.STANDARD_FORMAT)
                
                if start_time is None:
                    start_time = dt
                    minutes.append(0.0)
                else:
                    elapsed = (dt - start_time).total_seconds() / 60.0
                    minutes.append(elapsed)
                    
            except ValueError:
                # If timestamp parsing fails, use 0 or previous value
                if minutes:
                    minutes.append(minutes[-1])
                else:
                    minutes.append(0.0)
        
        return minutes
    
    @staticmethod
    def validate_timestamp_sequence(timestamps: List[str]) -> List[str]:
        """Validate timestamp sequence for anomalies"""
        warnings = []
        
        if len(timestamps) < 2:
            return warnings
        
        parsed_times = []
        for ts in timestamps:
            try:
                dt = datetime.strptime(ts, TimestampProcessor.STANDARD_FORMAT)
                parsed_times.append(dt)
            except ValueError:
                warnings.append(f"Invalid timestamp format: {ts}")
                continue
        
        # Check for chronological order
        for i in range(1, len(parsed_times)):
            if parsed_times[i] < parsed_times[i-1]:
                warnings.append("Timestamps are not in chronological order")
                break
        
        # Check for large gaps
        if len(parsed_times) > 1:
            intervals = [(parsed_times[i] - parsed_times[i-1]).total_seconds() / 60.0 
                        for i in range(1, len(parsed_times))]
            
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                large_gaps = [i for i in intervals if i > avg_interval * 3]
                if large_gaps:
                    warnings.append(f"Found {len(large_gaps)} unusually large time gaps")
        
        return warnings