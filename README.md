# Adaptive Rehab AI

AI-driven adaptive difficulty system for VR rehabilitation applications.

## Overview

A modular, extensible architecture that enables real-time AI-driven adaptation in VR rehabilitation while maintaining clinical-grade latency requirements.

**Components:**
- **Python Adaptation Service**: Standalone microservice with pluggable AI modules
- **Unity SDK Package**: Easy integration into Unity VR projects

## Features

- 🧩 **Modular Architecture**: Plug-and-play AI modules (RL, Fuzzy Logic, Rule-based)
- ⚡ **Low Latency**: <50ms adaptation loop for real-time performance
- 🛡️ **Clinical Safety**: Built-in safety wrapper with configurable bounds
- 🔄 **Hot-Swappable**: Change AI algorithms without stopping the session
- 📊 **Comprehensive Logging**: Session data, patient profiles, analytics
- 🎮 **Easy Integration**: Simple Unity SDK with example games

## Quick Start

### Python Service

```bash
# Install
pip install adaptive-rehab-ai

# Run service
adaptrehab-service --config config.yaml
```

### Unity SDK

```json
// Add to Unity package manifest.json
{
  "dependencies": {
    "com.adaptrehab.sdk": "https://github.com/arartawil/adaptive-rehab-ai.git?path=/unity-sdk"
  }
}
```

```csharp
// In your Unity script
using AdaptRehab;

var client = new AdaptRehabClient("localhost:50051");
await client.Initialize(patientProfile, taskConfig);

// In Update loop
var sensorData = sensorManager.CollectData();
var adaptation = await client.GetAdaptation(sensorData);
ApplyDifficulty(adaptation);
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Configuration & Policy Layer            │
├─────────────────────────────────────────────────┤
│           Adaptation Engine Layer               │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│   │   RL    │ │  Fuzzy  │ │  Rules  │          │
│   └─────────┘ └─────────┘ └─────────┘          │
├─────────────────────────────────────────────────┤
│        Performance Sensing Layer                │
├─────────────────────────────────────────────────┤
│          VR Interaction Layer (Unity)           │
├─────────────────────────────────────────────────┤
│            Data Persistence Layer               │
└─────────────────────────────────────────────────┘
```

## Example Games

- **Memory Card Game**: Grid size, time limit, card similarity adapt
- **Reaching Task**: Target distance, size, speed adapt
- **Balance Task**: Platform tilt, stability adapt

## Development Status

🚧 **Phase 1: Foundation** - In Progress

See [DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) for full roadmap.

## Documentation

- [Installation Guide](docs/installation.md)
- [API Reference](docs/api.md)
- [Creating Custom Games](docs/custom_games.md)
- [Adding AI Modules](docs/custom_modules.md)

## Requirements

**Python Service:**
- Python 3.8+
- gRPC, NumPy, PyYAML
- Optional: Stable-Baselines3, scikit-fuzzy

**Unity SDK:**
- Unity 2021.3 LTS or newer
- XR Interaction Toolkit
- gRPC for Unity

## License

MIT License - See [LICENSE](LICENSE)

## Citation

If you use this in research, please cite:

```bibtex
@software{adaptrehab2026,
  author = {Your Name},
  title = {Adaptive Rehab AI: Modular Architecture for VR Rehabilitation},
  year = {2026},
  url = {https://github.com/arartawil/adaptive-rehab-ai}
}
```

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

## Contact

- GitHub Issues: Bug reports and feature requests
- Discussions: Q&A and general discussion

---

**Research Paper**: "Adaptive VR Rehabilitation Software Architecture: A Modular Approach for Real-Time AI-Driven Difficulty Adaptation"
