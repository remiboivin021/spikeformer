"""Tests for P1-T1: Setup environnement."""

import pytest
import yaml
from pathlib import Path


class TestConfigLoader:
    """Test configuration loading system."""
    
    def test_load_model_config_small(self):
        """Test loading small model config."""
        from src.snn.config import load_model_config
        config = load_model_config("xpikeformer_small")
        assert config["model"]["d_model"] == 384
        assert config["model"]["n_layers"] == 4
        assert config["training"]["batch_size"] == 32
    
    def test_load_model_config_medium(self):
        """Test loading medium model config."""
        from src.snn.config import load_model_config
        config = load_model_config("xpikeformer_medium")
        assert config["model"]["d_model"] == 512
        assert config["model"]["n_layers"] == 6
    
    def test_load_model_config_large(self):
        """Test loading large model config."""
        from src.snn.config import load_model_config
        config = load_model_config("xpikeformer_large")
        assert config["model"]["d_model"] == 768
        assert config["model"]["n_layers"] == 8
    
    def test_load_training_config(self):
        """Test loading training config."""
        from src.snn.config import load_training_config
        config = load_training_config("conventional")
        assert config["training"]["mode"] == "ct"
        assert config["training"]["optimizer"]["type"] == "adamw"
    
    def test_load_hardware_config(self):
        """Test loading hardware config."""
        from src.snn.config import load_hardware_config
        config = load_hardware_config("pcm_crossbar")
        assert config["hardware"]["type"] == "pcm"
        assert config["hardware"]["adc"]["resolution"] == 5
    
    def test_generic_loader_model(self):
        """Test generic config loader for model."""
        from src.snn.config import load_config
        config = load_config("model", "xpikeformer_small")
        assert config["model"]["name"] == "xpikeformer_small"
    
    def test_generic_loader_training(self):
        """Test generic config loader for training."""
        from src.snn.config import load_config
        config = load_config("training", "conventional")
        assert config["training"]["name"] == "conventional"
    
    def test_generic_loader_hardware(self):
        """Test generic config loader for hardware."""
        from src.snn.config import load_config
        config = load_config("hardware", "pcm_crossbar")
        assert config["hardware"]["name"] == "pcm_crossbar"
    
    def test_config_files_exist(self):
        """Verify all config files exist."""
        config_dir = Path(__file__).parent.parent.parent / "config"
        
        expected_files = [
            "model/xpikeformer_small.yaml",
            "model/xpikeformer_medium.yaml",
            "model/xpikeformer_large.yaml",
            "training/conventional.yaml",
            "training/hardware_aware.yaml",
            "hardware/pcm_crossbar.yaml",
        ]
        
        for f in expected_files:
            assert (config_dir / f).exists(), f"Missing: {f}"


class TestPyprojectToml:
    """Test pyproject.toml configuration."""
    
    def test_dependencies_present(self):
        """Verify required dependencies are declared."""
        pyproject = Path(__file__).parent.parent.parent / "pyproject.toml"
        with open(pyproject) as f:
            content = f.read()
        
        assert "torch" in content
        assert "numpy" in content
        assert "pyyaml" in content
        assert "spikingjelly" in content
        assert "snntorch" in content
        assert "onnx" in content
    
    def test_dev_dependencies(self):
        """Verify dev dependencies are declared."""
        pyproject = Path(__file__).parent.parent.parent / "pyproject.toml"
        with open(pyproject) as f:
            content = f.read()
        
        assert "pytest" in content
        assert "ruff" in content


class TestGitHubActionsWorkflow:
    """Test GitHub Actions CI configuration."""
    
    def test_workflow_exists(self):
        """Verify CI workflow exists."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
        assert workflow_path.exists()
    
    def test_workflow_valid_yaml(self):
        """Verify workflow is valid YAML."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
        with open(workflow_path) as f:
            config = yaml.safe_load(f)
        
        assert "name" in config
        assert "jobs" in config
        assert "test" in config["jobs"]
        assert "smoke-test" in config["jobs"]