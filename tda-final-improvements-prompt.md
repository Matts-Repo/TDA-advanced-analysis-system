# Claude Code Implementation Prompt - Final TDA Dashboard Improvements

```xml
<task>
  <objective>
    Make final improvements to TDA Dashboard: correct units display, add zero-value filtering,
    temperature-dependent diffusion analysis, and cleaner plot layouts.
  </objective>

  <requirements>
    <unit_display_fix>
      <problem>Data Visualization tab shows ppm and ppm/min instead of mol and mol/min</problem>
      <solution>
        - Primary Y-axis (left): Display in mol/cm² and mol/cm²/min
        - Secondary Y-axis (right): Display in ppm and ppm/min
        - Both axes show the same data, just different units
        - Ensure proper scaling between mol and ppm conversions
      </solution>
      <implementation>
        - Modify make_dual_axis() in plotting.py
        - Calculate mol values from H_ppm using:
          * mol_H2 = (ppm × sample_mass × 10⁻⁶) / (2.016 g/mol)
          * For surface mode: already in mol/cm²
        - Plot same data on both Y-axes with different scaling
        - Update axis labels: 
          * Left: "H₂ Evolution Rate (mol/cm²/min)" and "Cumulative H₂ (mol/cm²)"
          * Right: "H₂ Evolution Rate (ppm/min)" and "Cumulative H₂ (ppm)"
      </implementation>
    </unit_display_fix>

    <zero_value_filtering>
      <data_visualization_tab>
        - Add checkbox: "Exclude zero values"
        - When checked: Remove all (time, value) pairs where value = 0.0
        - EXCEPTION: Always keep the (0, 0) point at time = 0
        - Apply to both evolution rate and cumulative plots
      </data_visualization_tab>
      
      <diffusion_analysis_tab>
        - Add checkbox: "Filter noise/zeros"
        - When checked, exclude:
          * Exact zero values
          * Values < 2% of rolling average of previous 5 points
          * Values below GC detection limit (if specified)
        - Add field: "GC Detection Limit:" with default 0.1 ppm
        - Show number of filtered points in results
      </diffusion_analysis_tab>

      <implementation>
        - Add filter_zeros() function in calcs.py
        - Parameters: df, keep_origin=True, threshold_percent=2
        - For diffusion: only apply to tail region data
      </implementation>
    </zero_value_filtering>

    <temperature_dependent_diffusion>
      <input_fields>
        - Add to Diffusion Analysis tab:
          * "Test Temperature (°C)": [25] (default room temp)
          * "Known D at test temp (cm²/s)": [blank] (optional override)
        - If D is manually entered, use it instead of calculating
      </input_fields>

      <temperature_correction>
        - For D calculation from slope, apply Arrhenius:
          * D(T) = D₀ × exp(-Q/RT)
          * Default Q = 7.5 kJ/mol for H in steel
          * Allow Q input for different materials
        - Literature comparison should adjust for temperature:
          * D_room = 1.0e-7 cm²/s at 25°C
          * D_900C = ~1.0e-4 cm²/s at 900°C
      </temperature_correction>

      <results_display>
        - Show: "D at {temp}°C = {value} cm²/s"
        - Show: "Expected D at {temp}°C ≈ {literature} cm²/s"
        - Calculate activation energy if multiple temperatures available
      </results_display>
    </temperature_dependent_diffusion>

    <plot_cleanup>
      <diffusion_plots>
        - Remove overlapping text boxes
        - Show only essential information:
          * Plot title
          * Axis labels with units
          * Linear fit line (if R² > 0.8)
          * Single text box with: "R² = {value}\nSlope = {value}"
        - Move detailed results to the Analysis Results text area only
        - Use smaller, cleaner font for annotations
        - Position text box in upper right or lower left (whichever is emptier)
      </diffusion_plots>

      <general_improvements>
        - Use matplotlib's tight_layout() to prevent label cutoff
        - Reduce marker size for cleaner appearance
        - Use semi-transparent fit line (alpha=0.7)
        - Consistent color scheme across all plots
      </general_improvements>
    </plot_cleanup>
  </requirements>

  <specific_changes>
    <file name="plotting.py">
      - Modify make_dual_axis():
        * Add mol-scale axis on left
        * Keep ppm-scale axis on right
        * Ensure proper scaling between units
      - Clean up all plot annotations:
        * Reduce text box clutter
        * Use ax.text() with bbox for single info box
        * Remove redundant information
    </file>

    <file name="gui.py">
      - Data Visualization tab:
        * Add "Exclude zero values" checkbox
        * Update plot when checkbox toggled
      - Diffusion Analysis tab:
        * Add temperature input field
        * Add optional D override field
        * Add "Filter noise/zeros" checkbox
        * Add GC detection limit field
    </file>

    <file name="calcs.py">
      - Add filter_zeros() function
      - Add temperature_correction() for D values
      - Update diffusion calculations for temperature
      - Add mol/ppm conversion functions
    </file>
  </specific_changes>

  <example_interface_updates>
    <data_visualization_controls>
      │ Plot Type: ◉ Dual Axis                │
      │ ☑ Exclude zero values                 │
      │ [Update Plot] [Clear Plot] [Export]    │
    </data_visualization_controls>

    <diffusion_analysis_controls>
      │ Tail Start Time: [120] min            │
      │ Test Temperature: [25] °C             │
      │ Known D (optional): [___] cm²/s       │
      │ GC Detection Limit: [0.1] ppm         │
      │ ☑ Filter noise/zeros                  │
    </diffusion_analysis_controls>

    <clean_plot_annotation>
      ┌─────────────────┐
      │ R² = 0.987      │
      │ Slope = -2.3e-6 │
      └─────────────────┘
      (positioned in empty corner)
    </clean_plot_annotation>
  </example_interface_updates>

  <validation>
    - Ensure mol/ppm conversion is correct
    - Validate temperature input (0 < T < 1200°C)
    - Check that filtered data still has >10 points
    - Verify dual-axis scaling is consistent
  </validation>
</task>
```