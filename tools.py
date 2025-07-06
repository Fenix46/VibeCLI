"""
Tool executor module for VibeCLI
Handles the 5 main tools: read_file, write_file, append_file, grep_search, execute_shell
Plus 22 additional tools for comprehensive development workflow
"""

import asyncio
import os
import subprocess
import re
import shutil
import glob
from pathlib import Path
from typing import Dict, Any, Union, List
import difflib
import json
import stat
import ast

import aiofiles
from utils import Colors, print_colored

class ToolExecutor:
    """Handles execution of tools with security checks and async support"""
    
    def __init__(self):
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
        
    async def execute_tool(self, function_call: Dict[str, Any], project_dir: str) -> str:
        """Execute a single tool call"""
        name = function_call["name"]
        args = function_call.get("arguments", {})
        
        try:
            # Original 5 tools
            if name == "read_file":
                return await self.read_file(args.get("file_path", ""), project_dir)
            elif name == "write_file":
                return await self.write_file(
                    args.get("file_path", ""), 
                    args.get("content", ""), 
                    project_dir
                )
            elif name == "append_file":
                return await self.append_file(
                    args.get("file_path", ""), 
                    args.get("content", ""), 
                    project_dir
                )
            elif name == "grep_search":
                return await self.grep_search(
                    args.get("pattern", ""), 
                    args.get("file_path", "."), 
                    project_dir
                )
            elif name == "execute_shell":
                return await self.execute_shell(args.get("command", ""), project_dir)
            
            # New 22 tools
            elif name == "list_dir":
                return await self.list_dir(
                    args.get("path", "."),
                    args.get("recursive", False),
                    project_dir
                )
            elif name == "copy_file":
                return await self.copy_file(
                    args.get("src", ""),
                    args.get("dst", ""),
                    args.get("overwrite", False),
                    project_dir
                )
            elif name == "move_file":
                return await self.move_file(
                    args.get("src", ""),
                    args.get("dst", ""),
                    args.get("overwrite", False),
                    project_dir
                )
            elif name == "delete_file":
                return await self.delete_file(
                    args.get("path", ""),
                    args.get("force", False),
                    project_dir
                )
            elif name == "make_dir":
                return await self.make_dir(
                    args.get("path", ""),
                    args.get("exist_ok", True),
                    project_dir
                )
            elif name == "file_stat":
                return await self.file_stat(args.get("path", ""), project_dir)
            elif name == "codebase_search":
                return await self.codebase_search(
                    args.get("query", ""),
                    args.get("file_glob", "**/*.{py,ts,js}"),
                    project_dir
                )
            elif name == "search_replace":
                return await self.search_replace(
                    args.get("pattern", ""),
                    args.get("replacement", ""),
                    args.get("file_glob", ""),
                    args.get("preview", True),
                    project_dir
                )
            elif name == "format_code":
                return await self.format_code(
                    args.get("file_glob", "**/*.py"),
                    args.get("style", "black"),
                    project_dir
                )
            elif name == "lint_code":
                return await self.lint_code(
                    args.get("file_glob", "**/*.py"),
                    args.get("linter", "ruff"),
                    project_dir
                )
            elif name == "run_tests":
                return await self.run_tests(
                    args.get("test_cmd", "pytest -q"),
                    project_dir
                )
            elif name == "run_python":
                return await self.run_python(
                    args.get("module_or_path", ""),
                    args.get("args", []),
                    project_dir
                )
            elif name == "compile_code":
                return await self.compile_code(
                    args.get("file_glob", "**/*.py"),
                    project_dir
                )
            elif name == "git_status":
                return await self.git_status(project_dir)
            elif name == "git_diff":
                return await self.git_diff(
                    args.get("rev", "HEAD"),
                    project_dir
                )
            elif name == "git_commit":
                return await self.git_commit(
                    args.get("message", ""),
                    args.get("add_all", True),
                    project_dir
                )
            elif name == "pip_install":
                return await self.pip_install(
                    args.get("package", ""),
                    args.get("version", None),
                    project_dir
                )
            elif name == "manage_venv":
                return await self.manage_venv(
                    args.get("action", ""),
                    args.get("path", ""),
                    project_dir
                )
            elif name == "generate_doc":
                return await self.generate_doc(
                    args.get("file_glob", ""),
                    args.get("style", "google"),
                    project_dir
                )
            elif name == "code_metrics":
                return await self.code_metrics(
                    args.get("file_glob", "**/*.py"),
                    project_dir
                )
            elif name == "scan_secrets":
                return await self.scan_secrets(
                    args.get("file_glob", "**/*"),
                    project_dir
                )
            elif name == "open_file_range":
                return await self.open_file_range(
                    args.get("path", ""),
                    args.get("start", 1),
                    args.get("end", 10),
                    project_dir
                )
            elif name == "diff_files":
                return await self.diff_files(
                    args.get("old_path", ""),
                    args.get("new_path", ""),
                    project_dir
                )
            else:
                raise ValueError(f"Unknown tool: {name}")
                
        except Exception as e:
            return f"Error executing {name}: {str(e)}"

    async def read_file(self, file_path: str, project_dir: str) -> str:
        """Read file contents"""
        if not file_path:
            raise ValueError("file_path è richiesto")
            
        full_path = Path(project_dir) / file_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"File non trovato: {file_path}")
            
        if not full_path.is_file():
            raise ValueError(f"Il percorso non è un file: {file_path}")
            
        try:
            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return f"📄 Contenuto di {file_path}:\n{content}"
        except UnicodeDecodeError:
            # Try binary mode for non-text files
            async with aiofiles.open(full_path, 'rb') as f:
                content = await f.read()
                return f"📄 File binario {file_path} ({len(content)} bytes)"

    async def write_file(self, file_path: str, content: str, project_dir: str) -> str:
        """Write content to file with diff display"""
        if not file_path:
            raise ValueError("file_path è richiesto")
            
        full_path = Path(project_dir) / file_path
        
        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing content for diff
        old_content = ""
        if full_path.exists():
            try:
                async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                    old_content = await f.read()
            except UnicodeDecodeError:
                old_content = "[Binary file]"
        
        # Write new content
        async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
            await f.write(content)
        
        # Generate diff
        diff = self.generate_diff(old_content, content, file_path)
        
        return f"✅ File scritto: {file_path}\n{diff}"

    async def append_file(self, file_path: str, content: str, project_dir: str) -> str:
        """Append content to file"""
        if not file_path:
            raise ValueError("file_path è richiesto")
            
        full_path = Path(project_dir) / file_path
        
        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing content for diff
        old_content = ""
        if full_path.exists():
            try:
                async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                    old_content = await f.read()
            except UnicodeDecodeError:
                old_content = "[Binary file]"
        
        # Append content
        async with aiofiles.open(full_path, 'a', encoding='utf-8') as f:
            await f.write(content)
        
        # Generate diff
        new_content = old_content + content
        diff = self.generate_diff(old_content, new_content, file_path)
        
        return f"✅ Contenuto aggiunto a: {file_path}\n{diff}"

    async def grep_search(self, pattern: str, file_path: str, project_dir: str) -> str:
        """Search for pattern in files"""
        if not pattern:
            raise ValueError("pattern è richiesto")
            
        search_path = Path(project_dir) / file_path if file_path != "." else Path(project_dir)
        
        if not search_path.exists():
            raise FileNotFoundError(f"Percorso non trovato: {file_path}")
        
        results = []
        
        try:
            if search_path.is_file():
                # Search in single file
                matches = await self._search_in_file(search_path, pattern)
                if matches:
                    results.extend(matches)
            else:
                # Search in directory
                for file_path in search_path.rglob("*"):
                    if file_path.is_file() and not self._should_skip_file(file_path):
                        matches = await self._search_in_file(file_path, pattern)
                        if matches:
                            results.extend(matches)
                            
        except Exception as e:
            raise RuntimeError(f"Errore durante la ricerca: {str(e)}")
        
        if not results:
            return f"🔍 Nessun risultato trovato per: {pattern}"
        
        return f"🔍 Risultati per '{pattern}':\n" + "\n".join(results[:50])  # Limit results

    async def execute_shell(self, command: str, project_dir: str) -> str:
        """Execute shell command with security checks"""
        if not command:
            raise ValueError("command è richiesto")
            
        # Security checks
        if self._is_dangerous_command(command):
            raise ValueError(f"Comando pericoloso bloccato: {command}")
        
        try:
            # Execute command in project directory
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await process.communicate()
            
            result = f"💻 Comando: {command}\n"
            result += f"📁 Directory: {project_dir}\n"
            result += f"🔢 Exit code: {process.returncode}\n"
            
            if stdout:
                result += f"📤 STDOUT:\n{stdout.decode('utf-8', errors='replace')}\n"
            if stderr:
                result += f"📤 STDERR:\n{stderr.decode('utf-8', errors='replace')}\n"
                
            return result
            
        except Exception as e:
            raise RuntimeError(f"Errore nell'esecuzione del comando: {str(e)}")

    async def list_dir(self, path: str, recursive: bool, project_dir: str) -> str:
        """List directory contents"""
        full_path = Path(project_dir) / path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Directory non trovata: {path}")
        
        if not full_path.is_dir():
            raise ValueError(f"Il percorso non è una directory: {path}")
        
        try:
            items = []
            if recursive:
                for item in full_path.rglob("*"):
                    if not self._should_skip_file(item):
                        relative_path = item.relative_to(full_path)
                        item_type = "📁" if item.is_dir() else "📄"
                        size = f" ({item.stat().st_size} bytes)" if item.is_file() else ""
                        items.append(f"{item_type} {relative_path}{size}")
            else:
                for item in full_path.iterdir():
                    if not self._should_skip_file(item):
                        item_type = "📁" if item.is_dir() else "📄"
                        size = f" ({item.stat().st_size} bytes)" if item.is_file() else ""
                        items.append(f"{item_type} {item.name}{size}")
            
            return f"📂 Contenuti di {path}:\n" + "\n".join(sorted(items))
            
        except Exception as e:
            raise RuntimeError(f"Errore nella lettura della directory: {str(e)}")

    async def copy_file(self, src: str, dst: str, overwrite: bool, project_dir: str) -> str:
        """Copy file from source to destination"""
        if not src or not dst:
            raise ValueError("src e dst sono richiesti")
        
        src_path = Path(project_dir) / src
        dst_path = Path(project_dir) / dst
        
        if not src_path.exists():
            raise FileNotFoundError(f"File sorgente non trovato: {src}")
        
        if dst_path.exists() and not overwrite:
            raise ValueError(f"File destinazione già esistente: {dst}")
        
        try:
            # Create parent directories if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            if src_path.is_file():
                shutil.copy2(src_path, dst_path)
                return f"✅ File copiato: {src} → {dst}"
            elif src_path.is_dir():
                if dst_path.exists():
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
                return f"✅ Directory copiata: {src} → {dst}"
            else:
                raise ValueError(f"Tipo di file non supportato: {src}")
                
        except Exception as e:
            raise RuntimeError(f"Errore nella copia: {str(e)}")

    async def move_file(self, src: str, dst: str, overwrite: bool, project_dir: str) -> str:
        """Move file from source to destination"""
        if not src or not dst:
            raise ValueError("src e dst sono richiesti")
        
        src_path = Path(project_dir) / src
        dst_path = Path(project_dir) / dst
        
        if not src_path.exists():
            raise FileNotFoundError(f"File sorgente non trovato: {src}")
        
        if dst_path.exists() and not overwrite:
            raise ValueError(f"File destinazione già esistente: {dst}")
        
        try:
            # Create parent directories if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            return f"✅ File spostato: {src} → {dst}"
            
        except Exception as e:
            raise RuntimeError(f"Errore nello spostamento: {str(e)}")

    async def delete_file(self, path: str, force: bool, project_dir: str) -> str:
        """Delete file or directory"""
        if not path:
            raise ValueError("path è richiesto")
        
        full_path = Path(project_dir) / path
        
        if not full_path.exists():
            return f"⚠️ File già inesistente: {path}"
        
        try:
            if full_path.is_file():
                full_path.unlink()
                return f"✅ File eliminato: {path}"
            elif full_path.is_dir():
                if force:
                    shutil.rmtree(full_path)
                    return f"✅ Directory eliminata: {path}"
                else:
                    full_path.rmdir()  # Only works if empty
                    return f"✅ Directory vuota eliminata: {path}"
            else:
                raise ValueError(f"Tipo di file non supportato: {path}")
                
        except Exception as e:
            raise RuntimeError(f"Errore nell'eliminazione: {str(e)}")

    async def make_dir(self, path: str, exist_ok: bool, project_dir: str) -> str:
        """Create directory"""
        if not path:
            raise ValueError("path è richiesto")
        
        full_path = Path(project_dir) / path
        
        try:
            full_path.mkdir(parents=True, exist_ok=exist_ok)
            return f"✅ Directory creata: {path}"
            
        except FileExistsError:
            return f"⚠️ Directory già esistente: {path}"
        except Exception as e:
            raise RuntimeError(f"Errore nella creazione della directory: {str(e)}")

    async def file_stat(self, path: str, project_dir: str) -> str:
        """Get file statistics"""
        if not path:
            raise ValueError("path è richiesto")
        
        full_path = Path(project_dir) / path
        
        if not full_path.exists():
            raise FileNotFoundError(f"File non trovato: {path}")
        
        try:
            stat_info = full_path.stat()
            
            result = f"📊 Statistiche per {path}:\n"
            result += f"Tipo: {'Directory' if full_path.is_dir() else 'File'}\n"
            result += f"Dimensione: {stat_info.st_size} bytes\n"
            result += f"Permessi: {oct(stat_info.st_mode)[-3:]}\n"
            result += f"Modificato: {stat_info.st_mtime}\n"
            result += f"Creato: {stat_info.st_ctime}\n"
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Errore nel recupero delle statistiche: {str(e)}")

    async def codebase_search(self, query: str, file_glob: str, project_dir: str) -> str:
        """Search for code patterns in codebase"""
        if not query:
            raise ValueError("query è richiesta")
        
        try:
            results = []
            base_path = Path(project_dir)
            
            # Expand glob pattern for multiple extensions
            if "*.{" in file_glob:
                # Handle pattern like "**/*.{py,ts,js}"
                base_pattern = file_glob.split("*.{")[0]
                extensions = file_glob.split("*.{")[1].rstrip("}").split(",")
                
                for ext in extensions:
                    pattern = f"{base_pattern}*.{ext.strip()}"
                    for file_path in base_path.glob(pattern):
                        if file_path.is_file() and not self._should_skip_file(file_path):
                            matches = await self._search_in_file(file_path, query)
                            if matches:
                                results.extend(matches)
            else:
                # Simple glob pattern
                for file_path in base_path.glob(file_glob):
                    if file_path.is_file() and not self._should_skip_file(file_path):
                        matches = await self._search_in_file(file_path, query)
                        if matches:
                            results.extend(matches)
            
            if not results:
                return f"🔍 Nessun risultato trovato per: {query}"
            
            return f"🔍 Risultati codebase per '{query}':\n" + "\n".join(results[:100])
            
        except Exception as e:
            raise RuntimeError(f"Errore nella ricerca codebase: {str(e)}")

    async def search_replace(self, pattern: str, replacement: str, file_glob: str, preview: bool, project_dir: str) -> str:
        """Search and replace text in files"""
        if not pattern or not file_glob:
            raise ValueError("pattern e file_glob sono richiesti")
        
        try:
            base_path = Path(project_dir)
            changes = []
            
            for file_path in base_path.glob(file_glob):
                if file_path.is_file() and not self._should_skip_file(file_path):
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                        
                        new_content = re.sub(pattern, replacement, content)
                        
                        if content != new_content:
                            if not preview:
                                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                                    await f.write(new_content)
                            
                            changes.append(f"📝 {file_path.relative_to(base_path)}")
                            
                    except (UnicodeDecodeError, PermissionError):
                        continue
            
            if not changes:
                return f"🔍 Nessuna sostituzione trovata per: {pattern}"
            
            action = "Preview" if preview else "Applicato"
            return f"✅ {action} sostituzioni:\n" + "\n".join(changes)
            
        except Exception as e:
            raise RuntimeError(f"Errore nella sostituzione: {str(e)}")

    async def format_code(self, file_glob: str, style: str, project_dir: str) -> str:
        """Format code using specified formatter"""
        try:
            if style == "black":
                cmd = f"black {file_glob}"
            else:
                return f"❌ Formatter non supportato: {style}"
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await process.communicate()
            
            result = f"🎨 Formattazione codice con {style}:\n"
            if stdout:
                result += stdout.decode('utf-8', errors='replace')
            if stderr:
                result += stderr.decode('utf-8', errors='replace')
            
            return result
            
        except Exception as e:
            return f"❌ Errore nella formattazione: {str(e)}"

    async def lint_code(self, file_glob: str, linter: str, project_dir: str) -> str:
        """Lint code using specified linter"""
        try:
            if linter == "ruff":
                cmd = f"ruff check {file_glob}"
            else:
                return f"❌ Linter non supportato: {linter}"
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await process.communicate()
            
            result = f"🔍 Linting con {linter}:\n"
            if stdout:
                result += stdout.decode('utf-8', errors='replace')
            if stderr:
                result += stderr.decode('utf-8', errors='replace')
            
            return result
            
        except Exception as e:
            return f"❌ Errore nel linting: {str(e)}"

    async def run_tests(self, test_cmd: str, project_dir: str) -> str:
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
            
            result = f"🧪 Test eseguiti: {test_cmd}\n"
            result += f"Exit code: {process.returncode}\n"
            if stdout:
                result += f"STDOUT:\n{stdout.decode('utf-8', errors='replace')}\n"
            if stderr:
                result += f"STDERR:\n{stderr.decode('utf-8', errors='replace')}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Errore nell'esecuzione dei test: {str(e)}"

    async def run_python(self, module_or_path: str, args: List[str], project_dir: str) -> str:
        """Run Python module or script"""
        if not module_or_path:
            raise ValueError("module_or_path è richiesto")
        
        try:
            cmd_args = ["python", module_or_path] + args
            
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            result = f"🐍 Python eseguito: {' '.join(cmd_args)}\n"
            result += f"Exit code: {process.returncode}\n"
            if stdout:
                result += f"STDOUT:\n{stdout.decode('utf-8', errors='replace')}\n"
            if stderr:
                result += f"STDERR:\n{stderr.decode('utf-8', errors='replace')}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Errore nell'esecuzione Python: {str(e)}"

    async def compile_code(self, file_glob: str, project_dir: str) -> str:
        """Compile Python code (syntax check)"""
        try:
            base_path = Path(project_dir)
            results = []
            
            for file_path in base_path.glob(file_glob):
                if file_path.is_file() and file_path.suffix == '.py':
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                        
                        compile(content, str(file_path), 'exec')
                        results.append(f"✅ {file_path.relative_to(base_path)}")
                        
                    except SyntaxError as e:
                        results.append(f"❌ {file_path.relative_to(base_path)}: {e}")
                    except Exception as e:
                        results.append(f"⚠️ {file_path.relative_to(base_path)}: {e}")
            
            return f"🔧 Compilazione Python:\n" + "\n".join(results)
            
        except Exception as e:
            return f"❌ Errore nella compilazione: {str(e)}"

    async def git_status(self, project_dir: str) -> str:
        """Get git status"""
        try:
            process = await asyncio.create_subprocess_shell(
                "git status --porcelain",
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return f"❌ Git non disponibile o non in repository git"
            
            status = stdout.decode('utf-8', errors='replace').strip()
            
            if not status:
                return "✅ Repository git pulito"
            
            return f"📊 Git status:\n{status}"
            
        except Exception as e:
            return f"❌ Errore git status: {str(e)}"

    async def git_diff(self, rev: str, project_dir: str) -> str:
        """Get git diff"""
        try:
            process = await asyncio.create_subprocess_shell(
                f"git diff {rev}",
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return f"❌ Errore git diff: {stderr.decode('utf-8', errors='replace')}"
            
            diff = stdout.decode('utf-8', errors='replace').strip()
            
            if not diff:
                return f"✅ Nessuna differenza con {rev}"
            
            return f"📝 Git diff {rev}:\n{diff}"
            
        except Exception as e:
            return f"❌ Errore git diff: {str(e)}"

    async def git_commit(self, message: str, add_all: bool, project_dir: str) -> str:
        """Commit changes to git"""
        if not message:
            raise ValueError("message è richiesto")
        
        try:
            if add_all:
                # Add all changes
                process = await asyncio.create_subprocess_shell(
                    "git add .",
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    shell=True
                )
                await process.communicate()
            
            # Commit
            process = await asyncio.create_subprocess_shell(
                f'git commit -m "{message}"',
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return f"❌ Errore git commit: {stderr.decode('utf-8', errors='replace')}"
            
            return f"✅ Git commit: {message}\n{stdout.decode('utf-8', errors='replace')}"
            
        except Exception as e:
            return f"❌ Errore git commit: {str(e)}"

    async def pip_install(self, package: str, version: str, project_dir: str) -> str:
        """Install Python package with pip"""
        if not package:
            raise ValueError("package è richiesto")
        
        try:
            pkg_spec = f"{package}=={version}" if version else package
            
            process = await asyncio.create_subprocess_shell(
                f"pip install {pkg_spec}",
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await process.communicate()
            
            result = f"📦 Pip install {pkg_spec}:\n"
            result += f"Exit code: {process.returncode}\n"
            if stdout:
                result += f"STDOUT:\n{stdout.decode('utf-8', errors='replace')}\n"
            if stderr:
                result += f"STDERR:\n{stderr.decode('utf-8', errors='replace')}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Errore pip install: {str(e)}"

    async def manage_venv(self, action: str, path: str, project_dir: str) -> str:
        """Manage Python virtual environment"""
        if not action:
            raise ValueError("action è richiesta")
        
        try:
            if action == "create":
                if not path:
                    path = "venv"
                
                process = await asyncio.create_subprocess_shell(
                    f"python -m venv {path}",
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    shell=True
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    return f"✅ Virtual environment creato: {path}"
                else:
                    return f"❌ Errore creazione venv: {stderr.decode('utf-8', errors='replace')}"
            
            elif action == "activate":
                return f"💡 Per attivare venv: source {path}/bin/activate (Linux/Mac) o {path}\\Scripts\\activate (Windows)"
            
            elif action == "deactivate":
                return f"💡 Per disattivare venv: deactivate"
            
            else:
                return f"❌ Azione non supportata: {action}"
                
        except Exception as e:
            return f"❌ Errore gestione venv: {str(e)}"

    async def generate_doc(self, file_glob: str, style: str, project_dir: str) -> str:
        """Generate documentation for code files"""
        if not file_glob:
            raise ValueError("file_glob è richiesto")
        
        try:
            base_path = Path(project_dir)
            docs = []
            
            for file_path in base_path.glob(file_glob):
                if file_path.is_file() and file_path.suffix == '.py':
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                        
                        # Extract docstrings (basic implementation)
                        tree = ast.parse(content)
                        
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                                docstring = ast.get_docstring(node)
                                if docstring:
                                    docs.append(f"📖 {file_path.relative_to(base_path)}::{node.name}")
                                    docs.append(f"   {docstring[:100]}...")
                                    
                    except Exception:
                        continue
            
            if not docs:
                return f"📚 Nessuna documentazione trovata in {file_glob}"
            
            return f"📚 Documentazione trovata:\n" + "\n".join(docs)
            
        except Exception as e:
            return f"❌ Errore generazione documentazione: {str(e)}"

    async def code_metrics(self, file_glob: str, project_dir: str) -> str:
        """Calculate code metrics"""
        try:
            base_path = Path(project_dir)
            metrics = {
                'files': 0,
                'lines': 0,
                'functions': 0,
                'classes': 0
            }
            
            for file_path in base_path.glob(file_glob):
                if file_path.is_file() and file_path.suffix == '.py':
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                        
                        metrics['files'] += 1
                        metrics['lines'] += len(content.splitlines())
                        
                        # Count functions and classes
                        tree = ast.parse(content)
                        
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                metrics['functions'] += 1
                            elif isinstance(node, ast.ClassDef):
                                metrics['classes'] += 1
                                
                    except Exception:
                        continue
            
            result = f"📊 Metriche codice:\n"
            result += f"File: {metrics['files']}\n"
            result += f"Righe: {metrics['lines']}\n"
            result += f"Funzioni: {metrics['functions']}\n"
            result += f"Classi: {metrics['classes']}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Errore calcolo metriche: {str(e)}"

    async def scan_secrets(self, file_glob: str, project_dir: str) -> str:
        """Scan for potential secrets in code"""
        try:
            # Try to use bandit if available
            process = await asyncio.create_subprocess_shell(
                f"bandit -r {file_glob}",
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 127:  # Command not found
                return "⚠️ Bandit non disponibile. Installare con: pip install bandit"
            
            result = f"🔒 Scansione sicurezza:\n"
            if stdout:
                result += stdout.decode('utf-8', errors='replace')
            if stderr:
                result += stderr.decode('utf-8', errors='replace')
            
            return result
            
        except Exception as e:
            return f"❌ Errore scansione sicurezza: {str(e)}"

    async def open_file_range(self, path: str, start: int, end: int, project_dir: str) -> str:
        """Read specific line range from file"""
        if not path:
            raise ValueError("path è richiesto")
        
        full_path = Path(project_dir) / path
        
        if not full_path.exists():
            raise FileNotFoundError(f"File non trovato: {path}")
        
        try:
            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                lines = await f.readlines()
            
            # Adjust for 1-based indexing
            start_idx = max(0, start - 1)
            end_idx = min(len(lines), end)
            
            selected_lines = lines[start_idx:end_idx]
            
            result = f"📄 {path} (righe {start}-{end}):\n"
            for i, line in enumerate(selected_lines, start=start):
                result += f"{i:4d}: {line.rstrip()}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Errore lettura file: {str(e)}"

    async def diff_files(self, old_path: str, new_path: str, project_dir: str) -> str:
        """Compare two files and show differences"""
        if not old_path or not new_path:
            raise ValueError("old_path e new_path sono richiesti")
        
        old_full_path = Path(project_dir) / old_path
        new_full_path = Path(project_dir) / new_path
        
        if not old_full_path.exists():
            raise FileNotFoundError(f"File non trovato: {old_path}")
        
        if not new_full_path.exists():
            raise FileNotFoundError(f"File non trovato: {new_path}")
        
        try:
            async with aiofiles.open(old_full_path, 'r', encoding='utf-8') as f:
                old_content = await f.read()
            
            async with aiofiles.open(new_full_path, 'r', encoding='utf-8') as f:
                new_content = await f.read()
            
            diff = self.generate_diff(old_content, new_content, f"{old_path} vs {new_path}")
            
            return f"📝 Differenze tra {old_path} e {new_path}:\n{diff}"
            
        except Exception as e:
            return f"❌ Errore confronto file: {str(e)}"

    async def _search_in_file(self, file_path: Path, pattern: str) -> list:
        """Search for pattern in a single file"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                
            matches = []
            for i, line in enumerate(content.splitlines(), 1):
                if re.search(pattern, line, re.IGNORECASE):
                    relative_path = file_path.relative_to(file_path.parents[len(file_path.parents)-1])
                    matches.append(f"{relative_path}:{i}: {line.strip()}")
                    
            return matches
            
        except (UnicodeDecodeError, PermissionError):
            return []

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during search"""
        skip_patterns = [
            ".git", "__pycache__", ".pyc", ".pyo", ".pyd",
            ".so", ".dll", ".dylib", ".exe", ".bin",
            ".jpg", ".jpeg", ".png", ".gif", ".bmp",
            ".mp3", ".mp4", ".avi", ".mov", ".pdf",
            ".zip", ".tar", ".gz", ".bz2", ".7z",
            "node_modules", ".venv", "venv", ".env"
        ]
        
        name = file_path.name.lower()
        return any(pattern in name for pattern in skip_patterns)

    def _is_dangerous_command(self, command: str) -> bool:
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