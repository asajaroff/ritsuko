# Testing Suite Summary

## Overview

A comprehensive integration test suite has been created for the Ritsuko bot that tests against a live running instance.

## Files Created

### Test Files
1. **`tests/test_integration.py`** (470+ lines)
   - Complete integration test suite
   - 30+ test cases across 7 test classes
   - Tests all bot commands, authorization, health endpoints, and edge cases

### Configuration Files
2. **`.env.test.example`**
   - Template for test environment configuration
   - Documents all required and optional variables

3. **`pytest.ini`**
   - Pytest configuration
   - Test markers for categorization
   - Coverage settings

### Scripts
4. **`run_integration_tests.sh`**
   - Executable test runner script
   - Loads environment configuration
   - Provides colored output and error handling

### Documentation
5. **`docs/INTEGRATION_TESTING.md`** (500+ lines)
   - Comprehensive testing guide
   - Setup instructions
   - Troubleshooting guide
   - Best practices
   - CI/CD integration examples

6. **`docs/TESTING_QUICKSTART.md`**
   - Quick start guide (5 minutes to get running)
   - Common commands reference
   - Quick troubleshooting

7. **`tests/README.md`**
   - Test suite overview
   - Quick reference for both unit and integration tests
   - Contributing guidelines

### CI/CD Examples
8. **`.github/workflows/integration-tests.yml.example`**
   - GitHub Actions workflow template
   - Includes deployment pipeline example
   - Slack notification on failure

### Makefile Updates
9. **`Makefile`** (updated)
   - `make test-integration` - Run integration tests
   - `make test-integration-verbose` - Run with verbose output
   - `make test-all` - Run all tests (unit + integration)

10. **`src/requirements.txt`** (updated)
    - Added `pytest-timeout==2.3.1` for better test control

## Test Categories

### 1. TestBotCommands
Tests all bot commands:
- ✓ help command (private & stream)
- ✓ status command (private & stream)
- ✓ version command
- ✓ clusters/cluster command
- ✓ node command (with/without args)
- ✓ nautobot command
- ✓ unknown command handling
- ✓ empty message handling

### 2. TestBotMentionBehavior
Tests mention handling:
- ✓ Responds to private messages
- ✓ Responds to stream mentions
- ✓ Ignores stream messages without mentions

### 3. TestBotAuthorization
Tests access control:
- ✓ Authorized user access
- ✓ Unauthorized user rejection (private)
- ✓ Unauthorized user rejection (stream)

### 4. TestBotHealthEndpoints
Tests HTTP endpoints:
- ✓ /healthz endpoint
- ✓ /readyz endpoint
- ✓ Invalid endpoint (404)

### 5. TestBotResponseTimes
Performance tests:
- ✓ Simple command response time (< 10s)
- ✓ Help command response time (< 10s)

### 6. TestBotEdgeCases
Edge case handling:
- ✓ Very long messages
- ✓ Special characters
- ✓ Multiple spaces
- ✓ Mixed case commands

### 7. TestNautobotCommand
Nautobot integration:
- ✓ Command without arguments
- ✓ Command with real node (optional)

## Features

### Smart Test Management
- **Automatic skipping** - Tests skip if requirements not met
- **Configurable timeouts** - 30s default, adjustable
- **Unique topics** - Each test uses timestamped topics
- **Parallel-safe** - Tests don't interfere with each other

### Pytest Markers
Tests are marked for easy filtering:
```bash
# Run only integration tests
pytest -m integration

# Run tests requiring bot
pytest -m requires_bot

# Run tests requiring Nautobot
pytest -m requires_nautobot

# Skip slow tests
pytest -m "not slow"
```

### Environment Variables

**Required:**
- `ZULIP_TEST_EMAIL` - Authorized test user email
- `ZULIP_TEST_API_KEY` - Test user API key
- `ZULIP_SITE` - Zulip instance URL

**Optional:**
- `ZULIP_BOT_EMAIL` - Bot email (default: ritsuko-bot@een.com)
- `RITSUKO_TEST_STREAM` - Test stream (default: test)
- `BOT_HEALTH_URL` - Health endpoint URL
- `RITSUKO_TEST_UNAUTHORIZED_EMAIL` - For auth tests
- `RITSUKO_TEST_UNAUTHORIZED_API_KEY` - For auth tests
- `RITSUKO_TEST_REAL_NODE` - Real node for node tests
- `RITSUKO_TEST_NAUTOBOT_NODE` - Real node for nautobot tests

## Quick Start

```bash
# 1. Setup (first time)
cp .env.test.example .env.test
# Edit .env.test with your credentials

# 2. Run tests
make test-integration

# Or use the script directly
./run_integration_tests.sh

# Or use pytest
source .env.test
python3 -m pytest tests/test_integration.py -v
```

## Usage Examples

```bash
# Run all integration tests
make test-integration

# Run with verbose output
make test-integration-verbose

# Run all tests (unit + integration)
make test-all

# Run specific test class
pytest tests/test_integration.py::TestBotCommands -v

# Run specific test
pytest tests/test_integration.py::TestBotCommands::test_help_command_private -v

# Run with markers
pytest -m "integration and requires_bot" -v

# Run tests excluding Nautobot tests
pytest -m "integration and not requires_nautobot" -v
```

## CI/CD Integration

Ready for continuous integration:

### GitHub Actions
```yaml
- name: Run integration tests
  env:
    ZULIP_TEST_EMAIL: ${{ secrets.ZULIP_TEST_EMAIL }}
    ZULIP_TEST_API_KEY: ${{ secrets.ZULIP_TEST_API_KEY }}
    ZULIP_SITE: ${{ secrets.ZULIP_SITE }}
  run: make test-integration
```

See `.github/workflows/integration-tests.yml.example` for complete workflow.

## Test Architecture

### BaseIntegrationTest Class
Provides helper methods:
- `send_private_message(content)` - Send private message to bot
- `send_stream_message(content, stream, topic)` - Send stream message
- `wait_for_bot_response(message_id, timeout)` - Wait for bot reply
- `send_and_wait(content, type)` - Send message and wait for response

### Test Flow
1. Test sends message to bot
2. Waits for response (polling every 0.5s)
3. Verifies response content
4. Uses unique message IDs and topics to avoid interference

## Success Metrics

✅ **30+ test cases** covering all bot functionality
✅ **7 test classes** organized by feature
✅ **Comprehensive documentation** (1000+ lines)
✅ **CI/CD ready** with GitHub Actions example
✅ **Zero dependencies** on external test infrastructure
✅ **Real environment testing** against live bot
✅ **Easy setup** - 5 minutes from clone to first test run

## Best Practices Implemented

1. **Isolation** - Tests don't depend on each other
2. **Timeouts** - Prevents hanging tests
3. **Clear naming** - Descriptive test names
4. **Documentation** - Comprehensive guides
5. **Configurability** - Environment variables for all settings
6. **Skipping** - Auto-skip when requirements not met
7. **Error handling** - Graceful failure with helpful messages
8. **Performance** - Response time assertions
9. **Coverage** - All commands and edge cases tested
10. **Maintainability** - Well-organized, commented code

## Maintenance

### Adding New Tests
1. Add test method to appropriate test class
2. Use `self.send_and_wait()` for simplicity
3. Add assertions for expected behavior
4. Update documentation if needed

### Updating Configuration
1. Update `.env.test.example` with new variables
2. Update documentation
3. Update CI/CD examples

### Regular Tasks
- Run tests before deployments
- Run tests after deployments
- Monitor test failures
- Update test data as infrastructure changes
- Clean up test stream periodically

## Troubleshooting

### Common Issues

**Bot not responding:**
- Check bot is running
- Check bot logs
- Verify user is authorized

**Tests timing out:**
- Increase MESSAGE_TIMEOUT
- Check bot performance
- Check network connectivity

**Import errors:**
- Ensure virtual environment is activated
- Install dependencies: `pip install -r src/requirements.txt`

**Permission errors:**
- Verify test user in authorized_users list
- Restart bot after configuration changes

## Support Resources

- **Quick Start:** `docs/TESTING_QUICKSTART.md`
- **Full Guide:** `docs/INTEGRATION_TESTING.md`
- **Test Reference:** `tests/README.md`
- **Example Workflow:** `.github/workflows/integration-tests.yml.example`

## Next Steps

1. **Configure credentials** - Copy `.env.test.example` to `.env.test`
2. **Run first test** - `make test-integration`
3. **Add to CI/CD** - Use provided GitHub Actions example
4. **Customize** - Add test data for your environment
5. **Monitor** - Set up regular test runs
6. **Extend** - Add tests for new features as developed

## Statistics

- **Test Files:** 1 (test_integration.py)
- **Test Classes:** 7
- **Test Methods:** 30+
- **Lines of Code:** 470+ (tests) + 500+ (docs)
- **Documentation Pages:** 3
- **Configuration Files:** 3
- **Scripts:** 1
- **CI/CD Examples:** 1

## License

Same as the Ritsuko bot project.
