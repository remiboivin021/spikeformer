"""Configuration loader for SpikeFormer."""

import yaml
import os
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def get_device(config_device: str = None) -> str:
    """Get device for training.
    
    Args:
        config_device: Device from config (cpu/cuda)
    
    Returns:
        Device string
    """
    if config_device == "cpu":
        return "cpu"
    
    # Try CUDA, fallback to CPU if not available
    if config_device == "cuda" or config_device is None:
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except Exception:
            pass
    return "cpu"


def load_model_config(name: str = "xpikeformer_small") -> Dict[str, Any]:
    """Load model configuration by name.
    
    Args:
        name: Config name (xpikeformer_small) or full path (config/model/xpikeformer_small.yaml)
    """
    # Check if it's already a full path
    if name.startswith("config/") or "/" in name or Path(name).exists():
        config_path = Path(name)
    else:
        config_path = CONFIG_DIR / "model" / f"{name}.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Model config not found: {config_path}")
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_training_config(name: str = "conventional") -> Dict[str, Any]:
    """Load training configuration by name.
    
    Args:
        name: Config name or full path
    """
    # Check if it's already a full path
    if name.startswith("config/") or "/" in name or Path(name).exists():
        config_path = Path(name)
    else:
        config_path = CONFIG_DIR / "training" / f"{name}.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Training config not found: {config_path}")
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_hardware_config(name: str = "pcm_crossbar") -> Dict[str, Any]:
    """Load hardware configuration by name.
    
    Args:
        name: Config name or full path
    """
    # Check if it's already a full path
    if name.startswith("config/") or "/" in name or Path(name).exists():
        config_path = Path(name)
    else:
        config_path = CONFIG_DIR / "hardware" / f"{name}.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Hardware config not found: {config_path}")
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_config(config_type: str, name: str) -> Dict[str, Any]:
    """Generic config loader.
    
    Args:
        config_type: One of 'model', 'training', 'hardware'
        name: Config name (without .yaml extension)
    
    Returns:
        Configuration dictionary
    """
    loaders = {
        "model": load_model_config,
        "training": load_training_config,
        "hardware": load_hardware_config,
    }
    if config_type not in loaders:
        raise ValueError(f"Unknown config type: {config_type}. Use: {list(loaders.keys())}")
    return loaders[config_type](name)


# Default configurations
DEFAULT_MODEL = "xpikeformer_small"
DEFAULT_TRAINING = "conventional"
DEFAULT_HARDWARE = "pcm_crossbar"