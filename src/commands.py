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
- `clusters` - Lists the cluster name and kubernetes cluster name
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
    # TODO: Readiness proble
    # TODO: MCP connection probes
    return "Bot is running normally. All systems operational."

def handle_clusters(message, args):
    """Handle the clusters command."""
    return f"""
c000  - F&F
c001  - aus1p1
c002  - test
c004  - aus1p6
c005  - aus1p2
c006  - nrt1p1
c007  - hnd1p1
c010  - sandbox
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

sources = [
    {'vmall': 'jsqMEvfSk&var'}
  ]

vm_source = 'jsqMEvfSk&var'

def handle_node(message, nodes):
    if not nodes:
        return "Usage: `node <node>` - Please provide node name."
    for node in nodes: # TODO: fix for more args
      return f"""## {node}
## Recent events TODO:
```shell-session
$ kubectl get events # Get events for this particular node
```

## Kubelet status
```shell-session
$ check_kubelet_status('{nodes}')
```
## Grafana links
1. [Kubernetes node monitoring](https://graphs.eencloud.com/d/000000001/kubernetes-node-monitoring?orgId=1&var-Pod={vm_source}-Node={node})
2. [Node exporter detailed](https://graphs.eencloud.com/d/bovUFBfGz/node-exporter-detailed?orgId=1&var-Pod={vm_source}-Node={node}&var-job=kubernetes-service-endpoints&var-diskdevices=%5Ba-z%5D%2B%7Cnvme%5B0-9%5D%2Bn%5B0-9%5D%2B)
3. [Node monitoring -DC-](https://graphs.eencloud.com/d/aedj1sncwnpc0a/dc-node-monitoring?orgId=1&refresh=1m&var-eepod={vm_source}-kubernetes_node={node})

```shell-session
$ ssh {node} -- journalctl -u kubelet -p 3 --since yesterday
<profit>
```
"""
    return f"https://graphs.eencloud.com/d/bovUFBfGz/node-exporter-detailed?orgId=1&var-Pod={vm_source}-Node={node_name}&var-job=kubernetes-service-endpoints&var-diskdevices=%5Ba-z%5D%2B%7Cnvme%5B0-9%5D%2Bn%5B0-9%5D%2B"

def node_info(node_name):
  # Cluster status dashboard
  # https://graphs.eencloud.com/d/ceby874mq9ds0e/kubernetes-resource-requests-limits-by-node-vm?orgId=1&var-pod=bebxvkipvaio0e&var-node=All
  # Node exporter dashboard
  # https://graphs.eencloud.com/d/bovUFBfGz/node-exporter-detailed?orgId=1
  return f"https://graphs.eencloud.com/d/bovUFBfGz/node-exporter-detailed?orgId=1&var-Pod={vm_source}-Node={node_name}&var-job=kubernetes-service-endpoints&var-diskdevices=%5Ba-z%5D%2B%7Cnvme%5B0-9%5D%2Bn%5B0-9%5D%2B"


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
        case 'clusters':
            return handle_clusters(message, args)
        case 'node':
            return handle_node(message, args)
        case 'echo':
            return handle_echo(message, args)
        case 'version':
            return handle_version(message, args)
        case _:
            return handle_unknown(message, command)
