"""Spike encoding modules for SpikeFormer."""

from .bernoulli_encoder import (
    BernoulliEncoder,
    encode_bernoulli,
    compute_spike_rate,
    validate_rate_convergence,
)

__all__ = [
    "BernoulliEncoder",
    "encode_bernoulli",
    "compute_spike_rate",
    "validate_rate_convergence",
]