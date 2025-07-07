"""
Configuration settings for VibeCLI
Uses pydantic for validation and automatic environment variable loading
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Main configuration settings for VibeCLI"""
    
    # API Configuration
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY", description="Gemini API key")
    gemini_model: str = Field("gemini-2.0-flash-001", env="GEMINI_MODEL", description="Gemini model name")
    api_timeout: int = Field(30, env="API_TIMEOUT", description="API timeout in seconds")
    max_retries: int = Field(3, env="MAX_RETRIES", description="Maximum API retries")
    
    # Performance Configuration
    max_file_size: int = Field(10_000_000, env="MAX_FILE_SIZE", description="Maximum file size to process in bytes")
    max_search_results: int = Field(50, env="MAX_SEARCH_RESULTS", description="Maximum search results to return")
    shell_timeout: int = Field(30, env="SHELL_TIMEOUT", description="Shell command timeout in seconds")
    max_output_size: int = Field(2000, env="MAX_OUTPUT_SIZE", description="Maximum output size to display")
    max_concurrent_ops: int = Field(10, env="MAX_CONCURRENT_OPS", description="Maximum concurrent operations")
    max_memory_mb: int = Field(500, env="MAX_MEMORY_MB", description="Maximum memory usage in MB")
    
    # Cache Configuration  
    cache_enabled: bool = Field(True, env="CACHE_ENABLED", description="Enable caching")
    cache_ttl_seconds: int = Field(300, env="CACHE_TTL", description="Cache TTL in seconds")
    cache_max_size: int = Field(100, env="CACHE_MAX_SIZE", description="Maximum cache entries")
    cache_file_max_size: int = Field(1_000_000, env="CACHE_FILE_MAX_SIZE", description="Maximum file size to cache in bytes")
    
    # UI Configuration
    use_colors: bool = Field(True, env="USE_COLORS", description="Enable colored output")
    progress_bars: bool = Field(True, env="PROGRESS_BARS", description="Show progress bars")
    menu_style: str = Field("default", env="MENU_STYLE", description="Menu style theme")
    show_file_tree: bool = Field(False, env="SHOW_FILE_TREE", description="Show file tree in UI")
    syntax_highlighting: bool = Field(True, env="SYNTAX_HIGHLIGHTING", description="Enable syntax highlighting")
    
    # Security Configuration
    dangerous_commands_enabled: bool = Field(False, env="DANGEROUS_COMMANDS", description="Allow dangerous shell commands")
    path_traversal_protection: bool = Field(True, env="PATH_PROTECTION", description="Enable path traversal protection")
    auto_confirm_safe: bool = Field(True, env="AUTO_CONFIRM_SAFE", description="Auto-confirm safe operations")
    dangerous_commands_protection: bool = Field(True, env="DANGEROUS_COMMANDS_PROTECTION", description="Enable dangerous command protection")
    
    # Tool Configuration
    default_linter: str = Field("ruff", env="DEFAULT_LINTER", description="Default code linter")
    default_formatter: str = Field("black", env="DEFAULT_FORMATTER", description="Default code formatter") 
    test_command: str = Field("pytest -q", env="TEST_COMMAND", description="Default test command")
    
    # Git Configuration
    git_auto_add: bool = Field(True, env="GIT_AUTO_ADD", description="Automatically add files before commit")
    git_editor: Optional[str] = Field(None, env="GIT_EDITOR", description="Git editor command")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL", description="Logging level")
    log_file: Optional[str] = Field(None, env="LOG_FILE", description="Log file path")
    log_format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT", description="Log format")
    
    # Custom file patterns  
    skip_patterns: Optional[Union[List[str], str]] = Field(
        default=None,
        env="SKIP_PATTERNS",
        description="File patterns to skip during operations"
    )
    
    @field_validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator("menu_style")
    def validate_menu_style(cls, v):
        """Validate menu style"""
        valid_styles = ["default", "minimal", "colorful", "corporate"]
        if v not in valid_styles:
            raise ValueError(f"Menu style must be one of: {valid_styles}")
        return v
    
    @field_validator("gemini_model")
    def validate_gemini_model(cls, v):
        """Validate Gemini model name"""
        valid_models = [
            "gemini-2.0-flash-001",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.0-pro"
        ]
        if v not in valid_models:
            raise ValueError(f"Model must be one of: {valid_models}")
        return v
    
    @field_validator("skip_patterns", mode="after")
    @classmethod
    def normalize_skip_patterns(cls, v):
        """Normalize skip patterns to List[str]"""
        # Default patterns
        default_patterns = [".git", "__pycache__", ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", 
                           ".exe", ".bin", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".mp3", ".mp4", 
                           ".avi", ".mov", ".pdf", ".zip", ".tar", ".gz", ".bz2", ".7z", "node_modules", 
                           ".venv", "venv", ".env"]
        
        # If None or empty, return default patterns
        if v is None:
            return default_patterns
        
        # If it's already a list, return as-is
        if isinstance(v, list):
            return v if v else default_patterns
        
        # If it's a string, parse it
        if isinstance(v, str):
            if not v.strip():
                return default_patterns
            patterns = [pattern.strip() for pattern in v.split(",") if pattern.strip()]
            return patterns if patterns else default_patterns
        
        # For any other type, return defaults
        return default_patterns
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration as dict"""
        return {
            "enabled": self.cache_enabled,
            "ttl_seconds": self.cache_ttl_seconds,
            "max_size": self.cache_max_size
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration as dict"""
        return {
            "dangerous_commands_enabled": self.dangerous_commands_enabled,
            "path_traversal_protection": self.path_traversal_protection,
            "auto_confirm_safe": self.auto_confirm_safe
        }
    
    def get_tool_defaults(self) -> Dict[str, str]:
        """Get tool default settings"""
        return {
            "linter": self.default_linter,
            "formatter": self.default_formatter,
            "test_command": self.test_command
        }
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment/file"""
    global _settings
    _settings = Settings()
    return _settings


def create_default_config_file(path: str = ".env") -> None:
    """Create a default configuration file with all settings documented"""
    config_content = '''# VibeCLI Configuration File
# All settings can be overridden by environment variables

# API Configuration (required for AI features)
# GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-001
API_TIMEOUT=30
MAX_RETRIES=3

# Performance Configuration
MAX_FILE_SIZE=10000000
MAX_SEARCH_RESULTS=50
SHELL_TIMEOUT=30
MAX_OUTPUT_SIZE=2000

# Cache Configuration
CACHE_ENABLED=true
CACHE_TTL=300
CACHE_MAX_SIZE=100

# UI Configuration
USE_COLORS=true
PROGRESS_BARS=true
MENU_STYLE=default

# Security Configuration
DANGEROUS_COMMANDS=false
PATH_PROTECTION=true
AUTO_CONFIRM_SAFE=true

# Tool Configuration
DEFAULT_LINTER=ruff
DEFAULT_FORMATTER=black
TEST_COMMAND=pytest -q

# Git Configuration
GIT_AUTO_ADD=true

# Logging Configuration
LOG_LEVEL=INFO

# File patterns to skip (comma-separated, no spaces around commas)
SKIP_PATTERNS=.git,__pycache__,.pyc,.pyo,.pyd,.so,.dll,.exe,node_modules,.venv,venv
'''
    
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✅ Created default configuration file: {path}")
        print("💡 Edit the file to customize your settings")
        
    except Exception as e:
        print(f"❌ Error creating config file: {e}")
        print("💡 You can create the .env file manually with the settings above")


if __name__ == "__main__":
    # Create example config file when run directly
    create_default_config_file()
    
    # Load and display current settings
    settings = get_settings()
    print("\n📋 Current settings:")
    for field_name, field_info in settings.__fields__.items():
        value = getattr(settings, field_name)
        print(f"{field_name}: {value}") 