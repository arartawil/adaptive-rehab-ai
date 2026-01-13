# Contributing to Adaptive Rehab AI

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/adaptive-rehab-ai.git
   cd adaptive-rehab-ai
   ```

3. **Set up development environment**
   ```bash
   cd service
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Python Service

1. **Code style**: Use Black formatter (line length 100)
   ```bash
   black adaptrehab/
   ```

2. **Type hints**: Use type hints for all functions
   ```python
   def my_function(param: int) -> str:
       return str(param)
   ```

3. **Run tests**
   ```bash
   pytest tests/
   ```

4. **Check coverage**
   ```bash
   pytest --cov=adaptrehab tests/
   ```

### Unity SDK

1. **Follow Unity C# conventions**
2. **Add XML documentation comments**
   ```csharp
   /// <summary>
   /// Brief description
   /// </summary>
   /// <param name="data">Parameter description</param>
   ```

3. **Test in Unity 2021.3 LTS minimum**

## Adding New AI Modules

1. Inherit from `AdaptationModule` base class
2. Implement all abstract methods
3. Add configuration schema
4. Write unit tests
5. Add example usage in documentation

Example:
```python
from adaptrehab.modules.base_module import AdaptationModule

class MyNewModule(AdaptationModule):
    async def initialize(self, config, patient_profile):
        # Implementation
        pass
    
    # ... implement other methods
```

## Pull Request Process

1. **Update documentation** if adding features
2. **Add tests** for new functionality (aim for >80% coverage)
3. **Update CHANGELOG.md** with your changes
4. **Ensure all tests pass**
5. **Create PR with descriptive title and description**

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Added unit tests
- [ ] Tested manually
- [ ] All tests pass

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## Code Review Process

- PRs require at least one approval
- Address reviewer comments
- Maintainers will merge after approval

## Reporting Bugs

Use GitHub Issues with:
- Clear title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, Unity version, OS)

## Feature Requests

Use GitHub Discussions for:
- Proposed features
- Design discussions
- Questions about architecture

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help create a welcoming environment

## Questions?

Open a Discussion or reach out via Issues.

Thank you for contributing! 🎉
