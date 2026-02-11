# AeroUnity: One Framework, Two Worlds

## Inspiration

The aerospace industry faces a fundamental challenge: **mission planning for aircraft and spacecraft are typically treated as completely separate problems**, each with custom tools, different optimization approaches, and isolated codebases. Yet both domains share the same underlying structure—they're constraint satisfaction problems with objectives to optimize.

We were inspired by the question: **What if we could build a single planning engine that works for both?** Not just two separate scripts in one repo, but a truly unified framework where the same constraint representation, objective functions, and solver architecture handle both UAV routing and satellite scheduling.

This is the essence of systems-level thinking in aerospace engineering: recognizing common patterns across domains and building reusable abstractions.

## What It Does

AeroUnity is a unified mission planning framework that solves two distinct aerospace problems using the **same underlying architecture**:

### Aircraft Mission Planning
- Plans optimal routes through waypoints for UAVs/fixed-wing aircraft
- Respects **wind fields** (time-varying and spatial)
- Enforces **energy/endurance limits** with battery consumption modeling
- Handles **maneuver constraints** (turn rate, bank angle, climb rate)
- Avoids **no-fly zones** using polygon geofencing
- Minimizes mission time or energy consumption

### Spacecraft Mission Planning
- Generates **7-day observation schedules** for CubeSat LEO missions
- Computes **ground target visibility windows** using orbit propagation
- Schedules **downlinks** during ground station contact windows
- Enforces **pointing/slew-rate limits** for attitude feasibility
- Manages **power/battery budget** with solar charging model
- Respects **duty cycle constraints** (thermal/operational limits)
- Maximizes total science value delivered

### 🔗 The Unified Core
Both planners extend the same `MissionPlanner` base class and use:
- **Common constraint representation** (hard/soft constraints with violation checking)
- **Common objective functions** (minimize time/energy, maximize value)
- **Google OR-Tools** as the unified solver (routing solver for aircraft, CP-SAT for spacecraft)
- **Shared validation framework** for constraint checking

## How We Built It

### Architecture Design

The key insight was recognizing that both problems are **constraint optimization problems**:

$$\text{minimize/maximize } f(x) \text{ subject to } g_i(x) \leq 0, h_j(x) = 0$$

We designed a three-layer architecture:

```
Layer 1: Core Planning Framework (domain-agnostic)
├── MissionPlanner (abstract base class)
├── Constraint validation system
└── Objective function interface

Layer 2: Domain-Specific Models
├── Aircraft: flight dynamics, wind, energy
└── Spacecraft: orbit mechanics, visibility

Layer 3: Solvers (OR-Tools)
├── Routing solver (aircraft waypoint optimization)
└── CP-SAT solver (spacecraft scheduling)
```

### Technology Stack

- **Python 3** for rapid development and reproducibility
- **Google OR-Tools** for constraint programming and routing
- **NumPy/SciPy** for numerical computation
- **Shapely** for geofencing polygon operations
- **Custom orbit propagator** (simplified two-body mechanics)

### Implementation Highlights

**Aircraft Module:**
- Implemented kinematic flight model with wind integration
- Used OR-Tools routing solver to find optimal waypoint sequences
- Built flight simulator for trajectory validation
- Energy model: $P = P_{\text{base}} + \frac{1}{2} C_d v^3 + mg\dot{h}$

**Spacecraft Module:**
- Two-body orbit propagation: $\ddot{\mathbf{r}} = -\frac{\mu}{r^3}\mathbf{r}$
- Visibility calculation using ECI→ECEF transformations
- Elevation angle: $\sin(\theta_{\text{el}}) = \frac{\mathbf{r}_{\text{sc}} \cdot \mathbf{n}}{|\mathbf{r}_{\text{sc}}|}$
- CP-SAT solver for discrete scheduling decisions

**Validation:**
- Monte-Carlo wind uncertainty testing
- Constraint violation checking (zero tolerance)
- Performance metrics tracking
- Reproducible results pipeline

## Challenges We Faced

### 1. **Abstraction Without Over-Engineering**
Finding the right level of abstraction was critical. Too generic and the framework becomes useless; too specific and it's just two separate tools. We iterated on the `MissionPlanner` interface multiple times to find the sweet spot.

**Solution:** Focus on the constraint-objective-solver pattern as the unifying concept, allowing domain-specific implementations while maintaining architectural consistency.

### 2. **Orbit Mechanics Complexity**
Spacecraft dynamics are inherently more complex than aircraft kinematics. Full orbital propagation with perturbations (J2, drag, solar pressure) would be overkill for a hackathon.

**Solution:** Implemented simplified two-body propagation with clear documentation of assumptions. This is acceptable for LEO missions over 7 days and keeps the code reproducible.

### 3. **Solver Selection**
OR-Tools offers multiple solvers (CP-SAT, routing, linear programming). Choosing the right one for each domain required understanding their strengths.

**Solution:** 
- Aircraft: Routing solver (TSP-like waypoint optimization)
- Spacecraft: CP-SAT (discrete scheduling with complex constraints)

### 4. **Reproducibility**
Making the framework truly reproducible meant managing dependencies, providing clear run instructions, and ensuring deterministic outputs.

**Solution:** 
- Pinned dependency versions in `requirements.txt`
- Single `main.py` entry point with CLI
- Documented expected outputs and runtime
- Seed control for stochastic elements (wind models)

### 5. **Time Constraints**
Building two complete mission planners in 13 days required ruthless prioritization.

**Solution:** 
- Core requirements first (unified framework, both domains working)
- Visualization and polish secondary
- Clear task breakdown and daily milestones

## What We Learned

1. **Systems thinking is powerful:** Recognizing common patterns across domains enables code reuse and cleaner architecture.

2. **Constraint programming is underutilized:** OR-Tools made complex scheduling problems tractable. More aerospace engineers should know about CP-SAT.

3. **Simplification is a skill:** Knowing what to simplify (two-body orbits) vs. what to model accurately (wind effects, energy) is crucial for tractable solutions.

4. **Reproducibility requires discipline:** It's not enough for code to work on your machine—clear instructions and dependency management are essential.

5. **Validation builds confidence:** Monte-Carlo testing and constraint checking aren't optional—they're how you prove your solution actually works.

## What's Next

AeroUnity demonstrates the feasibility of unified aerospace planning, but there's room to grow:

- **Enhanced physics:** J2 perturbations, atmospheric drag for spacecraft
- **Multi-vehicle coordination:** Fleet planning for multiple UAVs or satellite constellations
- **Real-time replanning:** Dynamic updates when conditions change
- **Hardware-in-the-loop:** Integration with actual flight controllers or satellite simulators
- **Machine learning integration:** Learning-based heuristics for faster solving

The framework is designed to be extensible—new constraint types, objectives, and even domains (ground vehicles, maritime) could be added following the same pattern.

---

**AeroUnity proves that with the right abstractions, we can build tools that work across the full spectrum of aerospace missions—from drones to satellites, unified by the power of constraint-based optimization.**
