"""SpikeFormer configuration package."""

from .config import (
    load_config,
    load_model_config,
    load_training_config,
    load_hardware_config,
    DEFAULT_MODEL,
    DEFAULT_TRAINING,
    DEFAULT_HARDWARE,
)

# Import core components
from .neurons.lif import LeakyIntegrateAndFire
from .neurons.bernoulli_neuron import BernoulliNeuron
from .encoding.bernoulli_encoder import BernoulliEncoder
from .architecture.ssa import SSAModule, TemporalConvolver, BNFBlock
from .attention.mhsa import MultiHeadAttention
from .hybrid.hybrid import HybridModel, ANNToSNNConverter, SNNHybridTrainer

# Import full model
from .spikeformer import (
    SpikeFormer,
    CIFAR10SpikeFormer,
    SpikeFormerLayer,
    SpikeFormerEncoder,
    create_spikeformer,
)

# Import benchmark
from .benchmark import (
    SpikeFormerBenchmark,
    BenchmarkResult,
    EnergyEstimates,
    format_benchmark_result,
    compare_models,
    print_comparison_table,
)

__all__ = [
    # Config
    "load_config",
    "load_model_config",
    "load_training_config",
    "load_hardware_config",
    "DEFAULT_MODEL",
    "DEFAULT_TRAINING",
    "DEFAULT_HARDWARE",
    # Neurons
    "LeakyIntegrateAndFire",
    "BernoulliNeuron",
    # Encoding
    "BernoulliEncoder",
    # Architecture
    "SSAModule",
    "TemporalConvolver",
    "BNFBlock",
    # Attention
    "MultiHeadAttention",
    # Hybrid
    "HybridModel",
    "ANNToSNNConverter",
    "SNNHybridTrainer",
    # Full model
    "SpikeFormer",
    "CIFAR10SpikeFormer",
    "SpikeFormerLayer",
    "SpikeFormerEncoder",
    "create_spikeformer",
    # Benchmark
    "SpikeFormerBenchmark",
    "BenchmarkResult",
    "EnergyEstimates",
    "format_benchmark_result",
    "compare_models",
    "print_comparison_table",
]