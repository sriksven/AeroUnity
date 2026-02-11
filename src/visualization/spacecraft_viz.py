"""
Spacecraft mission visualization.

This module creates plots for orbit ground tracks, schedules,
contact windows, and mission value timelines.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path


class SpacecraftVisualizer:
    """Visualize spacecraft mission planning results."""
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def plot_schedule_gantt(self, schedule: List[Dict[str, Any]],
                           save_name: str = "spacecraft_schedule_gantt.png"):
        """
        Plot Gantt chart of mission schedule.
        
        Args:
            schedule: Mission schedule list
            save_name: Output filename
        """
        if not schedule:
            print("⚠ No schedule data to plot")
            return
            
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Separate observations and downlinks
        observations = [s for s in schedule if s['type'] == 'observation']
        downlinks = [s for s in schedule if s['type'] == 'downlink']
        
        y_pos = 0
        colors = {'observation': 'steelblue', 'downlink': 'orangered'}
        
        # Plot observations
        for obs in observations:
            start = obs['start_time']
            duration = (obs['end_time'] - obs['start_time']).total_seconds() / 60.0  # minutes
            ax.barh(y_pos, duration, left=mdates.date2num(start), height=0.8,
                   color=colors['observation'], alpha=0.7, edgecolor='black')
            y_pos += 1
        
        # Plot downlinks
        for dl in downlinks:
            start = dl['start_time']
            duration = (dl['end_time'] - dl['start_time']).total_seconds() / 60.0
            ax.barh(y_pos, duration, left=mdates.date2num(start), height=0.8,
                   color=colors['downlink'], alpha=0.7, edgecolor='black')
            y_pos += 1
        
        # Format x-axis as dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=12))
        plt.xticks(rotation=45, ha='right')
        
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Activity Index', fontsize=12)
        ax.set_title('Mission Schedule (Gantt Chart)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=colors['observation'], alpha=0.7, edgecolor='black', label='Observation'),
            Patch(facecolor=colors['downlink'], alpha=0.7, edgecolor='black', label='Downlink')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Saved schedule Gantt chart to {save_name}")
    
    def plot_activity_timeline(self, schedule: List[Dict[str, Any]],
                              save_name: str = "spacecraft_timeline.png"):
        """
        Plot timeline showing observation and downlink activities.
        
        Args:
            schedule: Mission schedule list
            save_name: Output filename
        """
        if not schedule:
            print("⚠ No schedule data to plot")
            return
            
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Extract times and types
        times = []
        types = []
        
        for activity in schedule:
            times.append(activity['start_time'])
            types.append(1 if activity['type'] == 'observation' else 2)
        
        # Plot as scatter
        colors = ['steelblue' if t == 1 else 'orangered' for t in types]
        ax.scatter(times, types, c=colors, s=100, alpha=0.7, edgecolors='black', linewidth=1.5)
        
        # Format
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        plt.xticks(rotation=45, ha='right')
        
        ax.set_yticks([1, 2])
        ax.set_yticklabels(['Observation', 'Downlink'])
        ax.set_xlabel('Date', fontsize=12)
        ax.set_title('Activity Timeline (7-Day Mission)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Saved activity timeline to {save_name}")
    
    def plot_mission_statistics(self, stats: Dict[str, Any],
                                save_name: str = "spacecraft_statistics.png"):
        """
        Plot mission statistics as bar charts.
        
        Args:
            stats: Statistics dictionary
            save_name: Output filename
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # Activity counts
        obs_count = stats.get('num_observations', 0)
        dl_count = stats.get('num_downlinks', 0)
        axes[0].bar(['Observations', 'Downlinks'], [obs_count, dl_count],
                   color=['steelblue', 'orangered'], alpha=0.7, edgecolor='black')
        axes[0].set_ylabel('Count', fontsize=11)
        axes[0].set_title('Activity Counts', fontsize=12, fontweight='bold')
        axes[0].grid(True, alpha=0.3, axis='y')
        
        # Utilization
        util = stats.get('utilization_percent', 0)
        axes[1].bar(['Utilization'], [util], color='forestgreen', alpha=0.7, edgecolor='black')
        axes[1].set_ylabel('Percentage (%)', fontsize=11)
        axes[1].set_title('Schedule Utilization', fontsize=12, fontweight='bold')
        axes[1].set_ylim([0, 100])
        axes[1].grid(True, alpha=0.3, axis='y')
        
        # Duration
        duration = stats.get('total_duration_hours', 0)
        active = stats.get('active_time_hours', 0)
        axes[2].bar(['Total', 'Active'], [duration, active],
                   color=['gray', 'purple'], alpha=0.7, edgecolor='black')
        axes[2].set_ylabel('Hours', fontsize=11)
        axes[2].set_title('Mission Duration', fontsize=12, fontweight='bold')
        axes[2].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Saved mission statistics to {save_name}")
    
    def plot_target_coverage(self, solution: Dict[str, Any], 
                            all_targets: List[Any],
                            save_name: str = "spacecraft_coverage.png"):
        """
        Plot target coverage map.
        
        Args:
            solution: Mission solution
            all_targets: List of all ground targets
            save_name: Output filename
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Get observed targets
        observed = set()
        for activity in solution.get('schedule', []):
            if activity['type'] == 'observation':
                observed.add(activity['target_id'])
        
        # Plot all targets
        for target in all_targets:
            color = 'green' if target.name in observed else 'red'
            marker = 'o' if target.name in observed else 'x'
            label = 'Observed' if target.name in observed and len(observed) == 1 else ('Not Observed' if target.name not in observed and len(all_targets) - len(observed) == 1 else '')
            
            ax.scatter(target.longitude, target.latitude, c=color, s=200, 
                      marker=marker, alpha=0.7, edgecolors='black', linewidth=2,
                      label=label)
            ax.annotate(target.name, (target.longitude, target.latitude),
                       xytext=(5, 5), textcoords='offset points', fontsize=9)
        
        ax.set_xlabel('Longitude (°)', fontsize=12)
        ax.set_ylabel('Latitude (°)', fontsize=12)
        ax.set_title(f'Ground Target Coverage ({len(observed)}/{len(all_targets)} observed)', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Add legend
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(loc='best')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Saved target coverage map to {save_name}")
