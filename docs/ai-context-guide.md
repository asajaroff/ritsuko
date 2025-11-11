# AI Context Configuration Guide

This guide explains how to configure and maintain the AI context for Ritsuko, the SRE chat bot.

## Overview

The AI context system provides the Claude AI model with:
- **Response guidelines**: How the bot should communicate
- **Technology information**: Versions, clusters, and infrastructure details
- **MCP tool capabilities**: What operations are available
- **Domain knowledge**: Common issues, troubleshooting steps, and runbooks

## Configuration File

The AI context is defined in `src/ai_context.yaml`. This YAML file is loaded when the bot starts and provides the system prompt for all AI interactions.

## File Structure

```yaml
response_guidelines:    # How the AI should respond
technologies:           # Technologies and versions in use
mcp_tools:             # Available MCP operations
domain_knowledge:       # Common issues, runbooks, best practices
system_prompt:         # The complete system prompt (assembled from above)
```

## Updating the Context

### When to Update

You should update the AI context when:

1. **New clusters are added** - Add to `technologies.kubernetes.clusters`
2. **Versions change** - Update version numbers in `technologies`
3. **New dashboards created** - Add to `technologies.monitoring.grafana.key_dashboards`
4. **New MCP capabilities** - Add to `mcp_tools.available_operations`
5. **New runbooks** - Add to `domain_knowledge.runbooks`
6. **Common issues identified** - Document in `domain_knowledge.common_issues`

### How to Update

1. Edit `src/ai_context.yaml` directly
2. Validate YAML syntax (use a YAML linter or parser)
3. Test your changes by deploying and using the `ai` command
4. Commit the changes to version control

**Example: Adding a new cluster**

```yaml
technologies:
  kubernetes:
    version: "1.28+"
    clusters:
      - c001: "aus1p1"
      # ... existing clusters
      - c032: "new-cluster-name"  # Add your new cluster here
```

**Example: Adding a common issue**

```yaml
domain_knowledge:
  common_issues:
    ingress_503_errors:  # New issue category
      symptoms:
        - "503 Service Unavailable from ingress"
        - "Backend service not responding"
      troubleshooting_steps:
        - "Check backend pod status: `kubectl get pods -n <namespace>`"
        - "Verify service endpoints: `kubectl get endpoints <service> -n <namespace>`"
        - "Check ingress configuration: `kubectl describe ingress <name> -n <namespace>`"
```

## System Prompt

The `system_prompt` section at the bottom of the YAML file is the complete prompt sent to Claude. It should:

- Be concise but complete
- Reference key resources and commands
- Establish the bot's role and constraints
- Provide guidelines for escalation

You can modify this directly, or it can be assembled from the other sections programmatically if needed.

## Response Guidelines

These guide how the AI formats and structures its responses:

```yaml
response_guidelines:
  tone: "Professional, concise, and helpful"
  style: "Use markdown formatting"
  length: "Keep responses brief but complete"
  formatting:
    - "Use code blocks for commands"
    - "Use **bold** for warnings"
  escalation_triggers:
    - "Critical production issues"
    - "Security incidents"
```

### Best Practices for Response Guidelines

- Keep the tone consistent with your team culture
- Be specific about formatting preferences
- Clearly define escalation criteria
- Include safety constraints (read-only, no destructive ops)

## Technologies Section

Document all relevant technologies with versions:

```yaml
technologies:
  kubernetes:
    version: "1.28+"
    clusters: [...]
    common_namespaces: [...]

  python:
    version: "3.11+"
    key_packages: [...]

  monitoring:
    grafana:
      url: "https://graphs.eencloud.com"
      key_dashboards: [...]
```

### Why This Matters

The AI uses this information to:
- Suggest correct kubectl commands
- Reference appropriate dashboards
- Understand available tools and versions
- Provide context-aware troubleshooting

## MCP Tools Section

Document what operations the bot can perform via MCP:

```yaml
mcp_tools:
  available_operations:
    kubernetes:
      - name: "kubectl get"
        description: "Read Kubernetes resources"
        scope: "read-only"

    metrics:
      - name: "prometheus queries"
        description: "Query metrics"
        scope: "read-only"
```

### Adding New MCP Capabilities

When you add new MCP servers or capabilities:

1. Document the operation name
2. Provide a clear description
3. Specify the scope (read-only, read-write, etc.)
4. Add any constraints or prerequisites

## Domain Knowledge Section

This is where you encode tribal knowledge into the bot.

### Common Issues

Document recurring problems with:
- **Symptoms**: How users identify the issue
- **Troubleshooting steps**: Ordered list of diagnostic steps
- **Related resources**: Dashboards, docs, runbooks

```yaml
domain_knowledge:
  common_issues:
    pod_crashes:
      symptoms:
        - "CrashLoopBackOff status"
        - "OOMKilled events"
      troubleshooting_steps:
        - "Check pod logs: `kubectl logs <pod-name>`"
        - "Describe pod: `kubectl describe pod <pod-name>`"
```

### Runbooks

Link to existing runbooks and when to use them:

```yaml
runbooks:
  - name: "VMS Global Uptime Dashboard"
    description: "Monitor overall cluster health"
    url: "https://graphs.eencloud.com/d/jFpmPakGk/vms-global-uptime"
    when_to_use: "First place to check for service-wide issues"
```

### Best Practices

General guidelines for the AI to follow:

```yaml
best_practices:
  - "Always specify namespace when querying Kubernetes resources"
  - "Check multiple data sources (logs, metrics, events)"
  - "Correlate timing with recent deployments"
```

## Testing Changes

After updating the AI context:

1. **Syntax validation**: Ensure YAML is valid
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('src/ai_context.yaml'))"
   ```

2. **Deploy locally**: Test with `./run.sh`

3. **Test queries**: Ask the bot questions that exercise the new context
   ```
   @Ritsuko ai what clusters do we have?
   @Ritsuko ai how do I troubleshoot a CrashLoopBackOff?
   ```

4. **Review responses**: Ensure the bot uses the new information correctly

## Programmatic Access

The `src/ai_context.py` module provides programmatic access to the context:

```python
from ai_context import get_context_manager

# Get the context manager
context = get_context_manager()

# Access specific sections
system_prompt = context.get_system_prompt()
clusters = context.get_kubernetes_clusters()
runbooks = context.get_domain_knowledge()['runbooks']

# Reload context without restarting
context.reload_config()
```

### Adding New Helper Methods

If you need to access specific context frequently, add helper methods to `AIContextManager`:

```python
def get_grafana_dashboards(self) -> list:
    """Get list of Grafana dashboards."""
    tech = self.get_technologies()
    return tech.get('monitoring', {}).get('grafana', {}).get('key_dashboards', [])
```

## Troubleshooting

### Context Not Loading

**Symptom**: Bot doesn't seem to have context knowledge

**Check**:
1. File exists at `src/ai_context.yaml`
2. YAML syntax is valid
3. Check logs for loading errors: `grep "AI context" logs/*.log`

### Incorrect Responses

**Symptom**: Bot provides outdated or wrong information

**Check**:
1. Context file has been updated with correct info
2. Bot has been restarted to reload context
3. System prompt accurately reflects your needs

### Performance Issues

**Symptom**: AI responses are slow

**Consider**:
1. System prompt length (keep it concise)
2. Token limits (currently 4096)
3. Simplify complex nested structures in YAML

## Best Practices

1. **Version control**: Always commit context changes
2. **Document changes**: Update CHANGELOG when modifying context
3. **Test thoroughly**: Verify bot behavior after changes
4. **Keep it current**: Regular reviews to ensure accuracy
5. **Be concise**: AI context affects token usage and response quality
6. **Use comments**: YAML supports comments - use them!

```yaml
technologies:
  kubernetes:
    version: "1.28+"  # Updated after Q4 2024 upgrade
    clusters:
      - c001: "aus1p1"  # Primary production cluster
```

## Examples

### Example: Adding a New Technology Stack

If you deploy a new service mesh like Istio:

```yaml
technologies:
  service_mesh:
    name: "Istio"
    version: "1.20+"
    key_concepts:
      - "Virtual Services"
      - "Destination Rules"
      - "Gateways"
    common_commands:
      - "istioctl analyze"
      - "istioctl proxy-status"
```

### Example: Documenting a New Runbook

When you create a new runbook:

```yaml
domain_knowledge:
  runbooks:
    - name: "Database Failover Procedure"
      description: "Steps to failover primary database"
      url: "https://confluence.example.com/runbooks/db-failover"
      when_to_use: "Database primary is unresponsive or degraded"
      requires: "DBA approval for production"
```

## Version History

- **v1.0** (2025-01-11): Initial AI context system
  - Response guidelines
  - Technology inventory (K8s, Python, monitoring)
  - MCP tools documentation
  - Domain knowledge (common issues, runbooks, best practices)

## See Also

- [Ritsuko README](../README.md)
- [MCP Server Documentation](./mcp-servers.md) (if applicable)
- [Bot Commands Guide](./commands.md) (if applicable)
