"""ANN (Artificial Neural Network) baseline models.

This module provides ANN Transformer implementations for comparison
with the SNN SpikeFormer models.

Reference: Xpikeformer paper Phase 2 comparison baseline
"""

from .transformer import (
    ANNTransformer,
    CIFAR10ANNTransformer,
    ANNTransformerLayer,
    ANNTransformerEncoder,
    ANNAttention,
    create_ann_transformer,
)

__all__ = [
    "ANNTransformer",
    "CIFAR10ANNTransformer",
    "ANNTransformerLayer",
    "ANNTransformerEncoder",
    "ANNAttention",
    "create_ann_transformer",
]