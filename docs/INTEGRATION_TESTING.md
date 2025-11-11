# Integration Testing Guide

This guide explains how to run integration tests against a live Ritsuko bot instance.

## Overview

The integration test suite (`tests/test_integration.py`) tests the bot by sending actual messages to a live Zulip instance and verifying the bot's responses. This ensures the bot works correctly in a real environment.

## Test Categories

The test suite includes the following test categories:

### 1. Command Tests (`TestBotCommands`)
Tests all bot commands:
- `help` - Help message
- `status` - Bot status
- `version` - Bot version
- `clusters` / `cluster` - Cluster listing
- `node` - Node information
- `nautobot` - Nautobot device queries
- Unknown commands

### 2. Mention Behavior Tests (`TestBotMentionBehavior`)
Tests bot mention handling:
- Response to private messages
- Response to stream mentions
- Ignoring stream messages without mentions

### 3. Authorization Tests (`TestBotAuthorization`)
Tests access control:
- Authorized user access
- Unauthorized user rejection (private)
- Unauthorized user rejection (stream)

### 4. Health Endpoint Tests (`TestBotHealthEndpoints`)
Tests HTTP health check endpoints:
- `/healthz` endpoint
- `/readyz` endpoint
- Invalid endpoint (404)

### 5. Performance Tests (`TestBotResponseTimes`)
Tests response time performance:
- Simple command response time (< 10s)
- Help command response time (< 10s)

### 6. Edge Case Tests (`TestBotEdgeCases`)
Tests error handling:
- Very long messages
- Special characters
- Multiple spaces
- Mixed case commands

### 7. Nautobot Tests (`TestNautobotCommand`)
Tests Nautobot integration:
- Command without arguments
- Command with real node (optional)

## Setup

### Prerequisites

1. Python 3.8 or higher
2. Access to a Zulip instance with the bot deployed
3. A test user account with API access (must be in authorized users list)
4. (Optional) An unauthorized user account for authorization tests

### Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd ritsuko
```

2. Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip3 install -r src/requirements.txt
pip3 install pytest pytest-timeout
```

### Configuration

1. Copy the example environment file:
```bash
cp .env.test.example .env.test
```

2. Edit `.env.test` and fill in your credentials:
```bash
# Required
ZULIP_TEST_EMAIL=your-test-user@een.com
ZULIP_TEST_API_KEY=your-api-key-here
ZULIP_SITE=https://your-org.zulipchat.com
ZULIP_BOT_EMAIL=ritsuko-bot@een.com

# Optional
RITSUKO_TEST_STREAM=test
BOT_HEALTH_URL=http://localhost:8080
RITSUKO_TEST_UNAUTHORIZED_EMAIL=unauth@example.com
RITSUKO_TEST_UNAUTHORIZED_API_KEY=unauth-key
RITSUKO_TEST_REAL_NODE=aus1p1-worker-01
RITSUKO_TEST_NAUTOBOT_NODE=aus1p1-worker-01
```

### Getting Your Zulip API Key

1. Log in to your Zulip instance
2. Go to Settings → Account & Privacy
3. Under "API key", click "Show/generate API key"
4. Copy the API key to your `.env.test` file

## Running Tests

### Using the Test Runner Script (Recommended)

```bash
./run_integration_tests.sh
```

For verbose output:
```bash
./run_integration_tests.sh -v
```

### Using pytest Directly

```bash
# Load environment variables
source .env.test

# Run all tests
python3 -m pytest tests/test_integration.py -v

# Run specific test class
python3 -m pytest tests/test_integration.py::TestBotCommands -v

# Run specific test
python3 -m pytest tests/test_integration.py::TestBotCommands::test_help_command_private -v

# Run with verbose output
python3 -m pytest tests/test_integration.py -v -s
```

### Running a Subset of Tests

```bash
# Only command tests
python3 -m pytest tests/test_integration.py::TestBotCommands -v

# Only authorization tests
python3 -m pytest tests/test_integration.py::TestBotAuthorization -v

# Only health endpoint tests
python3 -m pytest tests/test_integration.py::TestBotHealthEndpoints -v
```

## Test Configuration Options

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `ZULIP_TEST_EMAIL` | Email of authorized test user |
| `ZULIP_TEST_API_KEY` | API key for test user |
| `ZULIP_SITE` | Zulip instance URL |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ZULIP_BOT_EMAIL` | Bot's email address | `ritsuko-bot@een.com` |
| `RITSUKO_TEST_STREAM` | Stream for testing | `test` |
| `BOT_HEALTH_URL` | Health endpoint URL | None (skips health tests) |
| `RITSUKO_TEST_UNAUTHORIZED_EMAIL` | Unauthorized user email | None (skips auth tests) |
| `RITSUKO_TEST_UNAUTHORIZED_API_KEY` | Unauthorized user API key | None (skips auth tests) |
| `RITSUKO_TEST_REAL_NODE` | Real node name for node tests | None (skips real node tests) |
| `RITSUKO_TEST_NAUTOBOT_NODE` | Real node name for nautobot tests | None (skips real nautobot tests) |

## Test Behavior

### Message Timeouts

- Tests wait up to 30 seconds for bot responses
- Polling interval: 0.5 seconds
- These can be adjusted in `test_integration.py` if needed

### Test Stream

By default, tests use the `test` stream. Messages are sent with unique topics to avoid interference:
- Topic format: `test-{timestamp}`
- This ensures each test is isolated

### Skip Conditions

Tests are automatically skipped if:
- Required environment variables are missing
- Bot is not found in the Zulip instance
- Optional features are not configured (e.g., health endpoints, unauthorized user)

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  integration-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r src/requirements.txt
          pip install pytest pytest-timeout

      - name: Run integration tests
        env:
          ZULIP_TEST_EMAIL: ${{ secrets.ZULIP_TEST_EMAIL }}
          ZULIP_TEST_API_KEY: ${{ secrets.ZULIP_TEST_API_KEY }}
          ZULIP_SITE: ${{ secrets.ZULIP_SITE }}
          ZULIP_BOT_EMAIL: ${{ secrets.ZULIP_BOT_EMAIL }}
          RITSUKO_TEST_STREAM: ci-test
        run: |
          python3 -m pytest tests/test_integration.py -v
```

### GitLab CI Example

```yaml
integration-tests:
  stage: test
  image: python:3.10
  before_script:
    - pip install -r src/requirements.txt
    - pip install pytest pytest-timeout
  script:
    - python3 -m pytest tests/test_integration.py -v
  variables:
    ZULIP_TEST_EMAIL: $ZULIP_TEST_EMAIL
    ZULIP_TEST_API_KEY: $ZULIP_TEST_API_KEY
    ZULIP_SITE: $ZULIP_SITE
    ZULIP_BOT_EMAIL: $ZULIP_BOT_EMAIL
    RITSUKO_TEST_STREAM: ci-test
```

## Troubleshooting

### Bot Not Responding

1. Check bot is running:
```bash
# If testing locally
ps aux | grep bot.py

# If testing deployed instance
kubectl get pods -l app=ritsuko
```

2. Check bot logs:
```bash
# Local
tail -f bot.log

# Kubernetes
kubectl logs -f deployment/ritsuko
```

3. Verify test user is authorized:
   - Check `src/bot.py` `authorized_users` list
   - Ensure your test email is in the list

### Connection Errors

1. Verify Zulip site URL:
```bash
curl -I https://your-org.zulipchat.com
```

2. Test API credentials:
```bash
curl -X GET https://your-org.zulipchat.com/api/v1/users/me \
  -u your-email@een.com:your-api-key
```

### Tests Timing Out

1. Increase timeout in `test_integration.py`:
```python
MESSAGE_TIMEOUT = 60  # Increase from 30 to 60 seconds
```

2. Check bot performance:
   - Is the bot overloaded?
   - Are external APIs (Nautobot, GitHub) responding slowly?

3. Check network latency between test runner and Zulip instance

### Flaky Tests

Integration tests can be flaky due to:
- Network issues
- Bot load
- External API availability
- Message ordering

To minimize flakiness:
1. Use unique topic names (already implemented)
2. Add retry logic for critical tests
3. Increase timeouts for slow commands
4. Run tests during low-traffic periods

### Permission Errors

If you get "Not authorized" errors:
1. Verify test user email is in `authorized_users` list
2. Restart the bot to pick up configuration changes
3. Check environment variables are loaded correctly

## Best Practices

### 1. Test Isolation
- Each test uses unique message IDs and topics
- Tests don't depend on each other
- Tests can run in any order

### 2. Clean Test Data
- Messages are timestamped to identify test runs
- Use a dedicated test stream
- Consider cleaning up old test messages periodically

### 3. Rate Limiting
- Tests include delays between message checks (0.5s)
- Avoid running tests too frequently
- Respect Zulip rate limits

### 4. Continuous Testing
- Run tests before deploying
- Run tests after deploying
- Run tests periodically to catch regressions
- Monitor test results in CI/CD

### 5. Test Coverage
- Add new tests when adding new commands
- Update tests when changing command behavior
- Test both success and failure cases
- Test edge cases and error handling

## Adding New Tests

### Example: Testing a New Command

```python
class TestBotCommands(BaseIntegrationTest):
    """Test bot command responses."""

    def test_new_command(self):
        """Test new command functionality."""
        response = self.send_and_wait('newcommand arg1 arg2')

        # Verify response contains expected content
        self.assertIn('expected text', response)
        self.assertIn('other expected text', response)

        # Verify response format
        self.assertIn('##', response)  # Has headers
        self.assertIn('```', response)  # Has code blocks
```

### Example: Testing Command Arguments

```python
def test_command_with_multiple_args(self):
    """Test command with multiple arguments."""
    response = self.send_and_wait('command arg1 arg2 arg3')

    # Verify all arguments are processed
    self.assertIn('arg1', response)
    self.assertIn('arg2', response)
    self.assertIn('arg3', response)
```

### Example: Testing Error Cases

```python
def test_command_error_handling(self):
    """Test command handles errors gracefully."""
    response = self.send_and_wait('command invalid-input')

    # Should return error message
    self.assertIn('error', response.lower())
    # Or usage message
    self.assertIn('Usage', response)
```

## Maintenance

### Regular Tasks

1. **Review test results weekly**
   - Check for flaky tests
   - Update timeouts if needed
   - Add tests for new features

2. **Update test data**
   - Update node names if infrastructure changes
   - Update expected cluster lists
   - Update API endpoints if they change

3. **Clean up test stream**
   - Periodically archive old test messages
   - Keep test stream focused

4. **Monitor test performance**
   - Track test execution time
   - Identify slow tests
   - Optimize as needed

### Updating Tests After Code Changes

When modifying bot code:
1. Run integration tests locally first
2. Update tests to match new behavior
3. Add tests for new functionality
4. Verify all tests pass before merging

## Support

For issues or questions:
1. Check bot logs for errors
2. Review this documentation
3. Check existing GitHub issues
4. Create a new issue with:
   - Test output
   - Bot logs
   - Environment details
   - Steps to reproduce
