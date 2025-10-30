# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

- **Nautobot integration** (`src/fetchers.py`, `src/commands.py`)
  - New `get_nautobot_devices()` function to query Nautobot API for device information
  - New `nautobot` command that accepts node names as arguments
  - Retrieves and displays device information including:
    - Device name with link to Nautobot
    - Rack information with link
    - Kubernetes version from custom fields
  - Supports querying multiple nodes in a single command
  - Comprehensive error handling for API requests (OSError, AttributeError, JSONDecodeError)
  - Uses `urllib3.PoolManager` for HTTP requests

- **Nautobot configuration** (`chart/templates/deployment.yaml`, `chart/templates/secret.yaml`, `chart/values.yaml`)
  - Added `NAUTOBOT_TOKEN` environment variable
  - Added `NAUTOBOT_URL` environment variable
  - New secret fields for Nautobot API credentials
  - Documented GitHub Matchbox token in values.yaml

- **Additional authorized user** (`src/bot.py`)
  - Added `manuvs@een.com` (without the dot)

### Changed

- **Makefile version bump**
  - Updated `IMAGE_TAG` from `v1.0.4` to `v1.1.0`
  - Modified release target to echo git commands instead of executing them (for safer releases)

- **Helm chart metadata** (`chart/Chart.yaml`)
  - Updated `appVersion` from `v1.0.4-05ebf72` to `v1.1.0-1e58eae`

- **Test suite enhancements** (`src/test_bot.py`)
  - Added comprehensive tests for Nautobot integration:
    - `test_get_nautobot_devices_success` - Tests successful device retrieval
    - `test_get_nautobot_devices_no_results` - Tests empty results handling
    - `test_get_nautobot_devices_with_missing_fields` - Tests handling of optional fields
    - `test_get_nautobot_devices_api_error` - Tests API error handling
    - `test_handle_nautobot_single_node` - Tests single node query
    - `test_handle_nautobot_multiple_nodes` - Tests multiple node queries
  - Updated all node command tests to mock HTTP requests properly
  - Added mock responses for Matchbox API calls in node tests
  - Added environment variable setup for `NAUTOBOT_TOKEN`, `NAUTOBOT_URL`, and `GITHUB_MATCHBOX_TOKEN`
  - Updated imports to include `json`, `Mock`, `handle_nautobot`, `get_nautobot_devices`, and `handle_node`
  - Fixed test expectations: changed "Useful system checks" to "Terminal one-liners"
  - Fixed kubectl command expectation: changed "kubectl events" to "kubectl get events"
  - All tests now properly mock external API calls

### Fixed

- **Bug in command routing** (`src/commands.py`)
  - Fixed reference to non-existent `handle_ping()` function in line 164
  - Changed `ai` command to return placeholder message: "AI command is not yet implemented. Coming soon!"
  - Changed `mcp` command to return placeholder message: "MCP command is not yet implemented. Coming soon!"

## [v1.0.4] - 2025-10-26 (commit 7e5afb7)

### Added

- **Health check HTTP server** (`src/bot.py`)
  - New HTTP server running on port 8080 for Kubernetes health checks
  - `/healthz` endpoint for liveness probes
  - `/readyz` endpoint for readiness probes
  - Runs in a separate daemon thread to avoid blocking bot operations
  - Includes `HealthCheckHandler` class with suppressed logging to avoid cluttering logs

- **Kubernetes probes configuration** (`chart/templates/deployment.yaml`, `chart/values.yaml`)
  - Added `livenessProbe` configuration:
    - HTTP GET to `/healthz` on port 8080
    - 10s initial delay, 10s period, 5s timeout, 3 failure threshold
  - Added `readinessProbe` configuration:
    - HTTP GET to `/readyz` on port 8080
    - 5s initial delay, 5s period, 3s timeout, 3 failure threshold
  - Container port 8080 exposed for health checks

- **Additional authorized users** (`src/bot.py`)
  - Added `miniguez@een.com`
  - Added `jchio@een.com`
  - Added `mgolden@een.com`
  - Added `pwhiteside@een.com`

- **Comprehensive test coverage for health checks** (`src/test_bot.py`)
  - Tests for health server startup
  - Tests for `/healthz` endpoint (200 OK response)
  - Tests for `/readyz` endpoint (200 OK response)
  - Tests for invalid endpoints (404 response)

- **Enhanced node command tests** (`src/test_bot.py`)
  - Tests for single and multiple node names
  - Tests for node command without arguments
  - Tests for node command from stream messages
  - Tests for kubectl commands in output
  - Tests for all three Grafana dashboard links
  - Tests for journalctl SSH examples
  - Tests for special characters in node names
  - Tests for markdown formatting

### Changed

- **Image repository** (`Makefile`, `chart/values.yaml`)
  - Changed from `asajaroff/ritsuko` to `harbor.eencloud.com/test/ritsuko`
  - Updated push target in Makefile to use new repository

- **Helm chart metadata** (`chart/Chart.yaml`)
  - Updated chart version from `0.1.0` to `0.2.0`
  - Updated app version from `v1.0.4-733efa6` to `v1.0.4-7b85980`
  - Improved chart description: "A Helm chart for deploying Ritsuko in a Kubernetes cluster"

- **Help command output** (`src/commands.py`)
  - Reorganized command list with better categorization
  - Added placeholders for upcoming features (ai, mcp, jira, confluence)
  - Improved formatting with markdown code blocks
  - Added usage examples
  - Removed `ping` and `echo` commands from help text

- **Node command output** (`src/commands.py`)
  - Enhanced output structure with better markdown formatting
  - Moved Grafana links to the top for easier access
  - Updated kubectl events command syntax: `kubectl events --for node/{node} --context $KUBE_CLUSTER`
  - Added useful system checks section with multiple systemctl commands:
    - kubelet.service status
    - containerd.service status
    - docker.service status
  - Updated journalctl command to include `--no-follow` flag

- **Clusters command output** (`src/commands.py`)
  - Added link to VMS Global Uptime dashboard in header
  - Removed obsolete clusters (c000, c004, c005, c010)

- **Command routing** (`src/commands.py`)
  - Reordered match cases: help, ai, mcp, node, clusters, status, version
  - Removed `ping` and `echo` command handlers

- **Version command** (`src/commands.py`)
  - Updated default version string to include more context

### Removed

- **Removed `src/run.sh` script**
  - Shell script is no longer needed for local development

### Technical Improvements

- **Production readiness**: Health checks enable proper Kubernetes lifecycle management
- **Reliability**: Kubernetes probes can detect and restart unhealthy pods
- **Monitoring**: Dedicated health endpoints separate from application logic
- **Developer experience**: Enhanced command outputs with better structure and more useful information

- **Command parsing system** (`src/commands.py`)
  - New `parse_command()` function that intelligently parses commands based on message type:
    - Stream messages: extracts second word (first word after bot mention)
    - Private messages: extracts first word directly
  - New `execute_command()` function with match/case (Python 3.10+) switch statement for command routing
  - Built-in commands:
    - `help` - Display available commands
    - `ping` - Health check / bot responsiveness test
    - `status` - Show bot operational status
    - `echo <text>` - Echo back provided text
    - `version` - Display bot version information
  - Extensible command handler architecture for easy addition of new commands
  - Unknown command handling with helpful error messages

- **Command parsing tests** in `src/test_bot.py`
  - Tests for command parsing from stream messages
  - Tests for command parsing from private messages
  - Tests for all command handlers (help, ping, status, echo, version)
  - Tests for edge cases (empty messages, unknown commands, missing arguments)
  - Integration tests for command execution within message handling flow
  - Total of 20 passing tests covering all functionality

- **Comprehensive error handling throughout the bot**
  - Environment variable validation at startup (checks for `ZULIP_EMAIL`, `ZULIP_API_KEY`, `ZULIP_SITE`)
  - Try-except block around Zulip client initialization with proper error logging
  - New `send_message()` helper function that wraps all message sending with error handling
  - Exception handling in `handle_message()` for `KeyError` and general exceptions
  - Graceful shutdown handling for `KeyboardInterrupt` in main message loop
  - Proper exit codes for different failure scenarios

- **Unit test suite** (`src/test_bot.py`)
  - Tests for `send_message()` function:
    - Successful message sending
    - Failed message sending (Zulip API errors)
    - Exception handling (network errors, etc.)
  - Tests for `handle_message()` function:
    - Bot ignoring its own messages
    - Authorized user messages in private chats
    - Authorized user messages in streams
    - Unauthorized user messages in private chats
    - Unauthorized user messages in streams
    - Handling of messages with missing required fields
  - All tests use proper mocking to avoid requiring actual Zulip connections

- **Testing dependencies**
  - Added `pytest==8.3.4` to requirements.txt
  - Added `pytest-cov==6.0.0` to requirements.txt for coverage reporting

- **Makefile targets for testing**
  - `make test`: Runs the full test suite with verbose output
  - `make test-coverage`: Runs tests with coverage report showing line-by-line coverage

### Changed

- **Bot message handling** (`src/bot.py`)
  - Integrated command parsing system via `execute_command()` import
  - Bot now routes all authorized user messages through the command parser
  - Responses are now generated by command handlers instead of simple echo
  - Message handling tests updated to validate command execution flow

- Refactored all `client.send_message()` calls to use the new `send_message()` helper function
- Added docstrings to `send_message()` and `handle_message()` functions
- Enhanced logging messages with better error context
- Bot now logs "Starting Zulip bot..." message on startup for better visibility

### Removed

- Removed commented-out code (lines 40-47) that was no longer needed
  - Removed unused `original_content` variable
  - Removed unused `original_sender` variable
  - Removed placeholder code for `@followup` functionality

### Technical Improvements

- **Robustness**: Bot will now fail fast with clear error messages if misconfigured
- **Observability**: All errors are properly logged with context for easier debugging
- **Maintainability**: Centralized error handling makes future changes easier
- **Testability**: Comprehensive test coverage ensures reliability and makes refactoring safer
- **Production-ready**: Proper signal handling allows clean shutdowns in containerized environments

### Test Coverage

The test suite covers:
- Authorization logic (authorized vs unauthorized users)
- Message type handling (private vs stream messages)
- Error scenarios (missing fields, API failures, network errors)
- Bot self-message filtering
- Message response content verification

## Previous Changes

### [Initial Release]

- Basic Zulip bot functionality with message echoing
- Authorization based on hardcoded user list
- Support for both private messages and stream messages
- Environment-based configuration for Zulip credentials
- Docker containerization support
- Helm chart for Kubernetes deployment
- Makefile for common operations
