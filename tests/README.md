# Ritsuko Test Suite

This directory contains both unit tests and integration tests for the Ritsuko bot.

## Test Types

### Unit Tests
Tests individual components in isolation with mocked dependencies.

**Files:**
- `test_bot.py` - Tests for bot message handling, authorization, health checks
- `test_fetcher.py` - Tests for API fetcher functions (Nautobot, GitHub)

**Run with:**
```bash
make test
# or
python3 -m pytest tests/test_bot.py tests/test_fetcher.py -v
```

### Integration Tests
Tests the bot running against a live Zulip instance by sending real messages.

**Files:**
- `test_integration.py` - Full end-to-end tests against live bot

**Run with:**
```bash
make test-integration
# or
./run_integration_tests.sh
```

## Quick Start

### Running Unit Tests
```bash
# Run all unit tests
make test

# Run with coverage
make test-coverage

# Run specific test file
python3 -m pytest tests/test_bot.py -v

# Run specific test
python3 -m pytest tests/test_bot.py::TestSendMessage::test_send_message_success -v
```

### Running Integration Tests

1. **Setup** (first time only):
   ```bash
   cp .env.test.example .env.test
   # Edit .env.test with your credentials
   ```

2. **Run tests**:
   ```bash
   make test-integration
   ```

3. **Run with verbose output**:
   ```bash
   make test-integration-verbose
   ```

### Running All Tests
```bash
make test-all
```

## Test Coverage

### Unit Tests Coverage

| Component | Test File | Coverage |
|-----------|-----------|----------|
| Message handling | test_bot.py | ✓ High |
| Authorization | test_bot.py | ✓ High |
| Command parsing | test_bot.py | ✓ High |
| Command execution | test_bot.py | ✓ High |
| Health endpoints | test_bot.py | ✓ High |
| Nautobot fetcher | test_bot.py | ✓ High |
| Node command | test_bot.py | ✓ High |

### Integration Tests Coverage

| Feature | Test Class | Status |
|---------|------------|--------|
| Commands | TestBotCommands | ✓ Complete |
| Mentions | TestBotMentionBehavior | ✓ Complete |
| Authorization | TestBotAuthorization | ✓ Complete |
| Health endpoints | TestBotHealthEndpoints | ✓ Complete |
| Performance | TestBotResponseTimes | ✓ Complete |
| Edge cases | TestBotEdgeCases | ✓ Complete |
| Nautobot | TestNautobotCommand | ✓ Complete |

## Documentation

- **[TESTING_QUICKSTART.md](../docs/TESTING_QUICKSTART.md)** - Quick start guide
- **[INTEGRATION_TESTING.md](../docs/INTEGRATION_TESTING.md)** - Complete integration testing guide

## Continuous Integration

Integration tests can run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run integration tests
  env:
    ZULIP_TEST_EMAIL: ${{ secrets.ZULIP_TEST_EMAIL }}
    ZULIP_TEST_API_KEY: ${{ secrets.ZULIP_TEST_API_KEY }}
    ZULIP_SITE: ${{ secrets.ZULIP_SITE }}
  run: make test-integration
```

See `.github/workflows/integration-tests.yml.example` for a complete example.

## Writing New Tests

### Adding Unit Tests

```python
# In test_bot.py
class TestNewFeature(unittest.TestCase):
    """Test new feature."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        bot.client = self.mock_client

    def test_new_feature(self):
        """Test description."""
        # Arrange
        input_data = "test"

        # Act
        result = some_function(input_data)

        # Assert
        self.assertEqual(result, "expected")
```

### Adding Integration Tests

```python
# In test_integration.py
class TestNewCommand(BaseIntegrationTest):
    """Test new command."""

    def test_new_command(self):
        """Test new command returns expected response."""
        response = self.send_and_wait('newcommand arg')

        self.assertIn('expected text', response)
        self.assertIsNotNone(response)
```

## Troubleshooting

### Unit Tests

**Problem:** Import errors
```bash
# Solution: Add src to path or install in editable mode
export PYTHONPATH="${PYTHONPATH}:./src"
```

**Problem:** Mock not working
```bash
# Solution: Ensure mocks are set up before importing the module
sys.modules['zulip'] = MagicMock()
import bot
```

### Integration Tests

**Problem:** Bot not responding
```bash
# Check bot is running
kubectl get pods -l app=ritsuko
# Check bot logs
kubectl logs -f deployment/ritsuko
```

**Problem:** Tests timing out
```python
# Increase timeout in test_integration.py
MESSAGE_TIMEOUT = 60  # seconds
```

**Problem:** "Not authorized" errors
- Verify test user is in `authorized_users` list in `src/bot.py`
- Restart bot after adding user

## Best Practices

### Unit Tests
- Use mocks for external dependencies
- Test both success and failure cases
- Keep tests fast (< 1 second each)
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

### Integration Tests
- Use unique topics/message IDs
- Add timeouts to prevent hanging
- Clean up test data periodically
- Test against staging before production
- Use dedicated test streams

## Test Statistics

Run this to see test statistics:
```bash
# Count tests
python3 -m pytest tests/ --collect-only | grep "test session starts"

# Run with timing
python3 -m pytest tests/ -v --durations=10

# Coverage report
make test-coverage
```

## Contributing

When adding new features:
1. Write unit tests first (TDD approach)
2. Ensure all unit tests pass
3. Add integration tests for end-to-end behavior
4. Update this README if adding new test categories
5. Run `make test-all` before committing

## Support

For help with testing:
1. Check the documentation in `docs/`
2. Review existing tests for examples
3. Check bot logs for errors
4. Create an issue with test output and details
