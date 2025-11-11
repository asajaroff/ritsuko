# Ritsuko

Zulip SRE Chat bot with MCP Access - A Python bot for infrastructure monitoring and operations.

## Description

Ritsuko is a Zulip chat bot that helps with SRE operations by providing:
- Node monitoring and information
- Kubernetes cluster status
- Nautobot device queries
- Integration with infrastructure APIs
- Health check endpoints

See [CLAUDE.md](CLAUDE.md) for detailed project information.

## Usage

### Running with Docker

```bash
docker run -ti asajaroff/ritsuko:latest
```

### Running locally

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r src/requirements.txt

# Run
./run.sh
```

## Testing

### Unit Tests
```bash
make test                 # Run unit tests
make test-coverage        # Run with coverage report
```

### Integration Tests
```bash
# Setup (first time)
cp .env.test.example .env.test
# Edit .env.test with your credentials

# Validate setup
./validate_test_setup.sh

# Run tests
make test-integration     # Run integration tests
make test-all            # Run all tests
```

See [docs/TESTING_QUICKSTART.md](docs/TESTING_QUICKSTART.md) for quick start guide.

See [docs/INTEGRATION_TESTING.md](docs/INTEGRATION_TESTING.md) for complete testing documentation.

## Makefile Targets

Run `make help` to see all available targets:

```bash
make build               # Build Docker image
make push                # Build and push to registry
make release             # Update chart version and release
make test                # Run unit tests
make test-integration    # Run integration tests against live bot
make test-all           # Run all tests
make helm-install        # Install via Helm
```

## 
