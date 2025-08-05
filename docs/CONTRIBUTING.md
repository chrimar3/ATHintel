# Contributing to ATHintel

Thank you for your interest in contributing to ATHintel! This guide will help you get started.

## 🎯 Project Overview

ATHintel is an AI-powered platform for Athens real estate investment intelligence. We welcome contributions that improve data collection, enhance ML models, add new features, or improve documentation.

## 🤝 Ways to Contribute

### 1. 🐛 Issues & Bug Reports
- Search existing issues before creating new ones
- Provide detailed reproduction steps
- Include error messages and logs
- Specify your environment (Python version, OS, etc.)

### 2. 💡 Feature Requests  
- Explain the problem you're trying to solve
- Describe your proposed solution
- Consider implementation complexity
- Discuss potential impact on existing functionality

### 3. 📊 Data & Analysis Improvements
- New data sources for validation
- Additional neighborhoods or cities
- Enhanced ML models and algorithms
- Investment strategy optimizations

### 4. 🔧 Code Contributions
- Bug fixes and performance improvements
- New analysis features
- API enhancements
- Infrastructure improvements

## 🛠️ Development Setup

### Prerequisites
```bash
# Python 3.8 or higher
python --version

# Git for version control
git --version
```

### Installation
```bash
# Clone the repository
git clone https://github.com/chrimar3/ATHintel.git
cd ATHintel

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r config/requirements.txt

# Run tests to verify setup
python -m pytest tests/
```

## 📝 Code Style Guidelines

### Python Code Style
- Follow PEP 8 style guidelines
- Use meaningful variable names
- Add docstrings to all functions and classes
- Include type hints where appropriate
- Limit line length to 88 characters (Black formatter)

### Example Function Format
```python
def analyze_investment_opportunity(
    property_data: Dict[str, Any], 
    confidence_level: float = 0.95
) -> InvestmentOpportunity:
    """
    Analyze a single property for investment potential.
    
    Args:
        property_data: Dictionary containing property information
        confidence_level: Statistical confidence level (default: 0.95)
    
    Returns:
        InvestmentOpportunity object with complete analysis
        
    Raises:
        ValueError: If required fields are missing from property_data
    """
    # Implementation here
    pass
```

### ML Model Guidelines
- Document all model assumptions and limitations
- Include model validation and performance metrics
- Provide clear explanations of feature engineering
- Use cross-validation for model evaluation

## 🔍 Testing Guidelines

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_intelligence_engine.py

# Run with coverage report
python -m pytest --cov=. tests/
```

### Writing Tests
- Test all public functions and methods
- Include edge cases and error conditions
- Use descriptive test names
- Mock external dependencies (web scraping, databases)

### Example Test
```python
def test_investment_score_calculation():
    """Test investment score calculation with known data."""
    # Arrange
    test_property = {
        'neighborhood': 'Κολωνάκι',
        'price': 500000,
        'sqm': 100,
        'energy_class': 'B+'
    }
    
    # Act
    score = calculate_investment_score(test_property)
    
    # Assert
    assert 1.0 <= score <= 10.0
    assert isinstance(score, float)
```

## 📊 Data Contribution Guidelines

### Data Quality Standards
- **Authenticity**: All data must be from real, verifiable sources
- **Completeness**: Core fields (price, sqm, energy_class) must be present
- **Accuracy**: Data should reflect current market conditions
- **Provenance**: Include source URL and extraction timestamp

### Adding New Data Sources
1. Document the source (platform, URL, access method)
2. Create extraction script following existing patterns
3. Implement validation for data quality
4. Add tests for the new data pipeline
5. Update documentation with new source details

### Data Privacy
- No personal information (owner names, contact details)
- Aggregate data only for public analysis
- Respect platform terms of service
- Follow ethical scraping practices

## 🧠 ML Model Contributions

### Model Development Guidelines
- Use appropriate validation techniques (cross-validation, holdout sets)
- Document feature selection and engineering processes
- Include model performance metrics and comparisons
- Provide interpretability analysis for investment decisions

### Model Integration
- Follow existing model interface patterns
- Include comprehensive unit tests
- Document model parameters and hypertuning
- Provide example usage and expected outputs

## 📋 Pull Request Process

### Before Submitting
- [ ] Run all tests and ensure they pass
- [ ] Update documentation for any new features
- [ ] Add tests for new functionality
- [ ] Follow code style guidelines
- [ ] Update CHANGELOG.md if applicable

### Pull Request Template
```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that causes existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Investment Impact
- [ ] No impact on existing investment analysis
- [ ] Results may change (explain why)
- [ ] New investment capabilities added

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Review Process
1. Automated checks must pass (GitHub Actions)
2. Code review by project maintainers
3. Analysis validation for ML/investment changes
4. Documentation review for completeness
5. Merge after approval

## 📚 Documentation Contributions

### Types of Documentation
- Code documentation (docstrings, comments)
- Investment methodology (analysis approaches)
- User guides (how to run analyses)
- API documentation (function references)

### Documentation Standards
- Clear and concise explanations
- Include practical examples
- Keep up to date with code changes
- Use proper markdown formatting

## 🚨 Issue Reporting

### Bug Report Template
```markdown
## Bug Description
Clear description of the bug.

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen.

## Actual Behavior
What actually happens.

## Environment
- OS: [e.g., macOS 12.0]
- Python version: [e.g., 3.9.7]
- ATHintel version: [e.g., 1.0.0]
- Dependencies: [paste relevant package versions]

## Additional Context
Any other relevant information.
```

### Feature Request Template
```markdown
## Feature Description
Clear description of the proposed feature.

## Problem Statement
What problem does this solve?

## Proposed Solution
How should this be implemented?

## Investment Impact
How would this improve investment analysis?

## Implementation Notes
Technical considerations or constraints.
```

## 🏆 Recognition

### Contributors
All contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in commit messages
- Acknowledged in release notes
- Invited to co-author research papers (for significant contributions)

### Academic Collaboration
For substantial research contributions:
- Co-authorship opportunities on academic publications
- Conference presentation opportunities
- Research collaboration on related projects

## 📞 Getting Help

### Communication Channels
- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For general questions and ideas
- **Pull Request Comments**: For code-specific discussions

### Response Times
- **Bug reports**: 24-48 hours for initial response
- **Feature requests**: 1-2 weeks for evaluation
- **Pull requests**: 3-5 days for initial review

## 🔒 Security

If you discover a security vulnerability, please send an email to security@athintel.com instead of using the issue tracker.

## 📄 License

By contributing to ATHintel, you agree that your contributions will be licensed under the same MIT License that covers the project.

---

**Thank you for contributing to advancing real estate investment intelligence through AI and data science!**

🤖 *This project uses AI-assisted development with human oversight to ensure quality and accuracy.*