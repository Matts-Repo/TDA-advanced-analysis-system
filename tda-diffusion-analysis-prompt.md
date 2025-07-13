# Claude Code Implementation Prompt - Diffusion Analysis Tab

```xml
<task>
  <objective>
    Add a new "Diffusion Analysis" tab to the TDA Dashboard for analyzing hydrogen desorption tails 
    using 1/√t plots to confirm diffusion-controlled behavior. Also add a refresh button to reset plots.
  </objective>

  <context>
    <physical_basis>
      - Isothermal TDA at room temperature with GC detection every 4 minutes
      - Initial peak (0-60 min): Electrochemically charged hydrogen from ~70 μm surface layer
      - Tail region (>2 hours): Pre-existing bulk hydrogen diffusing out
      - Diffusion-controlled flux follows J(t) ∝ 1/√t for semi-infinite solid
    </physical_basis>
    
    <current_system>
      - TDA Dashboard with Tkinter GUI
      - Multiple plot types in main tab
      - Data stored in DataFrames with time_minutes and H_ppm/H_mol_cm2 columns
    </current_system>
  </context>

  <requirements>
    <new_tab>
      <name>Diffusion Analysis</name>
      <location>Add as new tab alongside existing plot options</location>
      <purpose>Analyze tail region to confirm diffusion control and calculate D</purpose>
    </new_tab>

    <gui_components>
      <tail_region_selection>
        - Label: "Tail Region Start Time (minutes):"
        - Default: 120 (2 hours)
        - Spinbox or entry field with validation
        - Help text: "Select time after initial peak has decayed"
      </tail_region_selection>

      <plot_options>
        - Radio buttons for plot type:
          * "Desorption Rate vs 1/√t"
          * "Cumulative H vs √t"
          * "Log-Log Plot (log J vs log t)"
        - Checkbox: "Show linear fit"
        - Checkbox: "Calculate diffusion coefficient"
      </plot_options>

      <analysis_results>
        - Text display area showing:
          * R² value of linear fit
          * Slope and intercept
          * Calculated diffusion coefficient (if applicable)
          * Comparison with literature values
      </analysis_results>

      <refresh_button>
        - Add "Clear Plot" or "Refresh" button to ALL tabs
        - Location: Near "Update Plot" button
        - Function: Clear current plot and reset to blank canvas
        - Should not clear loaded data, only the visualization
      </refresh_button>
    </gui_components>

    <calculations>
      <tail_identification>
        - Automatic suggestion for tail start based on:
          * When desorption rate drops below 10% of peak maximum
          * Minimum 60 minutes after start
        - User can override with manual selection
      </tail_identification>

      <diffusion_plots>
        - Extract data for t > tail_start_time
        - Calculate 1/√t and √t arrays
        - For log-log: calculate log(J) and log(t)
        - Handle zero/negative values appropriately
      </diffusion_plots>

      <linear_regression>
        - Use scipy.stats.linregress or numpy.polyfit
        - Calculate R², slope, intercept, standard error
        - Only fit data points with sufficient signal (>noise threshold)
      </linear_regression>

      <diffusion_coefficient>
        - From slope of J vs 1/√t plot:
          * D = π × (slope × L)² / (4 × ΔC²)
        - Assumptions to document:
          * Semi-infinite geometry
          * Constant temperature
          * Surface concentration = 0
      </diffusion_coefficient>
    </calculations>

    <implementation_details>
      <file name="gui.py">
        - Add new notebook tab "Diffusion Analysis"
        - Create frame with tail time selection and plot options
        - Add results text widget
        - Implement refresh_plot() method for all tabs
        - Add "Clear Plot" button to control frames
      </file>

      <file name="plotting.py">
        - Add make_diffusion_plot() function
        - Support three plot types (1/√t, √t, log-log)
        - Include linear regression overlay
        - Add text annotations for R² and equation
      </file>

      <file name="calcs.py">
        - Add find_tail_start() to automatically identify tail region
        - Add calculate_diffusion_coefficient() 
        - Add perform_linear_regression() with proper error handling
      </file>

      <file name="cli.py">
        - Add --diffusion-analysis flag
        - Add --tail-start-time parameter
        - Generate diffusion plots in batch mode
      </file>
    </implementation_details>
  </requirements>

  <example_interface>
    <diffusion_tab_layout>
      ┌─────────────────────────────────────┐
      │ Diffusion Analysis                  │
      ├─────────────────────────────────────┤
      │ Tail Region Start Time: [120] min   │
      │ □ Auto-detect tail start            │
      │                                     │
      │ Plot Type:                          │
      │ ◉ Desorption Rate vs 1/√t          │
      │ ○ Cumulative H vs √t               │
      │ ○ Log-Log Plot                     │
      │                                     │
      │ ☑ Show linear fit                  │
      │ ☑ Calculate D coefficient          │
      │                                     │
      │ [Analyze] [Clear Plot] [Export]     │
      │                                     │
      │ ┌─────────────────────────────┐    │
      │ │                             │    │
      │ │      Plot Area             │    │
      │ │                             │    │
      │ └─────────────────────────────┘    │
      │                                     │
      │ Analysis Results:                   │
      │ ┌─────────────────────────────┐    │
      │ │ R² = 0.987                  │    │
      │ │ Slope = -2.34e-6            │    │
      │ │ D = 1.2e-7 cm²/s            │    │
      │ │ Literature: 1.0e-7 cm²/s    │    │
      │ └─────────────────────────────┘    │
      └─────────────────────────────────────┘
    </diffusion_tab_layout>
  </example_interface>

  <validation>
    - Ensure tail start time is after peak maximum
    - Handle cases with insufficient tail data
    - Validate positive values for 1/√t calculation
    - Check R² threshold (suggest >0.9 for good fit)
  </validation>

  <error_handling>
    - Graceful handling of experiments with no clear tail
    - Warning if tail region too short (<10 data points)
    - Handle division by zero in 1/√t calculation
    - Clear error messages in results display
  </error_handling>
</task>
```