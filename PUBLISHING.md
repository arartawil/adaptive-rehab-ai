# Publishing to PyPI

This guide shows how to publish Adaptive Rehab AI to PyPI so users can install it with `pip install adaptive-rehab-ai`.

## Prerequisites

1. **PyPI Account**: Create account at https://pypi.org
2. **Test PyPI Account** (optional): https://test.pypi.org
3. **Install tools**:
   ```bash
   pip install build twine
   ```

## Build the Package

```bash
# From project root
cd "c:\Users\ROG SRTIX\Desktop\vr PAPER\adaptive-rehab-ai"

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build source and wheel distributions
python -m build
```

This creates:
- `dist/adaptive-rehab-ai-0.1.0.tar.gz` (source)
- `dist/adaptive_rehab_ai-0.1.0-py3-none-any.whl` (wheel)

## Test Locally

```bash
# Install from local build
pip install dist/adaptive_rehab_ai-0.1.0-py3-none-any.whl

# Test it works
python -c "from adaptrehab.core import AdaptationEngine; print('Success!')"

# Uninstall
pip uninstall adaptive-rehab-ai
```

## Upload to Test PyPI (Optional)

Test before real upload:

```bash
# Upload to test.pypi.org
python -m twine upload --repository testpypi dist/*

# Install from test PyPI
pip install --index-url https://test.pypi.org/simple/ adaptive-rehab-ai

# Test it works
python -c "from adaptrehab.core import AdaptationEngine; print('Success!')"
```

## Upload to Real PyPI

```bash
# Upload to pypi.org
python -m twine upload dist/*

# Enter your PyPI username and password when prompted
```

## After Publishing

Users can now install with:

```bash
pip install adaptive-rehab-ai
```

## Update Version

When releasing updates:

1. Edit `setup.py` - change version number (e.g., `0.1.0` → `0.1.1`)
2. Rebuild: `python -m build`
3. Upload: `python -m twine upload dist/*`

## Versioning

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backward compatible
- **PATCH** (0.0.1): Bug fixes

---

## Alternative: GitHub Releases

Users can also install directly from GitHub:

```bash
pip install git+https://github.com/arartawil/adaptive-rehab-ai.git
```

Or specific version/branch:

```bash
pip install git+https://github.com/arartawil/adaptive-rehab-ai.git@v0.1.0
pip install git+https://github.com/arartawil/adaptive-rehab-ai.git@main
```
