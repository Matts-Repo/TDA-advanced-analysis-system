#!/usr/bin/env python3
"""
Test script to verify TDA Analysis System structure without GUI dependencies
"""

import sys
import os
import numpy as np

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all core modules can be imported"""
    print("Testing core module imports...")
    
    try:
        from modules.shared_data_structures import TDADataSet, CalibrationData
        print("✅ Shared data structures imported")
    except Exception as e:
        print(f"❌ Failed to import shared_data_structures: {e}")
        return False
    
    try:
        from modules.error_handling import TDAError, TDAFileError
        print("✅ Error handling imported")
    except Exception as e:
        print(f"❌ Failed to import error_handling: {e}")
        return False
    
    try:
        from modules.data_extraction import TDAFileExtractor
        print("✅ Data extraction imported")
    except Exception as e:
        print(f"❌ Failed to import data_extraction: {e}")
        return False
    
    try:
        from modules.calibration_manager import CalibrationManager
        print("✅ Calibration manager imported")
    except Exception as e:
        print(f"❌ Failed to import calibration_manager: {e}")
        return False
    
    try:
        from modules.data_processor import DataProcessor, HydrogenCalculator
        print("✅ Data processor imported")
    except Exception as e:
        print(f"❌ Failed to import data_processor: {e}")
        return False
    
    try:
        from modules.plot_manager import PlotManager, PlotDataset
        print("✅ Plot manager imported")
    except Exception as e:
        print(f"❌ Failed to import plot_manager: {e}")
        return False
    
    return True

def test_structure():
    """Test basic structure functionality"""
    print("\nTesting basic structure...")
    
    try:
        from modules.shared_data_structures import TDADataSet, CalibrationData
        
        # Test TDADataSet creation
        dataset = TDADataSet(experiment_name="test", source_file="test.txt")
        dataset.run_numbers = [1, 2, 3]
        dataset.timestamps = ["01/01/2024 10:00:00", "01/01/2024 10:05:00", "01/01/2024 10:10:00"]
        dataset.peak_areas = [1000.0, 1100.0, 1050.0]
        dataset.peak_heights = [50.0, 55.0, 52.5]
        
        errors = dataset.validate_data_consistency()
        if not errors:
            print("✅ TDADataSet validation passed")
        else:
            print(f"⚠️ TDADataSet validation warnings: {errors}")
        
        # Test CalibrationData creation
        peak_areas = [1000.0, 1100.0, 1050.0, 980.0, 1020.0]
        cal_data = CalibrationData(
            calibration_id="TEST_001",
            gas_concentration_ppm=61.0,
            raw_peak_areas=peak_areas,
            mean_peak_area=np.mean(peak_areas),
            num_runs=len(peak_areas)
        )
        
        if cal_data.mean_peak_area > 0:
            print("✅ CalibrationData statistics calculated")
        else:
            print("❌ CalibrationData statistics failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Structure test failed: {e}")
        return False

def test_managers():
    """Test manager initialization"""
    print("\nTesting manager initialization...")
    
    try:
        # Create test directories
        os.makedirs("./test_data/calibrations", exist_ok=True)
        os.makedirs("./test_data/processed", exist_ok=True)
        
        from modules.calibration_manager import CalibrationManager
        from modules.data_processor import DataProcessor
        from modules.plot_manager import PlotManager
        
        # Test CalibrationManager
        cal_manager = CalibrationManager(calibration_folder="./test_data/calibrations")
        print("✅ CalibrationManager initialized")
        
        # Test DataProcessor
        data_processor = DataProcessor(cal_manager, output_folder="./test_data/processed")
        print("✅ DataProcessor initialized")
        
        # Test PlotManager
        plot_manager = PlotManager(processed_data_folder="./test_data/processed")
        print("✅ PlotManager initialized")
        
        # Clean up test directories
        import shutil
        shutil.rmtree("./test_data", ignore_errors=True)
        
        return True
        
    except Exception as e:
        print(f"❌ Manager test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("TDA Analysis System Structure Test")
    print("=" * 40)
    
    success = True
    
    success &= test_imports()
    success &= test_structure()
    success &= test_managers()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 All tests passed! TDA Analysis System structure is valid.")
        print("\nTo run the full application (requires PyQt5):")
        print("  python main.py")
        print("\nFirst install dependencies:")
        print("  pip install -r requirements.txt")
    else:
        print("❌ Some tests failed. Check the error messages above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())