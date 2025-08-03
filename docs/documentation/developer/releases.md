# Release Process

This document describes the release process for A2A Registry.

## Overview

A2A Registry uses a manual release process with GitHub Actions for building, testing, and publishing packages. The process ensures quality and consistency across releases.

## Prerequisites

Before making a release, ensure you have:

1. **GitHub Secrets configured**:
   - `PYPI_API_TOKEN`: PyPI API token for publishing to PyPI
   - `TEST_PYPI_API_TOKEN`: TestPyPI API token for testing releases

2. **Write access** to the repository for creating releases

3. **All tests passing** on the main branch

## Release Process

### 1. Prepare the Release

Use the release script to update the version and prepare the release:

```bash
# Update version and build package
python scripts/release.py 0.1.1

# Or just update version without building
python scripts/release.py 0.1.1 --dry-run

# Skip tests (use with caution)
python scripts/release.py 0.1.1 --skip-tests
```

The script will:
- Update the version in `src/a2a_registry/__init__.py`
- Run linting, type checking, and tests
- Build the distribution packages

### 2. Manual Release via GitHub Actions

1. **Go to GitHub Actions**: Navigate to the Actions tab in the repository
2. **Select "Release" workflow**: Click on the "Release" workflow
3. **Run workflow**: Click "Run workflow" button
4. **Configure release**:
   - **Version**: Enter the version to release (e.g., `0.1.1`)
   - **Publish to TestPyPI**: Check to publish to TestPyPI first (recommended)
   - **Publish to PyPI**: Check to publish to PyPI (uncheck for dry run)

### 3. Workflow Steps

The release workflow performs the following steps:

#### Validation Job
- Runs linting, type checking, and tests
- Validates that the version in code matches the requested version
- Ensures all quality gates pass

#### Build Job
- Builds distribution packages (wheel and source distribution)
- Uploads build artifacts for use by subsequent jobs

#### TestPyPI Publishing (Optional)
- Publishes to TestPyPI for testing
- Allows verification before publishing to PyPI

#### PyPI Publishing (Optional)
- Publishes to PyPI for production use
- Only runs if "Publish to PyPI" is checked

#### GitHub Release Creation
- Creates a GitHub release with the built packages
- Includes release notes and documentation links
- Only runs if PyPI publishing is enabled

## Version Management

### Version Format
Versions follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Version Locations
The version is defined in:
- `src/a2a_registry/__init__.py` - `__version__` variable
- `pyproject.toml` - Uses dynamic versioning from `__init__.py`

## Release Checklist

Before triggering a release:

- [ ] All tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`make typecheck`)
- [ ] Documentation is up to date
- [ ] Version is updated in `__init__.py`
- [ ] Changes are committed and pushed to main branch
- [ ] GitHub secrets are configured

## Troubleshooting

### Common Issues

1. **Version Mismatch**: Ensure the version in `__init__.py` matches the requested release version
2. **Test Failures**: Fix any failing tests before releasing
3. **Build Failures**: Check that all dependencies are properly specified
4. **PyPI Upload Failures**: Verify API tokens are correct and have proper permissions

### Rollback Process

If a release needs to be rolled back:

1. **PyPI**: Use PyPI's web interface to delete the problematic version
2. **GitHub Release**: Delete the GitHub release and tag
3. **Documentation**: Update any references to the problematic version

## Security Considerations

- API tokens are stored as GitHub secrets
- Tokens have minimal required permissions
- TestPyPI is used for testing before production release
- All builds run in isolated environments

## Support

For issues with the release process:

1. Check the GitHub Actions logs for detailed error messages
2. Verify all prerequisites are met
3. Ensure the release script is working correctly
4. Contact the maintainers if issues persist