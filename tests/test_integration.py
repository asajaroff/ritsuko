"""
Integration tests for Ritsuko bot running against live Zulip instance.

These tests send actual messages to the bot and verify responses.
Requires environment variables to be set for Zulip access.

Usage:
    python3 -m pytest tests/test_integration.py -v
    python3 -m pytest tests/test_integration.py -m integration -v
    python3 -m pytest tests/test_integration.py::TestBotCommands -v

Environment variables:
    ZULIP_TEST_EMAIL - Email for test user (authorized)
    ZULIP_TEST_API_KEY - API key for test user
    ZULIP_SITE - Zulip site URL
    ZULIP_BOT_EMAIL - Email of the bot to test
    RITSUKO_TEST_UNAUTHORIZED_EMAIL - Email for unauthorized user testing (optional)
    RITSUKO_TEST_UNAUTHORIZED_API_KEY - API key for unauthorized user (optional)
"""

import os
import sys
import time
import unittest
import urllib.request

import pytest
import zulip

# Configuration
ZULIP_TEST_EMAIL = os.environ.get("ZULIP_TEST_EMAIL")
ZULIP_TEST_API_KEY = os.environ.get("ZULIP_TEST_API_KEY")
ZULIP_SITE = os.environ.get("ZULIP_SITE")
ZULIP_BOT_EMAIL = os.environ.get("ZULIP_BOT_EMAIL", "ritsuko-bot@een.com")
RITSUKO_TEST_STREAM = os.environ.get("RITSUKO_TEST_STREAM", "test")
BOT_HEALTH_URL = os.environ.get("BOT_HEALTH_URL", None)  # e.g., http://localhost:8080

# Optional unauthorized user for testing
UNAUTHORIZED_EMAIL = os.environ.get("RITSUKO_TEST_UNAUTHORIZED_EMAIL")
UNAUTHORIZED_API_KEY = os.environ.get("RITSUKO_TEST_UNAUTHORIZED_API_KEY")

# Test timeout settings
MESSAGE_TIMEOUT = 15  # seconds to wait for bot response
POLL_INTERVAL = 0.5  # seconds between checking for new messages

# Global shared topic for ALL integration tests across all classes
# This keeps all stream tests in the same conversation
SHARED_TOPIC = "integration-tests-ritsuko-bot"


class BaseIntegrationTest(unittest.TestCase):
    """Base class for integration tests with helper methods."""

    @classmethod
    def setUpClass(cls):
        """Set up Zulip client and validate configuration."""
        if not all([ZULIP_TEST_EMAIL, ZULIP_TEST_API_KEY, ZULIP_SITE]):
            raise unittest.SkipTest(
                "Integration tests require ZULIP_TEST_EMAIL, ZULIP_TEST_API_KEY, "
                "and ZULIP_SITE environment variables"
            )

        cls.client = zulip.Client(
            email=ZULIP_TEST_EMAIL, api_key=ZULIP_TEST_API_KEY, site=ZULIP_SITE
        )

        # Get bot user ID
        try:
            users = cls.client.get_users()
            bot_user = next(
                (u for u in users["members"] if u["email"] == ZULIP_BOT_EMAIL), None
            )
            if not bot_user:
                raise unittest.SkipTest(f"Bot {ZULIP_BOT_EMAIL} not found")
            cls.bot_user_id = bot_user["user_id"]
            cls.bot_full_name = bot_user.get("full_name", "Ritsuko")
        except Exception as e:
            raise unittest.SkipTest(f"Failed to get bot info: {e}")

    def send_private_message(self, content):
        """
        Send a private message to the bot.

        Args:
            content: Message content

        Returns:
            dict: Response from Zulip API
        """
        message = {"type": "private", "to": [ZULIP_BOT_EMAIL], "content": content}
        result = self.client.send_message(message)
        self.assertEqual(
            result["result"], "success", f"Failed to send message: {result}"
        )
        return result

    def send_stream_message(self, content, stream=None, topic=None):
        """
        Send a stream message mentioning the bot.

        Args:
            content: Message content (bot mention will be prepended)
            stream: Stream name (defaults to RITSUKO_TEST_STREAM)
            topic: Topic name (defaults to SHARED_TOPIC for all tests)

        Returns:
            dict: Response from Zulip API
        """
        if stream is None:
            stream = RITSUKO_TEST_STREAM
        if topic is None:
            # Use the global shared topic to keep all tests in one conversation
            topic = SHARED_TOPIC

        message = {
            "type": "stream",
            "to": stream,
            "subject": topic,
            "content": f"@**{self.bot_full_name}** {content}",
        }
        result = self.client.send_message(message)
        self.assertEqual(
            result["result"], "success", f"Failed to send message: {result}"
        )
        return result

    def wait_for_bot_response(self, after_message_id, timeout=MESSAGE_TIMEOUT):
        """
        Wait for bot to respond after a specific message ID.

        Args:
            after_message_id: Message ID to start looking after
            timeout: Maximum seconds to wait

        Returns:
            str: Bot response content or None if timeout
        """
        start_time = time.time()
        request = {
            "anchor": after_message_id,
            "num_before": 0,
            "num_after": 100,
            "narrow": [{"operator": "sender", "operand": ZULIP_BOT_EMAIL}],
        }

        while time.time() - start_time < timeout:
            result = self.client.get_messages(request)
            if result["result"] == "success" and result["messages"]:
                # Find messages after our trigger message
                for msg in result["messages"]:
                    if msg["id"] > after_message_id:
                        return msg["content"]

            time.sleep(POLL_INTERVAL)

        return None

    def send_and_wait(
        self, content, message_type="private", stream=None, topic=None, timeout=None
    ):
        """
        Send a message and wait for bot response.

        Args:
            content: Message content
            message_type: 'private' or 'stream'
            stream: Stream name (for stream messages)
            topic: Topic name (for stream messages)
            timeout: Maximum seconds to wait for response (defaults to MESSAGE_TIMEOUT)

        Returns:
            str: Bot response content
        """
        if message_type == "private":
            result = self.send_private_message(content)
        else:
            result = self.send_stream_message(content, stream, topic)

        if timeout is None:
            timeout = MESSAGE_TIMEOUT

        response = self.wait_for_bot_response(result["id"], timeout=timeout)
        self.assertIsNotNone(
            response, f"Bot did not respond within {timeout} seconds to: {content}"
        )
        return response


@pytest.mark.integration
@pytest.mark.requires_bot
class TestBotCommands(BaseIntegrationTest):
    """Test bot command responses."""

    def test_help_command_private(self):
        """Test help command in private message."""
        response = self.send_and_wait("help")
        self.assertIn("Available Commands", response)
        self.assertIn("status", response)
        self.assertIn("help", response)
        self.assertIn("node", response)

    def test_help_command_stream(self):
        """Test help command in stream."""
        response = self.send_and_wait("help", message_type="stream")
        self.assertIn("Available Commands", response)
        self.assertIn("status", response)

    def test_status_command_private(self):
        """Test status command in private message."""
        response = self.send_and_wait("status")
        self.assertIn("running normally", response.lower())
        self.assertIn("operational", response.lower())

    def test_status_command_stream(self):
        """Test status command in stream."""
        response = self.send_and_wait("status", message_type="stream")
        self.assertIn("running normally", response.lower())

    def test_version_command(self):
        """Test version command."""
        response = self.send_and_wait("version")
        self.assertIn("Ritsuko", response)
        # Should contain version info
        self.assertTrue(len(response) > len("Ritsuko"))

    def test_clusters_command(self):
        """Test clusters command."""
        response = self.send_and_wait("clusters")
        self.assertIn("Clusters", response)
        self.assertIn("aus1p1", response)
        self.assertIn("fra1p1", response)
        self.assertIn("VMS Global Uptime", response)

    def test_cluster_alias_command(self):
        """Test cluster command (alias for clusters)."""
        response = self.send_and_wait("cluster")
        self.assertIn("Clusters", response)
        self.assertIn("aus1p1", response)

    def test_unknown_command(self):
        """Test unknown command handling."""
        response = self.send_and_wait("unknowncommand12345")
        self.assertIn("Unknown command", response)
        self.assertIn("unknowncommand12345", response)

    def test_empty_message_with_mention(self):
        """Test bot response to message with only mention."""
        response = self.send_and_wait("@**Ritsuko**")
        # Bot should handle this gracefully
        self.assertTrue(len(response) > 0)

    def test_node_command_without_args(self):
        """Test node command without arguments."""
        response = self.send_and_wait("node")
        self.assertIn("usage", response.lower())
        # Check for the encoded version or plain text version
        self.assertTrue(
            "node <node>" in response.lower()
            or "node &lt;node&gt;" in response.lower(),
            f"Expected 'node <node>' in response: {response}",
        )

    @unittest.skipUnless(
        os.environ.get("RITSUKO_TEST_REAL_NODE"),
        "Set RITSUKO_TEST_REAL_NODE to test with real node name",
    )
    def test_node_command_with_real_node(self):
        """Test node command with real node name."""
        node_name = os.environ.get("RITSUKO_TEST_REAL_NODE")
        response = self.send_and_wait(f"node {node_name}")
        self.assertIn(node_name, response)
        self.assertIn("Grafana", response)
        self.assertIn("Recent events", response)


@pytest.mark.integration
@pytest.mark.requires_bot
class TestBotMentionBehavior(BaseIntegrationTest):
    """Test bot mention and response behavior."""

    def test_bot_responds_to_private_message(self):
        """Test bot responds to direct private message."""
        response = self.send_and_wait("status")
        self.assertIsNotNone(response)
        self.assertIn("operational", response.lower())

    def test_bot_responds_to_stream_mention(self):
        """Test bot responds when mentioned in stream."""
        # Use default topic (shared_topic) to keep all tests in same conversation
        response = self.send_and_wait("status", message_type="stream")
        self.assertIsNotNone(response)
        self.assertIn("operational", response.lower())

    def test_bot_ignores_stream_without_mention(self):
        """Test bot ignores stream messages without mention."""
        # Use shared topic but don't mention the bot
        message = {
            "type": "stream",
            "to": RITSUKO_TEST_STREAM,
            "subject": SHARED_TOPIC,
            "content": "status",  # No bot mention
        }
        result = self.client.send_message(message)
        self.assertEqual(result["result"], "success")

        # Wait a bit and verify no response
        time.sleep(5)
        response = self.wait_for_bot_response(result["id"], timeout=5)
        self.assertIsNone(
            response, "Bot should not respond to messages without mention"
        )


@pytest.mark.integration
@pytest.mark.requires_bot
class TestBotAuthorization(BaseIntegrationTest):
    """Test bot authorization checks."""

    @unittest.skipUnless(
        UNAUTHORIZED_EMAIL and UNAUTHORIZED_API_KEY,
        "Set RITSUKO_TEST_UNAUTHORIZED_EMAIL and RITSUKO_TEST_UNAUTHORIZED_API_KEY",
    )
    def test_unauthorized_user_private_message(self):
        """Test unauthorized user gets rejected in private message."""
        unauth_client = zulip.Client(
            email=UNAUTHORIZED_EMAIL, api_key=UNAUTHORIZED_API_KEY, site=ZULIP_SITE
        )

        message = {"type": "private", "to": [ZULIP_BOT_EMAIL], "content": "status"}
        result = unauth_client.send_message(message)
        self.assertEqual(result["result"], "success")

        # Wait for bot response
        response = self.wait_for_bot_response(result["id"])
        self.assertIsNotNone(response)
        self.assertIn("not authorized", response.lower())

    @unittest.skipUnless(
        UNAUTHORIZED_EMAIL and UNAUTHORIZED_API_KEY,
        "Set RITSUKO_TEST_UNAUTHORIZED_EMAIL and RITSUKO_TEST_UNAUTHORIZED_API_KEY",
    )
    def test_unauthorized_user_stream_message(self):
        """Test unauthorized user gets rejected in stream."""
        unauth_client = zulip.Client(
            email=UNAUTHORIZED_EMAIL, api_key=UNAUTHORIZED_API_KEY, site=ZULIP_SITE
        )

        # Use shared topic to keep all tests in same conversation
        message = {
            "type": "stream",
            "to": RITSUKO_TEST_STREAM,
            "subject": SHARED_TOPIC,
            "content": f"@**{self.bot_full_name}** status",
        }
        result = unauth_client.send_message(message)
        self.assertEqual(result["result"], "success")

        # Wait for bot response
        response = self.wait_for_bot_response(result["id"])
        self.assertIsNotNone(response)
        self.assertIn("not authorized", response.lower())


@pytest.mark.integration
class TestBotHealthEndpoints(unittest.TestCase):
    """Test bot health check HTTP endpoints."""

    @unittest.skipUnless(BOT_HEALTH_URL, "Set BOT_HEALTH_URL to test health endpoints")
    def test_healthz_endpoint(self):
        """Test /healthz endpoint returns 200 OK."""
        try:
            response = urllib.request.urlopen(f"{BOT_HEALTH_URL}/healthz", timeout=5)
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b"OK")
        except urllib.error.URLError as e:
            self.fail(f"Health endpoint request failed: {e}")

    @unittest.skipUnless(BOT_HEALTH_URL, "Set BOT_HEALTH_URL to test health endpoints")
    def test_readyz_endpoint(self):
        """Test /readyz endpoint returns 200 OK."""
        try:
            response = urllib.request.urlopen(f"{BOT_HEALTH_URL}/readyz", timeout=5)
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b"OK")
        except urllib.error.URLError as e:
            self.fail(f"Readiness endpoint request failed: {e}")

    @unittest.skipUnless(BOT_HEALTH_URL, "Set BOT_HEALTH_URL to test health endpoints")
    def test_invalid_endpoint_returns_404(self):
        """Test invalid endpoint returns 404."""
        try:
            urllib.request.urlopen(f"{BOT_HEALTH_URL}/invalid", timeout=5)
            self.fail("Should have raised HTTPError for invalid endpoint")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)
        except urllib.error.URLError as e:
            self.fail(f"Unexpected error: {e}")


@pytest.mark.integration
@pytest.mark.requires_bot
class TestBotResponseTimes(BaseIntegrationTest):
    """Test bot response time performance."""

    def test_simple_command_response_time(self):
        """Test bot responds to simple commands quickly."""
        start_time = time.time()
        response = self.send_and_wait("status")
        response_time = time.time() - start_time

        self.assertIsNotNone(response)
        self.assertLess(
            response_time, 10, f"Response took {response_time:.2f}s, expected < 10s"
        )

    def test_help_command_response_time(self):
        """Test help command responds quickly."""
        start_time = time.time()
        response = self.send_and_wait("help")
        response_time = time.time() - start_time

        self.assertIsNotNone(response)
        self.assertLess(
            response_time, 10, f"Response took {response_time:.2f}s, expected < 10s"
        )


@pytest.mark.integration
@pytest.mark.requires_bot
class TestBotEdgeCases(BaseIntegrationTest):
    """Test edge cases and error handling."""

    def test_very_long_message(self):
        """Test bot handles very long messages."""
        long_message = "help " + "a" * 1000
        response = self.send_and_wait(long_message)
        self.assertIsNotNone(response)
        # Should still respond with help text
        self.assertIn("Available Commands", response)

    def test_special_characters_in_message(self):
        """Test bot handles special characters."""
        special_msg = "help !@#$%^&*()"
        response = self.send_and_wait(special_msg)
        self.assertIsNotNone(response)

    def test_multiple_spaces_in_command(self):
        """Test bot handles multiple spaces in command."""
        response = self.send_and_wait("status    ")
        self.assertIsNotNone(response)
        self.assertIn("operational", response.lower())

    def test_mixed_case_command(self):
        """Test bot handles mixed case commands."""
        response = self.send_and_wait("STATUS")
        self.assertIsNotNone(response)
        self.assertIn("operational", response.lower())


@pytest.mark.integration
@pytest.mark.requires_bot
@pytest.mark.requires_nautobot
class TestNautobotCommand(BaseIntegrationTest):
    """Test nautobot command functionality."""

    def test_nautobot_command_without_args(self):
        """Test nautobot command without arguments."""
        response = self.send_and_wait("nautobot")
        # Should return usage message
        self.assertIsNotNone(response)
        self.assertIn("usage", response.lower())
        self.assertTrue(
            "nautobot <node>" in response.lower()
            or "nautobot &lt;node&gt;" in response.lower(),
            f"Expected 'nautobot <node>' in response: {response}",
        )

    @unittest.skipUnless(
        os.environ.get("RITSUKO_TEST_NAUTOBOT_NODE"),
        "Set RITSUKO_TEST_NAUTOBOT_NODE to test with real node",
    )
    def test_nautobot_command_with_real_node(self):
        """Test nautobot command with real node."""
        node_name = os.environ.get("RITSUKO_TEST_NAUTOBOT_NODE")
        response = self.send_and_wait(f"nautobot {node_name}")
        self.assertIsNotNone(response)
        # If results found, should contain device info
        if len(response.strip()) > 0:
            self.assertIn("Device", response)


@pytest.mark.integration
@pytest.mark.requires_bot
@pytest.mark.requires_anthropic
class TestAICommand(BaseIntegrationTest):
    """Test AI command functionality."""

    def test_ai_command_without_args(self):
        """Test AI command without arguments."""
        response = self.send_and_wait("ai")
        # Should return usage message
        self.assertIsNotNone(response)
        self.assertIn("usage", response.lower())
        self.assertTrue(
            "ai <prompt>" in response.lower()
            or "ai &lt;prompt&gt;" in response.lower(),
            f"Expected 'ai <prompt>' in response: {response}",
        )

    @unittest.skipUnless(
        os.environ.get("ANTHROPIC_API_KEY"),
        "Set ANTHROPIC_API_KEY to test AI command functionality",
    )
    def test_ai_command_simple_prompt_private(self):
        """Test AI command with simple prompt in private message."""
        # Use a simple question that should get a quick response
        response = self.send_and_wait("ai What is 2+2?", timeout=15)
        self.assertIsNotNone(response)
        # Response should contain some content (not an error)
        self.assertGreater(len(response), 0)
        # Should not contain error messages
        self.assertNotIn("error occurred", response.lower())
        self.assertNotIn("not available", response.lower())

    @unittest.skipUnless(
        os.environ.get("ANTHROPIC_API_KEY"),
        "Set ANTHROPIC_API_KEY to test AI command functionality",
    )
    def test_ai_command_simple_prompt_stream(self):
        """Test AI command with simple prompt in stream message."""
        # Use a simple question that should get a quick response
        response = self.send_and_wait(
            "ai What is the capital of France?", message_type="stream", timeout=15
        )
        self.assertIsNotNone(response)
        # Response should contain some content
        self.assertGreater(len(response), 0)
        # Should not contain error messages
        self.assertNotIn("error occurred", response.lower())
        self.assertNotIn("not available", response.lower())

    @unittest.skipUnless(
        os.environ.get("ANTHROPIC_API_KEY"),
        "Set ANTHROPIC_API_KEY to test AI command functionality",
    )
    def test_ai_command_response_time(self):
        """Test AI command responds within reasonable time."""
        start_time = time.time()
        response = self.send_and_wait("ai Say hello", timeout=20)
        response_time = time.time() - start_time

        self.assertIsNotNone(response)
        # AI responses might take longer, allow up to 20 seconds
        self.assertLess(
            response_time, 20, f"AI response took {response_time:.2f}s, expected < 20s"
        )

    @unittest.skipUnless(
        os.environ.get("ANTHROPIC_API_KEY"),
        "Set ANTHROPIC_API_KEY to test AI command functionality",
    )
    def test_ai_command_multiple_words_prompt(self):
        """Test AI command with multi-word prompt."""
        response = self.send_and_wait(
            "ai Explain what a Kubernetes pod is in one sentence", timeout=20
        )
        self.assertIsNotNone(response)
        self.assertGreater(len(response), 10)
        # Should mention relevant terms
        self.assertTrue(
            "pod" in response.lower()
            or "container" in response.lower()
            or "kubernetes" in response.lower(),
            f"Expected relevant content in AI response: {response[:100]}",
        )

    def test_ai_command_without_api_key_configured(self):
        """Test AI command behavior when ANTHROPIC_API_KEY is not configured."""
        # This test verifies the error message when API key is missing
        # Note: This will only work if the bot doesn't have ANTHROPIC_API_KEY set
        # If it does have one, the test will be skipped
        if os.environ.get("ANTHROPIC_API_KEY"):
            self.skipTest("ANTHROPIC_API_KEY is set, cannot test missing key scenario")

        response = self.send_and_wait("ai test")
        self.assertIsNotNone(response)
        self.assertTrue(
            "not available" in response.lower() or "not set" in response.lower(),
            f"Expected error about missing API key in response: {response}",
        )


def run_integration_tests():
    """Run integration tests with detailed output."""
    print("=" * 70)
    print("Ritsuko Bot Integration Tests")
    print("=" * 70)
    print(f"Zulip Site: {ZULIP_SITE}")
    print(f"Test User: {ZULIP_TEST_EMAIL}")
    print(f"Bot Email: {ZULIP_BOT_EMAIL}")
    print(f"Test Stream: {RITSUKO_TEST_STREAM}")
    print(f"Shared Topic: {SHARED_TOPIC}")
    if BOT_HEALTH_URL:
        print(f"Health URL: {BOT_HEALTH_URL}")
    print("=" * 70)
    print(
        "All stream tests will run in the same conversation: "
        f"{RITSUKO_TEST_STREAM} > {SHARED_TOPIC}"
    )
    print("Each test will be marked with a separator message.")
    print("=" * 70)
    print()

    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBotCommands))
    suite.addTests(loader.loadTestsFromTestCase(TestBotMentionBehavior))
    suite.addTests(loader.loadTestsFromTestCase(TestBotAuthorization))
    suite.addTests(loader.loadTestsFromTestCase(TestBotHealthEndpoints))
    suite.addTests(loader.loadTestsFromTestCase(TestBotResponseTimes))
    suite.addTests(loader.loadTestsFromTestCase(TestBotEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestNautobotCommand))
    suite.addTests(loader.loadTestsFromTestCase(TestAICommand))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 70)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_integration_tests())
