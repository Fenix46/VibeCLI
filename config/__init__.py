"""
Configuration package for VibeCLI
Centralized configuration management with environment variables and file support
"""

from .settings import Settings, get_settings

__all__ = ["Settings", "get_settings"] 