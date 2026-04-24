"""@file conftest.py

Pytest configuration and fixtures for SNN tests.
"""

import pytest
import numpy as np


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
def sample_tokens():
    """Generate sample tokens for testing."""
    return [0, 1, 2, 3, 4]


@pytest.fixture
def sample_logits():
    """Generate sample logits for testing."""
    np.random.seed(42)
    logits = np.random.randn(1000).astype(np.float32)
    return logits