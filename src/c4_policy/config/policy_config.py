"""@file policy_config.py

@brief C4 Policy configuration loader.

@details
Loads and provides access to policy layer configuration parameters.
"""

import os
from typing import Any, Dict, List
import yaml
from dataclasses import dataclass


@dataclass
class PolicyConfig:
    """Configuration for C4-Policy decision layer.

    @brief Loads and exposes policy parameters from YAML config.
    """

    num_actions: int = 10
    safe_mode_enabled: bool = True
    safety_threshold: float = 0.5
    default_action: str = "stop"

    action_map: Dict[int, str] = None

    filters_enabled: bool = True
    max_speed: float = 100.0
    min_proximity: float = 1.0
    forbidden_actions: List[str] = None

    safe_default_action: str = "stop"
    override_enabled: bool = True

    confidence_high: float = 0.8
    confidence_medium: float = 0.5
    confidence_low: float = 0.3
    confidence_minimum_safe: float = 0.5

    def __post_init__(self):
        if self.action_map is None:
            self.action_map = {
                0: "stop",
                1: "continue",
                2: "turn_left",
                3: "turn_right",
                4: "speed_up",
                5: "slow_down",
                6: "observe",
                7: "wait",
                8: "approach",
                9: "retreat",
            }
        if self.forbidden_actions is None:
            self.forbidden_actions = []

    @classmethod
    def from_yaml(cls, config_path: str = None) -> "PolicyConfig":
        """Load configuration from YAML file.

        @param config_path Path to config file

        @return PolicyConfig instance
        """
        if config_path is None:
            config_dir = os.path.dirname(__file__)
            config_path = os.path.join(config_dir, "policy_config.yaml")

        if not os.path.exists(config_path):
            return cls()

        with open(config_path, "r") as f:
            config_dict = yaml.safe_load(f)

        return cls._from_dict(config_dict)

    @classmethod
    def _from_dict(cls, config_dict: Dict[str, Any]) -> "PolicyConfig":
        """Build config from dictionary.

        @param config_dict Configuration dictionary

        @return PolicyConfig instance
        """
        policy = config_dict.get("policy", {})
        actions = config_dict.get("actions", {})
        safety_filters = config_dict.get("safety_filters", {})
        safe_mode = config_dict.get("safe_mode", {})
        confidence = config_dict.get("confidence", {})

        return cls(
            num_actions=policy.get("num_actions", 10),
            safe_mode_enabled=policy.get("safe_mode_enabled", True),
            safety_threshold=policy.get("safety_threshold", 0.5),
            default_action=policy.get("default_action", "stop"),
            action_map=actions,
            filters_enabled=safety_filters.get("enabled", True),
            max_speed=safety_filters.get("max_speed", 100.0),
            min_proximity=safety_filters.get("min_proximity", 1.0),
            forbidden_actions=safety_filters.get("forbidden_actions", []),
            safe_default_action=safe_mode.get("default_action", "stop"),
            override_enabled=safe_mode.get("override_enabled", True),
            confidence_high=confidence.get("high", 0.8),
            confidence_medium=confidence.get("medium", 0.5),
            confidence_low=confidence.get("low", 0.3),
            confidence_minimum_safe=confidence.get("minimum_safe", 0.5),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "policy": {
                "num_actions": self.num_actions,
                "safe_mode_enabled": self.safe_mode_enabled,
                "safety_threshold": self.safety_threshold,
                "default_action": self.default_action,
            },
            "actions": self.action_map,
            "safety_filters": {
                "enabled": self.filters_enabled,
                "max_speed": self.max_speed,
                "min_proximity": self.min_proximity,
                "forbidden_actions": self.forbidden_actions,
            },
            "safe_mode": {
                "default_action": self.safe_default_action,
                "override_enabled": self.override_enabled,
            },
            "confidence": {
                "high": self.confidence_high,
                "medium": self.confidence_medium,
                "low": self.confidence_low,
                "minimum_safe": self.confidence_minimum_safe,
            },
        }
