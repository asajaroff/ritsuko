import urllib3
import json
import logging
from os import environ

sources = [
    {'vmall': 'jsqMEvfSk&var'}
  ]

vm_source = 'jsqMEvfSk&var'

def get_matchbox_file(node):
  return ''

# Create a PoolManager instance
http = urllib3.PoolManager()
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
    response = http.request(
      "GET",
      url,
      headers=headers,
      redirect=True)

    json_string = response.data.decode('utf-8')
    matchbox_data = json.loads(json_string)
    context = matchbox_data.get('metadata', {}).get('pod', None)

    reply = []

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
