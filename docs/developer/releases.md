# Release Process

This document outlines the release process for the A2A Registry project.

## Release Types

### Semantic Versioning

We follow [Semantic Versioning](https://semver.org/) (SemVer):

- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (0.X.0): New features, backwards compatible
- **PATCH** (0.0.X): Bug fixes, backwards compatible

Examples:
- `1.0.0` → `1.0.1`: Bug fix
- `1.0.0` → `1.1.0`: New feature
- `1.0.0` → `2.0.0`: Breaking change

### Release Channels

- **Stable**: Production releases (e.g., `1.2.0`)
- **Pre-release**: Beta/RC versions (e.g., `1.2.0-beta.1`)
- **Development**: Snapshot builds from main branch

## Release Preparation

### 1. Version Planning

Before starting a release:

1. **Review milestone**: Check GitHub milestone for target features/fixes
2. **Test coverage**: Ensure adequate test coverage for new features
3. **Documentation**: Update documentation for new features
4. **Breaking changes**: Document any breaking changes clearly

### 2. Pre-release Checklist

- [ ] All CI checks passing
- [ ] No known critical bugs
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in `pyproject.toml`
- [ ] Tests passing locally and in CI
- [ ] Security audit completed (if applicable)

### 3. Version Bump

Update the version in `pyproject.toml`:

```toml
[project]
name = "a2a-registry"
version = "1.2.0"  # Update this version
```

### 4. Update Changelog

Maintain `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/):

```markdown
# Changelog

## [1.2.0] - 2025-01-15

### Added
- New search filters for agent discovery
- Support for agent health monitoring
- gRPC streaming endpoints

### Changed
- Improved error handling in REST API
- Updated A2A protocol to version 1.1.0

### Fixed
- Race condition in concurrent agent registration
- Memory leak in long-running server instances

### Deprecated
- Legacy search API (will be removed in v2.0.0)

## [1.1.0] - 2025-01-01
...
```

## Release Process

### Automated Release (Recommended)

We use GitHub Actions for automated releases:

1. **Create release branch**:
   ```bash
   git checkout -b release/v1.2.0
   git push origin release/v1.2.0
   ```

2. **Create pull request**:
   - Title: "Release v1.2.0"
   - Description: Include changelog excerpt
   - Base: `main`

3. **Review and merge**: After approval, merge the PR

4. **Create GitHub release**:
   - Tag: `v1.2.0`
   - Title: "A2A Registry v1.2.0"
   - Description: Include changelog
   - GitHub Actions will automatically:
     - Build packages
     - Run full test suite
     - Publish to PyPI
     - Deploy documentation

### Manual Release

If automated release fails:

1. **Tag the release**:
   ```bash
   git tag -a v1.2.0 -m "Release v1.2.0"
   git push origin v1.2.0
   ```

2. **Build and test**:
   ```bash
   make clean
   make build
   ```

3. **Publish to PyPI**:
   ```bash
   # Test PyPI first
   make publish-test
   
   # Then production PyPI
   make publish
   ```

4. **Deploy documentation**:
   ```bash
   make docs-deploy
   ```

5. **Create GitHub release**: Manually create release on GitHub

## Release Validation

### Post-Release Checks

After each release:

1. **PyPI verification**:
   ```bash
   pip install a2a-registry==1.2.0
   a2a-registry --version
   ```

2. **Docker verification**:
   ```bash
   docker run allendy/a2a-registry:1.2.0 --version
   ```

3. **Documentation check**: Verify docs site is updated

4. **Installation test**: Test installation on clean environment

### Smoke Tests

Run basic functionality tests:

```bash
# Start server
a2a-registry serve &
SERVER_PID=$!

# Basic API test
curl -f http://localhost:8000/health

# Register test agent
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{"agent_card": {"name": "test", "description": "test", "url": "http://test", "version": "1.0.0", "protocol_version": "1.0.0", "skills": []}}'

# List agents
curl -f http://localhost:8000/agents

# Cleanup
kill $SERVER_PID
```

## Hotfix Process

For critical bugs in production:

### 1. Create Hotfix Branch

```bash
git checkout main
git pull origin main
git checkout -b hotfix/v1.2.1
```

### 2. Apply Fix

- Make minimal changes to fix the issue
- Add regression test
- Update version to patch level (e.g., 1.2.0 → 1.2.1)

### 3. Test Thoroughly

```bash
make dev-check
# Additional manual testing for the specific issue
```

### 4. Fast-track Release

- Create PR with expedited review
- Merge and release immediately
- Follow standard release process but with higher urgency

## Release Artifacts

Each release produces:

### PyPI Package
- Source distribution (`.tar.gz`)
- Wheel distribution (`.whl`)
- Available at: https://pypi.org/project/a2a-registry/

### GitHub Release
- Release notes
- Source code archives
- Attached binaries (if any)

### Documentation
- Updated docs site
- API reference
- Examples and tutorials

### Docker Images
- `allendy/a2a-registry:latest`
- `allendy/a2a-registry:1.2.0`
- Multi-architecture support (amd64, arm64)

## Version Support

### Support Policy

- **Current major version**: Full support (features, bugs, security)
- **Previous major version**: Security fixes only for 12 months
- **Older versions**: Community support only

### Security Updates

Security issues are addressed with:
- Patch releases for supported versions
- Advisory notices for unsupported versions
- Coordination with security researchers

## Communication

### Release Announcements

1. **GitHub release notes**: Detailed changelog
2. **PyPI description**: Brief summary
3. **Documentation**: Updated with new features
4. **Community**: Announce in discussions/issues

### Breaking Changes

For major version releases with breaking changes:

1. **Migration guide**: Detailed upgrade instructions
2. **Deprecation warnings**: In previous minor releases
3. **Compatibility matrix**: Supported A2A protocol versions
4. **Examples**: Updated code examples

## Automation

### GitHub Actions Workflow

`.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: make install-dev
      
      - name: Run tests
        run: make dev-check
      
      - name: Build package
        run: make build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: make publish
      
      - name: Deploy docs
        run: make docs-deploy
      
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          generate_release_notes: true
```

### Release Scripts

Maintain release automation scripts:

```bash
#!/bin/bash
# scripts/release.sh

set -e

VERSION=$1
if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version>"
  exit 1
fi

echo "Preparing release $VERSION..."

# Update version
sed -i "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml

# Run checks
make dev-check

# Commit changes
git add pyproject.toml CHANGELOG.md
git commit -m "Release $VERSION"

# Create tag
git tag -a "v$VERSION" -m "Release $VERSION"

echo "Release $VERSION prepared. Push with:"
echo "  git push origin main"
echo "  git push origin v$VERSION"
```

## Rollback Procedure

If a release has critical issues:

### 1. Assess Impact
- Determine severity and affected users
- Check if hotfix is feasible vs. rollback

### 2. PyPI Rollback
- Cannot delete PyPI releases
- Publish new patch version with fix
- Mark problematic version in release notes

### 3. Documentation
- Update docs to reflect issues
- Provide workarounds or downgrade instructions

### 4. Communication
- Post issue notice on GitHub
- Update release notes
- Notify affected users

This release process ensures consistent, reliable releases while maintaining high quality standards.