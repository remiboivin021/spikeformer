"""@file test_policy.py

@brief Tests for C4-Policy module components.

@details
Unit tests for PolicyEngine, SafetyFilters, and SafeMode classes.
"""

import pytest
import numpy as np
from src.c4_policy import PolicyEngine, SafetyFilters, SafeMode
from interfaces.contracts import DecisionContract


class TestSafetyFilters:
    """Test cases for SafetyFilters class."""

    def test_filters_initialization(self):
        """Test safety filters can be created."""
        filters = SafetyFilters()
        assert filters.enabled is True
        assert filters.max_speed == 100.0

    def test_check_action_allowed(self):
        """Test action passes filters."""
        filters = SafetyFilters(enabled=True)
        context = {"velocity": 50.0, "proximity": 5.0}
        assert filters.check_action("stop", context) is True

    def test_check_action_speed_limit(self):
        """Test speed_up blocked at max speed."""
        filters = SafetyFilters(enabled=True)
        filters.set_max_speed(100.0)
        context = {"velocity": 100.0, "proximity": 5.0}
        assert filters.check_action("speed_up", context) is False

    def test_check_action_proximity(self):
        """Test approach blocked when too close."""
        filters = SafetyFilters(enabled=True)
        filters.set_min_proximity(2.0)
        context = {"velocity": 0.0, "proximity": 1.0}
        assert filters.check_action("approach", context) is False

    def test_check_action_forbidden(self):
        """Test forbidden action blocked."""
        filters = SafetyFilters(enabled=True)
        filters.add_forbidden_action("retreat")
        context = {"velocity": 0.0, "proximity": 5.0}
        assert filters.check_action("retreat", context) is False

    def test_disabled_filters(self):
        """Test disabled filters allow all actions."""
        filters = SafetyFilters(enabled=False)
        context = {"velocity": 200.0, "proximity": 0.1}
        assert filters.check_action("speed_up", context) is True


class TestSafeMode:
    """Test cases for SafeMode class."""

    def test_safe_mode_initialization(self):
        """Test safe mode can be created."""
        safe_mode = SafeMode()
        assert safe_mode.default_action == "stop"
        assert safe_mode.override_active is False

    def test_get_safe_action(self):
        """Test default safe action retrieval."""
        safe_mode = SafeMode()
        action = safe_mode.get_safe_action()
        assert action == "stop"

    def test_override_activation(self):
        """Test override activation."""
        safe_mode = SafeMode()
        safe_mode.activate_override("wait")
        assert safe_mode.is_override_active() is True
        assert safe_mode.get_safe_action() == "wait"

    def test_override_deactivation(self):
        """Test override deactivation."""
        safe_mode = SafeMode()
        safe_mode.activate_override("wait")
        safe_mode.deactivate_override()
        assert safe_mode.is_override_active() is False

    def test_get_safe_actions(self):
        """Test safe actions retrieval."""
        safe_mode = SafeMode()
        actions = safe_mode.get_safe_actions()
        assert "stop" in actions
        assert actions["stop"] == 1.0

    def test_add_safe_action(self):
        """Test adding new safe action."""
        safe_mode = SafeMode()
        safe_mode.add_safe_action("custom", 0.6)
        actions = safe_mode.get_safe_actions()
        assert "custom" in actions


class TestPolicyEngine:
    """Test cases for PolicyEngine class."""

    def test_engine_initialization(self):
        """Test policy engine can be created."""
        engine = PolicyEngine()
        assert engine.num_actions == 10
        assert engine.safe_mode_enabled is True

    def test_process_valid_tokens(self):
        """Test processing valid tokens."""
        engine = PolicyEngine()
        tokens = [0, 1, 2]
        decision = engine.process(tokens)
        assert isinstance(decision, DecisionContract)
        assert decision.action in engine.action_map.values()

    def test_process_empty_tokens(self):
        """Test processing empty tokens returns safe fallback."""
        engine = PolicyEngine()
        decision = engine.process([])
        assert decision.metadata["safe_mode_used"] is True

    def test_process_with_logits(self):
        """Test processing with confidence logits."""
        engine = PolicyEngine()
        tokens = [0]
        logits = np.array([5.0, 1.0, 0.5] + [0.0] * 997).astype(np.float32)
        decision = engine.process(tokens, logits)
        assert decision.confidence > 0

    def test_process_low_confidence(self):
        """Test low confidence triggers safe mode."""
        engine = PolicyEngine(safety_threshold=0.8)
        tokens = [0]
        decision = engine.process(tokens)
        assert decision.metadata["safe_mode_used"] is True

    def test_process_unsafe_action(self):
        """Test unsafe action triggers safe mode."""
        engine = PolicyEngine()
        engine.safety_filters.set_max_speed(0.0)
        tokens = [4]  # speed_up
        context = {"velocity": 0.0, "proximity": 5.0}
        decision = engine.process(tokens, context=context)
        assert decision.metadata["safe_mode_used"] is True

    def test_set_action_map(self):
        """Test custom action mapping."""
        engine = PolicyEngine()
        custom_map = {0: "custom_action"}
        engine.set_action_map(custom_map)
        tokens = [0]
        decision = engine.process(tokens)
        assert decision.action == "custom_action"
