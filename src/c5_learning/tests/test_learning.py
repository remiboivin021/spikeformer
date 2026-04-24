"""@file test_learning.py

@brief Tests for C5-Learning module components.

@details
Unit tests for Trainer, ExperienceBuffer, ModelValidator,
and PromotionGate classes.
"""

import pytest
import numpy as np
from src.c5_learning import (
    Trainer,
    ExperienceBuffer,
    ModelValidator,
    PromotionGate,
)


class TestExperienceBuffer:
    """Test cases for ExperienceBuffer class."""

    def test_buffer_initialization(self):
        """Test experience buffer can be created."""
        buffer = ExperienceBuffer(max_capacity=100)
        assert buffer.size() == 0
        assert buffer.is_empty()

    def test_add_experience(self):
        """Test adding experience to buffer."""
        buffer = ExperienceBuffer(max_capacity=100)
        buffer.add(
            state=np.array([1, 2]),
            action="test",
            reward=1.0,
            next_state=np.array([2, 3]),
            done=False,
        )
        assert buffer.size() == 1

    def test_get_batch(self):
        """Test batch retrieval."""
        buffer = ExperienceBuffer(max_capacity=100)
        for i in range(50):
            buffer.add(
                state=i, action="test", reward=float(i), next_state=i + 1, done=False
            )

        batch = buffer.get_batch(10)
        assert len(batch) == 10

    def test_get_batch_insufficient(self):
        """Test batch retrieval fails with insufficient data."""
        buffer = ExperienceBuffer(max_capacity=100)
        buffer.add(state=1, action="test", reward=1.0, next_state=2, done=False)

        with pytest.raises(ValueError):
            buffer.get_batch(10)

    def test_capacity_limit(self):
        """Test buffer respects capacity."""
        buffer = ExperienceBuffer(max_capacity=5)
        for i in range(10):
            buffer.add(state=i, action="test", reward=1.0, next_state=i + 1, done=False)

        assert buffer.size() == 5


class TestModelValidator:
    """Test cases for ModelValidator class."""

    def test_validator_initialization(self):
        """Test model validator can be created."""
        validator = ModelValidator()
        assert validator.min_accuracy == 0.8
        assert validator.safety_checks_enabled is True

    def test_validate_candidate(self):
        """Test candidate validation."""
        validator = ModelValidator()
        model = {"weights": np.random.randn(10, 10)}
        result = validator.validate_candidate(model)
        assert isinstance(result, bool)

    def test_validate_none_model(self):
        """Test validation fails for None model."""
        validator = ModelValidator()
        with pytest.raises(ValueError):
            validator.validate_candidate(None)

    def test_get_validation_report(self):
        """Test validation report retrieval."""
        validator = ModelValidator()
        validator.validate_candidate({"test": "model"})
        report = validator.get_validation_report()
        assert "passed" in report


class TestPromotionGate:
    """Test cases for PromotionGate class."""

    def test_gate_initialization(self):
        """Test promotion gate can be created."""
        gate = PromotionGate()
        assert gate.stability_threshold == 0.05
        assert gate.retention_threshold == 5

    def test_should_promote_retention(self):
        """Test promotion fails without retention."""
        gate = PromotionGate(retention_threshold=10)
        results = {"epochs_completed": 5, "validation_scores": [0.9, 0.9, 0.9]}
        assert gate.should_promote(results) is False

    def test_should_promote_stability(self):
        """Test promotion fails without stability."""
        gate = PromotionGate(stability_threshold=0.01)
        results = {"epochs_completed": 10, "validation_scores": [0.5, 0.9, 0.8]}
        assert gate.should_promote(results) is False

    def test_should_promote_success(self):
        """Test promotion succeeds with good metrics."""
        gate = PromotionGate()
        results = {"epochs_completed": 10, "validation_scores": [0.9, 0.89, 0.88]}
        assert gate.should_promote(results) is True

    def test_reset(self):
        """Test gate reset."""
        gate = PromotionGate()
        gate.update_baseline(0.9)
        gate.reset()
        assert gate.baseline_score is None


class TestTrainer:
    """Test cases for Trainer class."""

    def test_trainer_initialization(self):
        """Test trainer can be created."""
        trainer = Trainer()
        assert trainer.batch_size == 32
        assert trainer.learning_rate == 0.001
        assert trainer.num_epochs == 10

    def test_add_experience(self):
        """Test adding experience."""
        trainer = Trainer()
        trainer.add_experience(
            state=np.array([1, 2]),
            action="test",
            reward=1.0,
            next_state=np.array([2, 3]),
            done=False,
        )
        assert trainer.experience_buffer.size() == 1

    def test_train_empty_buffer(self):
        """Test training fails with empty buffer."""
        trainer = Trainer()
        with pytest.raises(RuntimeError):
            trainer.train(model={"test": "model"})

    def test_get_model_version(self):
        """Test model version retrieval."""
        trainer = Trainer()
        assert trainer.get_model_version() == 1

    def test_training_history(self):
        """Test training history tracking."""
        trainer = Trainer()
        trainer.add_experience(
            state=1, action="test", reward=1.0, next_state=2, done=True
        )
        # Training would need proper model implementation
        # This just tests the attribute exists
        assert isinstance(trainer.training_history, list)
