import os
import unittest
from unittest.mock import MagicMock, patch, call
import sys

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
            'content': 'ping',
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
        self.assertIn('Pong', call_args['content'])

    @patch('bot.send_message')
    def test_handle_message_authorized_user_stream(self, mock_send):
        """Test handling message from authorized user in stream."""
        mock_send.return_value = True

        message = {
            'sender_email': 'asajaroff@een.com',
            'content': '@bot ping',
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
        self.assertIn('Pong', call_args['content'])

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
        self.assertIn('ping', response)

    def test_execute_command_ping(self):
        """Test ping command execution."""
        message = {
            'type': 'private',
            'content': 'ping'
        }

        response = execute_command(message)

        self.assertIn('Pong', response)

    def test_execute_command_echo_with_args(self):
        """Test echo command with arguments."""
        message = {
            'type': 'private',
            'content': 'echo hello world'
        }

        response = execute_command(message)

        self.assertEqual(response, 'hello world')

    def test_execute_command_echo_no_args(self):
        """Test echo command without arguments."""
        message = {
            'type': 'private',
            'content': 'echo'
        }

        response = execute_command(message)

        self.assertIn('Usage', response)

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
        self.assertIn('local-dev', response)


if __name__ == '__main__':
    unittest.main()
