# AeroUnity

**One Framework, Two Worlds: Unified Mission Planning for Air and Space**

A unified aerospace mission planning framework for AeroHack 2026 that demonstrates both aircraft (UAV/fixed-wing) and spacecraft (CubeSat LEO) mission planning using a single, shared constraint-based optimization approach.

## Overview

AeroUnity solves two distinct aerospace problems using the **same underlying planning architecture**:

- **🛩️ Aircraft Mission Planning**: UAV route optimization with wind, energy, maneuver constraints, and geofencing
- **🛰️ Spacecraft Mission Planning**: 7-day CubeSat observation and downlink scheduling with orbit mechanics

Both modules share:
- Common constraint representation framework
- Common objective functions (minimize time/energy, maximize value)
- Google OR-Tools as the unified solver
- Shared validation and metrics framework

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip package manager
- ~5 minutes for setup
- ~2-3 minutes for full validation run

### Installation

```bash
# Clone the repository
cd AeroUnity

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Reproduce Results

Run the complete validation pipeline to generate all results:

```bash
python run_complete_validation.py
```

This single command will:
1. ✅ Run aircraft mission planning with Monte-Carlo wind uncertainty (100 trials)
2. ✅ Run spacecraft mission planning with 7-day scheduling
3. ✅ Validate all constraints (zero violations required)
4. ✅ Generate all plots and visualizations
5. ✅ Export schedules and metrics to JSON/CSV
6. ✅ Create complete results bundle

**Expected runtime**: 2-3 minutes on modern hardware

### Expected Outputs

After running, check the `outputs/` directory:

```
outputs/
├── aircraft_flight_path.png          # 2D flight path with geofences
├── aircraft_altitude_profile.png     # Altitude over time
├── aircraft_performance.png          # Time/distance/energy metrics
├── aircraft_monte_carlo.png          # Monte-Carlo robustness results
├── spacecraft_schedule_gantt.png     # 7-day schedule Gantt chart
├── spacecraft_timeline.png           # Activity timeline
├── spacecraft_statistics.png         # Mission statistics
├── spacecraft_coverage.png           # Ground target coverage map
├── spacecraft_schedule.json          # Full schedule (JSON)
├── spacecraft_schedule.csv           # Full schedule (CSV)
├── summary_results.json              # Overall summary
└── validation/
    ├── aircraft_monte_carlo.json
    ├── aircraft_constraint_checks.json
    ├── aircraft_performance_metrics.json
    ├── spacecraft_feasibility.json
    ├── spacecraft_value_metrics.json
    └── spacecraft_stress_tests.json
```

## Key Results

### Aircraft Mission
- **Success Rate**: >95% under wind uncertainty (100 Monte-Carlo trials)
- **Constraint Violations**: 0 (geofence, altitude, energy, turn rate)
- **Mission Time**: ~8-10 minutes
- **Energy Efficiency**: ~120-140 Wh for 5km mission

### Spacecraft Mission
- **Observations Scheduled**: 15-25 targets over 7 days
- **Downlinks Scheduled**: 8-12 ground station contacts
- **Science Value**: 100+ (priority-weighted)
- **Schedule Utilization**: 2-5% (realistic for LEO operations)

## Project Structure

```
AeroUnity/
├── main.py                      # Simple demo (both missions)
├── run_complete_validation.py   # Full validation pipeline
├── requirements.txt             # Python dependencies
├── src/
│   ├── core/                    # Unified planning framework
│   │   ├── planner_base.py      # Abstract MissionPlanner
│   │   ├── constraints.py       # Constraint classes
│   │   └── objectives.py        # Objective functions
│   ├── aircraft/                # Aircraft-specific modules
│   │   ├── models.py            # Flight dynamics
│   │   ├── constraints.py       # Geofence, energy, turn rate
│   │   ├── planner.py           # AircraftMissionPlanner
│   │   └── simulator.py         # Flight simulator
│   ├── spacecraft/              # Spacecraft-specific modules
│   │   ├── orbit.py             # Orbit propagation
│   │   ├── constraints.py       # Pointing, power, duty cycle
│   │   ├── planner.py           # SpacecraftMissionPlanner
│   │   └── scheduler.py         # Schedule management
│   └── visualization/           # Plotting modules
│       ├── aircraft_viz.py
│       └── spacecraft_viz.py
├── validation/                  # Validation & testing
│   ├── aircraft_validation.py   # Monte-Carlo, metrics
│   ├── spacecraft_validation.py # Feasibility, stress tests
│   └── test_core.py             # Unit tests
├── outputs/                     # Generated results
└── docs/
    ├── devpost_story.md         # Project story
    └── technical_report.md      # Technical report (draft)
```

## Unified Architecture

Both aircraft and spacecraft planners extend the same base class:

```python
class MissionPlanner(ABC):
    def define_decision_variables() -> List[DecisionVariable]
    def define_constraints() -> List[Constraint]
    def define_objectives() -> List[Objective]
    def solve() -> Dict[str, Any]
    def validate_solution(solution) -> (bool, List[str])
```

**Key Design Principle**: Same constraint-objective-solver pattern across both domains, implemented using Google OR-Tools (routing solver for aircraft, CP-SAT for spacecraft).

## Technologies Used

- **Python 3.10+** - Core language
- **Google OR-Tools** - Constraint programming and routing
- **NumPy/SciPy** - Numerical computation
- **Shapely** - Geofencing geometry
- **Matplotlib** - Visualization
- **pytest** - Unit testing

## Running Individual Components

```bash
# Run aircraft mission only
python main.py --mission aircraft

# Run spacecraft mission only
python main.py --mission spacecraft

# Run unit tests
python validation/test_core.py

# Run aircraft validation only
python validation/aircraft_validation.py

# Run spacecraft validation only
python validation/spacecraft_validation.py
```

## Validation & Robustness

### Aircraft
- ✅ Monte-Carlo wind uncertainty (100 trials, >95% success)
- ✅ Zero constraint violations (geofence, altitude, energy, turn rate)
- ✅ Performance metrics (time, distance, energy efficiency)

### Spacecraft
- ✅ Schedule feasibility (no overlaps, constraints satisfied)
- ✅ Mission value optimization (priority-weighted observations)
- ✅ Stress testing (limited stations, high priority, short missions)

## License

MIT License - See LICENSE file for details

## Contact

For questions about this submission: [Your contact info]

---

**AeroHack 2026 Submission** | Built with Python, OR-Tools, and systems-level thinking
