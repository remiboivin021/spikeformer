"""@file test_transformer.py

@brief Tests for C3-Transformer module components.

@details
Unit tests for TransformerEngine, DeterministicAttention,
FeedForward, EmbeddingProjection, and ArgmaxDecoder classes.
"""

import pytest
import numpy as np
from src.c3_transformer import (
    TransformerEngine,
    DeterministicAttention,
    FeedForward,
    EmbeddingProjection,
    ArgmaxDecoder,
)


class TestDeterministicAttention:
    """Test cases for DeterministicAttention class."""

    def test_attention_initialization(self):
        """Test attention can be created."""
        attention = DeterministicAttention(d_model=256, num_heads=8)
        assert attention.d_model == 256
        assert attention.num_heads == 8

    def test_attention_invalid_heads(self):
        """Test error on invalid number of heads."""
        with pytest.raises(ValueError):
            DeterministicAttention(d_model=256, num_heads=7)

    def test_attention_forward(self):
        """Test attention forward pass."""
        attention = DeterministicAttention(d_model=256, num_heads=8)
        x = np.random.randn(1, 10, 256).astype(np.float32)
        output = attention.forward(x, x, x)
        assert output.shape == x.shape

    def test_attention_with_mask(self):
        """Test attention with mask."""
        attention = DeterministicAttention(d_model=256, num_heads=8)
        x = np.random.randn(1, 10, 256).astype(np.float32)
        mask = np.ones((10, 10))
        output = attention.forward(x, x, x, mask)
        assert output.shape == x.shape

    def test_attention_computes_weights(self):
        """Test attention weights computation."""
        attention = DeterministicAttention(d_model=256, num_heads=8)
        x = np.random.randn(1, 10, 256).astype(np.float32)
        output, weights = attention.compute_attention(x, x, x)
        assert weights.shape == (1, 8, 10, 10)


class TestFeedForward:
    """Test cases for FeedForward class."""

    def test_ffn_initialization(self):
        """Test FFN can be created."""
        ffn = FeedForward(d_model=256, d_ff=1024)
        assert ffn.d_model == 256
        assert ffn.d_ff == 1024

    def test_ffn_forward(self):
        """Test FFN forward pass."""
        ffn = FeedForward(d_model=256, d_ff=1024)
        x = np.random.randn(1, 10, 256).astype(np.float32)
        output = ffn.forward(x)
        assert output.shape == x.shape

    def test_gelu_activation(self):
        """Test GELU activation function."""
        ffn = FeedForward()
        x = np.array([-1.0, 0.0, 1.0])
        output = ffn.gelu(x)
        assert output.shape == x.shape


class TestEmbeddingProjection:
    """Test cases for EmbeddingProjection class."""

    def test_projection_initialization(self):
        """Test projection can be created."""
        proj = EmbeddingProjection(d_model=256, vocab_size=1000)
        assert proj.d_model == 256
        assert proj.vocab_size == 1000

    def test_projection_forward(self):
        """Test projection forward pass."""
        proj = EmbeddingProjection(d_model=256, vocab_size=1000)
        x = np.random.randn(1, 10, 256).astype(np.float32)
        logits = proj.forward(x)
        assert logits.shape == (1, 10, 1000)

    def test_token_probabilities(self):
        """Test probability computation."""
        proj = EmbeddingProjection(d_model=256, vocab_size=1000)
        x = np.random.randn(1, 10, 256).astype(np.float32)
        probs = proj.get_token_probabilities(x)
        assert probs.shape == (1, 10, 1000)
        assert np.allclose(probs.sum(axis=-1), 1.0)


class TestArgmaxDecoder:
    """Test cases for ArgmaxDecoder class."""

    def test_decoder_initialization(self):
        """Test decoder can be created."""
        decoder = ArgmaxDecoder(vocab_size=1000)
        assert decoder.vocab_size == 1000

    def test_decode_single(self):
        """Test decoding single sample."""
        decoder = ArgmaxDecoder(vocab_size=1000)
        logits = np.random.randn(1000).astype(np.float32)
        tokens = decoder.decode(logits)
        assert len(tokens) == 1

    def test_decode_batch(self):
        """Test decoding batch."""
        decoder = ArgmaxDecoder(vocab_size=1000)
        logits = np.random.randn(2, 5, 1000).astype(np.float32)
        tokens = decoder.decode(logits)
        assert len(tokens) == 10

    def test_decode_top_k(self):
        """Test top-k decoding."""
        decoder = ArgmaxDecoder(vocab_size=1000)
        logits = np.random.randn(1000).astype(np.float32)
        top_k = decoder.decode_top_k(logits, k=5)
        assert len(top_k[0]) == 5

    def test_get_confidence(self):
        """Test confidence calculation."""
        decoder = ArgmaxDecoder(vocab_size=1000)
        logits = np.random.randn(1000).astype(np.float32)
        confidence = decoder.get_confidence(logits)
        assert 0.0 <= confidence <= 1.0


class TestTransformerEngine:
    """Test cases for TransformerEngine class."""

    def test_engine_initialization(self):
        """Test transformer engine can be created."""
        engine = TransformerEngine()
        assert engine.d_model == 256
        assert engine.num_heads == 8
        assert engine.num_layers == 4

    def test_engine_forward(self):
        """Test transformer forward pass."""
        engine = TransformerEngine()
        embeddings = np.random.randn(1, 10, 256).astype(np.float32)
        logits = engine.forward(embeddings)
        assert logits.shape == (1, 10, 1000)

    def test_engine_predict(self):
        """Test token prediction."""
        engine = TransformerEngine()
        embeddings = np.random.randn(1, 10, 256).astype(np.float32)
        tokens = engine.predict(embeddings)
        assert len(tokens) == 10

    def test_engine_dimension_mismatch(self):
        """Test error on dimension mismatch."""
        engine = TransformerEngine()
        embeddings = np.random.randn(1, 10, 128).astype(np.float32)
        with pytest.raises(ValueError):
            engine.forward(embeddings)

    def test_get_attention_weights(self):
        """Test attention weight extraction."""
        engine = TransformerEngine()
        embeddings = np.random.randn(1, 10, 256).astype(np.float32)
        weights = engine.get_attention_weights(embeddings)
        assert weights.shape == (1, 8, 10, 10)
