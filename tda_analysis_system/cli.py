#!/usr/bin/env python3
"""
Command Line Interface for TDA Analysis System

Provides command-line access to diffusion analysis functionality for batch processing.
"""

import argparse
import os
import sys
from typing import Optional

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.plot_manager import PlotManager, PlotOptions, ExportOptions
from modules.calcs import DiffusionAnalysisEngine
from modules.error_handling import TDAError, TDAFileError


def setup_argument_parser():
    """Set up command line argument parser"""
    parser = argparse.ArgumentParser(
        description="TDA Analysis System - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run diffusion analysis on a processed CSV file
  python cli.py --diffusion-analysis data/processed/sample.csv
  
  # Specify custom tail start time
  python cli.py --diffusion-analysis data/processed/sample.csv --tail-start-time 150
  
  # Generate all three plot types
  python cli.py --diffusion-analysis data/processed/sample.csv --plot-type all
  
  # Export to specific format
  python cli.py --diffusion-analysis data/processed/sample.csv --export-format PDF
        """
    )
    
    # Input file
    parser.add_argument(
        'input_file',
        nargs='?',
        help='Path to processed TDA CSV file'
    )
    
    # Diffusion analysis options
    parser.add_argument(
        '--diffusion-analysis',
        action='store_true',
        help='Perform diffusion analysis on the input file'
    )
    
    parser.add_argument(
        '--plot-type',
        choices=['1_sqrt_t', 'sqrt_t', 'log_log', 'all'],
        default='1_sqrt_t',
        help='Type of diffusion plot to generate (default: 1_sqrt_t)'
    )
    
    parser.add_argument(
        '--tail-start-time',
        type=float,
        help='Manual tail start time in minutes (auto-detect if not specified)'
    )
    
    parser.add_argument(
        '--sample-thickness',
        type=float,
        default=0.1,
        help='Sample thickness in cm for diffusion coefficient calculation (default: 0.1)'
    )
    
    parser.add_argument(
        '--no-linear-fit',
        action='store_true',
        help='Disable linear fit overlay'
    )
    
    parser.add_argument(
        '--no-diffusion-coeff',
        action='store_true',
        help='Disable diffusion coefficient calculation'
    )
    
    # Output options
    parser.add_argument(
        '--output-dir',
        default='./output',
        help='Output directory for generated plots (default: ./output)'
    )
    
    parser.add_argument(
        '--export-format',
        choices=['PNG', 'PDF', 'SVG', 'EPS'],
        default='PNG',
        help='Export format for plots (default: PNG)'
    )
    
    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        help='DPI for exported plots (default: 300)'
    )
    
    # General options
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        help='Suppress all output except errors'
    )
    
    return parser


def perform_diffusion_analysis(csv_path: str,
                              plot_type: str = '1_sqrt_t',
                              tail_start_time: Optional[float] = None,
                              sample_thickness: float = 0.1,
                              show_linear_fit: bool = True,
                              calculate_D: bool = True,
                              output_dir: str = './output',
                              export_format: str = 'PNG',
                              dpi: int = 300,
                              verbose: bool = False) -> None:
    """
    Perform diffusion analysis on a processed CSV file
    
    Args:
        csv_path: Path to processed TDA CSV file
        plot_type: Type of plot ('1_sqrt_t', 'sqrt_t', 'log_log', or 'all')
        tail_start_time: Manual tail start time (auto-detect if None)
        sample_thickness: Sample thickness in cm
        show_linear_fit: Whether to show linear fit
        calculate_D: Whether to calculate diffusion coefficient
        output_dir: Output directory for plots
        export_format: Export format
        dpi: DPI for exported plots
        verbose: Enable verbose output
    """
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize plot manager and load dataset
        processed_data_folder = os.path.dirname(csv_path)
        plot_manager = PlotManager(processed_data_folder)
        
        if verbose:
            print(f"Loading dataset: {csv_path}")
        
        dataset = plot_manager.load_dataset(csv_path)
        
        if verbose:
            print(f"Dataset loaded: {dataset.experiment_name}")
            print(f"Data points: {len(dataset.time_minutes)}")
            print(f"Duration: {dataset.duration_hours:.1f} hours")
            print(f"Calculation mode: {dataset.calculation_mode}")
        
        # Determine plot types to generate
        if plot_type == 'all':
            plot_types = ['1_sqrt_t', 'sqrt_t', 'log_log']
        else:
            plot_types = [plot_type]
        
        # Generate plots for each type
        for ptype in plot_types:
            if verbose:
                print(f"\nGenerating {ptype} plot...")
            
            # Create plot options
            options = PlotOptions()
            options.figure_size = (10, 8)
            options.dpi = 100
            options.show_legend = True
            options.show_grid = True
            
            # Generate diffusion plot
            figure, analysis_result = plot_manager.generate_diffusion_plot(
                dataset=dataset,
                plot_type=ptype,
                tail_start_time=tail_start_time,
                show_linear_fit=show_linear_fit,
                calculate_D=calculate_D,
                sample_thickness=sample_thickness,
                options=options
            )
            
            # Create output filename
            base_name = os.path.splitext(os.path.basename(csv_path))[0]
            output_filename = f"{base_name}_diffusion_{ptype}.{export_format.lower()}"
            output_path = os.path.join(output_dir, output_filename)
            
            # Export plot
            export_options = ExportOptions()
            export_options.filename = output_path
            export_options.format = export_format
            export_options.dpi = dpi
            
            plot_manager.export_plot(figure, export_options)
            
            if verbose:
                print(f"Plot saved: {output_path}")
                print(f"Analysis results:")
                print(f"  Tail start: {analysis_result.tail_start_time:.1f} min")
                print(f"  R² value: {analysis_result.r_squared:.4f}")
                print(f"  Fit quality: {analysis_result.goodness_of_fit}")
                if analysis_result.diffusion_coefficient > 0:
                    print(f"  Diffusion coefficient: {analysis_result.diffusion_coefficient:.2e} cm²/s")
            else:
                print(f"Generated: {output_filename}")
        
        if verbose:
            print(f"\nDiffusion analysis complete. Outputs saved to: {output_dir}")
    
    except Exception as e:
        raise TDAError(f"Diffusion analysis failed: {str(e)}")


def main():
    """Main CLI entry point"""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Set up logging level
    verbose = args.verbose and not args.quiet
    
    try:
        # Check if input file is provided when needed
        if args.diffusion_analysis and not args.input_file:
            parser.error("Input file required for diffusion analysis")
        
        # Check if input file exists
        if args.input_file and not os.path.exists(args.input_file):
            raise TDAFileError(f"Input file not found: {args.input_file}")
        
        # Perform diffusion analysis
        if args.diffusion_analysis:
            if not args.quiet:
                print("TDA Diffusion Analysis - Command Line Interface")
                print("=" * 50)
            
            perform_diffusion_analysis(
                csv_path=args.input_file,
                plot_type=args.plot_type,
                tail_start_time=args.tail_start_time,
                sample_thickness=args.sample_thickness,
                show_linear_fit=not args.no_linear_fit,
                calculate_D=not args.no_diffusion_coeff,
                output_dir=args.output_dir,
                export_format=args.export_format,
                dpi=args.dpi,
                verbose=verbose
            )
            
            if not args.quiet:
                print("\nAnalysis completed successfully!")
        
        else:
            # No specific action requested, show help
            parser.print_help()
    
    except (TDAError, TDAFileError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()