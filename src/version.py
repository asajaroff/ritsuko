"""
Version management for Ritsuko bot.

This module provides version information using a hybrid approach:
1. Attempts to get version from git describe (if .git exists)
2. Falls back to hardcoded __version__ (for containerized deployments)
3. Can be overridden by RITSUKO_VERSION environment variable
"""

import subprocess
import os
from pathlib import Path

# This will be updated during build process
__version__ = "v1.5.0-dev"


def _get_git_version():
    """
    Attempt to get version from git describe.

    Returns:
        str: Version string from git describe, or None if git not available
    """
    try:
        # Check if we're in a git repository
        repo_root = Path(__file__).parent.parent
        git_dir = repo_root / ".git"

        if not git_dir.exists():
            return None

        # Run git describe
        result = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        )

        version = result.stdout.strip()
        return version if version else None

    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        # Git not available or command failed
        return None


def get_version():
    """
    Get the current version of Ritsuko.

    Priority order:
    1. RITSUKO_VERSION environment variable (set in deployment)
    2. Git describe output (for development)
    3. Hardcoded __version__ (fallback)

    Returns:
        str: Version string
    """
    # First check environment variable (set during deployment)
    env_version = os.environ.get("RITSUKO_VERSION")
    if env_version:
        return env_version

    # Try git describe (for local development)
    git_version = _get_git_version()
    if git_version:
        return git_version

    # Fall back to hardcoded version
    return __version__


def get_version_info():
    """
    Get detailed version information including context.

    Returns:
        dict: Dictionary with version details
    """
    version = get_version()

    # Determine context
    context = "unknown"
    if os.environ.get("KUBERNETES_SERVICE_HOST"):
        context = "kubernetes"
    elif os.environ.get("RITSUKO_VERSION"):
        context = "container"
    elif _get_git_version():
        context = "development"
    else:
        context = "local"

    return {
        "version": version,
        "context": context,
        "source": "git" if _get_git_version() else "metadata",
    }


if __name__ == "__main__":
    # For testing and build scripts
    print(get_version())
