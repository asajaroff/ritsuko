"""
Input validation and sanitization utilities.

This module provides functions to validate and sanitize user inputs
to prevent injection attacks and ensure data integrity.
"""

import re
import logging
from typing import Tuple


def validate_node_name(node_name: str) -> Tuple[bool, str]:
    """
    Validate a node name to ensure it's safe for API calls.

    Node names should only contain:
    - Alphanumeric characters (a-z, A-Z, 0-9)
    - Hyphens (-)
    - Dots (.)
    - Underscores (_)

    Args:
        node_name: The node name to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if valid, False otherwise
        - error_message: Empty string if valid, error description if invalid
    """
    if not node_name:
        return False, "Node name cannot be empty"

    # Check length (reasonable limit for node names)
    if len(node_name) > 255:
        return False, f"Node name too long (max 255 characters, got {len(node_name)})"

    # Check for valid characters: alphanumeric, dash, dot, underscore
    pattern = r'^[a-zA-Z0-9\-\._]+$'
    if not re.match(pattern, node_name):
        return False, "Node name contains invalid characters. Only alphanumeric, dash, dot, and underscore are allowed"

    # Additional safety check: prevent directory traversal attempts
    if '..' in node_name or node_name.startswith('.') or node_name.startswith('-'):
        return False, "Node name contains suspicious patterns"

    return True, ""


def validate_ai_prompt(prompt: str) -> Tuple[bool, str]:
    """
    Validate an AI prompt to ensure it's within acceptable limits.

    Args:
        prompt: The AI prompt to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if valid, False otherwise
        - error_message: Empty string if valid, error description if invalid
    """
    if not prompt:
        return False, "Prompt cannot be empty"

    # Reasonable limit for prompt length (Claude API has ~100k token limit)
    # 16000 characters is roughly ~4000 tokens
    if len(prompt) > 16000:
        return False, f"Prompt too long (max 16000 characters, got {len(prompt)})"

    # Check for null bytes which can cause issues
    if '\x00' in prompt:
        return False, "Prompt contains invalid null bytes"

    return True, ""


def sanitize_for_logging(text: str, max_length: int = 200) -> str:
    """
    Sanitize text for safe logging by removing potentially problematic characters.

    Args:
        text: The text to sanitize
        max_length: Maximum length to include in logs (prevents log flooding)

    Returns:
        Sanitized text safe for logging
    """
    if not text:
        return ""

    # Remove null bytes and control characters except newlines and tabs
    sanitized = ''.join(char for char in text if char == '\n' or char == '\t' or (ord(char) >= 32 and ord(char) != 127))

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."

    return sanitized


def validate_url_component(component: str) -> Tuple[bool, str]:
    """
    Validate a URL component (like a node name that will be inserted into a URL).

    Args:
        component: The URL component to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if valid, False otherwise
        - error_message: Empty string if valid, error description if invalid
    """
    if not component:
        return False, "URL component cannot be empty"

    # Check for URL-unsafe characters that could cause injection
    # Allow alphanumeric, dash, underscore, dot, and percent-encoded characters
    pattern = r'^[a-zA-Z0-9\-\._~%]+$'
    if not re.match(pattern, component):
        return False, "URL component contains unsafe characters"

    # Check for suspicious patterns
    dangerous_patterns = ['..', '//', '\\', '<', '>', '"', "'", ';', '&', '|', '`', '$', '(', ')']
    for pattern in dangerous_patterns:
        if pattern in component:
            return False, f"URL component contains dangerous pattern: {pattern}"

    return True, ""
