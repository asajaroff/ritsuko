import logging
from os import environ
import urllib3
import json

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

sources = [
    {'vmall': 'jsqMEvfSk&var'}
  ]

vm_source = 'jsqMEvfSk&var'

def handle_node(message, nodes):
    # Create a PoolManager instance
    http = urllib3.PoolManager()
    if not nodes:
        return "Usage: `node <node>` - Please provide node name."
    for node in nodes: # **TODO**: fix for more args

      token = environ.get('GITHUB_MATCHBOX_TOKEN', None)
      owner = "EENCloud"
      repo = "matchbox"
      node = node
      path = f"groups/{node}.json"

      url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

      # Define headers
      headers = {
          "Accept": "application/vnd.github.raw+json",
          "Authorization": f"Bearer {token}",
          "X-GitHub-Api-Version": "2022-11-28"
      }

      # Make the request
      response = http.request(
          "GET",
          url,
          headers=headers,
          redirect=True
      )

      json_string = response.data.decode('utf-8')
      matchbox_data = json.loads(json_string)
      context = matchbox_data['metadata']['pod']


      return f"""### {node}
**Cluster**: {matchbox_data['metadata']['pod']} | **PublicIP**: \t{matchbox_data['metadata']['public_ip']}
Kubernetes: {matchbox_data['metadata']['kubernetes_version']}
Flatcar: {matchbox_data['metadata']['flatcar_version']}

```spoiler Grafana dashboard
## Grafana links
0. [Cluster Status Dashboard](https://graphs.eencloud.com/d/ceby874mq9ds0e/kubernetes-resource-requests-limits-by-node-vm?orgId=1&var-pod=bebxvkipvaio0e&var-node=All)
1. [Kubernetes node monitoring](https://graphs.eencloud.com/d/000000001/kubernetes-node-monitoring?orgId=1&var-Pod={vm_source}-Node={node})
2. [Node exporter detailed](https://graphs.eencloud.com/d/bovUFBfGz/node-exporter-detailed?orgId=1&var-Pod={vm_source}-Node={node}&var-job=kubernetes-service-endpoints&var-diskdevices=%5Ba-z%5D%2B%7Cnvme%5B0-9%5D%2Bn%5B0-9%5D%2B)
3. [Node monitoring -DC-](https://graphs.eencloud.com/d/aedj1sncwnpc0a/dc-node-monitoring?orgId=1&refresh=1m&var-eepod={vm_source}-kubernetes_node={node})
```

```spoiler Matchbox file
```json
{json.dumps(matchbox_data, indent=2)}
```
```

```spoiler Kubernetes events

## Recent events

```bash
kubectl get events --context {context} \
      --field-selector involvedObject.name={node} \
      --sort-by=metadata.creationTimestamp \
      -A
```

```bash
kubectl get pods --context {context} -A \
      --field-selector='status.phase=Failed' \
```

```bash
# Check latests helm deploys -command is slow and expensive for the k8s masters-
helm list --date --reverse
```
```

```spoiler Terminal one-liners
```shell-session
# Check kubelet service
$ ssh {node} -- systemctl status kubelet.service

# Check `containerd`
$ ssh {node} -- systemctl status containerd.service

# Check `docker`
$ ssh {node} -- systemctl status docker.service

# Check `kubelet`
$ ssh {node} -- journalctl -u kubelet -p 3 --since yesterday --no-follow
```
```
"""

def node_info(node_name):
  # Node exporter dashboard
  # https://graphs.eencloud.com/d/bovUFBfGz/node-exporter-detailed?orgId=1
  return f"https://graphs.eencloud.com/d/bovUFBfGz/node-exporter-detailed?orgId=1&var-Pod={vm_source}-Node={node_name}&var-job=kubernetes-service-endpoints&var-diskdevices=%5Ba-z%5D%2B%7Cnvme%5B0-9%5D%2Bn%5B0-9%5D%2B"

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
