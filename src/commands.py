import logging
from os import environ
import urllib3
import json

from nodes import handle_node

from fetchers import get_nautobot_devices

def parse_command(message):
    """
    Parse command from a Zulip message.

    For stream messages: extracts the second word (first word after bot mention)
    For private messages: extracts the first word (or second if first is a mention)

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
        # Unless it's a bot mention (e.g., @**BotName** or @_**BotName**), then second word is the command
        start_idx = 0
        if (words[0].startswith('@**') or words[0].startswith('@_**')) and words[0].endswith('**'):
            # First word is a bot mention, skip it
            start_idx = 1

        if start_idx >= len(words):
            return None, []

        command = words[start_idx].lower()
        args = words[start_idx + 1:] if len(words) > start_idx + 1 else []

    return command, args


def handle_help(message, args):
    help_text = """markdown
**Available Commands:**
- `ai <prompt>` - Interact with an LLM **TODO**
- `mcp <prompt>` - Interact with an LLM and MCP servers **TODO**
- `status` - Get bot status information
- `clusters` | `clusters <cluster>` - Lists the cluster name and kubernetes cluster name - If a cluster is selected will bring data from that
- `node <node_name>` - Get information about a node
- `jira <prompt>` - Interact with Jira #TODO
- `confluence <prompt>` - Interact with Confluence **TODO**
- `help` - Show this help message
- `version` - Show bot version and debug info

Usage:
```markdown
@**Ritsuko** <command> [opts]
```
"""
    return help_text


def handle_status(message, args):
    """Handle the status command."""
    # **TODO**: Readiness proble
    # **TODO**: MCP connection probes
    return "Bot is running normally. All systems operational."

def handle_clusters(message, args):
    """Handle the clusters command."""
    return f"""## Clusters - [VMS Global Uptime](https://graphs.eencloud.com/d/jFpmPakGk/vms-global-uptime)
c001  - aus1p1
c002  - test
c006  - nrt1p1
c007  - hnd1p1
c011  - hkg1p1
c012  - aus1p3
c013  - fra1p1
c014  - aus1p4
c015  - aus1p5
c016  - aus1p7
c017  - aus1p8
c018  - aus1p9
c019  - fra1p2
c020  - aus1p10
c021  - aus1p11
c022  - lon1p1
c023  - aus1p12 (test)
c024  - aus1p13
c025  - yyz1p1
c026  - aus1p14
c027  - aus1p15
c028  - aus1p16
c029  - ruh1p1
c030  - aus1p17
c031  - aus2p1
"""

def handle_nautobot(args):
  if not args:
    return "Usage: `nautobot <node>` - Please provide node name."

  all_devices = []
  for node in args:
    devices = get_nautobot_devices(node)
    all_devices.extend(devices)

  result = '\n'.join(all_devices)
  return result if result else "No devices found."

def handle_version(message, args):
    """Handle the version command."""
    return f"Ritsuko {environ.get('RITSUKO_VERSION', 'v1.0.5 running in Alejandro\'s laptop')}"

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
        case 'ai':
            return "AI command is not yet implemented. Coming soon!"
        case 'mcp':
            return "MCP command is not yet implemented. Coming soon!"
        case 'node':
            return handle_node(message, args)
        case 'nautobot':
            return handle_nautobot(args)
        case 'cluster':
            return handle_clusters(message, args)
        case 'clusters':
            return handle_clusters(message, args)
        case 'status':
            return handle_status(message, args)
        case 'version':
            return handle_version(message, args)
        case _:
            return handle_unknown(message, command)
