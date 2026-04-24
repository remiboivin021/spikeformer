# Kaggle Training Notebooks

Train **ANN Transformer** (baseline) and **SNN SpikeFormer** models on CIFAR-10 using Kaggle's free GPU (30h/week).

## Files

| File | Description |
|------|-------------|
| `train_spikeformer.ipynb` | Train both models |
| `benchmark_spikeformer.ipynb` | Benchmark trained models |

## Quick Start

1. **Upload to Kaggle**
   - Download this folder
   - Upload both `.ipynb` files to Kaggle

2. **Enable GPU**
   - Kaggle → Notebook → Settings → Accelerator → GPU (T4)

3. **Train Models**
   - Run `train_spikeformer.ipynb`
   - Uses ~30min per epoch for SNN on T4 GPU
   - Train for 50-100 epochs

4. **Download Checkpoints**
   - Zip files are created: `ann_checkpoints.zip`, `snn_checkpoints.zip`
   - Download and place in local `checkpoints_ann/` and `checkpoints/` directories

5. **Benchmark Locally**
   - Run `benchmark_models.py --checkpoint` to verify accuracy
   - Or run `benchmark_spikeformer.ipynb` on Kaggle

## Model Comparison

| Model | Parameters | Expected Accuracy | Training Time/Epoch |
|-------|------------|-------------------|---------------------|
| ANN Transformer | ~809K | ~75-80% | ~30s (T4 GPU) |
| SNN SpikeFormer | ~85K | ~70-75% | ~2min (T4 GPU) |

## Configuration

Edit `Config` class in `train_spikeformer.ipynb`:

```python
class Config:
    model_type = 'both'  # 'ann', 'snn', or 'both'
    batch_size = 128
    num_epochs = 100
    learning_rate = 1e-3
    timesteps = 4  # SNN only
```

## Expected Results

After 100 epochs on CIFAR-10:

- **ANN**: ~75-80% test accuracy
- **SNN**: ~70-75% test accuracy
- **SNN energy**: ~100x less than ANN on neuromorphic hardware