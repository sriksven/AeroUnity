"""
Spacecraft orbit mechanics and visibility calculations.

This module implements simplified two-body orbit propagation and
ground target/station visibility calculations for LEO missions.
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


# Earth parameters
EARTH_RADIUS = 6371.0  # km
EARTH_MU = 398600.4418  # km^3/s^2 (gravitational parameter)
EARTH_J2 = 1.08263e-3  # J2 perturbation coefficient
EARTH_ROTATION_RATE = 7.2921159e-5  # rad/s


@dataclass
class OrbitalElements:
    """Classical orbital elements."""
    semi_major_axis: float  # km
    eccentricity: float
    inclination: float  # radians
    raan: float  # Right Ascension of Ascending Node (radians)
    arg_periapsis: float  # Argument of periapsis (radians)
    true_anomaly: float  # radians
    epoch: datetime


@dataclass
class SpacecraftState:
    """Spacecraft state at a point in time."""
    time: datetime
    position_eci: np.ndarray  # [x, y, z] in ECI frame (km)
    velocity_eci: np.ndarray  # [vx, vy, vz] in ECI frame (km/s)
    battery_level: float  # 0.0 to 1.0
    pointing_direction: Optional[np.ndarray] = None  # Unit vector


@dataclass
class GroundTarget:
    """Ground target for observation."""
    name: str
    latitude: float  # degrees
    longitude: float  # degrees
    priority: float  # Science value/priority
    min_elevation: float = 10.0  # Minimum elevation angle (degrees)


@dataclass
class GroundStation:
    """Ground station for downlink."""
    name: str
    latitude: float  # degrees
    longitude: float  # degrees
    min_elevation: float = 5.0  # Minimum elevation angle (degrees)


class OrbitPropagator:
    """Two-body orbit propagator with simplified J2 perturbations."""
    
    def __init__(self, orbital_elements: OrbitalElements):
        self.elements = orbital_elements
        
    def orbital_period(self) -> float:
        """Compute orbital period in seconds."""
        a = self.elements.semi_major_axis
        return 2 * np.pi * np.sqrt(a**3 / EARTH_MU)
    
    def mean_motion(self) -> float:
        """Compute mean motion in rad/s."""
        return 2 * np.pi / self.orbital_period()
    
    def elements_to_state(self, elements: OrbitalElements) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert orbital elements to position and velocity (ECI frame).
        
        Returns:
            (position_eci, velocity_eci) in km and km/s
        """
        a = elements.semi_major_axis
        e = elements.eccentricity
        i = elements.inclination
        omega = elements.arg_periapsis
        Omega = elements.raan
        nu = elements.true_anomaly
        
        # Compute position and velocity in perifocal frame
        p = a * (1 - e**2)
        r_mag = p / (1 + e * np.cos(nu))
        
        r_pqw = r_mag * np.array([np.cos(nu), np.sin(nu), 0.0])
        
        v_pqw = np.sqrt(EARTH_MU / p) * np.array([
            -np.sin(nu),
            e + np.cos(nu),
            0.0
        ])
        
        # Rotation matrix from perifocal to ECI
        R = self.rotation_matrix_pqw_to_eci(omega, i, Omega)
        
        r_eci = R @ r_pqw
        v_eci = R @ v_pqw
        
        return r_eci, v_eci
    
    @staticmethod
    def rotation_matrix_pqw_to_eci(omega: float, i: float, Omega: float) -> np.ndarray:
        """Compute rotation matrix from perifocal to ECI frame."""
        cos_omega = np.cos(omega)
        sin_omega = np.sin(omega)
        cos_i = np.cos(i)
        sin_i = np.sin(i)
        cos_Omega = np.cos(Omega)
        sin_Omega = np.sin(Omega)
        
        R = np.array([
            [cos_Omega * cos_omega - sin_Omega * sin_omega * cos_i,
             -cos_Omega * sin_omega - sin_Omega * cos_omega * cos_i,
             sin_Omega * sin_i],
            [sin_Omega * cos_omega + cos_Omega * sin_omega * cos_i,
             -sin_Omega * sin_omega + cos_Omega * cos_omega * cos_i,
             -cos_Omega * sin_i],
            [sin_omega * sin_i,
             cos_omega * sin_i,
             cos_i]
        ])
        
        return R
    
    def propagate(self, dt: float) -> SpacecraftState:
        """
        Propagate orbit forward by dt seconds (simplified).
        
        Args:
            dt: Time step in seconds
            
        Returns:
            New spacecraft state
        """
        # Simple Keplerian propagation (ignoring perturbations for now)
        n = self.mean_motion()
        
        # Update true anomaly (simplified for circular/near-circular orbits)
        new_nu = self.elements.true_anomaly + n * dt
        new_nu = new_nu % (2 * np.pi)
        
        # Create new elements
        new_elements = OrbitalElements(
            semi_major_axis=self.elements.semi_major_axis,
            eccentricity=self.elements.eccentricity,
            inclination=self.elements.inclination,
            raan=self.elements.raan,
            arg_periapsis=self.elements.arg_periapsis,
            true_anomaly=new_nu,
            epoch=self.elements.epoch + timedelta(seconds=dt)
        )
        
        # Convert to state
        pos, vel = self.elements_to_state(new_elements)
        
        return SpacecraftState(
            time=new_elements.epoch,
            position_eci=pos,
            velocity_eci=vel,
            battery_level=1.0  # Will be updated by power model
        )


class VisibilityCalculator:
    """Calculate visibility between spacecraft and ground locations."""
    
    @staticmethod
    def eci_to_ecef(r_eci: np.ndarray, time: datetime) -> np.ndarray:
        """
        Convert ECI to ECEF coordinates (simplified).
        
        Args:
            r_eci: Position in ECI frame (km)
            time: Current time
            
        Returns:
            Position in ECEF frame (km)
        """
        # Simplified: rotate by Earth rotation angle
        # (ignoring precession, nutation, etc.)
        epoch = datetime(2000, 1, 1, 12, 0, 0)  # J2000
        dt = (time - epoch).total_seconds()
        theta = EARTH_ROTATION_RATE * dt
        
        R_z = np.array([
            [np.cos(theta), np.sin(theta), 0],
            [-np.sin(theta), np.cos(theta), 0],
            [0, 0, 1]
        ])
        
        return R_z @ r_eci
    
    @staticmethod
    def ecef_to_lla(r_ecef: np.ndarray) -> Tuple[float, float, float]:
        """
        Convert ECEF to latitude, longitude, altitude (simplified).
        
        Returns:
            (latitude_deg, longitude_deg, altitude_km)
        """
        x, y, z = r_ecef
        
        lon = np.arctan2(y, x)
        lat = np.arctan2(z, np.sqrt(x**2 + y**2))
        alt = np.linalg.norm(r_ecef) - EARTH_RADIUS
        
        return np.degrees(lat), np.degrees(lon), alt
    
    @staticmethod
    def lla_to_ecef(lat_deg: float, lon_deg: float, alt_km: float = 0.0) -> np.ndarray:
        """Convert latitude, longitude, altitude to ECEF."""
        lat = np.radians(lat_deg)
        lon = np.radians(lon_deg)
        
        r = EARTH_RADIUS + alt_km
        
        x = r * np.cos(lat) * np.cos(lon)
        y = r * np.cos(lat) * np.sin(lon)
        z = r * np.sin(lat)
        
        return np.array([x, y, z])
    
    @staticmethod
    def compute_elevation_angle(sc_pos_ecef: np.ndarray, 
                               ground_pos_ecef: np.ndarray) -> float:
        """
        Compute elevation angle from ground location to spacecraft.
        
        Args:
            sc_pos_ecef: Spacecraft position in ECEF (km)
            ground_pos_ecef: Ground location in ECEF (km)
            
        Returns:
            Elevation angle in degrees
        """
        # Vector from ground to spacecraft
        range_vec = sc_pos_ecef - ground_pos_ecef
        
        # Local vertical (normal to Earth surface at ground location)
        local_vertical = ground_pos_ecef / np.linalg.norm(ground_pos_ecef)
        
        # Elevation angle
        range_mag = np.linalg.norm(range_vec)
        if range_mag < 1e-6:
            return 90.0
            
        sin_el = np.dot(range_vec, local_vertical) / range_mag
        sin_el = np.clip(sin_el, -1.0, 1.0)
        
        return np.degrees(np.arcsin(sin_el))
    
    @staticmethod
    def is_visible(sc_state: SpacecraftState, 
                  ground_location: Tuple[float, float],
                  min_elevation: float = 10.0) -> bool:
        """
        Check if spacecraft is visible from ground location.
        
        Args:
            sc_state: Spacecraft state
            ground_location: (latitude_deg, longitude_deg)
            min_elevation: Minimum elevation angle (degrees)
            
        Returns:
            True if visible
        """
        # Convert spacecraft position to ECEF
        sc_ecef = VisibilityCalculator.eci_to_ecef(
            sc_state.position_eci, sc_state.time
        )
        
        # Convert ground location to ECEF
        ground_ecef = VisibilityCalculator.lla_to_ecef(
            ground_location[0], ground_location[1]
        )
        
        # Compute elevation angle
        elevation = VisibilityCalculator.compute_elevation_angle(
            sc_ecef, ground_ecef
        )
        
        return elevation >= min_elevation
