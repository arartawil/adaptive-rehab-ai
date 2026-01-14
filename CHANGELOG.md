# Changelog

All notable changes to Adaptive Rehab AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Unity SDK C# client
- Fuzzy logic adaptation module
- Reinforcement learning (PPO) module
- Progress analytics dashboard
- Therapist configuration UI

## [0.1.0] - 2026-01-14

### Added
- **Core Engine**
  - AdaptationEngine with pluggable AI modules
  - SafetyWrapper with configurable bounds
  - EventBus for publish/subscribe events
  - ConfigManager for YAML configuration
  
- **AI Modules**
  - RuleBasedModule - Threshold-based adaptation
  
- **Communication**
  - gRPC server for Unity/C# clients
  - REST API server for web applications
  - Direct Python integration
  
- **Demo Applications**
  - Memory card matching game (Tkinter)
  - Reaction time game (Tkinter)
  - HTML memory game (browser-based)
  
- **Testing**
  - Comprehensive test suite
  - Performance benchmarks
  - Integration tests
  
- **Documentation**
  - README with quick start guide
  - Architecture documentation
  - API examples
  - Publishing guide

### Performance
- Core latency: <1ms
- gRPC latency: 2.78ms
- Throughput: 17,307 adaptations/sec

---

## Release History

### Version Numbering
- **0.1.x**: Initial release, core features
- **0.2.x**: Unity SDK
- **0.3.x**: Advanced AI modules (fuzzy, RL)
- **1.0.0**: Production-ready stable release
