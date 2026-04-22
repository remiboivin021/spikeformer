# ADR-002: PyTorch Training Pipeline Integration

**Date**: 2026-04-16  
**Status**: Accepted  
**Deciders**: SpikeFormer Team

---

## Context

SpikeFormer currently uses numpy-based placeholder implementations for:
- Transformer weights (not initialized)
- Training loop (returns random values)

The model cannot learn or function without proper training infrastructure.

**Problem Statement**:  
How to add real training capability to SpikeFormer using PyTorch while preserving:
- Determinism in inference mode
- C1-C4 pipeline integrity
- C5 sandbox isolation
- EmbeddingContract v1 compatibility

---

## Decision Drivers

1. **PyTorch ecosystem**: Standard for deep learning, GPU acceleration
2. **Autograd**: Automatic differentiation for backpropagation
3. **Serialization**: `.pt` format for model export
4. **Determinism**: `torch.manual_seed()` for reproducibility
5. **Community**: Large community, good documentation

---

## Decision

Integrate PyTorch for training-only operations in C5, while keeping inference components flexible:

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  C3-TRANSFORMER (Inference - PyTorch or NumPy)          │
│  - Forward pass uses frozen weights                       │
│  - Deterministic: torch.manual_seed(seed)                │
│  - Input: numpy array (from C2) → convert to tensor    │
│  - Output: tensor → convert to numpy array              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  C5-LEARNING (Training - PyTorch only)                  │
│  - Forward/backward passes                               │
│  - Dataset: NavigationDataset                            │
│  - Optimizer: Adam/SGD                                  │
│  - Loss: CrossEntropy + custom                          │
│  - Checkpoint: torch.save(state_dict)                   │
└─────────────────────────────────────────────────────────────┘
```

### Module Changes

| Module | Action | Notes |
|--------|--------|-------|
| `src/c3_transformer/pytorch_attention.py` | CREATE | PyTorch attention layer |
| `src/c3_transformer/pytorch_feedforward.py` | CREATE | PyTorch FFN |
| `src/c3_transformer/pytorch_transformer.py` | CREATE | Complete PyTorch model |
| `src/c3_transformer/weights.py` | CREATE | Weight initialization |
| `src/c3_transformer/transformer_engine.py` | MODIFY | Adapter to PyTorch |
| `src/c5_learning/pytorch_trainer.py` | CREATE | Training loop |
| `src/c5_learning/navigation_dataset.py` | CREATE | Training dataset |
| `src/c5_learning/loss_functions.py` | CREATE | Loss implementations |

---

## Alternatives Considered

### Option A: Pure NumPy Implementation
- Pros: No new dependencies, educational
- Cons: Slow, no GPU, manual gradient computation
- **Rejected**: Not practical for real navigation model

### Option B: TensorFlow
- Pros: Mature ecosystem
- Cons: Less flexible, different API style
- **Rejected**: PyTorch more common in research

### Option C: JAX
- Pros: Functional, HP-transform compatible
- Cons: Steeper learning curve, smaller community
- **Rejected**: PyTorch is standard in SNN community

---

## Consequences

### Positive
- Real model training capability
- GPU acceleration for faster training
- Automatic differentiation (autograd)
- Model serialization (`.pt` files)
- Large ecosystem of optimizers, losses, utilities

### Negative
- New dependency (PyTorch)
- NumPy ↔ PyTorch tensor conversion overhead
- Additional complexity in C3

### Risks
- **R-01**: CUDA OOM with large models → Mitigation: Gradient accumulation
- **R-02**: Non-deterministic GPU ops → Mitigation: `torch.use_deterministic_algorithms()`
- **R-03**: Model export format changes → Mitigation: Versioned checkpoints

---

## Determinism Strategy

```python
# Inference mode - deterministic
torch.manual_seed(42)
model.eval()  # Dropout disabled
with torch.no_grad():
    output = model(input_tensor)

# Training mode - controlled randomness
torch.manual_seed(42)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
```

---

## Migration Plan

### Phase 1: Foundation
1. Create `weights.py` with Xavier initialization
2. Create PyTorch attention/FFN/Transformer
3. Test forward pass determinism

### Phase 2: Training
4. Create `NavigationDataset`
5. Create training loop
6. Test convergence

### Phase 3: Integration
7. Update `trainer.py` to use PyTorch
8. Add checkpoint save/load
9. Integration tests

### Rollback
- Disable PyTorch modules via config
- Fallback to existing numpy implementation
- C3 can work without C5 training

---

## Compliance Checklist

- [x] Training works with GPU acceleration
- [x] Determinism preserved in inference
- [x] EmbeddingContract v1 unchanged
- [x] C5 training is isolated
- [x] Model exportable to `.pt`
- [x] No runtime weight mutation

---

## References

- [PyTorch Documentation](https://pytorch.org/docs/)
- [Deterministic Operations](https://pytorch.org/docs/stable/notes/determinism.html)
- ADR-001: Navigation Cognitive Architecture Integration
