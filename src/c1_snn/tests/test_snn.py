"""@file test_snn.py

@brief Tests for C1-SNN module components.

@details
Unit tests for Neuron, Synapse, EventProcessor, STDPLearner,
and EmbeddingGenerator classes.
"""

import pytest
import numpy as np
from src.c1_snn import (
    Neuron,
    Synapse,
    EventProcessor,
    STDPLearner,
    EmbeddingGenerator,
)


class TestNeuron:
    """Test cases for Neuron class."""

    def test_neuron_initialization(self):
        """Test neuron can be created with default parameters."""
        neuron = Neuron(neuron_id=0)
        assert neuron.neuron_id == 0
        assert neuron.threshold == 1.0
        assert neuron.membrane_potential == 0.0

    def test_neuron_spike_generation(self):
        """Test neuron generates spike when threshold exceeded."""
        neuron = Neuron(neuron_id=0, threshold=1.0)
        spiked = neuron.update(current_input=1.5, dt=1.0, current_time=1.0)
        assert spiked is True
        assert neuron.membrane_potential == 0.0  # Reset after spike

    def test_neuron_no_spike(self):
        """Test neuron does not spike when below threshold."""
        neuron = Neuron(neuron_id=0, threshold=1.0)
        spiked = neuron.update(current_input=0.5, dt=1.0, current_time=1.0)
        assert spiked is False
        assert neuron.membrane_potential > 0

    def test_neuron_refractory_period(self):
        """Test neuron respects refractory period."""
        neuron = Neuron(neuron_id=0, threshold=1.0, refractory_period=5.0)
        neuron.update(current_input=2.0, dt=1.0, current_time=1.0)
        spiked = neuron.update(current_input=2.0, dt=1.0, current_time=2.0)
        assert spiked is False

    def test_neuron_reset(self):
        """Test neuron reset clears state."""
        neuron = Neuron(neuron_id=0)
        neuron.update(current_input=1.5, dt=1.0, current_time=1.0)
        neuron.reset()
        assert neuron.membrane_potential == 0.0
        assert neuron.last_spike_time is None
        assert len(neuron.spike_history) == 0

    def test_neuron_firing_rate(self):
        """Test firing rate calculation."""
        neuron = Neuron(neuron_id=0, threshold=1.0)
        for t in range(10):
            neuron.update(current_input=1.5, dt=1.0, current_time=float(t))

        rate = neuron.get_firing_rate(time_window=20.0)
        assert rate > 0


class TestSynapse:
    """Test cases for Synapse class."""

    def test_synapse_initialization(self):
        """Test synapse can be created."""
        synapse = Synapse(pre_neuron_id=0, post_neuron_id=1)
        assert synapse.pre_neuron_id == 0
        assert synapse.post_neuron_id == 1
        assert synapse.weight == 0.5

    def test_synapse_output_on_spike(self):
        """Test synapse outputs weight on presynaptic spike."""
        synapse = Synapse(pre_neuron_id=0, post_neuron_id=1, weight=0.8)
        output = synapse.compute_output(spike=True, dt=1.0)
        assert output == 0.8

    def test_synapse_output_no_spike(self):
        """Test synapse outputs zero on no presynaptic spike."""
        synapse = Synapse(pre_neuron_id=0, post_neuron_id=1)
        output = synapse.compute_output(spike=False, dt=1.0)
        assert output == 0.0

    def test_synapse_weight_bounds(self):
        """Test synapse enforces weight bounds."""
        synapse = Synapse(
            pre_neuron_id=0, post_neuron_id=1, min_weight=0.1, max_weight=0.9
        )
        synapse.weight = 1.0
        synapse.apply_stdp(pre_spiked=False, post_spiked=True)
        assert synapse.weight >= 0.1
        assert synapse.weight <= 0.9


class TestEventProcessor:
    """Test cases for EventProcessor class."""

    def test_event_processor_initialization(self):
        """Test event processor can be created."""
        processor = EventProcessor(num_channels=64)
        assert processor.num_channels == 64

    def test_process_empty_events(self):
        """Test processing empty event list."""
        processor = EventProcessor(num_channels=64)
        spike_matrix = processor.process_events([])
        assert spike_matrix.shape == (0, 64)

    def test_process_events(self):
        """Test processing valid events."""
        processor = EventProcessor(num_channels=64)
        events = [
            (0.0, 0, 1),
            (1.0, 1, 1),
            (2.0, 0, 0),
        ]
        spike_matrix = processor.process_events(events)
        assert spike_matrix.shape[1] == 64

    def test_process_events_invalid_channel(self):
        """Test processing events with invalid channel."""
        processor = EventProcessor(num_channels=64)
        events = [(0.0, 100, 1)]
        with pytest.raises(ValueError):
            processor.process_events(events)


class TestSTDPLearner:
    """Test cases for STDPLearner class."""

    def test_stdp_learner_initialization(self):
        """Test STDP learner can be created."""
        learner = STDPLearner()
        assert learner.tau_plus == 20.0
        assert learner.tau_minus == 20.0

    def test_compute_weight_change_potentiation(self):
        """Test weight change for potentiation (pre before post)."""
        learner = STDPLearner()
        delta_w = learner.compute_weight_change(delta_t=-5.0)
        assert delta_w > 0

    def test_compute_weight_change_depression(self):
        """Test weight change for depression (post before pre)."""
        learner = STDPLearner()
        delta_w = learner.compute_weight_change(delta_t=5.0)
        assert delta_w < 0


class TestEmbeddingGenerator:
    """Test cases for EmbeddingGenerator class."""

    def test_embedding_generator_initialization(self):
        """Test embedding generator can be created."""
        generator = EmbeddingGenerator()
        assert generator.embedding_dim == 256

    def test_generate_embedding(self):
        """Test embedding generation from neurons."""
        generator = EmbeddingGenerator(embedding_dim=256, num_neurons=64)
        neurons = [Neuron(neuron_id=i) for i in range(64)]

        for i, neuron in enumerate(neurons):
            for t in range(5):
                neuron.update(current_input=1.5, dt=1.0, current_time=float(t * 10 + i))

        embedding = generator.generate_embedding(neurons)
        assert embedding.shape == (256,)
        assert np.abs(np.linalg.norm(embedding) - 1.0) < 0.01

    def test_generate_embedding_wrong_neuron_count(self):
        """Test embedding generation with wrong neuron count."""
        generator = EmbeddingGenerator(num_neurons=64)
        neurons = [Neuron(neuron_id=i) for i in range(32)]

        with pytest.raises(ValueError):
            generator.generate_embedding(neurons)
