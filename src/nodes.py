import urllib3
from urllib3.util.retry import Retry
import json
import logging
from os import environ

sources = [
    {'vmall': 'jsqMEvfSk&var'}
  ]

vm_source = 'jsqMEvfSk&var'

def get_matchbox_file(node):
  return ''

# Configure retry strategy for transient failures
retry_strategy = Retry(
    total=3,  # Total number of retries
    status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry
    backoff_factor=1,  # Wait 1s, 2s, 4s between retries
    raise_on_status=False  # Return response instead of raising exception
)

# Create a PoolManager instance with timeouts and retry logic
http = urllib3.PoolManager(
    timeout=urllib3.Timeout(connect=5.0, read=30.0),  # 5s connect, 30s read timeout
    retries=retry_strategy,
    maxsize=10,  # Maximum number of connections to keep in pool
    block=False  # Raise exception if pool is exhausted instead of blocking
)

token = environ.get('GITHUB_MATCHBOX_TOKEN', None)
owner = "EENCloud"
repo = "matchbox"

# Define headers
headers = {
    "Accept": "application/vnd.github.raw+json",
    "Authorization": f"Bearer {token}",
    "X-GitHub-Api-Version": "2022-11-28"
}

def handle_node(message, nodes):
  if not nodes:
      return "Usage: `node <node>` - Please provide node name."

  for node in nodes:
    node = node
    url = f"https://api.github.com/repos/{owner}/{repo}/contents//groups/{node}.json"

    try:
      response = http.request(
        "GET",
        url,
        headers=headers,
        redirect=True)

      # Check for HTTP errors (404, 403, etc.)
      if response.status == 404:
        logging.error(f"Node '{node}' not found in matchbox repository")
        return f"**Error**: Node `{node}` not found in matchbox repository.\n\nPlease verify the node name is correct. You can also try the `nautobot {node}` command to search for the node in Nautobot."
      elif response.status == 403:
        logging.error(f"Access forbidden to matchbox repository for node '{node}'")
        return f"**Error**: Access forbidden when querying node `{node}`. The GitHub token may be invalid or lack necessary permissions."
      elif response.status >= 400:
        logging.error(f"HTTP error {response.status} when querying node '{node}'")
        return f"**Error**: Failed to retrieve node `{node}` from matchbox repository (HTTP {response.status})."

      json_string = response.data.decode('utf-8')
      matchbox_data = json.loads(json_string)
      context = matchbox_data.get('metadata', {}).get('pod', None)
    except urllib3.exceptions.TimeoutError as e:
      logging.error(f"Timeout when querying node '{node}' from GitHub: {e}")
      return f"**Error**: Request timed out while retrieving node `{node}` from matchbox repository. GitHub API may be slow or unavailable. Please try again."
    except urllib3.exceptions.MaxRetryError as e:
      logging.error(f"Max retries exceeded when querying node '{node}': {e}")
      return f"**Error**: Failed to connect to GitHub API after multiple attempts while querying node `{node}`. Please check network connectivity or try again later."
    except json.JSONDecodeError as e:
      logging.error(f"Failed to parse matchbox data for node '{node}': {e}")
      return f"**Error**: Failed to parse matchbox data for node `{node}`. The data may be corrupted or in an unexpected format."
    except Exception as e:
      logging.error(f"Unexpected error when querying node '{node}': {e}")
      return f"**Error**: An unexpected error occurred while retrieving node `{node}`: {str(e)}"

    reply = []

    return f"""### {node}
**Cluster**: {matchbox_data['metadata'].get('pod', 'N/A')} | **PublicIP**: \t{matchbox_data['metadata'].get('public_ip', 'N/A')}
Kubernetes: {matchbox_data['metadata'].get('kubernetes_version', 'N/A')}
Flatcar: {matchbox_data['metadata'].get('flatcar_version', 'N/A')}

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
kubectl get events --context {context} \\
      --field-selector involvedObject.name={node} \\
      --sort-by=metadata.creationTimestamp \\
      -A
```

```bash
kubectl get pods --context {context} -A \\
      --field-selector='status.phase=Failed'
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
