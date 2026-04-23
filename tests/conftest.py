"""@file conftest.py

@brief Pytest configuration and fixtures.

@details
Provides shared pytest fixtures for SpikeFormer tests.
"""

import pytest
import numpy as np
from src.orchestrator import CognitiveOrchestrator
from src.c1_snn import Neuron, EventProcessor, EmbeddingGenerator
from src.c2_embedding_adapter import EmbeddingAdapter, EmbeddingValidator
from src.c3_transformer import TransformerEngine
from src.c4_policy import PolicyEngine, SafetyFilters, SafeMode


@pytest.fixture
def sample_embedding():
    """Generate sample embedding for testing."""
    np.random.seed(42)
    embedding = np.random.randn(256).astype(np.float32)
    embedding = embedding / np.linalg.norm(embedding)
    return embedding


@pytest.fixture
def sample_events():
    """Generate sample sensor events for testing."""
    return [
        (0.0, 0, 1),
        (1.0, 1, 1),
        (2.0, 2, 0),
        (3.0, 0, 1),
        (4.0, 1, 0),
    ]


@pytest.fixture
def neuron():
    """Create a test neuron."""
    return Neuron(neuron_id=0, threshold=1.0)


@pytest.fixture
def event_processor():
    """Create an event processor."""
    return EventProcessor(num_channels=64)


@pytest.fixture
def embedding_generator():
    """Create an embedding generator."""
    return EmbeddingGenerator(embedding_dim=256, num_neurons=64)


@pytest.fixture
def embedding_adapter():
    """Create an embedding adapter."""
    return EmbeddingAdapter(output_dim=256)


@pytest.fixture
def embedding_validator():
    """Create an embedding validator."""
    return EmbeddingValidator()


@pytest.fixture
def transformer_engine():
    """Create a transformer engine."""
    return TransformerEngine(d_model=256, num_heads=8, num_layers=4)


@pytest.fixture
def policy_engine():
    """Create a policy engine."""
    return PolicyEngine(num_actions=10)


@pytest.fixture
def safety_filters():
    """Create safety filters."""
    return SafetyFilters(enabled=True)


@pytest.fixture
def safe_mode():
    """Create safe mode."""
    return SafeMode()


@pytest.fixture
def orchestrator():
    """Create a cognitive orchestrator."""
    return CognitiveOrchestrator()


@pytest.fixture
def sample_tokens():
    """Generate sample tokens for testing."""
    return [0, 1, 2, 3, 4]


@pytest.fixture
def sample_logits():
    """Generate sample logits for testing."""
    np.random.seed(42)
    logits = np.random.randn(1000).astype(np.float32)
    return logits
