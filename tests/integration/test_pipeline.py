"""@file test_pipeline.py

@brief Integration tests for complete cognitive pipeline.

@details
Tests the full C1→C2→C3→C4 pipeline from sensor events
to decision outputs.
"""

import pytest
import numpy as np
from src.orchestrator import CognitiveOrchestrator


class TestCognitivePipeline:
    """Integration tests for complete pipeline."""

    def test_full_pipeline(self, orchestrator, sample_events):
        """Test complete C1→C2→C3→C4 pipeline."""
        decision = orchestrator.process(sample_events)

        assert decision is not None
        assert decision.action is not None
        assert 0.0 <= decision.confidence <= 1.0

    def test_empty_events(self, orchestrator):
        """Test pipeline with empty events."""
        decision = orchestrator.process([])

        assert decision is not None
        assert decision.metadata.get("safe_mode_used", False)

    def test_single_event(self, orchestrator):
        """Test pipeline with single event."""
        events = [(0.0, 0, 1)]
        decision = orchestrator.process(events)

        assert decision is not None
        assert decision.action is not None

    def test_batch_processing(self, orchestrator, sample_events):
        """Test batch processing."""
        batch = [sample_events, sample_events[:3]]
        decisions = orchestrator.process_batch(batch)

        assert len(decisions) == 2
        for d in decisions:
            assert d.action is not None

    def test_pipeline_with_context(self, orchestrator, sample_events):
        """Test pipeline with context."""
        context = {"velocity": 50.0, "proximity": 5.0}
        decision = orchestrator.process(sample_events, context=context)

        assert decision is not None

    def test_orchestrator_state(self, orchestrator):
        """Test orchestrator state tracking."""
        state = orchestrator.get_state()

        assert "c1_snn" in state
        assert "c2_adapter" in state
        assert "c3_transformer" in state
        assert "c4_policy" in state

    def test_orchestrator_reset(self, orchestrator, sample_events):
        """Test orchestrator reset."""
        orchestrator.process(sample_events)
        orchestrator.reset()

        for neuron in orchestrator.neurons:
            assert neuron.membrane_potential == 0.0

    def test_high_frequency_events(self, orchestrator):
        """Test with high frequency event stream."""
        events = [(float(i), i % 64, 1) for i in range(1000)]
        decision = orchestrator.process(events)

        assert decision is not None
        assert decision.action is not None

    def test_safe_mode_activation(self, orchestrator):
        """Test safe mode activation on unsafe action."""
        orchestrator.policy_engine.safety_filters.set_max_speed(0.0)

        events = [(0.0, 0, 1)]
        context = {"velocity": 0.0, "proximity": 5.0}
        decision = orchestrator.process(events, context=context)

        assert decision.metadata.get("safe_mode_used", False) is True
