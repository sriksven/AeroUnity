"""
Aircraft mission visualization.

This module creates plots for flight paths, geofences, wind fields,
and performance metrics.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from typing import List, Dict, Any
from pathlib import Path


class AircraftVisualizer:
    """Visualize aircraft mission planning results."""
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def plot_flight_path(self, solution: Dict[str, Any], 
                        no_fly_zones: List[Any] = None,
                        save_name: str = "aircraft_flight_path.png"):
        """
        Plot 2D flight path with waypoints and geofences.
        
        Args:
            solution: Mission solution from planner
            no_fly_zones: List of Shapely Polygon objects
            save_name: Output filename
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        path = solution['path']
        
        # Extract x, y coordinates
        x_coords = [p[0] for p in path]
        y_coords = [p[1] for p in path]
        
        # Plot path
        ax.plot(x_coords, y_coords, 'b-', linewidth=2, label='Flight Path', zorder=3)
        
        # Plot waypoints
        ax.scatter(x_coords, y_coords, c='red', s=100, zorder=4, label='Waypoints')
        
        # Mark start and end
        ax.scatter(x_coords[0], y_coords[0], c='green', s=200, marker='s', 
                  zorder=5, label='Start')
        ax.scatter(x_coords[-1], y_coords[-1], c='purple', s=200, marker='*', 
                  zorder=5, label='End')
        
        # Plot no-fly zones
        if no_fly_zones:
            for i, zone in enumerate(no_fly_zones):
                coords = list(zone.exterior.coords)
                polygon = MplPolygon(coords, alpha=0.3, facecolor='red', 
                                   edgecolor='darkred', linewidth=2,
                                   label='No-Fly Zone' if i == 0 else '')
                ax.add_patch(polygon)
        
        # Add waypoint numbers
        for i, (x, y) in enumerate(zip(x_coords, y_coords)):
            ax.annotate(f'{i}', (x, y), xytext=(5, 5), textcoords='offset points',
                       fontsize=9, fontweight='bold')
        
        ax.set_xlabel('X Position (m)', fontsize=12)
        ax.set_ylabel('Y Position (m)', fontsize=12)
        ax.set_title('Aircraft Flight Path with Geofencing', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        ax.set_aspect('equal')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Saved flight path plot to {save_name}")
    
    def plot_altitude_profile(self, solution: Dict[str, Any],
                             save_name: str = "aircraft_altitude_profile.png"):
        """
        Plot altitude profile over time.
        
        Args:
            solution: Mission solution from planner
            save_name: Output filename
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        path = solution['path']
        times = solution.get('times', list(range(len(path))))
        
        altitudes = [p[2] for p in path]
        
        ax.plot(times, altitudes, 'b-', linewidth=2, marker='o', markersize=6)
        
        ax.set_xlabel('Time (s)', fontsize=12)
        ax.set_ylabel('Altitude (m)', fontsize=12)
        ax.set_title('Altitude Profile', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Add altitude bounds if available
        ax.axhline(y=50, color='r', linestyle='--', alpha=0.5, label='Min Altitude (50m)')
        ax.axhline(y=500, color='r', linestyle='--', alpha=0.5, label='Max Altitude (500m)')
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Saved altitude profile to {save_name}")
    
    def plot_performance_metrics(self, metrics: Dict[str, Any],
                                save_name: str = "aircraft_performance.png"):
        """
        Plot performance metrics as bar chart.
        
        Args:
            metrics: Performance metrics dictionary
            save_name: Output filename
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # Time
        axes[0].bar(['Mission Time'], [metrics.get('total_time_min', 0)], color='steelblue')
        axes[0].set_ylabel('Time (minutes)', fontsize=11)
        axes[0].set_title('Mission Duration', fontsize=12, fontweight='bold')
        axes[0].grid(True, alpha=0.3, axis='y')
        
        # Distance
        axes[1].bar(['Distance'], [metrics.get('total_distance_km', 0)], color='forestgreen')
        axes[1].set_ylabel('Distance (km)', fontsize=11)
        axes[1].set_title('Total Distance', fontsize=12, fontweight='bold')
        axes[1].grid(True, alpha=0.3, axis='y')
        
        # Energy
        axes[2].bar(['Energy'], [metrics.get('total_energy_wh', 0)], color='orangered')
        axes[2].set_ylabel('Energy (Wh)', fontsize=11)
        axes[2].set_title('Energy Consumption', fontsize=12, fontweight='bold')
        axes[2].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Saved performance metrics to {save_name}")
    
    def plot_monte_carlo_results(self, mc_results: Dict[str, Any],
                                save_name: str = "aircraft_monte_carlo.png"):
        """
        Plot Monte-Carlo simulation results.
        
        Args:
            mc_results: Monte-Carlo results dictionary
            save_name: Output filename
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        times = mc_results.get('times', [])
        energies = mc_results.get('energies', [])
        
        if not times:
            print("⚠ No Monte-Carlo data to plot")
            return
        
        # Time distribution
        axes[0, 0].hist(times, bins=20, color='steelblue', alpha=0.7, edgecolor='black')
        axes[0, 0].axvline(np.mean(times), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(times):.1f}s')
        axes[0, 0].set_xlabel('Mission Time (s)', fontsize=11)
        axes[0, 0].set_ylabel('Frequency', fontsize=11)
        axes[0, 0].set_title('Mission Time Distribution', fontsize=12, fontweight='bold')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Energy distribution
        axes[0, 1].hist(energies, bins=20, color='orangered', alpha=0.7, edgecolor='black')
        axes[0, 1].axvline(np.mean(energies), color='blue', linestyle='--', linewidth=2, label=f'Mean: {np.mean(energies):.1f}J')
        axes[0, 1].set_xlabel('Energy Consumption (J)', fontsize=11)
        axes[0, 1].set_ylabel('Frequency', fontsize=11)
        axes[0, 1].set_title('Energy Distribution', fontsize=12, fontweight='bold')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Success rate
        success_rate = mc_results.get('success_rate', 0) * 100
        failure_rate = 100 - success_rate
        axes[1, 0].pie([success_rate, failure_rate], labels=['Success', 'Failure'],
                      colors=['green', 'red'], autopct='%1.1f%%', startangle=90)
        axes[1, 0].set_title(f'Success Rate: {success_rate:.1f}%', fontsize=12, fontweight='bold')
        
        # Time vs Energy scatter
        axes[1, 1].scatter(times, energies, alpha=0.6, c='purple', s=50)
        axes[1, 1].set_xlabel('Mission Time (s)', fontsize=11)
        axes[1, 1].set_ylabel('Energy Consumption (J)', fontsize=11)
        axes[1, 1].set_title('Time vs Energy Trade-off', fontsize=12, fontweight='bold')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.suptitle(f'Monte-Carlo Wind Uncertainty Analysis ({len(times)} trials)', 
                    fontsize=14, fontweight='bold', y=1.00)
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Saved Monte-Carlo results to {save_name}")
