# GitHub Actions Setup Guide

## Required Secrets

To enable automatic publishing to PyPI, you need to set up the following secret in your GitHub repository:

### PYPI_API_TOKEN

1. Go to your GitHub repository: https://github.com/david2004kang/barcode-label-printer
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `PYPI_API_TOKEN`
5. Value: Your PyPI API token (get it from https://pypi.org/manage/account/token/)
6. Click **Add secret**

## Workflow Behavior

### On Pull Requests
- Runs tests on multiple Python versions and OS
- Does NOT publish to PyPI
- Validates package can be built

### On Push to Master
- Runs all tests
- Builds the package
- Publishes to PyPI (if tests pass)
- Verifies the published package can be installed

## Manual Testing

You can test the workflows locally:

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run self-test
python tests/self_test.py

# Build package
python -m build

# Check package
python -m twine check dist/*
```
