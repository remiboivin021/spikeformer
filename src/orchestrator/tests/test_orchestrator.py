"""@file test_orchestrator.py

@brief Tests for Orchestrator module components.

@details
Unit tests for CognitiveOrchestrator, Router, and StateManager classes.
"""

import pytest
import numpy as np
from src.orchestrator import CognitiveOrchestrator, Router, StateManager
from interfaces.contracts import DecisionContract


class TestRouter:
    """Test cases for Router class."""

    def test_router_initialization(self):
        """Test router can be created."""
        router = Router()
        assert router.enable_safe_mode_bypass is True

    def test_route_to_next(self):
        """Test sequential routing."""
        router = Router()
        first_stage = router.get_stage()
        next_stage = router.route_to_next()
        assert next_stage.value == "c2_adapter"

    def test_route_to_safe_mode(self):
        """Test safe mode routing."""
        router = Router()
        safe_stage = router.route_to_safe_mode()
        assert safe_stage.value == "safe_mode"

    def test_reset(self):
        """Test router reset."""
        router = Router()
        router.route_to_next()
        router.route_to_safe_mode()
        router.reset()
        assert router.get_stage().value == "c1_snn"
        assert len(router.get_route_history()) == 0


class TestStateManager:
    """Test cases for StateManager class."""

    def test_state_manager_initialization(self):
        """Test state manager can be created."""
        state_mgr = StateManager()
        stats = state_mgr.get_stats()
        assert stats["total_processed"] == 0

    def test_record_processing(self):
        """Test processing record."""
        state_mgr = StateManager()
        state_mgr.record_processing(10.5, "stop", {"test": "data"})
        stats = state_mgr.get_stats()
        assert stats["total_processed"] == 1

    def test_record_error(self):
        """Test error record."""
        state_mgr = StateManager()
        state_mgr.record_error("TestError", "Test message")
        errors = state_mgr.get_errors()
        assert len(errors) == 1
        assert errors[0]["error_type"] == "TestError"

    def test_record_safe_mode(self):
        """Test safe mode activation record."""
        state_mgr = StateManager()
        state_mgr.record_safe_mode()
        stats = state_mgr.get_stats()
        assert stats["safe_mode_activations"] == 1

    def test_get_history(self):
        """Test history retrieval."""
        state_mgr = StateManager()
        for i in range(5):
            state_mgr.record_processing(float(i))

        history = state_mgr.get_history(limit=3)
        assert len(history) == 3

    def test_reset(self):
        """Test state manager reset."""
        state_mgr = StateManager()
        state_mgr.record_processing(10.0)
        state_mgr.reset()
        stats = state_mgr.get_stats()
        assert stats["total_processed"] == 0


class TestCognitiveOrchestrator:
    """Test cases for CognitiveOrchestrator class."""

    def test_orchestrator_initialization(self):
        """Test orchestrator can be created."""
        orchestrator = CognitiveOrchestrator()
        state = orchestrator.get_state()
        assert state["c1_snn"]["num_neurons"] == 64

    def test_process_empty_events(self):
        """Test processing empty events."""
        orchestrator = CognitiveOrchestrator()
        decision = orchestrator.process([])
        assert isinstance(decision, DecisionContract)

    def test_process_valid_events(self):
        """Test processing valid events."""
        orchestrator = CognitiveOrchestrator()
        events = [
            (0.0, 0, 1),
            (1.0, 1, 1),
            (2.0, 2, 0),
        ]
        decision = orchestrator.process(events)
        assert isinstance(decision, DecisionContract)
        assert decision.action is not None

    def test_process_with_context(self):
        """Test processing with context."""
        orchestrator = CognitiveOrchestrator()
        events = [(0.0, 0, 1)]
        context = {"velocity": 50.0, "proximity": 5.0}
        decision = orchestrator.process(events, context=context)
        assert isinstance(decision, DecisionContract)

    def test_process_batch(self):
        """Test batch processing."""
        orchestrator = CognitiveOrchestrator()
        batch = [
            [(0.0, 0, 1)],
            [(0.0, 1, 1), (1.0, 2, 0)],
        ]
        decisions = orchestrator.process_batch(batch)
        assert len(decisions) == 2
        for d in decisions:
            assert isinstance(d, DecisionContract)

    def test_get_state(self):
        """Test state retrieval."""
        orchestrator = CognitiveOrchestrator()
        state = orchestrator.get_state()
        assert "c1_snn" in state
        assert "c2_adapter" in state
        assert "c3_transformer" in state
        assert "c4_policy" in state

    def test_reset(self):
        """Test orchestrator reset."""
        orchestrator = CognitiveOrchestrator()
        events = [(0.0, 0, 1)]
        orchestrator.process(events)
        orchestrator.reset()
        # Check that neurons are reset
        assert all(n.membrane_potential == 0.0 for n in orchestrator.neurons)
