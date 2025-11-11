# Requirements and Docker Images Split

## Overview

The project now uses separate requirements files and Docker images for production and development/testing environments.

## Changes Made

### 1. Requirements Files

- **`src/requirements.txt`** - Production dependencies only
  - Core bot functionality (zulip, anthropic, requests, etc.)
  - ~169MB Docker image size

- **`src/requirements-test.txt`** - Testing dependencies
  - pytest, pytest-cov, pytest-timeout
  - Only installed in development and debug images

### 2. Docker Images

- **`Dockerfile`** - Production image (minimal)
  - No debug tools
  - No testing dependencies
  - Smaller image size for faster deployment
  - Used by default for production deployments

- **`Dockerfile.debug`** - Debug/development image
  - Includes network debugging tools: curl, dnsutils, iputils-ping
  - Includes editor: vim
  - Includes testing dependencies
  - Used for local debugging and troubleshooting

### 3. Makefile Targets

- `make build` - Build production image
- `make build-debug` - Build debug image with all tools
- `make debug` - Build and run debug container locally
- `make test` - Run tests (automatically installs test requirements)
- `make test-coverage` - Run tests with coverage report

## Benefits

1. **Smaller Production Images**: Production image is ~56MB smaller (25% reduction)
2. **Faster Deployments**: Less data to transfer during deployment
3. **Better Security**: Fewer tools in production means smaller attack surface
4. **Clearer Separation**: Development tools clearly separated from production code
5. **Easier Maintenance**: Dependencies organized by purpose

## Usage

### For Production Deployment

```bash
make build
make push
make helm-install
```

### For Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
pip install -r src/requirements-test.txt
./run.sh
```

### For Debugging in Container

```bash
make debug  # Runs debug container with all tools
```

### For Testing

```bash
make test           # Run unit tests
make test-coverage  # Run tests with coverage
```

## Image Sizes

- Production image: ~169MB
- Debug image: ~225MB (includes all debugging tools)
- Size reduction: ~56MB (25% smaller)
