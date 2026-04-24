"""@file snn_config.py

@brief SNN configuration loader.

@details
Loads and provides access to SNN layer configuration parameters.
"""

import os
from typing import Any, Dict
import yaml
from dataclasses import dataclass


@dataclass
class SNNConfig:
    """Configuration for C1-SNN perception layer.

    @brief Loads and exposes SNN parameters from YAML config.
    """

    # Neuron parameters
    threshold: float = 1.0
    reset_value: float = 0.0
    tau_m: float = 20.0
    refractory_period: float = 2.0

    # Synapse parameters
    initial_weight: float = 0.5
    min_weight: float = 0.0
    max_weight: float = 1.0

    # STDP parameters
    tau_plus: float = 20.0
    tau_minus: float = 20.0
    a_plus: float = 0.01
    a_minus: float = 0.012
    stdp_enabled: bool = False

    # Event processing
    num_channels: int = 64
    time_resolution: float = 1.0

    # Embedding
    embedding_dim: int = 256
    num_neurons: int = 64
    embedding_time_window: float = 100.0

    # Network
    input_neurons: int = 64
    hidden_neurons: int = 128
    output_neurons: int = 64

    @classmethod
    def from_yaml(cls, config_path: str = None) -> "SNNConfig":
        """Load configuration from YAML file.

        @param config_path Path to config file

        @return SNNConfig instance
        """
        if config_path is None:
            config_dir = os.path.dirname(__file__)
            config_path = os.path.join(config_dir, "snn_config.yaml")

        if not os.path.exists(config_path):
            return cls()

        with open(config_path, "r") as f:
            config_dict = yaml.safe_load(f)

        return cls._from_dict(config_dict)

    @classmethod
    def _from_dict(cls, config_dict: Dict[str, Any]) -> "SNNConfig":
        """Build config from dictionary.

        @param config_dict Configuration dictionary

        @return SNNConfig instance
        """
        return cls(
            threshold=config_dict.get("neuron", {}).get("threshold", 1.0),
            reset_value=config_dict.get("neuron", {}).get("reset_value", 0.0),
            tau_m=config_dict.get("neuron", {}).get("tau_m", 20.0),
            refractory_period=config_dict.get("neuron", {}).get(
                "refractory_period", 2.0
            ),
            initial_weight=config_dict.get("synapse", {}).get("initial_weight", 0.5),
            min_weight=config_dict.get("synapse", {}).get("min_weight", 0.0),
            max_weight=config_dict.get("synapse", {}).get("max_weight", 1.0),
            tau_plus=config_dict.get("stdp", {}).get("tau_plus", 20.0),
            tau_minus=config_dict.get("stdp", {}).get("tau_minus", 20.0),
            a_plus=config_dict.get("stdp", {}).get("a_plus", 0.01),
            a_minus=config_dict.get("stdp", {}).get("a_minus", 0.012),
            stdp_enabled=config_dict.get("stdp", {}).get("enabled", False),
            num_channels=config_dict.get("event_processor", {}).get("num_channels", 64),
            time_resolution=config_dict.get("event_processor", {}).get(
                "time_resolution", 1.0
            ),
            embedding_dim=config_dict.get("embedding", {}).get("dimension", 256),
            num_neurons=config_dict.get("embedding", {}).get("num_neurons", 64),
            embedding_time_window=config_dict.get("embedding", {}).get(
                "time_window", 100.0
            ),
            input_neurons=config_dict.get("network", {}).get("input_neurons", 64),
            hidden_neurons=config_dict.get("network", {}).get("hidden_neurons", 128),
            output_neurons=config_dict.get("network", {}).get("output_neurons", 64),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary.

        @return Configuration as nested dictionary
        """
        return {
            "neuron": {
                "threshold": self.threshold,
                "reset_value": self.reset_value,
                "tau_m": self.tau_m,
                "refractory_period": self.refractory_period,
            },
            "synapse": {
                "initial_weight": self.initial_weight,
                "min_weight": self.min_weight,
                "max_weight": self.max_weight,
            },
            "stdp": {
                "tau_plus": self.tau_plus,
                "tau_minus": self.tau_minus,
                "a_plus": self.a_plus,
                "a_minus": self.a_minus,
                "enabled": self.stdp_enabled,
            },
            "event_processor": {
                "num_channels": self.num_channels,
                "time_resolution": self.time_resolution,
            },
            "embedding": {
                "dimension": self.embedding_dim,
                "num_neurons": self.num_neurons,
                "time_window": self.embedding_time_window,
            },
            "network": {
                "input_neurons": self.input_neurons,
                "hidden_neurons": self.hidden_neurons,
                "output_neurons": self.output_neurons,
            },
        }
