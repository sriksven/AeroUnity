"""
Spacecraft mission scheduler.

This module provides utilities for generating and managing
time-ordered mission schedules.
"""

import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json


class MissionScheduler:
    """Manages spacecraft mission schedules."""
    
    @staticmethod
    def format_schedule(schedule: List[Dict[str, Any]]) -> str:
        """
        Format schedule as human-readable string.
        
        Args:
            schedule: List of scheduled activities
            
        Returns:
            Formatted string
        """
        if not schedule:
            return "Empty schedule"
            
        lines = ["Mission Schedule", "=" * 60]
        
        for i, item in enumerate(schedule):
            start = item['start_time'].strftime("%Y-%m-%d %H:%M:%S")
            end = item['end_time'].strftime("%Y-%m-%d %H:%M:%S")
            
            if item['type'] == 'observation':
                lines.append(
                    f"{i+1}. OBSERVATION - Target: {item['target_id']}"
                )
                lines.append(f"   Time: {start} to {end}")
                lines.append(f"   Priority: {item['priority']:.2f}")
            elif item['type'] == 'downlink':
                lines.append(
                    f"{i+1}. DOWNLINK - Station: {item['station_id']}"
                )
                lines.append(f"   Time: {start} to {end}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def export_to_csv(schedule: List[Dict[str, Any]], filename: str):
        """Export schedule to CSV file."""
        import csv
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Index', 'Type', 'Target/Station', 'Start Time', 
                           'End Time', 'Duration (s)', 'Priority'])
            
            for i, item in enumerate(schedule):
                duration = (item['end_time'] - item['start_time']).total_seconds()
                
                if item['type'] == 'observation':
                    target = item['target_id']
                    priority = item['priority']
                elif item['type'] == 'downlink':
                    target = item['station_id']
                    priority = 'N/A'
                else:
                    target = 'Unknown'
                    priority = 'N/A'
                
                writer.writerow([
                    i + 1,
                    item['type'],
                    target,
                    item['start_time'].isoformat(),
                    item['end_time'].isoformat(),
                    duration,
                    priority
                ])
    
    @staticmethod
    def export_to_json(schedule: List[Dict[str, Any]], filename: str):
        """Export schedule to JSON file."""
        # Convert datetime objects to ISO format strings
        json_schedule = []
        
        for item in schedule:
            json_item = item.copy()
            json_item['start_time'] = item['start_time'].isoformat()
            json_item['end_time'] = item['end_time'].isoformat()
            
            # Convert numpy arrays to lists
            if 'target_position' in json_item:
                json_item['target_position'] = json_item['target_position'].tolist()
            
            json_schedule.append(json_item)
        
        with open(filename, 'w') as f:
            json.dump(json_schedule, f, indent=2)
    
    @staticmethod
    def compute_statistics(schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute statistics for a schedule.
        
        Returns:
            Dictionary of statistics
        """
        if not schedule:
            return {
                'total_activities': 0,
                'num_observations': 0,
                'num_downlinks': 0,
                'total_duration_hours': 0.0,
                'utilization_percent': 0.0
            }
        
        num_obs = sum(1 for s in schedule if s['type'] == 'observation')
        num_downlinks = sum(1 for s in schedule if s['type'] == 'downlink')
        
        # Compute total active time
        total_active_time = sum(
            (s['end_time'] - s['start_time']).total_seconds()
            for s in schedule
        )
        
        # Compute mission duration
        mission_start = schedule[0]['start_time']
        mission_end = schedule[-1]['end_time']
        mission_duration = (mission_end - mission_start).total_seconds()
        
        utilization = (total_active_time / mission_duration * 100) if mission_duration > 0 else 0.0
        
        return {
            'total_activities': len(schedule),
            'num_observations': num_obs,
            'num_downlinks': num_downlinks,
            'total_duration_hours': mission_duration / 3600.0,
            'active_time_hours': total_active_time / 3600.0,
            'utilization_percent': utilization
        }
