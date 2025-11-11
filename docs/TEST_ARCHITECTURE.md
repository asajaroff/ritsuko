# Test Architecture

## Overview

This document describes the architecture of the Ritsuko bot testing suite.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Test Suite                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────┐         ┌─────────────────────────┐    │
│  │   Unit Tests       │         │  Integration Tests       │    │
│  │  (test_bot.py)     │         │  (test_integration.py)   │    │
│  ├────────────────────┤         ├─────────────────────────┤    │
│  │ • Mocked Zulip     │         │ • Live Zulip Instance    │    │
│  │ • Mocked APIs      │         │ • Real Bot Responses     │    │
│  │ • Fast execution   │         │ • E2E Testing            │    │
│  │ • Isolated tests   │         │ • Real API calls         │    │
│  └────────────────────┘         └─────────────────────────┘    │
│           │                              │                       │
│           │                              │                       │
│           └──────────────┬───────────────┘                       │
│                          │                                       │
│                    ┌─────▼─────┐                                │
│                    │  pytest   │                                 │
│                    │ (runner)  │                                 │
│                    └───────────┘                                 │
└─────────────────────────────────────────────────────────────────┘

                              │
                              ▼

┌─────────────────────────────────────────────────────────────────┐
│                    Integration Test Flow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────┐   1. Send    ┌──────────┐   2. Process  ┌───────┐ │
│  │  Test   ├──────────────►  Zulip   ├───────────────► Bot   │ │
│  │  Runner │              │  Server  │               │ (Live)│ │
│  └────┬────┘              └──────────┘               └───┬───┘ │
│       │                                                   │     │
│       │                                              3. Response│
│       │                                                   │     │
│       │  4. Poll for      ┌──────────┐                   │     │
│       └───────────────────┤  Zulip   ◄───────────────────┘     │
│         response          │  Server  │                         │
│                           └──────────┘                         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Test Runner (pytest)
- Discovers and executes tests
- Manages test lifecycle
- Collects and reports results
- Handles markers and filtering

### 2. Unit Tests (test_bot.py)
Tests individual components with mocked dependencies:

```
TestSendMessage
├── test_send_message_success
├── test_send_message_failure
└── test_send_message_exception

TestHandleMessage
├── test_handle_message_from_bot_itself
├── test_handle_message_authorized_user_private
├── test_handle_message_unauthorized_user_private
└── test_handle_message_*

TestCommandParsing
├── test_parse_command_stream_message
├── test_parse_command_private_message
└── test_execute_command_*

TestNodeCommand
TestHealthCheckServer
TestNautobotFetcher
```

### 3. Integration Tests (test_integration.py)
Tests against live bot instance:

```
BaseIntegrationTest (base class)
├── send_private_message()
├── send_stream_message()
├── wait_for_bot_response()
└── send_and_wait()

TestBotCommands
├── test_help_command_private
├── test_status_command_private
├── test_version_command
├── test_clusters_command
└── test_node_command_*

TestBotMentionBehavior
├── test_bot_responds_to_private_message
├── test_bot_responds_to_stream_mention
└── test_bot_ignores_stream_without_mention

TestBotAuthorization
├── test_unauthorized_user_private_message
└── test_unauthorized_user_stream_message

TestBotHealthEndpoints
├── test_healthz_endpoint
├── test_readyz_endpoint
└── test_invalid_endpoint_returns_404

TestBotResponseTimes
├── test_simple_command_response_time
└── test_help_command_response_time

TestBotEdgeCases
├── test_very_long_message
├── test_special_characters_in_message
└── test_mixed_case_command

TestNautobotCommand
└── test_nautobot_command_*
```

## Test Execution Flow

### Unit Test Flow

```
1. Setup Phase
   ├── Create mock objects
   ├── Set environment variables
   └── Initialize test fixtures

2. Execution Phase
   ├── Call function under test
   ├── Mock returns predefined values
   └── Function executes with mocks

3. Assertion Phase
   ├── Check return values
   ├── Verify mock calls
   └── Assert expected behavior

4. Cleanup Phase
   └── Tear down mocks
```

### Integration Test Flow

```
1. Setup Phase
   ├── Load environment configuration (.env.test)
   ├── Create Zulip client
   ├── Get bot user info
   └── Verify bot exists

2. Execution Phase
   ├── Send message to bot (private or stream)
   ├── Record message ID
   ├── Poll for bot response
   │   ├── Query Zulip for new messages
   │   ├── Check if message is from bot
   │   ├── Wait if no response yet
   │   └── Timeout after 30 seconds
   └── Return bot response

3. Assertion Phase
   ├── Verify response received
   ├── Check response content
   ├── Assert expected patterns
   └── Verify response time (if applicable)

4. Cleanup Phase
   └── No cleanup needed (messages remain in Zulip)
```

## Configuration Flow

```
┌─────────────────┐
│ .env.test       │
│ (user config)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐         ┌──────────────────┐
│ Environment     ├────────►│ Test Runner      │
│ Variables       │         │ (bash script)    │
└─────────────────┘         └────────┬─────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │ pytest           │
                            │ (test execution) │
                            └────────┬─────────┘
                                     │
         ┌───────────────────────────┼─────────────────────┐
         │                           │                     │
         ▼                           ▼                     ▼
┌─────────────────┐     ┌────────────────────┐   ┌────────────────┐
│ Unit Tests      │     │ Integration Tests  │   │ Test Reports   │
│ (fast, mocked)  │     │ (slow, real)       │   │ (output)       │
└─────────────────┘     └────────────────────┘   └────────────────┘
```

## Data Flow

### Unit Test Data Flow

```
Test Input
    │
    ▼
┌────────────┐
│  Function  │ (with mocked dependencies)
└──────┬─────┘
       │
       ▼
Mocked Response ───► Assertions ───► Pass/Fail
```

### Integration Test Data Flow

```
Test Input (message)
    │
    ▼
┌──────────────┐
│ Zulip API    │
│ (send msg)   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Zulip Server │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Bot Instance │
│ (processes)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Zulip Server │
│ (bot reply)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Zulip API    │
│ (poll msgs)  │
└──────┬───────┘
       │
       ▼
Bot Response ───► Assertions ───► Pass/Fail
```

## Test Isolation

### Unit Tests
- Each test is independent
- Mocks are reset between tests
- No shared state
- No external dependencies

### Integration Tests
- Unique message IDs prevent interference
- Unique stream topics per test
- No cleanup required (Zulip persists messages)
- Tests can run in parallel (different topics)

## Error Handling

```
Test Execution
    │
    ├─► Success ─────► Report Pass
    │
    ├─► Assertion Failure ─────► Report Failure
    │                              ├── Expected vs Actual
    │                              └── Stack trace
    │
    ├─► Timeout ─────► Report Error
    │                   └── "Bot did not respond"
    │
    ├─► Connection Error ─────► Report Error
    │                            └── "Cannot reach Zulip"
    │
    └─► Exception ─────► Report Error
                         ├── Exception type
                         ├── Error message
                         └── Stack trace
```

## Performance Characteristics

| Test Type | Execution Time | Resources | Dependencies |
|-----------|---------------|-----------|--------------|
| Unit Tests | < 1s per test | Low | None (mocked) |
| Integration Tests | 5-10s per test | Medium | Zulip, Bot, APIs |
| Full Suite | ~5 minutes | Medium | All |

## Scaling Considerations

### Running Tests in Parallel

```python
# pytest can run tests in parallel with pytest-xdist
pytest tests/ -n auto  # Use all CPU cores
pytest tests/ -n 4     # Use 4 workers
```

Integration tests are safe to run in parallel because:
- Each test uses unique message IDs
- Each test uses unique stream topics
- No shared state between tests

### CI/CD Optimization

```yaml
# Run different test types in parallel
jobs:
  unit-tests:
    - run: pytest tests/test_bot.py

  integration-tests:
    - run: pytest tests/test_integration.py
```

## Monitoring and Reporting

### Test Output Structure

```
Test Session
├── Collection Phase
│   └── Discover all tests
├── Setup Phase
│   └── Initialize fixtures
├── Execution Phase
│   ├── Run each test
│   └── Collect results
└── Reporting Phase
    ├── Summary statistics
    ├── Passed tests
    ├── Failed tests
    ├── Skipped tests
    └── Error details
```

### Artifacts Generated

```
test-results/
├── test-report.xml       (JUnit format)
├── coverage.xml          (Coverage report)
├── htmlcov/             (HTML coverage report)
└── logs/                (Test execution logs)
```

## Extension Points

### Adding New Test Types

1. Create new test class inheriting from `BaseIntegrationTest`
2. Add pytest markers for categorization
3. Implement test methods
4. Update documentation

### Adding New Assertions

```python
class CustomAssertions:
    """Custom assertion helpers."""

    def assertContainsMarkdown(self, response):
        """Assert response contains markdown."""
        self.assertIn('```', response)
        self.assertIn('##', response)

    def assertValidGrafanaLink(self, response):
        """Assert response contains valid Grafana link."""
        self.assertIn('graphs.eencloud.com', response)
        self.assertRegex(response, r'https://.*orgId=1')
```

### Adding New Test Utilities

```python
class TestHelpers:
    """Helper functions for tests."""

    @staticmethod
    def generate_test_node_name():
        """Generate unique test node name."""
        return f"test-node-{int(time.time())}"

    @staticmethod
    def cleanup_test_messages(client, stream, topic):
        """Clean up test messages after test."""
        # Implementation here
        pass
```

## Best Practices Summary

1. **Isolation**: Tests don't depend on each other
2. **Repeatability**: Tests produce same results on each run
3. **Speed**: Unit tests fast, integration tests acceptable
4. **Clarity**: Test names describe what they test
5. **Coverage**: All features and edge cases covered
6. **Documentation**: Tests are documented and maintainable
7. **CI/CD Ready**: Tests run in automated pipelines
8. **Failure Handling**: Clear error messages on failure

## References

- [INTEGRATION_TESTING.md](./INTEGRATION_TESTING.md) - Complete testing guide
- [TESTING_QUICKSTART.md](./TESTING_QUICKSTART.md) - Quick start
- [../tests/README.md](../tests/README.md) - Test suite overview
- [pytest documentation](https://docs.pytest.org/)
