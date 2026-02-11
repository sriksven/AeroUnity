# AeroUnity Project Structure

## Directory Organization

```
AeroUnity/
├── README.md                      # Main documentation
├── requirements.txt               # Python dependencies
├── .gitignore                     # Git ignore rules
│
├── main.py                        # Quick demo entry point
├── run_complete_validation.py    # Standard validation pipeline
├── run_enhanced_validation.py    # Enhanced validation with edge cases
│
├── src/                           # Source code
│   ├── core/                      # Unified planning framework
│   │   ├── __init__.py
│   │   ├── planner_base.py        # Abstract MissionPlanner class
│   │   ├── constraints.py         # Constraint representation
│   │   └── objectives.py          # Objective functions
│   │
│   ├── aircraft/                  # Aircraft mission module
│   │   ├── __init__.py
│   │   ├── models.py              # Flight dynamics, wind model
│   │   ├── constraints.py         # Aircraft-specific constraints
│   │   ├── planner.py             # AircraftMissionPlanner
│   │   └── simulator.py           # Flight simulation
│   │
│   ├── spacecraft/                # Spacecraft mission module
│   │   ├── __init__.py
│   │   ├── orbit.py               # Orbital mechanics
│   │   ├── constraints.py         # Spacecraft-specific constraints
│   │   ├── planner.py             # SpacecraftMissionPlanner
│   │   └── scheduler.py           # Schedule utilities
│   │
│   └── visualization/             # Plotting utilities
│       ├── __init__.py
│       ├── aircraft_viz.py        # Aircraft visualizations
│       └── spacecraft_viz.py      # Spacecraft visualizations
│
├── validation/                    # Test and validation suites
│   ├── test_core.py               # Unit tests for core framework
│   ├── aircraft_validation.py    # Aircraft validation suite
│   ├── spacecraft_validation.py  # Spacecraft validation suite
│   └── edge_case_tests.py        # Edge case and stress tests
│
├── docs/                          # Documentation
│   ├── EDGE_CASE_TESTING.md       # Edge case testing results
│   └── devpost_story.md           # Devpost project story
│
└── outputs/                       # Generated results
    ├── *.json                     # Validation results (tracked)
    ├── *.csv                      # Schedule exports (tracked)
    ├── *.png                      # Plots (ignored, regenerable)
    ├── validation/                # Standard validation results
    │   ├── aircraft_monte_carlo.json
    │   ├── aircraft_constraint_checks.json
    │   ├── aircraft_performance_metrics.json
    │   ├── spacecraft_feasibility.json
    │   ├── spacecraft_value_metrics.json
    │   └── spacecraft_stress_tests.json
    └── edge_cases/                # Edge case test results
        ├── extreme_wind_tests.json
        ├── battery_stress_tests.json
        ├── geofencing_tests.json
        ├── orbit_edge_cases.json
        └── failure_mode_tests.json
```

## File Counts

- **Source code**: 14 Python files (276 KB)
- **Validation**: 4 test suites (108 KB)
- **Documentation**: 3 markdown files
- **Results**: 15 JSON files, 1 CSV file (validation data)
- **Visualizations**: 8 PNG files (regenerable, not tracked)

## What's Tracked in Git

### Tracked 
- All source code (`src/`)
- All validation suites (`validation/`)
- All documentation (`docs/`, `README.md`)
- Validation results (`outputs/**/*.json`, `outputs/**/*.csv`)
- Configuration (`requirements.txt`, `.gitignore`)

### Ignored 
- Generated plots (`outputs/*.png`) - regenerable via validation scripts
- Log files (`*.log`) - temporary
- Python cache (`__pycache__/`, `*.pyc`)
- Virtual environment (`venv/`)
- OS files (`.DS_Store`)

## Regenerating Outputs

All ignored files can be regenerated:

```bash
# Regenerate all plots and validation results
python run_complete_validation.py

# Or with edge cases
python run_enhanced_validation.py
```

## Clean Repository

The repository is now optimized for:
- **Minimal size**: Only essential files tracked
- **Reproducibility**: All outputs can be regenerated
- **Clarity**: Clear separation of code, tests, docs, and results
- **Professional**: No temporary files or redundant directories
