# Integration Testing Quick Start

Quick guide to get started with integration testing.

## Setup (5 minutes)

1. **Copy configuration file**
   ```bash
   cp .env.test.example .env.test
   ```

2. **Get your Zulip API key**
   - Go to Zulip → Settings → Account & Privacy
   - Click "Show/generate API key"
   - Copy the key

3. **Edit `.env.test`**
   ```bash
   ZULIP_TEST_EMAIL=your-email@een.com
   ZULIP_TEST_API_KEY=paste-your-key-here
   ZULIP_SITE=https://een.zulipchat.com
   ZULIP_BOT_EMAIL=ritsuko-bot@een.com
   ```

4. **Run tests**
   ```bash
   ./run_integration_tests.sh
   ```

## Common Commands

```bash
# Run all tests
./run_integration_tests.sh

# Verbose output
./run_integration_tests.sh -v

# Run specific test class
python3 -m pytest tests/test_integration.py::TestBotCommands -v

# Run specific test
python3 -m pytest tests/test_integration.py::TestBotCommands::test_help_command_private -v
```

## What Gets Tested

✅ All bot commands (help, status, version, clusters, node, nautobot)
✅ Bot mention behavior (private messages, stream messages)
✅ Authorization (authorized and unauthorized users)
✅ Health check endpoints (/healthz, /readyz)
✅ Response times (< 10 seconds for simple commands)
✅ Edge cases (long messages, special characters, etc.)

## Troubleshooting

### "Bot did not respond"
- Check bot is running: `kubectl get pods -l app=ritsuko`
- Check bot logs: `kubectl logs -f deployment/ritsuko`
- Verify you're in authorized_users list

### "Missing environment variables"
- Make sure `.env.test` exists and has all required variables
- Source it: `source .env.test`

### Tests timing out
- Increase `MESSAGE_TIMEOUT` in `test_integration.py`
- Check bot performance and external API availability

## Next Steps

For detailed information, see [INTEGRATION_TESTING.md](./INTEGRATION_TESTING.md)

## Test Output Example

```
======================================
Ritsuko Bot Integration Tests
======================================
Zulip Site: https://een.zulipchat.com
Test User: test@een.com
Bot Email: ritsuko-bot@een.com
======================================

tests/test_integration.py::TestBotCommands::test_help_command_private PASSED
tests/test_integration.py::TestBotCommands::test_status_command_private PASSED
tests/test_integration.py::TestBotCommands::test_version_command PASSED
...

======================================
Tests run: 25
Failures: 0
Errors: 0
Skipped: 3
======================================
✓ All tests passed
```
