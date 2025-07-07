"""
Base classes for VibeCLI tools
Provides common interfaces and utilities for all tool implementations
"""

import asyncio
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import aiofiles
import difflib

from utils import Colors, print_colored
from config import get_settings


@dataclass
class ToolResult:
    """Standardized result from tool execution"""
    success: bool
    content: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseTool(ABC):
    """Abstract base class for all tools"""
    
    def __init__(self):
        self.settings = get_settings()
        self.dangerous_commands = [
            r'sudo\s',
            r'rm\s+-rf',
            r'rm\s+.*\*',
            r'>\s*/dev/',
            r'curl\s+.*http',
            r'wget\s+.*http',
            r'dd\s+if=',
            r'mkfs\.',
            r'fdisk',
            r'parted',
            r'systemctl',
            r'service\s',
            r'shutdown',
            r'reboot',
            r'init\s+[0-6]',
            r'kill\s+-9',
            r'killall',
            r'chmod\s+777',
            r'chown\s+.*root',
        ]
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name identifier"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description"""
        pass
    
    @property
    @abstractmethod
    def is_destructive(self) -> bool:
        """Whether tool performs destructive operations"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        pass
    
    def validate_path(self, file_path: str, project_dir: str) -> Path:
        """Validate and resolve file path safely"""
        if not file_path:
            raise ValueError("file_path è richiesto")
        
        full_path = Path(project_dir) / file_path
        
        # Basic path traversal protection
        try:
            full_path.resolve().relative_to(Path(project_dir).resolve())
        except ValueError:
            raise ValueError(f"Percorso non sicuro: {file_path}")
        
        return full_path
    
    def is_dangerous_command(self, command: str) -> bool:
        """Check if command is potentially dangerous"""
        command_lower = command.lower()
        for pattern in self.dangerous_commands:
            if re.search(pattern, command_lower):
                return True
        return False
    
    def generate_diff(self, old_content: str, new_content: str, filename: str) -> str:
        """Generate unified diff between old and new content"""
        if old_content == new_content:
            return "📝 Nessuna modifica"
            
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=""
        )
        
        diff_text = "".join(diff)
        if not diff_text:
            return "📝 Nessuna modifica"
            
        return f"📝 Diff:\n{diff_text}"
    
    def should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during operations"""
        name = file_path.name.lower()
        return any(pattern in name for pattern in self.settings.skip_patterns)


class ToolExecutor:
    """Centralized tool executor with routing to modular tools"""
    
    def __init__(self):
        from .filesystem import FileSystemTools
        from .development import DevelopmentTools
        from .git import GitTools
        from .python_env import PythonEnvironmentTools
        from .analysis import AnalysisTools
        
        # Initialize tool categories
        self.filesystem = FileSystemTools()
        self.development = DevelopmentTools()
        self.git = GitTools()
        self.python_env = PythonEnvironmentTools()
        self.analysis = AnalysisTools()
        
        # Tool routing map
        self.tool_map = {
            # Filesystem tools
            "read_file": self.filesystem.read_file,
            "write_file": self.filesystem.write_file,
            "append_file": self.filesystem.append_file,
            "list_dir": self.filesystem.list_dir,
            "copy_file": self.filesystem.copy_file,
            "move_file": self.filesystem.move_file,
            "delete_file": self.filesystem.delete_file,
            "make_dir": self.filesystem.make_dir,
            "file_stat": self.filesystem.file_stat,
            "open_file_range": self.filesystem.open_file_range,
            "diff_files": self.filesystem.diff_files,
            
            # Search tools
            "grep_search": self.filesystem.grep_search,
            "codebase_search": self.filesystem.codebase_search,
            "search_replace": self.filesystem.search_replace,
            
            # Development tools
            "format_code": self.development.format_code,
            "lint_code": self.development.lint_code,
            "compile_code": self.development.compile_code,
            "run_tests": self.development.run_tests,
            "run_python": self.development.run_python,
            "execute_shell": self.development.execute_shell,
            
            # Git tools
            "git_status": self.git.git_status,
            "git_diff": self.git.git_diff,
            "git_commit": self.git.git_commit,
            
            # Python environment tools
            "pip_install": self.python_env.pip_install,
            "manage_venv": self.python_env.manage_venv,
            
            # Analysis tools
            "generate_doc": self.analysis.generate_doc,
            "code_metrics": self.analysis.code_metrics,
            "scan_secrets": self.analysis.scan_secrets,
        }
    
    async def execute_tool(self, function_call: Dict[str, Any], project_dir: str) -> str:
        """Execute a tool by name with arguments"""
        name = function_call["name"]
        args = function_call.get("arguments", {})
        
        if name not in self.tool_map:
            return f"❌ Tool sconosciuto: {name}"
        
        try:
            # Add project_dir to args
            args["project_dir"] = project_dir
            
            # Execute the tool
            result = await self.tool_map[name](**args)
            
            if isinstance(result, ToolResult):
                if result.success:
                    return result.content
                else:
                    return f"❌ {result.error or 'Errore sconosciuto'}"
            else:
                # Backward compatibility for string returns
                return result
                
        except Exception as e:
            return f"❌ Errore eseguendo {name}: {str(e)}" 