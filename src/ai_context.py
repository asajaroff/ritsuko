"""
AI Context Management for Ritsuko Bot

This module loads and manages the AI context configuration from ai_context.yaml,
providing the system prompt and context information for AI interactions.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional


class AIContextManager:
    """Manages AI context configuration for the bot."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the AI Context Manager.

        Args:
            config_path: Path to the ai_context.yaml file. If None, uses default location.
        """
        if config_path is None:
            # Default to ai_context.yaml in the same directory as this file
            config_path = os.path.join(os.path.dirname(__file__), 'ai_context.yaml')

        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load the AI context configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
                logging.info(f"Successfully loaded AI context from {self.config_path}")
        except FileNotFoundError:
            logging.error(f"AI context file not found at {self.config_path}")
            self.config = {}
        except yaml.YAMLError as e:
            logging.error(f"Error parsing AI context YAML: {e}")
            self.config = {}
        except Exception as e:
            logging.error(f"Unexpected error loading AI context: {e}")
            self.config = {}

    def reload_config(self) -> bool:
        """
        Reload the configuration from disk.

        Returns:
            bool: True if reload was successful, False otherwise
        """
        try:
            self._load_config()
            return bool(self.config)
        except Exception as e:
            logging.error(f"Error reloading AI context: {e}")
            return False

    def get_system_prompt(self) -> str:
        """
        Get the system prompt for AI interactions.

        Returns:
            str: The system prompt text
        """
        return self.config.get('system_prompt', '')

    def get_response_guidelines(self) -> Dict[str, Any]:
        """
        Get the response guidelines configuration.

        Returns:
            dict: Response guidelines including tone, style, length, etc.
        """
        return self.config.get('response_guidelines', {})

    def get_technologies(self) -> Dict[str, Any]:
        """
        Get the technologies and versions information.

        Returns:
            dict: Technologies configuration including k8s, python, monitoring, etc.
        """
        return self.config.get('technologies', {})

    def get_mcp_tools(self) -> Dict[str, Any]:
        """
        Get the available MCP tools configuration.

        Returns:
            dict: MCP tools and operations information
        """
        return self.config.get('mcp_tools', {})

    def get_domain_knowledge(self) -> Dict[str, Any]:
        """
        Get the domain-specific knowledge configuration.

        Returns:
            dict: Domain knowledge including common issues, runbooks, best practices
        """
        return self.config.get('domain_knowledge', {})

    def get_kubernetes_clusters(self) -> list:
        """
        Get the list of Kubernetes clusters.

        Returns:
            list: List of cluster dictionaries
        """
        technologies = self.get_technologies()
        k8s = technologies.get('kubernetes', {})
        return k8s.get('clusters', [])

    def get_grafana_url(self) -> str:
        """
        Get the Grafana base URL.

        Returns:
            str: Grafana URL or empty string if not configured
        """
        technologies = self.get_technologies()
        monitoring = technologies.get('monitoring', {})
        grafana = monitoring.get('grafana', {})
        return grafana.get('url', '')

    def format_context_summary(self) -> str:
        """
        Format a summary of the current context for debugging or display.

        Returns:
            str: Formatted context summary
        """
        if not self.config:
            return "No AI context loaded."

        summary = ["# AI Context Summary\n"]

        # Response guidelines
        guidelines = self.get_response_guidelines()
        if guidelines:
            summary.append("## Response Guidelines")
            summary.append(f"- **Tone**: {guidelines.get('tone', 'N/A')}")
            summary.append(f"- **Style**: {guidelines.get('style', 'N/A')}")
            summary.append(f"- **Length**: {guidelines.get('length', 'N/A')}\n")

        # Technologies
        technologies = self.get_technologies()
        if technologies:
            summary.append("## Technologies")
            if 'kubernetes' in technologies:
                k8s = technologies['kubernetes']
                summary.append(f"- **Kubernetes**: {k8s.get('version', 'N/A')}")
                summary.append(f"  - Clusters: {len(k8s.get('clusters', []))}")
            if 'python' in technologies:
                py = technologies['python']
                summary.append(f"- **Python**: {py.get('version', 'N/A')}")
            summary.append("")

        # MCP Tools
        mcp = self.get_mcp_tools()
        if mcp and 'available_operations' in mcp:
            ops = mcp['available_operations']
            summary.append("## Available MCP Operations")
            summary.append(f"- Kubernetes operations: {len(ops.get('kubernetes', []))}")
            summary.append(f"- Metrics operations: {len(ops.get('metrics', []))}")
            summary.append(f"- Network operations: {len(ops.get('network', []))}")
            summary.append("")

        # Domain Knowledge
        domain = self.get_domain_knowledge()
        if domain:
            summary.append("## Domain Knowledge")
            if 'common_issues' in domain:
                summary.append(f"- Common issues documented: {len(domain['common_issues'])}")
            if 'runbooks' in domain:
                summary.append(f"- Runbooks available: {len(domain['runbooks'])}")
            if 'best_practices' in domain:
                summary.append(f"- Best practices: {len(domain['best_practices'])}")
            summary.append("")

        return "\n".join(summary)


# Global instance for easy access
_context_manager: Optional[AIContextManager] = None


def get_context_manager() -> AIContextManager:
    """
    Get the global AI context manager instance.

    Returns:
        AIContextManager: The global context manager instance
    """
    global _context_manager
    if _context_manager is None:
        _context_manager = AIContextManager()
    return _context_manager


def get_system_prompt() -> str:
    """
    Convenience function to get the system prompt.

    Returns:
        str: The system prompt text
    """
    return get_context_manager().get_system_prompt()


def reload_context() -> bool:
    """
    Convenience function to reload the context configuration.

    Returns:
        bool: True if reload was successful, False otherwise
    """
    return get_context_manager().reload_config()
