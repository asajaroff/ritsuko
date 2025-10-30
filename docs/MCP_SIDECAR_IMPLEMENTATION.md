# MCP Sidecar Implementation Plan

## Overview

This document outlines the implementation steps for adding Model Context Protocol (MCP) servers as sidecar containers within the Ritsuko Zulip bot pod. This architecture will enable the bot to interact with multiple MCP servers via HTTP on localhost, providing enhanced capabilities for infrastructure monitoring, log analysis, and debugging.

## Architecture

### Current State
- Single container pod running the Ritsuko Zulip bot
- Bot handles commands and responds to messages
- Limited to built-in functionality

### Target State
- Multi-container pod with:
  - Main container: Ritsuko bot (Python application)
  - Sidecar containers: MCP servers (one per MCP service)
- All containers share localhost network space
- Bot communicates with MCP servers via HTTP on localhost
- Each MCP server exposes specific tools/capabilities

## Implementation Steps

### Phase 1: MCP Client Integration in Bot

#### 1.1 Add MCP Client Dependencies
**File:** `src/requirements.txt`

Add Python MCP client library:
```
anthropic-mcp>=0.1.0  # or appropriate MCP client library
httpx>=0.25.0  # for HTTP communication with MCP servers
```

#### 1.2 Create MCP Client Module
**File:** `src/mcp_client.py`

Create a new module to handle MCP server communication:
```python
import httpx
import logging
from typing import Dict, List, Any, Optional

class MCPClient:
    """Client for communicating with MCP servers running as sidecars."""

    def __init__(self, servers: Dict[str, str]):
        """
        Initialize MCP client with server configurations.

        Args:
            servers: Dict mapping server names to their localhost URLs
                    e.g., {'kubernetes': 'http://localhost:8081'}
        """
        self.servers = servers
        self.client = httpx.AsyncClient(timeout=30.0)

    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """List available tools from an MCP server."""
        # Implementation
        pass

    async def call_tool(self, server_name: str, tool_name: str,
                       arguments: Dict[str, Any]) -> Any:
        """Call a tool on an MCP server."""
        # Implementation
        pass

    async def close(self):
        """Close HTTP client connections."""
        await self.client.aclose()
```

#### 1.3 Update Bot to Initialize MCP Client
**File:** `src/bot.py`

Add MCP client initialization:
```python
from mcp_client import MCPClient

# Add after environment variable validation
mcp_servers = {
    'kubernetes': os.environ.get('MCP_KUBERNETES_URL', 'http://localhost:8081'),
    'prometheus': os.environ.get('MCP_PROMETHEUS_URL', 'http://localhost:8082'),
    # Add more MCP servers as needed
}

try:
    mcp_client = MCPClient(mcp_servers)
    logging.info(f'Initialized MCP client with servers: {list(mcp_servers.keys())}')
except Exception as e:
    logging.warning(f'Failed to initialize MCP client: {e}')
    mcp_client = None
```

#### 1.4 Add MCP Command Handler
**File:** `src/commands.py`

Add handler for MCP commands:
```python
async def handle_mcp(message, args, mcp_client):
    """
    Handle MCP command to interact with MCP servers.

    Usage:
        mcp <server> <tool> [args...]
        mcp list - List all available MCP servers and their tools
    """
    if not mcp_client:
        return "MCP client is not available. Check bot configuration."

    if not args:
        return "Usage: `mcp <server> <tool> [args...]` or `mcp list`"

    if args[0] == 'list':
        # List all servers and their tools
        return await list_mcp_capabilities(mcp_client)

    server_name = args[0]
    if len(args) < 2:
        return f"Usage: `mcp {server_name} <tool> [args...]`"

    tool_name = args[1]
    tool_args = args[2:]

    try:
        result = await mcp_client.call_tool(server_name, tool_name, tool_args)
        return format_mcp_result(result)
    except Exception as e:
        logging.error(f'MCP command failed: {e}')
        return f"Error executing MCP command: {str(e)}"
```

Update command router to include MCP handler with async support.

### Phase 2: Helm Chart Updates for Sidecar Containers

#### 2.1 Update values.yaml
**File:** `chart/values.yaml`

Add sidecar configuration section:
```yaml
# MCP Sidecar containers configuration
mcpSidecars:
  enabled: true

  # Kubernetes MCP server
  kubernetes:
    enabled: true
    image:
      repository: harbor.eencloud.com/mcp/kubernetes-server
      tag: "v0.1.0"
      pullPolicy: IfNotPresent
    port: 8081
    resources:
      limits:
        cpu: 200m
        memory: 256Mi
      requests:
        cpu: 100m
        memory: 128Mi
    env:
      - name: MCP_PORT
        value: "8081"
      - name: LOG_LEVEL
        value: "INFO"
    # Mount kubeconfig if needed
    volumeMounts: []

  # Prometheus/Metrics MCP server
  prometheus:
    enabled: true
    image:
      repository: harbor.eencloud.com/mcp/prometheus-server
      tag: "v0.1.0"
      pullPolicy: IfNotPresent
    port: 8082
    resources:
      limits:
        cpu: 200m
        memory: 256Mi
      requests:
        cpu: 100m
        memory: 128Mi
    env:
      - name: MCP_PORT
        value: "8082"
      - name: PROMETHEUS_URL
        value: "https://graphs.eencloud.com"

  # Logs MCP server
  logs:
    enabled: false
    image:
      repository: harbor.eencloud.com/mcp/logs-server
      tag: "v0.1.0"
      pullPolicy: IfNotPresent
    port: 8083
    resources:
      limits:
        cpu: 200m
        memory: 256Mi
      requests:
        cpu: 100m
        memory: 128Mi

# Environment variables for main bot container
env:
  logLevel: "INFO"
  mcpKubernetesUrl: "http://localhost:8081"
  mcpPrometheusUrl: "http://localhost:8082"
  mcpLogsUrl: "http://localhost:8083"
```

#### 2.2 Update deployment.yaml
**File:** `chart/templates/deployment.yaml`

Add sidecar containers section after the main container definition (around line 93):

```yaml
      {{- if .Values.mcpSidecars.enabled }}
      # MCP Sidecar Containers
      {{- if .Values.mcpSidecars.kubernetes.enabled }}
        - name: mcp-kubernetes
          image: "{{ .Values.mcpSidecars.kubernetes.image.repository }}:{{ .Values.mcpSidecars.kubernetes.image.tag }}"
          imagePullPolicy: {{ .Values.mcpSidecars.kubernetes.image.pullPolicy }}
          ports:
            - name: mcp-k8s
              containerPort: {{ .Values.mcpSidecars.kubernetes.port }}
              protocol: TCP
          env:
            {{- toYaml .Values.mcpSidecars.kubernetes.env | nindent 12 }}
          {{- with .Values.mcpSidecars.kubernetes.resources }}
          resources:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.mcpSidecars.kubernetes.volumeMounts }}
          volumeMounts:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          livenessProbe:
            httpGet:
              path: /health
              port: {{ .Values.mcpSidecars.kubernetes.port }}
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: {{ .Values.mcpSidecars.kubernetes.port }}
            initialDelaySeconds: 5
            periodSeconds: 10
      {{- end }}

      {{- if .Values.mcpSidecars.prometheus.enabled }}
        - name: mcp-prometheus
          image: "{{ .Values.mcpSidecars.prometheus.image.repository }}:{{ .Values.mcpSidecars.prometheus.image.tag }}"
          imagePullPolicy: {{ .Values.mcpSidecars.prometheus.image.pullPolicy }}
          ports:
            - name: mcp-prom
              containerPort: {{ .Values.mcpSidecars.prometheus.port }}
              protocol: TCP
          env:
            {{- toYaml .Values.mcpSidecars.prometheus.env | nindent 12 }}
          {{- with .Values.mcpSidecars.prometheus.resources }}
          resources:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          livenessProbe:
            httpGet:
              path: /health
              port: {{ .Values.mcpSidecars.prometheus.port }}
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: {{ .Values.mcpSidecars.prometheus.port }}
            initialDelaySeconds: 5
            periodSeconds: 10
      {{- end }}

      {{- if .Values.mcpSidecars.logs.enabled }}
        - name: mcp-logs
          image: "{{ .Values.mcpSidecars.logs.image.repository }}:{{ .Values.mcpSidecars.logs.image.tag }}"
          imagePullPolicy: {{ .Values.mcpSidecars.logs.image.pullPolicy }}
          ports:
            - name: mcp-logs
              containerPort: {{ .Values.mcpSidecars.logs.port }}
              protocol: TCP
          env:
            {{- toYaml .Values.mcpSidecars.logs.env | nindent 12 }}
          {{- with .Values.mcpSidecars.logs.resources }}
          resources:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          livenessProbe:
            httpGet:
              path: /health
              port: {{ .Values.mcpSidecars.logs.port }}
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: {{ .Values.mcpSidecars.logs.port }}
            initialDelaySeconds: 5
            periodSeconds: 10
      {{- end }}
      {{- end }}
```

Update main container environment variables to include MCP URLs (around line 51):

```yaml
          env:
            - name: LOG_LEVEL
              value: {{ .Values.env.logLevel | quote }}
            - name: RITSUKO_VERSION
              value: "{{ $.Chart.AppVersion }} running in context 'test'"
            {{- if .Values.mcpSidecars.enabled }}
            - name: MCP_KUBERNETES_URL
              value: {{ .Values.env.mcpKubernetesUrl | quote }}
            - name: MCP_PROMETHEUS_URL
              value: {{ .Values.env.mcpPrometheusUrl | quote }}
            - name: MCP_LOGS_URL
              value: {{ .Values.env.mcpLogsUrl | quote }}
            {{- end }}
            {{- if .Values.secrets.create }}
            # ... existing secret env vars ...
```

### Phase 3: MCP Server Container Images

#### 3.1 Create MCP Server Dockerfiles

Each MCP server needs its own Dockerfile. Example structure:

**Directory structure:**
```
mcp-servers/
├── kubernetes/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── server.py
├── prometheus/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── server.py
└── logs/
    ├── Dockerfile
    ├── requirements.txt
    └── server.py
```

**Example Dockerfile for MCP server:**
```dockerfile
FROM python:3.13-slim-bookworm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

# Create non-root user
RUN useradd -m -s /bin/bash mcp-server
USER mcp-server

EXPOSE 8081

CMD ["python3", "server.py"]
```

#### 3.2 Implement MCP Server Logic

Each server should:
- Expose HTTP endpoints for MCP protocol
- Implement health check endpoint at `/health`
- Provide tool listing endpoint
- Provide tool execution endpoints
- Handle authentication/authorization if needed

### Phase 4: Testing

#### 4.1 Unit Tests
**File:** `src/test_bot.py`

Add tests for MCP client:
```python
import pytest
from mcp_client import MCPClient

@pytest.mark.asyncio
async def test_mcp_client_initialization():
    """Test MCP client can be initialized."""
    servers = {'test': 'http://localhost:8081'}
    client = MCPClient(servers)
    assert client is not None
    await client.close()

@pytest.mark.asyncio
async def test_mcp_list_tools():
    """Test listing tools from MCP server."""
    # Mock server or use test server
    pass

@pytest.mark.asyncio
async def test_mcp_call_tool():
    """Test calling a tool on MCP server."""
    # Mock server or use test server
    pass
```

#### 4.2 Local Development Testing

Update `Makefile` to support local testing with docker-compose:

**File:** `docker-compose.yml` (new file)
```yaml
version: '3.8'

services:
  ritsuko:
    build: .
    environment:
      - LOG_LEVEL=DEBUG
      - ZULIP_EMAIL=${ZULIP_EMAIL}
      - ZULIP_API_KEY=${ZULIP_API_KEY}
      - ZULIP_SITE=${ZULIP_SITE}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - MCP_KUBERNETES_URL=http://localhost:8081
      - MCP_PROMETHEUS_URL=http://localhost:8082
    network_mode: "host"

  mcp-kubernetes:
    build: ./mcp-servers/kubernetes
    environment:
      - MCP_PORT=8081
      - LOG_LEVEL=DEBUG
    network_mode: "host"

  mcp-prometheus:
    build: ./mcp-servers/prometheus
    environment:
      - MCP_PORT=8082
      - LOG_LEVEL=DEBUG
      - PROMETHEUS_URL=https://graphs.eencloud.com
    network_mode: "host"
```

Add Makefile target:
```makefile
.PHONY: dev-compose
dev-compose: ## Run with docker-compose for local development
	docker-compose up --build
```

#### 4.3 Integration Testing

Create integration tests that:
1. Start the bot with mock MCP servers
2. Send test commands
3. Verify MCP servers are called correctly
4. Verify responses are formatted correctly

### Phase 5: Documentation Updates

#### 5.1 Update README.md

Add section on MCP architecture:
```markdown
## MCP Architecture

Ritsuko uses Model Context Protocol (MCP) servers as sidecar containers to provide
extended capabilities:

- **Kubernetes MCP Server**: Query cluster resources, get node information, check pod status
- **Prometheus MCP Server**: Query metrics, create dashboard links, analyze performance
- **Logs MCP Server**: Search logs, aggregate errors, trace requests

All MCP servers run as sidecar containers in the same pod and communicate via HTTP
on localhost.

### Available MCP Commands

```
@Ritsuko mcp list                          # List all available MCP servers and tools
@Ritsuko mcp kubernetes get pods           # Get pods from Kubernetes
@Ritsuko mcp prometheus query cpu_usage    # Query Prometheus metrics
```
```

#### 5.2 Update CLAUDE.md

Document MCP integration for future AI assistance:
```markdown
## MCP Integration

The bot integrates with MCP servers running as sidecars:
- Each MCP server runs in its own container within the pod
- Communication happens via HTTP on localhost
- MCP client code is in `src/mcp_client.py`
- Command handlers in `src/commands.py` use async/await for MCP calls
- Sidecar configuration is in `chart/values.yaml` under `mcpSidecars`
```

### Phase 6: Deployment

#### 6.1 Build and Push MCP Server Images

Add to Makefile:
```makefile
.PHONY: build-mcp-servers
build-mcp-servers: ## Build all MCP server images
	docker build -t $(IMAGE_NAME)/mcp-kubernetes:$(IMAGE_TAG) mcp-servers/kubernetes/
	docker build -t $(IMAGE_NAME)/mcp-prometheus:$(IMAGE_TAG) mcp-servers/prometheus/
	docker build -t $(IMAGE_NAME)/mcp-logs:$(IMAGE_TAG) mcp-servers/logs/

.PHONY: push-mcp-servers
push-mcp-servers: build-mcp-servers ## Push all MCP server images
	docker push $(IMAGE_NAME)/mcp-kubernetes:$(IMAGE_TAG)
	docker push $(IMAGE_NAME)/mcp-prometheus:$(IMAGE_TAG)
	docker push $(IMAGE_NAME)/mcp-logs:$(IMAGE_TAG)
```

#### 6.2 Deploy with Helm

Update values-override.yaml for environment-specific configuration:
```yaml
mcpSidecars:
  enabled: true
  kubernetes:
    enabled: true
    image:
      tag: "v1.0.0"
  prometheus:
    enabled: true
    image:
      tag: "v1.0.0"
    env:
      - name: PROMETHEUS_URL
        value: "https://graphs.eencloud.com"
```

Deploy:
```bash
make helm-reinstall
```

## Security Considerations

1. **Network Isolation**: MCP servers only accessible via localhost within pod
2. **Authentication**: Bot authenticates to MCP servers via shared secrets (environment variables)
3. **Authorization**: MCP servers validate requests before executing tools
4. **Resource Limits**: Each sidecar has CPU/memory limits defined
5. **Read-Only Operations**: MCP servers should prioritize read-only operations
6. **Audit Logging**: All MCP tool calls should be logged with user information

## Monitoring and Observability

1. **Health Checks**: Each MCP server exposes `/health` endpoint
2. **Metrics**: Consider adding Prometheus metrics for MCP call latency and errors
3. **Logging**: Structured logging for all MCP interactions
4. **Alerts**: Set up alerts for MCP server failures or high error rates

## Rollback Plan

If issues occur after deployment:

1. Set `mcpSidecars.enabled: false` in values.yaml
2. Run `helm upgrade` to remove sidecars
3. Bot will gracefully handle missing MCP client
4. Investigate issues and redeploy when fixed

## Future Enhancements

1. **Dynamic MCP Discovery**: Auto-discover available MCP servers
2. **MCP Server Mesh**: Allow MCP servers to communicate with each other
3. **Enhanced Error Handling**: Better error messages and retry logic
4. **MCP Server Marketplace**: Easy addition of new MCP servers
5. **Performance Optimization**: Connection pooling, caching, etc.

## Timeline Estimate

- Phase 1 (MCP Client Integration): 2-3 days
- Phase 2 (Helm Chart Updates): 1 day
- Phase 3 (MCP Server Implementation): 3-5 days (per server)
- Phase 4 (Testing): 2-3 days
- Phase 5 (Documentation): 1 day
- Phase 6 (Deployment): 1 day

**Total**: ~2-3 weeks for full implementation with 2-3 MCP servers

## Success Criteria

- [ ] Bot can list available MCP servers and their tools
- [ ] Bot can execute commands via MCP servers
- [ ] All MCP servers have health checks and are monitored
- [ ] Helm chart properly configures sidecar containers
- [ ] Documentation is complete and accurate
- [ ] Unit and integration tests pass
- [ ] Successfully deployed to test environment
- [ ] Performance meets requirements (<1s response time for simple queries)
