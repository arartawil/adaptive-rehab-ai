# Quick Setup Guide

## Phase 1 Complete! ✅

You now have the foundation structure set up. Here's what to do next:

## 1. Initialize Git Repository

```powershell
cd "c:\Users\ROG SRTIX\Desktop\vr PAPER\adaptive-rehab-ai"
git init
git add .
git commit -m "Initial commit: Phase 1 foundation"
git branch -M main
git remote add origin https://github.com/arartawil/adaptive-rehab-ai.git
git push -u origin main
```

## 2. Set Up Python Environment

```powershell
cd service
python -m venv venv
.\venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Generate gRPC Code

```powershell
cd protos
python -m grpc_tools.protoc -I. --python_out=../adaptrehab/comms --grpc_python_out=../adaptrehab/comms adaptation.proto
```

## 4. Run Tests (when implemented)

```powershell
cd ..
pytest tests/ -v
```

## What's Been Created

### ✅ Project Structure
- Complete folder hierarchy
- Python package structure
- Unity SDK structure

### ✅ Core Files
- **AMI Interface** (`base_module.py`) - The contract all AI modules follow
- **gRPC Protocol** (`adaptation.proto`) - Communication definition
- **Configuration files** (setup.py, pyproject.toml, requirements.txt)
- **Unity package.json** - UPM compatible

### ✅ Documentation
- README.md with project overview
- LICENSE (MIT)
- CONTRIBUTING.md
- .gitignore

## Next Steps (Phase 2)

### Week 3-4: Core Implementation

1. **Implement AdaptationEngine** (`core/adaptation_engine.py`)
   - Module registry
   - Event loop
   - Hot-swapping logic

2. **Create Rule-Based Module** (`modules/rule_based.py`)
   - Simple baseline algorithm
   - Threshold-based decisions

3. **Implement Safety Wrapper** (`core/safety_wrapper.py`)
   - Bounds checking
   - Clinical constraints

4. **Build gRPC Server** (`comms/grpc_server.py`)
   - Service implementation
   - Connection handling

## Verification Checklist

- [ ] Git repository initialized and pushed
- [ ] Python virtual environment created
- [ ] Dependencies installed successfully
- [ ] No import errors when running `python -c "import adaptrehab"`
- [ ] gRPC files generated successfully

## Useful Commands

```powershell
# Format code
black adaptrehab/

# Run type checking
mypy adaptrehab/

# Check code style
flake8 adaptrehab/

# Install in development mode
pip install -e .
```

## Current Project Status

📊 **Completion: Phase 1 of 10 (10%)**

✅ Foundation laid
⏳ Next: Core engine implementation
🎯 Goal: Working prototype in 8 weeks

## Questions?

- Check [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md) for detailed roadmap
- See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines

---

**You're ready to start Phase 2!** 🚀
