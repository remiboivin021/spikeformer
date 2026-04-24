"""@file learning_config.py

@brief C5 Learning configuration loader.

@details
Loads and provides access to learning system configuration parameters.
"""

import os
from typing import Any, Dict, Optional
import yaml
from dataclasses import dataclass


@dataclass
class LearningConfig:
    """Configuration for C5-Learning system (offline only).

    @brief Loads and exposes learning parameters from YAML config.
    """

    batch_size: int = 32
    learning_rate: float = 0.001
    num_epochs: int = 10
    optimizer: str = "adam"
    weight_decay: float = 0.0001
    gradient_clip: float = 1.0

    buffer_max_capacity: int = 100000
    buffer_min_capacity: int = 1000
    buffer_sample_strategy: str = "random"

    validation_min_accuracy: float = 0.8
    validation_safety_checks: bool = True
    validation_determinism_checks: bool = True
    validation_memory_checks: bool = True
    validation_split: float = 0.2

    promotion_stability_threshold: float = 0.05
    promotion_retention_threshold: int = 5
    promotion_improvement_threshold: float = 0.02

    checkpoint_save_frequency: int = 5
    checkpoint_keep_last: int = 3
    checkpoint_save_best: bool = True
    checkpoint_dir: str = "checkpoints/"

    offline_only: bool = True
    training_enabled: bool = False

    @classmethod
    def from_yaml(cls, config_path: str = None) -> "LearningConfig":
        """Load configuration from YAML file.

        @param config_path Path to config file

        @return LearningConfig instance
        """
        if config_path is None:
            config_dir = os.path.dirname(__file__)
            config_path = os.path.join(config_dir, "learning_config.yaml")

        if not os.path.exists(config_path):
            return cls()

        with open(config_path, "r") as f:
            config_dict = yaml.safe_load(f)

        return cls._from_dict(config_dict)

    @classmethod
    def _from_dict(cls, config_dict: Dict[str, Any]) -> "LearningConfig":
        """Build config from dictionary.

        @param config_dict Configuration dictionary

        @return LearningConfig instance
        """
        training = config_dict.get("training", {})
        experience = config_dict.get("experience_buffer", {})
        validation = config_dict.get("validation", {})
        promotion = config_dict.get("promotion_gate", {})
        checkpoint = config_dict.get("checkpoint", {})
        mode = config_dict.get("mode", {})

        return cls(
            batch_size=training.get("batch_size", 32),
            learning_rate=training.get("learning_rate", 0.001),
            num_epochs=training.get("num_epochs", 10),
            optimizer=training.get("optimizer", "adam"),
            weight_decay=training.get("weight_decay", 0.0001),
            gradient_clip=training.get("gradient_clip", 1.0),
            buffer_max_capacity=experience.get("max_capacity", 100000),
            buffer_min_capacity=experience.get("min_capacity", 1000),
            buffer_sample_strategy=experience.get("sample_strategy", "random"),
            validation_min_accuracy=validation.get("min_accuracy", 0.8),
            validation_safety_checks=validation.get("safety_checks", True),
            validation_determinism_checks=validation.get("determinism_checks", True),
            validation_memory_checks=validation.get("memory_checks", True),
            validation_split=validation.get("validation_split", 0.2),
            promotion_stability_threshold=promotion.get("stability_threshold", 0.05),
            promotion_retention_threshold=promotion.get("retention_threshold", 5),
            promotion_improvement_threshold=promotion.get("improvement_threshold", 0.02),
            checkpoint_save_frequency=checkpoint.get("save_frequency", 5),
            checkpoint_keep_last=checkpoint.get("keep_last", 3),
            checkpoint_save_best=checkpoint.get("save_best", True),
            checkpoint_dir=checkpoint.get("checkpoint_dir", "checkpoints/"),
            offline_only=mode.get("offline_only", True),
            training_enabled=mode.get("training_enabled", False),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "training": {
                "batch_size": self.batch_size,
                "learning_rate": self.learning_rate,
                "num_epochs": self.num_epochs,
                "optimizer": self.optimizer,
                "weight_decay": self.weight_decay,
                "gradient_clip": self.gradient_clip,
            },
            "experience_buffer": {
                "max_capacity": self.buffer_max_capacity,
                "min_capacity": self.buffer_min_capacity,
                "sample_strategy": self.buffer_sample_strategy,
            },
            "validation": {
                "min_accuracy": self.validation_min_accuracy,
                "safety_checks": self.validation_safety_checks,
                "determinism_checks": self.validation_determinism_checks,
                "memory_checks": self.validation_memory_checks,
                "validation_split": self.validation_split,
            },
            "promotion_gate": {
                "stability_threshold": self.promotion_stability_threshold,
                "retention_threshold": self.promotion_retention_threshold,
                "improvement_threshold": self.promotion_improvement_threshold,
            },
            "checkpoint": {
                "save_frequency": self.checkpoint_save_frequency,
                "keep_last": self.checkpoint_keep_last,
                "save_best": self.checkpoint_save_best,
                "checkpoint_dir": self.checkpoint_dir,
            },
            "mode": {
                "offline_only": self.offline_only,
                "training_enabled": self.training_enabled,
            },
        }
