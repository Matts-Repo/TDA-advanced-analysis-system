# Claude Code Implementation Prompt

```xml
<task>
  <objective>
    Add a new calculation mode to the existing TDA Dashboard that calculates hydrogen desorption 
    as moles per square centimeter of charging surface area (mol/cm²) instead of ppm by weight.
  </objective>

  <context>
    <current_system>
      - TDA Dashboard currently converts peak areas to H ppm (parts per million by weight)
      - Uses calibration factor from gas concentration/peak area ratio
      - Formula: H_ppm = (peak_area * calibration_factor) / sample_mass
      - GUI has manual calibration inputs for concentration (ppm) and peak area
    </current_system>
    
    <motivation>
      - Current ppm calculation is affected by effective charging depth variations
      - Surface area normalization provides better standardization across specimens
      - Enables more accurate comparison between samples with different geometries
    </motivation>
  </context>

  <requirements>
    <calculation_changes>
      - Add new calculation mode: "Surface Area Normalized" alongside existing "Mass Normalized (ppm)"
      - New formula: H_mol_per_cm2 = (peak_area * calibration_factor * conversion_to_moles) / surface_area
      - Conversion factor: Use ideal gas law at STP (22.414 L/mol) and H2 molecular weight (2.016 g/mol)
      - Keep existing calibration setup (concentration/peak area ratio)
    </calculation_changes>

    <gui_modifications>
      - Add radio buttons or dropdown to select calculation mode:
        * "Mass Normalized (ppm wt%)" [default]
        * "Surface Area Normalized (mol/cm²)"
      - Add input field for "Sample Surface Area (cm²)" that appears when surface mode is selected
      - Input field should be near existing calibration inputs
      - Update plot labels dynamically based on selected mode:
        * Y-axis: "H ppm/cycle" → "H (mol/cm²)/cycle"
        * Secondary Y-axis: "Cumulative H ppm" → "Cumulative H (mol/cm²)"
    </gui_modifications>

    <data_flow>
      - Modify calcs.py to support both calculation modes
      - Add surface_area parameter to apply_calibration() function
      - Add calculation_mode parameter to determine which formula to use
      - Ensure DataFrame column names reflect the units (e.g., 'H_mol_cm2' vs 'H_ppm')
    </data_flow>

    <implementation_details>
      - Maintain backward compatibility - existing functionality must remain unchanged
      - Surface area input should remember last value during session
      - Export filenames should indicate calculation mode (e.g., "experiment_surface_normalized.csv")
      - Both modes should use the same calibration factor from concentration/peak area
    </implementation_details>
  </requirements>

  <specific_changes>
    <file name="calcs.py">
      - Add calculation_mode parameter to apply_calibration()
      - Add surface_area parameter to apply_calibration()
      - Implement conversion formula for mol/cm² mode
      - Add helper function to convert from calibrated peak area to moles H2
    </file>

    <file name="gui.py">
      - Add radio buttons for calculation mode selection
      - Add surface area input field (show/hide based on mode)
      - Modify apply_manual_calibration() to pass new parameters
      - Update plot labels based on selected mode
      - Store calculation mode in experiment metadata
    </file>

    <file name="plotting.py">
      - Make axis labels dynamic based on data units
      - Detect units from DataFrame column names or metadata
    </file>

    <file name="cli.py">
      - Add --surface-area and --calculation-mode arguments
      - Update help text to explain both modes
    </file>
  </specific_changes>

  <example_usage>
    <gui_workflow>
      1. User loads experiments as normal
      2. User enters calibration gas concentration and peak area
      3. User selects "Surface Area Normalized (mol/cm²)" mode
      4. Surface area input field appears
      5. User enters surface area in cm²
      6. Plots update with mol/cm² units
      7. Exported files contain surface-normalized data
    </gui_workflow>

    <cli_example>
      python -m tda_dash process --root /experiments --calculation-mode surface --surface-area 2.5
    </cli_example>
  </example_usage>

  <testing_requirements>
    - Verify calculations are correct for both modes
    - Test GUI mode switching updates plots correctly
    - Ensure exported data includes proper units in headers
    - Validate that switching modes recalculates existing data
  </testing_requirements>
</task>
```