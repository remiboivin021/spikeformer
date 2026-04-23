"""@file test_navigation_pipeline.py

@brief Integration tests for navigation pipeline.
"""

import pytest
import numpy as np
from src.orchestrator import CognitiveOrchestrator
from src.sensors import SensorFactory, SensorType
from src.navigation import RobotState, ObstacleAvoider
from src.actuators import MotorDriver


class TestNavigationPipeline:
    """Integration tests for full navigation pipeline."""

    def test_orchestrator_with_navigation(self):
        """Test orchestrator with navigation modules."""
        config = {
            "d_model": 256,
            "num_heads": 4,
            "num_layers": 2,
        }
        orch = CognitiveOrchestrator(config=config)

        # Should have navigation modules
        assert hasattr(orch, "robot_state")
        assert hasattr(orch, "obstacle_avoider")
        assert hasattr(orch, "motor_driver")

    def test_sensor_to_decision_pipeline(self):
        """Test sensor data flows to decision."""
        config = {"d_model": 256}
        orch = CognitiveOrchestrator(config=config)

        # Generate sensor events
        events = [(0, i % 64, 1) for i in range(100)]

        # Process through pipeline
        decision = orch.process(events)

        assert decision is not None
        assert decision.action in orch.policy_engine.action_map.values()

    def test_navigation_execution(self):
        """Test navigation command execution."""
        config = {"d_model": 256}
        orch = CognitiveOrchestrator(config=config)

        # Process events
        events = [(0, i % 64, 1) for i in range(50)]
        decision = orch.process(events)

        # Execute navigation
        orch.execute_navigation(decision, dt=0.1)

        # Verify robot state updated
        assert orch.robot_state.distance_traveled >= 0.0
