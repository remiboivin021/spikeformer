"""@file adapter_config.py

@brief C2 Adapter configuration loader.

@details
Loads and provides access to adapter layer configuration parameters.
"""

import os
from typing import Any, Dict
import yaml
from dataclasses import dataclass


@dataclass
class AdapterConfig:
    """Configuration for C2-Embedding Adapter layer.

    @brief Loads and exposes adapter parameters from YAML config.
    """

    output_dim: int = 256
    normalize: bool = True
    clamp_min: float = -10.0
    clamp_max: float = 10.0

    max_norm: float = 2.0
    allow_negative: bool = True

    contract_version: str = "v1"

    @classmethod
    def from_yaml(cls, config_path: str = None) -> "AdapterConfig":
        """Load configuration from YAML file.

        @param config_path Path to config file

        @return AdapterConfig instance
        """
        if config_path is None:
            config_dir = os.path.dirname(__file__)
            config_path = os.path.join(config_dir, "adapter_config.yaml")

        if not os.path.exists(config_path):
            return cls()

        with open(config_path, "r") as f:
            config_dict = yaml.safe_load(f)

        return cls._from_dict(config_dict)

    @classmethod
    def _from_dict(cls, config_dict: Dict[str, Any]) -> "AdapterConfig":
        """Build config from dictionary.

        @param config_dict Configuration dictionary

        @return AdapterConfig instance
        """
        adapter = config_dict.get("adapter", {})
        clamp = adapter.get("clamp_range", [-10.0, 10.0])
        validation = config_dict.get("validation", {})
        contract = config_dict.get("contract", {})

        return cls(
            output_dim=adapter.get("output_dim", 256),
            normalize=adapter.get("normalize", True),
            clamp_min=clamp[0] if isinstance(clamp, list) else -10.0,
            clamp_max=clamp[1] if isinstance(clamp, list) else 10.0,
            max_norm=validation.get("max_norm", 2.0),
            allow_negative=validation.get("allow_negative", True),
            contract_version=contract.get("version", "v1"),
        )

    @property
    def clamp_range(self):
        """Get clamp range as tuple."""
        return (self.clamp_min, self.clamp_max)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "adapter": {
                "output_dim": self.output_dim,
                "normalize": self.normalize,
                "clamp_range": [self.clamp_min, self.clamp_max],
            },
            "validation": {
                "max_norm": self.max_norm,
                "allow_negative": self.allow_negative,
            },
            "contract": {
                "version": self.contract_version,
            },
        }
