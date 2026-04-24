"""@file transformer_config.py

@brief C3 Transformer configuration loader.

@details
Loads and provides access to transformer layer configuration parameters.
"""

import os
from typing import Any, Dict, Optional
import yaml
from dataclasses import dataclass


@dataclass
class TransformerConfig:
    """Configuration for C3-Transformer reasoning layer.

    @brief Loads and exposes transformer parameters from YAML config.
    """

    d_model: int = 256
    num_heads: int = 8
    num_layers: int = 4
    d_ff: int = 1024
    vocab_size: int = 1000

    no_dropout: bool = True
    no_random_sampling: bool = True

    attention_scale: bool = True
    attention_causal: bool = False

    ffn_activation: str = "gelu"
    ffn_dropout: float = 0.0

    decoding_strategy: str = "argmax"
    decoding_top_k: int = 1

    layer_norm_eps: float = 1e-6
    layer_norm_bias: bool = True

    projection_init_scale: float = 0.02

    @classmethod
    def from_yaml(cls, config_path: str = None) -> "TransformerConfig":
        """Load configuration from YAML file.

        @param config_path Path to config file

        @return TransformerConfig instance
        """
        if config_path is None:
            config_dir = os.path.dirname(__file__)
            config_path = os.path.join(config_dir, "transformer_config.yaml")

        if not os.path.exists(config_path):
            return cls()

        with open(config_path, "r") as f:
            config_dict = yaml.safe_load(f)

        return cls._from_dict(config_dict)

    @classmethod
    def _from_dict(cls, config_dict: Dict[str, Any]) -> "TransformerConfig":
        """Build config from dictionary.

        @param config_dict Configuration dictionary

        @return TransformerConfig instance
        """
        model = config_dict.get("model", {})
        determinism = config_dict.get("determinism", {})
        attention = config_dict.get("attention", {})
        ffn = config_dict.get("feed_forward", {})
        decoding = config_dict.get("decoding", {})
        layer_norm = config_dict.get("layer_norm", {})
        projection = config_dict.get("projection", {})

        return cls(
            d_model=model.get("d_model", 256),
            num_heads=model.get("num_heads", 8),
            num_layers=model.get("num_layers", 4),
            d_ff=model.get("d_ff", 1024),
            vocab_size=model.get("vocab_size", 1000),
            no_dropout=determinism.get("no_dropout", True),
            no_random_sampling=determinism.get("no_random_sampling", True),
            attention_scale=attention.get("scale", True),
            attention_causal=attention.get("causal", False),
            ffn_activation=ffn.get("activation", "gelu"),
            ffn_dropout=ffn.get("dropout", 0.0),
            decoding_strategy=decoding.get("strategy", "argmax"),
            decoding_top_k=decoding.get("top_k", 1),
            layer_norm_eps=layer_norm.get("eps", 1e-6),
            layer_norm_bias=layer_norm.get("bias", True),
            projection_init_scale=projection.get("init_scale", 0.02),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "model": {
                "d_model": self.d_model,
                "num_heads": self.num_heads,
                "num_layers": self.num_layers,
                "d_ff": self.d_ff,
                "vocab_size": self.vocab_size,
            },
            "determinism": {
                "no_dropout": self.no_dropout,
                "no_random_sampling": self.no_random_sampling,
            },
            "attention": {
                "scale": self.attention_scale,
                "causal": self.attention_causal,
            },
            "feed_forward": {
                "activation": self.ffn_activation,
                "dropout": self.ffn_dropout,
            },
            "decoding": {
                "strategy": self.decoding_strategy,
                "top_k": self.decoding_top_k,
            },
            "layer_norm": {
                "eps": self.layer_norm_eps,
                "bias": self.layer_norm_bias,
            },
            "projection": {
                "init_scale": self.projection_init_scale,
            },
        }
