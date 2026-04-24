"""@file test_navigation.py

@brief Unit tests for navigation modules.
"""

import pytest
import numpy as np
from src.navigation import RobotState, ObstacleAvoider, AvoidanceDirection


class TestRobotState:
    """Tests for RobotState."""

    def test_initialization(self):
        """Test state initialization."""
        state = RobotState()
        assert state.x == 0.0
        assert state.y == 0.0
        assert state.theta == 0.0

    def test_update_forward(self):
        """Test forward movement."""
        state = RobotState()
        state.update(left_speed=1.0, right_speed=1.0, dt=0.1)
        assert state.x > 0.0  # Moved forward

    def test_update_turn(self):
        """Test turning."""
        state = RobotState()
        initial_theta = state.theta
        state.update(left_speed=-0.5, right_speed=0.5, dt=0.1)
        assert state.theta != initial_theta

    def test_reset(self):
        """Test state reset."""
        state = RobotState()
        state.update(1.0, 1.0, 0.1)
        state.reset()
        assert state.x == 0.0
        assert state.y == 0.0


class TestObstacleAvoider:
    """Tests for ObstacleAvoider."""

    def test_initialization(self):
        """Test avoider initialization."""
        avoider = ObstacleAvoider()
        assert avoider.avoidance_direction == AvoidanceDirection.NONE

    def test_clear_path(self):
        """Test with no obstacles."""
        avoider = ObstacleAvoider()
        # All far distances
        scan = np.ones(64)  # Normalized, far
        direction = avoider.analyze_lidar(scan)
        assert direction == AvoidanceDirection.NONE

    def test_obstacle_front(self):
        """Test obstacle in front."""
        avoider = ObstacleAvoider()
        # Front sectors (indices 28-36 in 64-point scan) close
        scan = np.ones(64) * 0.5  # Medium distance
        scan[28:36] = 0.1  # Close obstacle in front
        direction = avoider.analyze_lidar(scan)
        assert direction in [AvoidanceDirection.LEFT, AvoidanceDirection.RIGHT]

    def test_should_stop(self):
        """Test stop detection."""
        avoider = ObstacleAvoider()
        assert avoider.should_stop() is False
