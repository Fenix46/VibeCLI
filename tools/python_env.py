"""
Python environment tools for VibeCLI
Handles package installation and virtual environment management
"""

import asyncio
from pathlib import Path
from typing import Optional

from .base import BaseTool, ToolResult


class PythonEnvironmentTools(BaseTool):
    """Python environment and package management tools"""
    
    @property
    def name(self) -> str:
        return "python_env"
    
    @property
    def description(self) -> str:
        return "Python package management and virtual environment tools"
    
    @property
    def is_destructive(self) -> bool:
        return True  # Package installation can be destructive
    
    async def execute(self, **kwargs) -> ToolResult:
        """Not used in this implementation - tools called directly"""
        pass
    
    async def pip_install(self, package: str, version: Optional[str] = None, project_dir: str = "") -> str:
        """Install Python package using pip"""
        try:
            if not package:
                raise ValueError("package è richiesto")
            
            # Build package specification
            package_spec = package
            if version:
                package_spec = f"{package}=={version}"
            
            result = f"📦 Installazione pacchetto: {package_spec}\n"
            
            # Run pip install
            process = await asyncio.create_subprocess_exec(
                "pip", "install", package_spec,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result += "✅ Installazione completata\n"
                if stdout:
                    output = stdout.decode('utf-8', errors='replace')
                    # Extract key information
                    lines = output.split('\n')
                    for line in lines:
                        if 'Successfully installed' in line:
                            result += f"📋 {line}\n"
                        elif 'Requirement already satisfied' in line:
                            result += f"ℹ️ {line}\n"
            else:
                result += "❌ Errore installazione\n"
                if stderr:
                    error_output = stderr.decode('utf-8', errors='replace')
                    result += f"Errore: {error_output}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Errore pip install: {str(e)}"
    
    async def manage_venv(self, action: str, path: str = "", project_dir: str = "") -> str:
        """Manage Python virtual environments"""
        try:
            if not action:
                raise ValueError("action è richiesta")
            
            action = action.lower()
            
            if action == "create":
                venv_path = path or "venv"
                full_venv_path = Path(project_dir) / venv_path
                
                result = f"🐍 Creazione virtual environment: {venv_path}\n"
                
                # Create virtual environment
                process = await asyncio.create_subprocess_exec(
                    "python", "-m", "venv", str(full_venv_path),
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    result += f"✅ Virtual environment creato in {venv_path}\n"
                    result += f"💡 Per attivarlo:\n"
                    result += f"   Windows: {venv_path}\\Scripts\\activate\n"
                    result += f"   Unix/MacOS: source {venv_path}/bin/activate\n"
                else:
                    result += "❌ Errore creazione virtual environment\n"
                    if stderr:
                        result += stderr.decode('utf-8', errors='replace')
                
                return result
                
            elif action == "list":
                result = "🐍 Virtual environments trovati:\n"
                
                base_path = Path(project_dir)
                venv_dirs = []
                
                # Look for common venv directory names
                for venv_name in ["venv", ".venv", "env", ".env", "virtualenv"]:
                    venv_path = base_path / venv_name
                    if venv_path.exists() and venv_path.is_dir():
                        # Check if it looks like a venv (has Scripts/bin and pyvenv.cfg)
                        scripts_dir = venv_path / "Scripts" if (venv_path / "Scripts").exists() else venv_path / "bin"
                        if scripts_dir.exists() and (venv_path / "pyvenv.cfg").exists():
                            venv_dirs.append(venv_name)
                
                if venv_dirs:
                    for venv_dir in venv_dirs:
                        result += f"📁 {venv_dir}\n"
                else:
                    result += "ℹ️ Nessun virtual environment trovato"
                
                return result
                
            elif action == "info":
                venv_path = path or "venv"
                full_venv_path = Path(project_dir) / venv_path
                
                if not full_venv_path.exists():
                    return f"❌ Virtual environment non trovato: {venv_path}"
                
                result = f"🐍 Informazioni virtual environment: {venv_path}\n"
                
                # Check pyvenv.cfg
                cfg_path = full_venv_path / "pyvenv.cfg"
                if cfg_path.exists():
                    with open(cfg_path, 'r') as f:
                        cfg_content = f.read()
                    result += f"📋 Configurazione:\n{cfg_content}\n"
                
                # List installed packages
                scripts_dir = full_venv_path / "Scripts" if (full_venv_path / "Scripts").exists() else full_venv_path / "bin"
                pip_executable = scripts_dir / "pip"
                
                if pip_executable.exists():
                    process = await asyncio.create_subprocess_exec(
                        str(pip_executable), "list",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode == 0:
                        packages = stdout.decode('utf-8', errors='replace')
                        result += f"📦 Pacchetti installati:\n{packages}"
                
                return result
                
            else:
                return f"❌ Azione non supportata: {action}. Usa: create, list, info"
                
        except Exception as e:
            return f"❌ Errore gestione venv: {str(e)}" 