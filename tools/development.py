"""
Development tools for VibeCLI
Handles code formatting, linting, testing, compilation, and shell execution
"""

import asyncio
import shlex
from pathlib import Path
from typing import List

from .base import BaseTool, ToolResult


class DevelopmentTools(BaseTool):
    """Development and code quality tools"""
    
    @property
    def name(self) -> str:
        return "development"
    
    @property
    def description(self) -> str:
        return "Code formatting, linting, testing, and compilation tools"
    
    @property
    def is_destructive(self) -> bool:
        return True  # Shell execution can be destructive
    
    async def execute(self, **kwargs) -> ToolResult:
        """Not used in this implementation - tools called directly"""
        pass
    
    async def format_code(self, file_glob: str = "**/*.py", style: str = "black", project_dir: str = "") -> str:
        """Format code using specified formatter"""
        try:
            if style.lower() == "black":
                # Try to use black formatter
                process = await asyncio.create_subprocess_shell(
                    f"black {file_glob}",
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    shell=True
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 127:  # Command not found
                    return "⚠️ Black non disponibile. Installare con: pip install black"
                
                result = f"🎨 Formattazione codice con {style}:\n"
                if stdout:
                    result += stdout.decode('utf-8', errors='replace')
                if stderr:
                    result += stderr.decode('utf-8', errors='replace')
                
                return result
            else:
                return f"⚠️ Stile formattazione non supportato: {style}"
                
        except Exception as e:
            return f"❌ Errore formattazione: {str(e)}"
    
    async def lint_code(self, file_glob: str = "**/*.py", linter: str = "ruff", project_dir: str = "") -> str:
        """Lint code using specified linter"""
        try:
            if linter.lower() == "ruff":
                process = await asyncio.create_subprocess_shell(
                    f"ruff check {file_glob}",
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    shell=True
                )
            elif linter.lower() == "flake8":
                process = await asyncio.create_subprocess_shell(
                    f"flake8 {file_glob}",
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    shell=True
                )
            else:
                return f"⚠️ Linter non supportato: {linter}"
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 127:  # Command not found
                return f"⚠️ {linter} non disponibile. Installare con: pip install {linter}"
            
            result = f"🔍 Analisi codice con {linter}:\n"
            
            if process.returncode == 0:
                result += "✅ Nessun problema trovato"
            else:
                if stdout:
                    result += stdout.decode('utf-8', errors='replace')
                if stderr:
                    result += stderr.decode('utf-8', errors='replace')
            
            return result
            
        except Exception as e:
            return f"❌ Errore linting: {str(e)}"
    
    async def run_tests(self, test_cmd: str = "pytest -q", project_dir: str = "") -> str:
        """Run tests using specified command"""
        try:
            process = await asyncio.create_subprocess_shell(
                test_cmd,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 127:  # Command not found
                return f"⚠️ Comando test non trovato: {test_cmd}"
            
            result = f"🧪 Esecuzione test: {test_cmd}\n"
            result += f"Exit code: {process.returncode}\n"
            
            if stdout:
                result += f"Output:\n{stdout.decode('utf-8', errors='replace')}\n"
            if stderr:
                result += f"Errori:\n{stderr.decode('utf-8', errors='replace')}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Errore esecuzione test: {str(e)}"
    
    async def run_python(self, module_or_path: str, args: List[str] = None, project_dir: str = "") -> str:
        """Run Python module or script"""
        try:
            if not module_or_path:
                raise ValueError("module_or_path è richiesto")
            
            args = args or []
            
            # Build command
            if module_or_path.endswith('.py'):
                # Run as script
                cmd_parts = ["python", module_or_path] + args
            else:
                # Run as module
                cmd_parts = ["python", "-m", module_or_path] + args
            
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            result = f"🐍 Esecuzione Python: {' '.join(cmd_parts)}\n"
            result += f"Exit code: {process.returncode}\n"
            
            if stdout:
                result += f"Output:\n{stdout.decode('utf-8', errors='replace')}\n"
            if stderr:
                result += f"Errori:\n{stderr.decode('utf-8', errors='replace')}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Errore esecuzione Python: {str(e)}"
    
    async def compile_code(self, file_glob: str = "**/*.py", project_dir: str = "") -> str:
        """Compile/check code syntax"""
        try:
            import ast
            import aiofiles
            
            base_path = Path(project_dir)
            results = []
            errors = []
            
            for file_path in base_path.glob(file_glob):
                if file_path.is_file() and not self.should_skip_file(file_path):
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                        
                        # Check syntax by parsing
                        ast.parse(content)
                        results.append(f"✅ {file_path.relative_to(base_path)}")
                        
                    except SyntaxError as e:
                        relative_path = file_path.relative_to(base_path)
                        errors.append(f"❌ {relative_path}:{e.lineno} - {e.msg}")
                    except Exception:
                        continue
            
            result = f"🔧 Controllo sintassi per {file_glob}:\n"
            
            if results:
                result += f"\nFile validi ({len(results)}):\n" + "\n".join(results)
            
            if errors:
                result += f"\nErrori di sintassi ({len(errors)}):\n" + "\n".join(errors)
            
            if not results and not errors:
                result += "Nessun file trovato"
            
            return result
            
        except Exception as e:
            return f"❌ Errore controllo sintassi: {str(e)}"
    
    async def execute_shell(self, command: str, project_dir: str = "") -> str:
        """Execute shell command with safety checks"""
        try:
            if not command:
                raise ValueError("command è richiesto")
            
            # Check for dangerous commands
            if self.is_dangerous_command(command):
                return f"⚠️ Comando potenzialmente pericoloso bloccato: {command}"
            
            # Use shlex.split for safer command parsing
            try:
                cmd_parts = shlex.split(command)
            except ValueError:
                return f"❌ Comando non valido: {command}"
            
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=30.0  # 30 second timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return f"⏰ Comando timeout: {command}"
            
            result = f"💻 Comando: {command}\n"
            result += f"Exit code: {process.returncode}\n"
            
            if stdout:
                output = stdout.decode('utf-8', errors='replace')
                # Limit output length
                if len(output) > 2000:
                    output = output[:2000] + "\n... (output troncato)"
                result += f"Output:\n{output}\n"
            
            if stderr:
                error_output = stderr.decode('utf-8', errors='replace')
                if len(error_output) > 1000:
                    error_output = error_output[:1000] + "\n... (errori troncati)"
                result += f"Errori:\n{error_output}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Errore esecuzione comando: {str(e)}" 