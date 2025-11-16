import logging
import threading
import time
from os import environ

from ai_context import get_system_prompt
from fetchers import get_nautobot_devices
from nodes import handle_node
from rate_limiter import claude_rate_limiter
from validation import sanitize_for_logging, validate_ai_prompt, validate_node_name

# Import anthropic for AI functionality
try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logging.warning("anthropic package not available. AI command will not work.")


def parse_command(message):
    """
    Parse command from a Zulip message.

    For stream messages: extracts the second word (first word after bot mention)
    For private messages: extracts the first word (or second if first is a mention)

    Args:
        message: Zulip message dict

    Returns:
        tuple: (command, args) where command is the parsed command string
            and args is the rest
    """
    content = message.get("content", "").strip()
    words = content.split()

    if not words:
        return None, []

    if message["type"] == "stream":
        # In stream messages, first word is typically the bot mention (@bot)
        # Command is the second word
        if len(words) < 2:
            return None, []
        command = words[1].lower()
        args = words[2:] if len(words) > 2 else []
    else:  # private message
        # In private messages, first word is the command
        # Unless it's a bot mention (e.g., @**BotName** or @_**BotName**),
        # then second word is the command
        start_idx = 0
        if (words[0].startswith("@**") or words[0].startswith("@_**")) and words[
            0
        ].endswith("**"):
            # First word is a bot mention, skip it
            start_idx = 1

        if start_idx >= len(words):
            return None, []

        command = words[start_idx].lower()
        args = words[start_idx + 1 :] if len(words) > start_idx + 1 else []

    return command, args


def handle_help(message, args):
    help_text = """markdown
**Available Commands:**
- `ai <prompt>` - Interact with an LLM
- ~~`mcp <prompt>` - Interact with an LLM and MCP servers~~ **TODO**
- `nautobot <node>` - Get the nautobot info for the given node
- `status` - Get bot status information
- `clusters` | `clusters <cluster>` - Lists the cluster name and kubernetes
  cluster name - If a cluster is selected will bring data from that
- `node <node_name>` - Get information about a node
- ~~`jira <prompt>` - Interact with Jira~~ #TODO
- ~~`confluence <prompt>` - Interact with Confluence~~ **TODO**
- `help` - Show this help message
- `version` - Show bot version and debug information

Usage:
```markdown
@**Ritsuko** <command> [opts]
```
"""
    return help_text


def handle_ai(message, args, send_message_callback=None):
    """
    Handle the AI command to interact with Claude API.

    Args:
        message: Zulip message dict
        args: List of arguments passed to the AI command
        send_message_callback: Optional callback function to send intermediate messages

    Returns:
        str: AI response or error message
    """
    if not ANTHROPIC_AVAILABLE:
        return (
            "AI functionality is not available. The anthropic package is not installed."
        )

    api_key = environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return (
            "AI functionality is not available. "
            "ANTHROPIC_API_KEY environment variable is not set."
        )

    if not args:
        return "Usage: `ai <prompt>` - Please provide a prompt for the AI."

    # Join all args into a single prompt
    prompt = " ".join(args)

    # Validate prompt
    is_valid, error_msg = validate_ai_prompt(prompt)
    if not is_valid:
        logging.warning(
            f"Invalid AI prompt from {message.get('sender_email', 'unknown')}: "
            f"{error_msg}"
        )
        return f"Invalid prompt: {error_msg}"

    # Log sanitized version of prompt
    logging.info(
        f"AI prompt from {message.get('sender_email', 'unknown')}: "
        f"{sanitize_for_logging(prompt, 100)}"
    )

    # Apply rate limiting
    if not claude_rate_limiter.acquire(timeout=30.0):
        logging.warning(
            "Rate limit exceeded for AI request from "
            f"{message.get('sender_email', 'unknown')}"
        )
        return (
            "I'm currently processing too many requests. "
            "Please try again in a moment.\n\n"
            "If this persists, the bot may be experiencing high load. "
            "Contact your administrator."
        )

    try:
        # Send a processing message if we have a callback and it's expected to take time
        processing_notified = False
        start_time = time.time()

        # Create a timer to send processing notification after 5 seconds
        def notify_processing():
            nonlocal processing_notified
            if not processing_notified and send_message_callback:
                processing_notified = True
                processing_msg = {
                    "type": message["type"],
                    "content": "Processing your request... This may take a moment.",
                }

                if message["type"] == "stream":
                    processing_msg["to"] = message["display_recipient"]
                    processing_msg["subject"] = message["subject"]
                else:  # private
                    processing_msg["to"] = [
                        r["email"]
                        for r in message["display_recipient"]
                        if r["email"] != environ.get("ZULIP_EMAIL")
                    ]

                send_message_callback(processing_msg)

        timer = None
        if send_message_callback:
            timer = threading.Timer(5.0, notify_processing)
            timer.start()

        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=api_key)

        # Get system prompt from context
        system_prompt = get_system_prompt()

        # Build messages list
        messages = [{"role": "user", "content": prompt}]

        # Call Claude API with system prompt
        api_params = {
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 4096,
            "messages": messages,
        }

        # Add system prompt if available
        if system_prompt:
            api_params["system"] = system_prompt
            logging.debug("Using AI context system prompt")
        else:
            logging.warning("No AI context system prompt found, proceeding without it")

        response = client.messages.create(**api_params)

        # Cancel the timer if it hasn't fired yet
        if timer:
            timer.cancel()

        elapsed_time = time.time() - start_time
        logging.info(f"AI request completed in {elapsed_time:.2f} seconds")

        # Extract text from response
        if response.content and len(response.content) > 0:
            return response.content[0].text
        else:
            return "I received an empty response from the AI. Please try again."

    except Exception as e:
        # Cancel the timer in case of error
        if timer:
            timer.cancel()

        logging.error(f"Error in AI command: {e}")
        return f"An error occurred while processing your AI request: {str(e)}"


def handle_status(message, args):
    """Handle the status command with rate limiter metrics."""
    # Get rate limiter metrics
    metrics = claude_rate_limiter.get_metrics()

    status_text = f"""**Bot Status**: Running normally

**Rate Limiter Metrics**:
- Available tokens: {metrics['available_tokens']}/\
{metrics['burst_size']}
- Total requests processed: {metrics['total_requests']}
- Requests queued: {metrics['total_queued']}
- Requests rejected: {metrics['total_rejected']}
- Rate limit: {metrics['requests_per_minute']} requests/minute

**Features**:
"""
    ai_available = ANTHROPIC_AVAILABLE and environ.get("ANTHROPIC_API_KEY")
    node_available = environ.get("GITHUB_MATCHBOX_TOKEN")
    nautobot_available = environ.get("NAUTOBOT_TOKEN")

    status_text += f"""- AI commands: {'✓' if ai_available else '✗'}
- Node queries: {'✓' if node_available else '✗'}
- Nautobot queries: {'✓' if nautobot_available else '✗'}
"""
    return status_text


def handle_clusters(message, args):
    """Handle the clusters command."""
    return (
        "## Clusters - [VMS Global Uptime]"
        "(https://graphs.eencloud.com/d/jFpmPakGk/vms-global-uptime)\n"
        "c001  - aus1p1\n"
        "c002  - test\n"
        "c006  - nrt1p1\n"
        "c007  - hnd1p1\n"
        "c011  - hkg1p1\n"
        "c012  - aus1p3\n"
        "c013  - fra1p1\n"
        "c014  - aus1p4\n"
        "c015  - aus1p5\n"
        "c016  - aus1p7\n"
        "c017  - aus1p8\n"
        "c018  - aus1p9\n"
        "c019  - fra1p2\n"
        "c020  - aus1p10\n"
        "c021  - aus1p11\n"
        "c022  - lon1p1\n"
        "c023  - aus1p12 (test)\n"
        "c024  - aus1p13\n"
        "c025  - yyz1p1\n"
        "c026  - aus1p14\n"
        "c027  - aus1p15\n"
        "c028  - aus1p16\n"
        "c029  - ruh1p1\n"
        "c030  - aus1p17\n"
        "c031  - aus2p1\n"
    )


def handle_nautobot(args):
    if not args:
        return "Usage: `nautobot <node>` - Please provide node name."

    # Validate all node names before processing
    invalid_nodes = []
    for node in args:
        is_valid, error_msg = validate_node_name(node)
        if not is_valid:
            invalid_nodes.append(f"`{sanitize_for_logging(node, 50)}`: {error_msg}")

    if invalid_nodes:
        return "Invalid node name(s):\n" + "\n".join(invalid_nodes)

    all_devices = []
    for node in args:
        devices = get_nautobot_devices(node)
        all_devices.extend(devices)

    result = "\n".join(all_devices)
    return result


def handle_version(message, args):
    """Handle the version command."""
    default_version = "v1.0.5 running in Alejandro's laptop"
    return f"Ritsuko {environ.get('RITSUKO_VERSION', default_version)}"


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
        case "help":
            return handle_help(message, args)
        case "ai":
            return handle_ai(message, args)
        case "mcp":
            return "MCP command is not yet implemented. Coming soon!"
        case "node":
            return handle_node(message, args)
        case "nautobot":
            return handle_nautobot(args)
        case "cluster":
            return handle_clusters(message, args)
        case "clusters":
            return handle_clusters(message, args)
        case "status":
            return handle_status(message, args)
        case "version":
            return handle_version(message, args)
        case _:
            return handle_unknown(message, command)
