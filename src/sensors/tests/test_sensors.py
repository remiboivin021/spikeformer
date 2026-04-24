"""@file test_sensors.py

@brief Unit tests for sensor modules.
"""

import pytest
import numpy as np
from src.sensors import EventCamera, Lidar, SensorFactory, SensorType


class TestEventCamera:
    """Tests for EventCamera sensor."""

    def test_initialization(self):
        """Test sensor initialization."""
        camera = EventCamera()
        assert camera.sensor_type == "event_camera"
        assert camera.is_active is True

    def test_perceive_returns_embedding(self):
        """Test perceive returns proper embedding."""
        camera = EventCamera()
        embedding = camera.perceive({"duration": 10.0})
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (64,)  # 8x8 grid

    def test_validate_input(self):
        """Test input validation."""
        camera = EventCamera()
        assert camera.validate_input(None) is True
        assert camera.validate_input({"duration": 10.0}) is True
        assert camera.validate_input({"duration": -1.0}) is False

    def test_reset(self):
        """Test sensor reset."""
        camera = EventCamera()
        camera.perceive({"duration": 10.0})
        camera.reset()
        assert camera.timestamp == 0.0


class TestLidar:
    """Tests for Lidar sensor."""

    def test_initialization(self):
        """Test sensor initialization."""
        lidar = Lidar()
        assert lidar.sensor_type == "lidar"
        assert lidar.max_range == 10.0

    def test_perceive_returns_embedding(self):
        """Test perceive returns proper embedding."""
        lidar = Lidar()
        embedding = lidar.perceive({"num_points": 3})
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (64,)

    def test_scan_count(self):
        """Test scan counter."""
        lidar = Lidar()
        assert lidar.scan_count == 0
        lidar.perceive()
        assert lidar.scan_count == 1


class TestSensorFactory:
    """Tests for SensorFactory."""

    def test_create_event_camera(self):
        """Test sensor creation."""
        factory = SensorFactory()
        sensor = factory.create_sensor(SensorType.EVENT_CAMERA)
        assert isinstance(sensor, EventCamera)

    def test_create_lidar(self):
        """Test lidar creation."""
        factory = SensorFactory()
        sensor = factory.create_sensor(SensorType.LIDAR)
        assert isinstance(sensor, Lidar)

    def test_create_all_sensors(self):
        """Test batch sensor creation."""
        factory = SensorFactory()
        sensors = factory.create_all_sensors()
        assert SensorType.EVENT_CAMERA in sensors
        assert SensorType.LIDAR in sensors
