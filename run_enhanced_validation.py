"""
Enhanced AeroUnity validation pipeline with edge case testing.

Runs comprehensive validation including:
- Standard validation suite
- Edge case testing (25+ scenarios)
- Stress testing
- Failure mode analysis
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from run_complete_validation import run_complete_pipeline
from validation.edge_case_tests import run_all_edge_cases


def run_enhanced_validation():
    """Run complete validation including edge cases."""
    
    print("\n" + "="*90)
    print(" "*15 + "AEROUNITY - ENHANCED VALIDATION WITH EDGE CASES")
    print("="*90)
    print("\nThis will run:")
    print("  1. Standard validation suite (Monte-Carlo, constraints, performance)")
    print("  2. Edge case testing (25+ scenarios)")
    print("  3. Stress testing (extreme conditions)")
    print("  4. Failure mode analysis")
    print("\nEstimated runtime: 3-5 minutes\n")
    
    # Run standard validation
    print("\n" + "█"*90)
    print(" "*25 + "PHASE 1: STANDARD VALIDATION")
    print("█"*90)
    standard_results = run_complete_pipeline()
    
    # Run edge case testing
    print("\n" + "█"*90)
    print(" "*25 + "PHASE 2: EDGE CASE TESTING")
    print("█"*90)
    edge_case_results = run_all_edge_cases()
    
    # Final summary
    print("\n" + "="*90)
    print(" "*30 + "FINAL SUMMARY")
    print("="*90)
    
    print("\nSTANDARD VALIDATION:")
    print(f"   • Aircraft Monte-Carlo: {standard_results['aircraft']['monte_carlo_success_rate']*100:.1f}% success")
    print(f"   • Spacecraft Schedule: {standard_results['spacecraft']['num_observations']} observations")
    
    print("\nEDGE CASE TESTING:")
    print(f"   • Extreme wind scenarios: {len(edge_case_results['extreme_wind'])} tested")
    print(f"   • Battery stress tests: {len(edge_case_results['battery_stress'])} tested")
    print(f"   • Geofencing complexity: {len(edge_case_results['complex_geofencing'])} tested")
    print(f"   • Orbit configurations: {len(edge_case_results['orbit_edge_cases'])} tested")
    print(f"   • Failure modes: {len(edge_case_results['failure_modes'])} tested")
    
    # Count total scenarios
    total_scenarios = (
        100 +  # Monte-Carlo trials
        len(edge_case_results['extreme_wind']) +
        len(edge_case_results['battery_stress']) +
        len(edge_case_results['complex_geofencing']) +
        len(edge_case_results['orbit_edge_cases']) +
        len(edge_case_results['failure_modes']) +
        3  # Spacecraft stress tests
    )
    
    print(f"\nTOTAL TEST SCENARIOS: {total_scenarios}")
    print("\nALL RESULTS SAVED TO:")
    print("   • outputs/validation/ (standard tests)")
    print("   • outputs/edge_cases/ (edge case tests)")
    print("   • outputs/*.png (8 visualization plots)")
    
    print("\n" + "="*90)
    print(" "*20 + "ENHANCED VALIDATION COMPLETE! ")
    print("="*90 + "\n")
    
    return {
        'standard': standard_results,
        'edge_cases': edge_case_results,
        'total_scenarios': total_scenarios
    }


if __name__ == "__main__":
    run_enhanced_validation()
