# SpikeFormer

[![CI][ci-shield]][ci-url]
[![Coverage][coverage-shield]][coverage-url]
[![Python Version][python-shield]][python-url]
[![License][license-shield]][license-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/spikeformer/SpikeFormer">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">SpikeFormer</h3>

  <p align="center">
    A Hybrid SNN-Transformer Cognitive Architecture — Reimplementation of Xpikeformer (arXiv:2408.08794v2)
    <br />
    <a href="docs/architecture/"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/spikeformer/SpikeFormer">View Demo</a>
    &middot;
    <a href="https://github.com/spikeformer/SpikeFormer/issues/new?labels=bug&template=bug---.yml">Report Bug</a>
    &middot;
    <a href="https://github.com/spikeformer/SpikeFormer/issues/new?labels=enhancement&template=feature---.yml">Request Feature</a>
  </p>
</div>


## About The Project

SpikeFormer is a PyTorch reimplementation of **Xpikeformer** (Song et al., 2025), a Spiking Neural Network (SNN) Transformer architecture using:
- **AIMC Engine** — Analog In-Memory Computing for feedforward layers
- **SSA Engine** — Stochastic Spiking Attention

The project follows a 3-phase approach:
1. **Phase 1**: SNN Transformer (exact reimplementation)
2. **Phase 2**: ANN Transformer (equivalent for comparison)
3. **Phase 3**: Hybrid SNN/ANN (if validated)

### Goal

Validate that SNN Transformers can match ANN accuracy while significantly reducing energy consumption, as a foundation for hybrid mobile robotics applications.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Built With

[![PyTorch][pytorch-shield]][pytorch-url]
[![Python][python-shield]][python-url]

* [PyTorch](https://pytorch.org/) — ML framework
* [SpikingJelly](https://github.com/fangwei123456/SpikingJelly) — SNN framework
* [snnTorch](https://github.com/jeshraghian/snntorch) — SNN training helpers
* [AIHWKit](https://github.com/IBM/aihwkit) — PCM hardware simulation
* [ONNX](https://onnx.ai/) — Model export
* [wandb](https://wandb.ai/) — Training tracking

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Getting Started

### Prerequisites

- Python 3.10+
- NVIDIA GPU (for training)
- ~10GB disk space

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/spikeformer/SpikeFormer.git
   cd SpikeFormer
   ```

2. Create virtual environment
   ```sh
   python -m venv .venv
   source .venv/Scripts/activate  # Windows
   # or source .venv/bin/activate  # Linux
   ```

3. Install dependencies
   ```sh
   pip install -e ".[dev]"
   pip install -r requirements.txt
   ```

4. Install SNN frameworks (requires separate install)
   ```sh
   pip install spikingjelly snntorch aihwkit
   ```

### Quick Test

```python
import torch
from src.snn import XpikeFormer

config = {"d_model": 384, "n_heads": 6, "n_layers": 4, "T": 8}
model = XpikeFormer(config)

# Dummy input (CIFAR-10 format)
x = torch.randn(4, 3, 32, 32)
output = model(x)

print(f"Output shape: {output.shape}")  # (4, 10)
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Usage

### Training (Kaggle)

```python
# Run on Kaggle Notebooks
!pip install torch spikingjelly snntorch wandb onnx -q

# Train Phase 1 (SNN)
python scripts/train_ct.py --config config/model/xpikeformer_small.yaml
```

### Export ONNX

```python
python scripts/export_onnx.py --checkpoint models/checkpoint.pt --output models/xpikeformer_small.onnx
```

### Import MATLAB

```matlab
% Import ONNX model
net = importONNXNetwork('models/xpikeformer_small.onnx');

% Inference
input = rand(1, 3, 32, 32);
output = predict(net, input);
```

For more examples, please refer to the [Documentation](docs/architecture/).

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Project Structure

```
spikeformer/
├── src/
│   ├── snn/              # Phase 1: SNN Transformer
│   │   ├── neurons/       # LIF, Bernoulli neurons
│   │   ├── encoding/     # Spike encoding
│   │   ├── engines/      # AIMC + SSA
│   │   ├── model/        # Model assembly
│   │   └── training/     # Training loop
│   ├── ann/              # Phase 2: ANN equivalent
│   └── bridge/           # Phase 3: Hybrid
├── config/               # YAML configurations
│   ├── model/           # small/medium/large
│   └── training/        # CT + HWAT
├── models/              # Checkpoints & ONNX
├── tests/               # Unit & integration tests
├── scripts/             # Training & export scripts
├── notebooks/           # Visualizations
├── context/             # Product/technical context
└── docs/                # Architecture docs
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Roadmap

- [ ] Phase 1: Implement LIF neuron + Bernoulli encoder
- [ ] Phase 1: Implement AIMC Engine (crossbar simulation)
- [ ] Phase 1: Implement SSA Engine (stochastic attention)
- [ ] Phase 1: Assemble XpikeFormer model
- [ ] Phase 1: Train on CIFAR-10 (≥80% accuracy)
- [ ] Phase 2: Implement ANN equivalent
- [ ] Phase 2: Compare metrics (accuracy/latency/energy)
- [ ] Phase 3: Hybrid SNN/ANN (if validated)

See [issues](https://github.com/spikeformer/SpikeFormer/issues) for full roadmap.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Contact

Rémi Boivin — team@spikeformer.ai

Project Link: [https://github.com/spikeformer/SpikeFormer](https://github.com/spikeformer/SpikeFormer)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Acknowledgments

- Song et al., "Xpikeformer: Efficient All-to-All Spiking Neural Network" (arXiv:2408.08794v2)
- SpikingJelly team
- snntorch team

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->

[ci-shield]: https://img.shields.io/github/actions/workflow/status/spikeformer/SpikeFormer/ci.yml?style=for-the-badge&label=CI
[ci-url]: https://github.com/spikeformer/SpikeFormer/actions
[coverage-shield]: https://img.shields.io/codecov/c/gh/spikeformer/SpikeFormer?style=for-the-badge
[coverage-url]: https://codecov.io/gh/spikeformer/SpikeFormer
[python-shield]: https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white
[python-url]: https://www.python.org/
[license-shield]: https://img.shields.io/badge/license-MIT-green?style=for-the-badge
[license-url]: https://github.com/spikeformer/SpikeFormer/blob/main/LICENSE.txt
[pytorch-shield]: https://img.shields.io/badge/PyTorch-2.0+-ee4c2c?style=for-the-badge&logo=pytorch&logoColor=white
[pytorch-url]: https://pytorch.org/
