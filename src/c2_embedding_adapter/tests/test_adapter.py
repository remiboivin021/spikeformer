"""@file test_adapter.py

@brief Tests for C2-Embedding Adapter module components.

@details
Unit tests for EmbeddingAdapter and EmbeddingValidator classes.
"""

import pytest
import numpy as np
from src.c2_embedding_adapter import EmbeddingAdapter, EmbeddingValidator
from interfaces.contracts import EmbeddingContract
from interfaces.exceptions import ContractValidationError


class TestEmbeddingAdapter:
    """Test cases for EmbeddingAdapter class."""

    def test_adapter_initialization(self):
        """Test adapter can be created with default parameters."""
        adapter = EmbeddingAdapter()
        assert adapter.output_dim == 256
        assert adapter.normalize is True

    def test_adapt_valid_embedding(self):
        """Test adapting valid embedding."""
        adapter = EmbeddingAdapter(output_dim=256)
        embedding = np.random.randn(256).astype(np.float32)
        contract = adapter.adapt(embedding, validate=False)
        assert isinstance(contract, EmbeddingContract)
        assert contract.version == "v1"

    def test_adapt_normalization(self):
        """Test embedding is normalized."""
        adapter = EmbeddingAdapter(normalize=True)
        embedding = np.random.randn(256).astype(np.float32) * 5.0
        contract = adapter.adapt(embedding, validate=False)
        norm = np.linalg.norm(contract.embedding)
        assert abs(norm - 1.0) < 0.01

    def test_adapt_dimension_mismatch(self):
        """Test error on dimension mismatch."""
        adapter = EmbeddingAdapter(output_dim=256)
        embedding = np.random.randn(128).astype(np.float32)
        with pytest.raises(ValueError):
            adapter.adapt(embedding, validate=False)

    def test_adapt_clamping(self):
        """Test embedding value clamping."""
        adapter = EmbeddingAdapter(clamp_range=(-1.0, 1.0), normalize=False)
        embedding = np.array([2.0, 0.5, -1.5], dtype=np.float32)
        contract = adapter.adapt(embedding, validate=False)
        assert np.all(contract.embedding >= -1.0)
        assert np.all(contract.embedding <= 1.0)

    def test_adapt_batch(self):
        """Test batch adaptation."""
        adapter = EmbeddingAdapter(output_dim=256)
        embeddings = np.random.randn(4, 256).astype(np.float32)
        contracts = adapter.adapt_batch(embeddings, validate=False)
        assert len(contracts) == 4
        for c in contracts:
            assert isinstance(c, EmbeddingContract)


class TestEmbeddingValidator:
    """Test cases for EmbeddingValidator class."""

    def test_validator_initialization(self):
        """Test validator can be created."""
        validator = EmbeddingValidator()
        assert validator.max_norm == 2.0

    def test_validate_valid_contract(self):
        """Test validation passes for valid contract."""
        validator = EmbeddingValidator()
        embedding = np.random.randn(256).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)
        contract = EmbeddingContract(version="v1", embedding=embedding, metadata={})
        validator.validate(contract)

    def test_validate_missing_version(self):
        """Test validation fails for missing version."""
        validator = EmbeddingValidator()
        embedding = np.random.randn(256).astype(np.float32)
        contract = EmbeddingContract(version="", embedding=embedding, metadata={})
        with pytest.raises(ContractValidationError):
            validator.validate(contract)

    def test_validate_wrong_version(self):
        """Test validation fails for wrong version."""
        validator = EmbeddingValidator()
        embedding = np.random.randn(256).astype(np.float32)
        contract = EmbeddingContract(version="v2", embedding=embedding, metadata={})
        with pytest.raises(ContractValidationError):
            validator.validate(contract)

    def test_validate_nan_embedding(self):
        """Test validation fails for NaN embedding."""
        validator = EmbeddingValidator()
        embedding = np.array([np.nan] * 256, dtype=np.float32)
        contract = EmbeddingContract(version="v1", embedding=embedding, metadata={})
        with pytest.raises(ContractValidationError):
            validator.validate(contract)

    def test_validate_inf_embedding(self):
        """Test validation fails for Inf embedding."""
        validator = EmbeddingValidator()
        embedding = np.array([np.inf] * 256, dtype=np.float32)
        contract = EmbeddingContract(version="v1", embedding=embedding, metadata={})
        with pytest.raises(ContractValidationError):
            validator.validate(contract)

    def test_validate_raw_valid(self):
        """Test raw validation with valid embedding."""
        validator = EmbeddingValidator()
        embedding = np.random.randn(256).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)
        assert validator.validate_raw(embedding) is True

    def test_validate_raw_invalid(self):
        """Test raw validation with invalid embedding."""
        validator = EmbeddingValidator()
        embedding = np.array([np.nan] * 256, dtype=np.float32)
        assert validator.validate_raw(embedding) is False
