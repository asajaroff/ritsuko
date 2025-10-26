import os
import unittest
from unittest.mock import MagicMock, patch, call
import sys
import urllib.request
import time

# Set up required environment variables before importing bot
os.environ['ZULIP_EMAIL'] = 'bot@example.com'
os.environ['ZULIP_API_KEY'] = 'test_api_key'
os.environ['ZULIP_SITE'] = 'https://test.zulipchat.com'

# Mock zulip module before importing bot
sys.modules['zulip'] = MagicMock()

import bot
from commands import parse_command, execute_command


class TestSendMessage(unittest.TestCase):
    """Test the send_message helper function."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        bot.client = self.mock_client

    def test_send_message_success(self):
        """Test successful message sending."""
        self.mock_client.send_message.return_value = {'result': 'success'}

        message_dict = {
            'type': 'private',
            'to': ['test@example.com'],
            'content': 'Test message'
        }

        result = bot.send_message(message_dict)

        self.assertTrue(result)
        self.mock_client.send_message.assert_called_once_with(message_dict)

    def test_send_message_failure(self):
        """Test failed message sending."""
        self.mock_client.send_message.return_value = {
            'result': 'error',
            'msg': 'Invalid recipient'
        }

        message_dict = {
            'type': 'private',
            'to': ['invalid@example.com'],
            'content': 'Test message'
        }

        result = bot.send_message(message_dict)

        self.assertFalse(result)

    def test_send_message_exception(self):
        """Test exception handling in send_message."""
        self.mock_client.send_message.side_effect = Exception('Network error')

        message_dict = {
            'type': 'private',
            'to': ['test@example.com'],
            'content': 'Test message'
        }

        result = bot.send_message(message_dict)

        self.assertFalse(result)


class TestHandleMessage(unittest.TestCase):
    """Test the handle_message function."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        bot.client = self.mock_client
        os.environ['ZULIP_EMAIL'] = 'bot@example.com'

    @patch('bot.send_message')
    def test_handle_message_from_bot_itself(self, mock_send):
        """Test that bot ignores its own messages."""
        message = {
            'sender_email': 'bot@example.com',
            'content': 'Test message',
            'type': 'private'
        }

        bot.handle_message(message)

        mock_send.assert_not_called()

    @patch('bot.send_message')
    def test_handle_message_authorized_user_private(self, mock_send):
        """Test handling message from authorized user in private chat."""
        mock_send.return_value = True

        message = {
            'sender_email': 'asajaroff@een.com',
            'content': 'status',
            'type': 'private',
            'display_recipient': [
                {'email': 'asajaroff@een.com'},
                {'email': 'bot@example.com'}
            ]
        }

        bot.handle_message(message)

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        self.assertEqual(call_args['type'], 'private')
        self.assertIn('running normally', call_args['content'])

    @patch('bot.send_message')
    def test_handle_message_authorized_user_stream(self, mock_send):
        """Test handling message from authorized user in stream."""
        mock_send.return_value = True

        message = {
            'sender_email': 'asajaroff@een.com',
            'content': '@bot status',
            'type': 'stream',
            'display_recipient': 'general',
            'subject': 'test topic'
        }

        bot.handle_message(message)

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        self.assertEqual(call_args['type'], 'stream')
        self.assertEqual(call_args['to'], 'general')
        self.assertEqual(call_args['subject'], 'test topic')
        self.assertIn('running normally', call_args['content'])

    @patch('bot.send_message')
    def test_handle_message_unauthorized_user_private(self, mock_send):
        """Test handling message from unauthorized user in private chat."""
        mock_send.return_value = True

        message = {
            'sender_email': 'unauthorized@example.com',
            'content': 'Hello bot',
            'type': 'private',
            'display_recipient': [
                {'email': 'unauthorized@example.com'},
                {'email': 'bot@example.com'}
            ]
        }

        bot.handle_message(message)

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        self.assertIn('not authorized', call_args['content'])

    @patch('bot.send_message')
    def test_handle_message_unauthorized_user_stream(self, mock_send):
        """Test handling message from unauthorized user in stream."""
        mock_send.return_value = True

        message = {
            'sender_email': 'unauthorized@example.com',
            'content': 'Hello bot',
            'type': 'stream',
            'display_recipient': 'general',
            'subject': 'test topic'
        }

        bot.handle_message(message)

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        self.assertIn('not authorized', call_args['content'])

    @patch('bot.send_message')
    def test_handle_message_missing_field(self, mock_send):
        """Test handling message with missing required field."""
        message = {
            'content': 'Hello bot',
            'type': 'private'
            # Missing sender_email
        }

        # Should not raise exception, just log error
        bot.handle_message(message)

        # Should not try to send a message
        mock_send.assert_not_called()


class TestCommandParsing(unittest.TestCase):
    """Test command parsing functionality."""

    def test_parse_command_stream_message(self):
        """Test parsing command from stream message (second word)."""
        message = {
            'type': 'stream',
            'content': '@bot help me please'
        }

        command, args = parse_command(message)

        self.assertEqual(command, 'help')
        self.assertEqual(args, ['me', 'please'])

    def test_parse_command_private_message(self):
        """Test parsing command from private message (first word)."""
        message = {
            'type': 'private',
            'content': 'ping test 123'
        }

        command, args = parse_command(message)

        self.assertEqual(command, 'ping')
        self.assertEqual(args, ['test', '123'])

    def test_parse_command_stream_no_command(self):
        """Test parsing stream message with only bot mention."""
        message = {
            'type': 'stream',
            'content': '@bot'
        }

        command, args = parse_command(message)

        self.assertIsNone(command)
        self.assertEqual(args, [])

    def test_parse_command_empty_message(self):
        """Test parsing empty message."""
        message = {
            'type': 'private',
            'content': ''
        }

        command, args = parse_command(message)

        self.assertIsNone(command)
        self.assertEqual(args, [])

    def test_execute_command_help(self):
        """Test help command execution."""
        message = {
            'type': 'private',
            'content': 'help'
        }

        response = execute_command(message)

        self.assertIn('Available Commands', response)
        self.assertIn('help', response)
        self.assertIn('status', response)
        self.assertIn('node', response)

    def test_execute_command_status(self):
        """Test status command execution."""
        message = {
            'type': 'private',
            'content': 'status'
        }

        response = execute_command(message)

        self.assertIn('running normally', response)
        self.assertIn('operational', response)

    def test_execute_command_unknown(self):
        """Test unknown command execution."""
        message = {
            'type': 'private',
            'content': 'unknowncommand'
        }

        response = execute_command(message)

        self.assertIn('Unknown command', response)
        self.assertIn('unknowncommand', response)

    def test_execute_command_stream_message(self):
        """Test command execution from stream message."""
        message = {
            'type': 'stream',
            'content': '@bot status check'
        }

        response = execute_command(message)

        self.assertIn('running normally', response)

    def test_execute_command_version(self):
        """Test version command."""
        message = {
            'type': 'private',
            'content': 'version'
        }

        response = execute_command(message)

        self.assertIn('Ritsuko', response)
        # Version string will vary based on environment
        self.assertTrue('v1.0' in response or 'laptop' in response or 'local' in response.lower())


class TestNodeCommand(unittest.TestCase):
    """Test the node command functionality."""

    def test_execute_command_node_with_single_node(self):
        """Test node command with a single node name."""
        message = {
            'type': 'private',
            'content': 'node test-node-01'
        }

        response = execute_command(message)

        self.assertIn('test-node-01', response)
        self.assertIn('Recent events', response)
        self.assertIn('Useful system checks', response)
        self.assertIn('Grafana links', response)
        self.assertIn('graphs.eencloud.com', response)
        self.assertIn('kubernetes-node-monitoring', response)
        self.assertIn('node-exporter-detailed', response)

    def test_execute_command_node_with_multiple_nodes(self):
        """Test node command with multiple node names."""
        message = {
            'type': 'private',
            'content': 'node node1 node2 node3'
        }

        response = execute_command(message)

        # Should only process first node due to current implementation
        self.assertIn('node1', response)
        self.assertIn('Recent events', response)
        self.assertIn('Grafana links', response)

    def test_execute_command_node_no_args(self):
        """Test node command without arguments."""
        message = {
            'type': 'private',
            'content': 'node'
        }

        response = execute_command(message)

        self.assertIn('Usage', response)
        self.assertIn('node <node>', response)
        self.assertIn('provide node name', response)

    def test_execute_command_node_from_stream(self):
        """Test node command from stream message."""
        message = {
            'type': 'stream',
            'content': '@bot node aus1p1-worker-01'
        }

        response = execute_command(message)

        self.assertIn('aus1p1-worker-01', response)
        self.assertIn('Grafana links', response)

    def test_node_command_includes_kubectl_commands(self):
        """Test that node command output includes kubectl command examples."""
        message = {
            'type': 'private',
            'content': 'node test-node'
        }

        response = execute_command(message)

        self.assertIn('kubectl events', response)
        self.assertIn('systemctl status kubelet', response)

    def test_node_command_includes_grafana_dashboard_links(self):
        """Test that node command includes all three Grafana dashboard links."""
        message = {
            'type': 'private',
            'content': 'node worker-node-123'
        }

        response = execute_command(message)

        # Check for all three Grafana dashboard links
        self.assertIn('Kubernetes node monitoring', response)
        self.assertIn('Node exporter detailed', response)
        self.assertIn('Node monitoring -DC-', response)

        # Verify URL structure
        self.assertIn('Node=worker-node-123', response)
        self.assertIn('kubernetes_node=worker-node-123', response)

    def test_node_command_includes_journalctl_example(self):
        """Test that node command includes journalctl SSH example."""
        message = {
            'type': 'private',
            'content': 'node prod-node-05'
        }

        response = execute_command(message)

        self.assertIn('ssh prod-node-05', response)
        self.assertIn('journalctl -u kubelet', response)
        self.assertIn('--since yesterday', response)

    def test_node_command_with_special_characters(self):
        """Test node command with node name containing special characters."""
        message = {
            'type': 'private',
            'content': 'node aus1p1-worker-01.example.com'
        }

        response = execute_command(message)

        self.assertIn('aus1p1-worker-01.example.com', response)
        self.assertIn('Grafana links', response)

    def test_node_command_formatting(self):
        """Test that node command response is properly formatted with markdown."""
        message = {
            'type': 'private',
            'content': 'node test-node'
        }

        response = execute_command(message)

        # Check for markdown formatting elements
        self.assertIn('##', response)  # Headers
        self.assertIn('```', response)  # Code blocks
        self.assertIn('[', response)    # Links
        self.assertIn(']', response)


class TestHealthCheckServer(unittest.TestCase):
    """Test the health check HTTP server."""

    def test_health_server_starts(self):
        """Test that health server starts successfully."""
        server = bot.start_health_server(port=8081)

        # Give server time to start
        time.sleep(0.5)

        self.assertIsNotNone(server)

        # Clean up
        server.shutdown()

    def test_healthz_endpoint(self):
        """Test /healthz endpoint returns 200 OK."""
        server = bot.start_health_server(port=8082)

        # Give server time to start
        time.sleep(0.5)

        try:
            response = urllib.request.urlopen('http://localhost:8082/healthz', timeout=2)
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b'OK')
        finally:
            server.shutdown()

    def test_readyz_endpoint(self):
        """Test /readyz endpoint returns 200 OK."""
        server = bot.start_health_server(port=8083)

        # Give server time to start
        time.sleep(0.5)

        try:
            response = urllib.request.urlopen('http://localhost:8083/readyz', timeout=2)
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b'OK')
        finally:
            server.shutdown()

    def test_invalid_endpoint_returns_404(self):
        """Test that invalid endpoints return 404."""
        server = bot.start_health_server(port=8084)

        # Give server time to start
        time.sleep(0.5)

        try:
            urllib.request.urlopen('http://localhost:8084/invalid', timeout=2)
            self.fail("Should have raised HTTPError")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)
        finally:
            server.shutdown()


if __name__ == '__main__':
    unittest.main()
