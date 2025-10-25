import logging
from os import environ

def parse_command(message):
    """
    Parse command from a Zulip message.

    For stream messages: extracts the second word (first word after bot mention)
    For private messages: extracts the first word

    Args:
        message: Zulip message dict

    Returns:
        tuple: (command, args) where command is the parsed command string and args is the rest
    """
    content = message.get('content', '').strip()
    words = content.split()

    if not words:
        return None, []

    if message['type'] == 'stream':
        # In stream messages, first word is typically the bot mention (@bot)
        # Command is the second word
        if len(words) < 2:
            return None, []
        command = words[1].lower()
        args = words[2:] if len(words) > 2 else []
    else:  # private message
        # In private messages, first word is the command
        command = words[0].lower()
        args = words[1:] if len(words) > 1 else []

    return command, args


def handle_help(message, args):
    """Handle the help command."""
    help_text = """
**Available Commands:**
- `help` - Show this help message
- `ping` - Check if bot is responsive
- `status` - Get bot status information
- `echo <text>` - Echo back the provided text
- `version` - Show bot version

More commands coming soon!
"""
    return help_text


def handle_ping(message, args):
    """Handle the ping command."""
    return "Pong! Bot is alive and responding."


def handle_status(message, args):
    """Handle the status command."""
    return "Bot is running normally. All systems operational."


def handle_echo(message, args):
    """Handle the echo command."""
    if not args:
        return "Usage: `echo <text>` - Please provide text to echo."
    return ' '.join(args)


def handle_version(message, args):
    """Handle the version command."""
    return f"Ritsuko {environ.get('RITSUKO_VERSION', 'local-dev')}"


def handle_unknown(message, command):
    """Handle unknown commands."""
    return f"Unknown command: `{command}`. Type `help` for available commands."


def execute_command(message):
    """
    Execute a command parsed from a Zulip message.

    Args:
        message: Zulip message dict

    Returns:
        str: Response text to send back
    """
    command, args = parse_command(message)

    if not command:
        return "No command specified. Type `help` for available commands."

    logging.info(f"Executing command: {command} with args: {args}")

    # Command router using match/case (Python 3.10+)
    match command:
        case 'help':
            return handle_help(message, args)
        case 'ping':
            return handle_ping(message, args)
        case 'status':
            return handle_status(message, args)
        case 'echo':
            return handle_echo(message, args)
        case 'version':
            return handle_version(message, args)
        case _:
            return handle_unknown(message, command)
