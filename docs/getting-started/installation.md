# Installation

This guide will help you install and set up the A2A Registry server.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)

## Installation Methods

### From PyPI (Recommended)

```bash
pip install a2a-registry
```

### From Source

If you want to install from source or contribute to the project:

```bash
# Clone the repository
git clone https://github.com/allenday/a2a-registry.git
cd a2a-registry

# Initialize submodules
git submodule update --init --recursive

# Install in development mode
make install-dev
```

## Verify Installation

After installation, verify that the A2A Registry is installed correctly:

```bash
a2a-registry --help
```

You should see the help output with available commands.

## Next Steps

- [Quick Start Guide](quickstart.md) - Get the server running in minutes
- [Configuration](configuration.md) - Customize server settings
- [API Overview](../api/overview.md) - Learn about the API endpoints