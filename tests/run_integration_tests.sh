#!/bin/bash
# Integration test runner for Ritsuko bot
# This script runs integration tests against a live bot instance

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Ritsuko Integration Test Runner"
echo "========================================"
echo ""

# Check if .env file exists
if [ -f "$SCRIPT_DIR/.env.test" ]; then
    echo -e "${GREEN}Loading configuration from .env.test${NC}"
    set -a
    source "$SCRIPT_DIR/.env.test"
    set +a
else
    echo -e "${YELLOW}Warning: .env.test file not found${NC}"
    echo "You can create one by copying .env.test.example"
    echo ""
fi

# Check required environment variables
REQUIRED_VARS=(
    "ZULIP_TEST_EMAIL"
    "ZULIP_TEST_API_KEY"
    "ZULIP_SITE"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}Error: Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please set these variables in .env.test or export them."
    exit 1
fi

# Display configuration
echo "Configuration:"
echo "  Zulip Site: $ZULIP_SITE"
echo "  Test User: $ZULIP_TEST_EMAIL"
echo "  Bot Email: ${ZULIP_BOT_EMAIL:-ritsuko-akagi-bot@chat.eencloud.com}"
echo "  Test Stream: ${RITSUKO_TEST_STREAM:-test}"
if [ -n "$BOT_HEALTH_URL" ]; then
    echo "  Health URL: $BOT_HEALTH_URL"
fi
echo ""

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv "$SCRIPT_DIR/.venv"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$SCRIPT_DIR/.venv/bin/activate"

# Install/update dependencies
echo "Installing dependencies..."
pip3 install -q -r "$SCRIPT_DIR/src/requirements.txt"
pip3 install -q pytest pytest-timeout

echo ""
echo "========================================"
echo "Running Integration Tests"
echo "========================================"
echo ""

# Run tests with pytest
if [ "$1" == "-v" ] || [ "$1" == "--verbose" ]; then
    python3 -m pytest "$SCRIPT_DIR/tests/test_integration.py" -v -s "$@"
else
    python3 -m pytest "$SCRIPT_DIR/tests/test_integration.py" -v "$@"
fi

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

exit $TEST_EXIT_CODE
