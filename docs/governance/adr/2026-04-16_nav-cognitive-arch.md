# ADR-001: Navigation Cognitive Architecture Integration

**Date**: 2026-04-16  
**Status**: Accepted  
**Deciders**: SpikeFormer Team  

---

## Context

SpikeFormer is a hybrid SNN-Transformer cognitive architecture that processes sensor events through a C1→C2→C3→C4 pipeline to produce decisions. The current implementation can process events but lacks navigation capabilities for autonomous robot movement.

**Problem Statement**:  
How to add navigation capabilities to SpikeFormer while preserving:
- Deterministic runtime behavior
- Safety guarantees (SAFE_MODE)
- C1-C4 pipeline integrity
- Runtime immutability principle

---

## Decision Drivers

1. Event camera preferred for SNN compatibility (temporal data)
2. Safety-critical: must fail gracefully
3. Determinism required in navigation decisions
4. Extensibility for future SLAM integration
5. Minimal blast radius on existing C1-C4 pipeline

---

## Decision

Add three new packages to SpikeFormer:

1. **src/sensors/** - Sensor interfaces (event camera, lidar)
2. **src/actuators/** - Motor control
3. **src/navigation/** - Navigation logic (obstacle avoidance, path planning)

### Module Structure

```
src/
├── sensors/           # NEW
│   ├── base_sensor.py       # Abstract interface
│   ├── event_camera.py     # Event camera integration
│   ├── lidar.py            # Lidar integration
│   └── sensor_factory.py    # Factory pattern
├── actuators/         # NEW
│   ├── base_actuator.py    # Abstract interface
│   ├── motor_driver.py     # Motor control
│   └── actuator_manager.py  # Actuator coordinator
├── navigation/        # NEW
│   ├── obstacle_avoider.py # Collision detection
│   ├── path_planner.py     # Path planning
│   ├── robot_state.py      # Odometry state
│   └── navigation_engine.py # Main navigation logic
└── [existing c1-c5 modules unchanged]
```

### Navigation Actions (C4 extension)

Extend DecisionContract with navigation actions:
- `move_forward(distance_m)`
- `move_backward(distance_m)`
- `turn_left(angle_rad)`
- `turn_right(angle_rad)`
- `stop()`
- `wait(duration_s)`

---

## Alternatives Considered

### Option A: Event Camera Only
- Pros: Native SNN input, low latency
- Cons: Limited range, no 360° coverage

### Option B: Standard Camera + CNN
- Pros: Rich visual data
- Cons: Not SNN-friendly, high compute, no temporal resolution

### Option C: Lidar Only
- Pros: Accurate distance measurement, 360° coverage
- Cons: No color/texture, expensive

### Selected: Option A + C Hybrid
- Event camera for temporal perception (C1 input)
- Lidar for obstacle detection and distance
- Fusion in navigation module

---

## Consequences

### Positive
- Navigation capability added without modifying C1-C4 core
- Event camera maintains SNN compatibility
- SAFE_MODE still controls all navigation outputs
- Determinism preserved through transformer reasoning

### Negative
- New dependencies: event camera SDK, lidar drivers
- Increased complexity in sensor integration
- C4 policy must validate navigation-specific actions

### Risks
- NAV-001: Lidar connection loss → SAFE_MODE stop
- NAV-002: Obstacle undetected → SAFE_MODE stop
- NAV-003: Path planning timeout → SAFE_MODE wait
- NAV-004: Motor failure → SAFE_MODE stop

---

## Contract Extensions

### DecisionContract (additions only)
```python
# Navigation action types
NAVIGATION_ACTIONS = {
    "move_forward": {"type": "float", "unit": "meters"},
    "move_backward": {"type": "float", "unit": "meters"},
    "turn_left": {"type": "float", "unit": "radians"},
    "turn_right": {"type": "float", "unit": "radians"},
    "stop": {"type": "null"},
    "wait": {"type": "float", "unit": "seconds"},
}
```

### EmbeddingContract v1
- **UNCHANGED** - Still shape [256], version v1
- Navigation uses same embedding format

---

## Migration Plan

### Phase 1: Infrastructure (no behavior change)
- Create sensor/actuator/navigation package structure
- Define abstract interfaces
- Mock implementations for testing

### Phase 2: Navigation Core
- Implement obstacle_avoider
- Implement robot_state (odometry)
- Extend C4 with navigation actions

### Phase 3: Integration
- Sensor fusion (event camera + lidar)
- Full pipeline test
- Performance benchmarks

### Rollback
- Disable via config: `navigation.enabled: false`
- Fallback to existing C1-C4 pipeline only

---

## Compliance Checklist

- [x] Does not break existing C1-C4 pipeline
- [x] Preserves EmbeddingContract v1
- [x] Maintains SAFE_MODE functionality
- [x] No runtime weight updates (C5 isolation)
- [x] Determinism preserved in C3 inference
- [x] Observable via metrics and logs
- [x] Test strategy defined

---

## References

- NLSpec: nl_specs/nlspec.hybrid-snn-transformer.md
- NLSpec: nl_specs/nlspec.orchestrator.md
- AGENTS.md (architecture triggers)