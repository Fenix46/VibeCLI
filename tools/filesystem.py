"""
Filesystem tools for VibeCLI
Handles file operations, directory management, and search functionality
"""

import asyncio
import os
import shutil
import glob
import re
import stat
from pathlib import Path
from typing import List

import aiofiles
from .base import BaseTool, ToolResult
from performance import SearchOptimizer, AsyncBatchProcessor, MemoryManager
from config import get_settings


class FileSystemTools(BaseTool):
    """File system operations and search tools"""
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        
        # 🚀 Performance optimizations
        self.search_optimizer = SearchOptimizer()
        self.batch_processor = AsyncBatchProcessor(max_concurrent=self.settings.max_concurrent_ops)
        self.memory_manager = MemoryManager(max_memory_mb=self.settings.max_memory_mb)
        
        # 💾 Cache for frequent operations
        self._file_cache = {} if self.settings.cache_enabled else None
        self._search_cache = {} if self.settings.cache_enabled else None
    
    @property
    def name(self) -> str:
        return "filesystem"
    
    @property
    def description(self) -> str:
        return "File and directory operations, search functionality"
    
    @property
    def is_destructive(self) -> bool:
        return True  # Contains destructive operations like delete, write
    
    async def execute(self, **kwargs) -> ToolResult:
        """Not used in this implementation - tools called directly"""
        pass
    
    async def read_file(self, file_path: str, encoding: str = "utf-8", project_dir: str = "") -> str:
        """Read file content with caching and memory management"""
        try:
            full_path = self.validate_path(file_path, project_dir)
            
            # 💾 Check cache first
            if self._file_cache and str(full_path) in self._file_cache:
                return f"📄 {file_path}:\n{self._file_cache[str(full_path)]}"
            
            # 🧠 Memory management for large files
            file_size = full_path.stat().st_size
            if file_size > self.settings.max_file_size:
                return f"❌ File troppo grande ({file_size / 1024 / 1024:.1f}MB). Limite: {self.settings.max_file_size / 1024 / 1024:.1f}MB"
            
            # 📖 Read with memory management
            content = await self.memory_manager.read_file_chunked(full_path, encoding)
            
            # 💾 Cache if enabled
            if self._file_cache and file_size < self.settings.cache_file_max_size:
                self._file_cache[str(full_path)] = content
            
            return f"📄 {file_path}:\n{content}"
            
        except Exception as e:
            return f"❌ Errore lettura {file_path}: {str(e)}"
    
    async def write_file(self, file_path: str, content: str, project_dir: str) -> str:
        """Write content to file with diff display"""
        try:
            full_path = self.validate_path(file_path, project_dir)
            
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing content for diff
            old_content = ""
            if full_path.exists():
                try:
                    async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                        old_content = await f.read()
                except UnicodeDecodeError:
                    old_content = "<binary file>"
            
            # Write new content
            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            # Generate diff
            diff = self.generate_diff(old_content, content, file_path)
            
            return f"✅ File scritto: {file_path}\n{diff}"
            
        except Exception as e:
            return f"❌ Errore scrittura file: {str(e)}"
    
    async def append_file(self, file_path: str, content: str, project_dir: str) -> str:
        """Append content to file"""
        try:
            full_path = self.validate_path(file_path, project_dir)
            
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing content for context
            old_content = ""
            if full_path.exists():
                try:
                    async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                        old_content = await f.read()
                except UnicodeDecodeError:
                    old_content = "<binary file>"
            
            # Append content
            async with aiofiles.open(full_path, 'a', encoding='utf-8') as f:
                await f.write(content)
            
            new_content = old_content + content
            diff = self.generate_diff(old_content, new_content, file_path)
            
            return f"✅ Contenuto aggiunto a: {file_path}\n{diff}"
            
        except Exception as e:
            return f"❌ Errore aggiunta contenuto: {str(e)}"
    
    async def list_dir(self, path: str = ".", recursive: bool = False, project_dir: str = "") -> str:
        """List directory contents"""
        try:
            full_path = self.validate_path(path, project_dir)
            
            if not full_path.exists():
                raise FileNotFoundError(f"Directory non trovata: {path}")
            
            if not full_path.is_dir():
                raise ValueError(f"Il percorso non è una directory: {path}")
            
            items = []
            
            if recursive:
                for item in full_path.rglob("*"):
                    if not self.should_skip_file(item):
                        relative_path = item.relative_to(full_path)
                        if item.is_dir():
                            items.append(f"📁 {relative_path}/")
                        else:
                            size = item.stat().st_size
                            items.append(f"📄 {relative_path} ({size} bytes)")
            else:
                for item in full_path.iterdir():
                    if not self.should_skip_file(item):
                        if item.is_dir():
                            items.append(f"📁 {item.name}/")
                        else:
                            size = item.stat().st_size
                            items.append(f"📄 {item.name} ({size} bytes)")
            
            if not items:
                return f"📂 Directory vuota: {path}"
            
            items.sort()
            return f"📂 Contenuto di {path}:\n" + "\n".join(items)
            
        except Exception as e:
            return f"❌ Errore lista directory: {str(e)}"
    
    async def copy_file(self, src: str, dst: str, overwrite: bool = False, project_dir: str = "") -> str:
        """Copy file or directory"""
        try:
            src_path = self.validate_path(src, project_dir)
            dst_path = self.validate_path(dst, project_dir)
            
            if not src_path.exists():
                raise FileNotFoundError(f"Sorgente non trovata: {src}")
            
            if dst_path.exists() and not overwrite:
                raise FileExistsError(f"Destinazione esiste già: {dst}")
            
            if src_path.is_dir():
                if dst_path.exists():
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
                return f"✅ Directory copiata: {src} → {dst}"
            else:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
                return f"✅ File copiato: {src} → {dst}"
                
        except Exception as e:
            return f"❌ Errore copia: {str(e)}"
    
    async def move_file(self, src: str, dst: str, overwrite: bool = False, project_dir: str = "") -> str:
        """Move file or directory"""
        try:
            src_path = self.validate_path(src, project_dir)
            dst_path = self.validate_path(dst, project_dir)
            
            if not src_path.exists():
                raise FileNotFoundError(f"Sorgente non trovata: {src}")
            
            if dst_path.exists() and not overwrite:
                raise FileExistsError(f"Destinazione esiste già: {dst}")
            
            if dst_path.exists():
                if dst_path.is_dir():
                    shutil.rmtree(dst_path)
                else:
                    dst_path.unlink()
            
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dst_path))
            
            return f"✅ Spostato: {src} → {dst}"
            
        except Exception as e:
            return f"❌ Errore spostamento: {str(e)}"
    
    async def delete_file(self, path: str, force: bool = False, project_dir: str = "") -> str:
        """Delete file or directory"""
        try:
            full_path = self.validate_path(path, project_dir)
            
            if not full_path.exists():
                raise FileNotFoundError(f"Percorso non trovato: {path}")
            
            if full_path.is_dir():
                if force or not any(full_path.iterdir()):
                    shutil.rmtree(full_path)
                    return f"✅ Directory eliminata: {path}"
                else:
                    raise ValueError(f"Directory non vuota: {path}. Usa force=True per eliminare.")
            else:
                full_path.unlink()
                return f"✅ File eliminato: {path}"
                
        except Exception as e:
            return f"❌ Errore eliminazione: {str(e)}"
    
    async def make_dir(self, path: str, exist_ok: bool = True, project_dir: str = "") -> str:
        """Create directory"""
        try:
            full_path = self.validate_path(path, project_dir)
            
            full_path.mkdir(parents=True, exist_ok=exist_ok)
            return f"✅ Directory creata: {path}"
            
        except FileExistsError:
            return f"❌ Directory esiste già: {path}"
        except Exception as e:
            return f"❌ Errore creazione directory: {str(e)}"
    
    async def file_stat(self, path: str, project_dir: str) -> str:
        """Get file statistics"""
        try:
            full_path = self.validate_path(path, project_dir)
            
            if not full_path.exists():
                raise FileNotFoundError(f"Percorso non trovato: {path}")
            
            stat_info = full_path.stat()
            
            result = f"📊 Statistiche di {path}:\n"
            result += f"Tipo: {'Directory' if full_path.is_dir() else 'File'}\n"
            result += f"Dimensione: {stat_info.st_size} bytes\n"
            result += f"Permessi: {stat.filemode(stat_info.st_mode)}\n"
            result += f"Modificato: {stat_info.st_mtime}\n"
            result += f"Creato: {stat_info.st_ctime}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Errore statistiche: {str(e)}"
    
    async def grep_search(self, pattern: str, file_path: str = ".", project_dir: str = "") -> str:
        """Search pattern in files with optimization"""
        try:
            if not pattern:
                raise ValueError("pattern è richiesto")
            
            search_path = self.validate_path(file_path, project_dir)
            
            # Use optimized search
            results = await self.search_optimizer.search_optimized(
                pattern, search_path, file_glob="**/*", context_lines=0
            )
            
            if not results:
                return f"🔍 Nessun match trovato per: {pattern}"
            
            # Format results
            formatted_matches = []
            for result in results:
                formatted_matches.append(f"{result.file_path}:{result.line_number}: {result.line_content}")
            
            return f"🔍 Trovati {len(results)} match per '{pattern}':\n" + "\n".join(formatted_matches)
            
        except Exception as e:
            return f"❌ Errore ricerca: {str(e)}"
    
    async def codebase_search(self, query: str, file_patterns: str = "*.py", project_dir: str = "") -> str:
        """🔍 Intelligent codebase search with optimization"""
        try:
            # 💾 Check search cache
            cache_key = f"{query}:{file_patterns}:{project_dir}"
            if self._search_cache and cache_key in self._search_cache:
                return self._search_cache[cache_key]
            
            # 🚀 Use optimized search
            results = await self.search_optimizer.semantic_search(
                query=query,
                directory=project_dir,
                file_patterns=file_patterns.split(","),
                max_results=self.settings.max_search_results
            )
            
            if not results:
                result = f"🔍 Nessun risultato per: {query}"
            else:
                result_lines = [f"🔍 Trovati {len(results)} risultati per: {query}\n"]
                
                for i, result in enumerate(results[:self.settings.max_search_results], 1):
                    result_lines.append(f"{i}. {result['file']}:{result['line']}")
                    result_lines.append(f"   {result['content']}")
                    if result.get('context'):
                        result_lines.append(f"   Context: {result['context']}")
                    result_lines.append("")
                
                result = "\n".join(result_lines)
            
            # 💾 Cache result
            if self._search_cache:
                self._search_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            return f"❌ Errore ricerca: {str(e)}"
    
    async def search_replace(self, pattern: str, replacement: str, file_glob: str = "", 
                           preview: bool = True, project_dir: str = "") -> str:
        """Search and replace text in files"""
        try:
            if not pattern or replacement is None:
                raise ValueError("pattern e replacement sono richiesti")
            
            base_path = Path(project_dir)
            changes = []
            
            # Default glob if not specified
            if not file_glob:
                file_glob = "**/*.py"
            
            for file_path in base_path.glob(file_glob):
                if file_path.is_file() and not self.should_skip_file(file_path):
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                        
                        new_content = re.sub(pattern, replacement, content)
                        
                        if new_content != content:
                            if not preview:
                                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                                    await f.write(new_content)
                            
                            relative_path = file_path.relative_to(base_path)
                            changes.append(str(relative_path))
                    
                    except (UnicodeDecodeError, PermissionError):
                        continue
            
            if not changes:
                return f"🔄 Nessuna sostituzione per pattern: {pattern}"
            
            action = "Preview" if preview else "Applicate"
            return f"🔄 {action} sostituzioni in {len(changes)} file:\n" + "\n".join(changes)
            
        except Exception as e:
            return f"❌ Errore sostituzione: {str(e)}"
    
    async def open_file_range(self, path: str, start: int, end: int, project_dir: str) -> str:
        """Read specific line range from file"""
        try:
            full_path = self.validate_path(path, project_dir)
            
            if not full_path.exists():
                raise FileNotFoundError(f"File non trovato: {path}")
            
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
        try:
            old_full_path = self.validate_path(old_path, project_dir)
            new_full_path = self.validate_path(new_path, project_dir)
            
            if not old_full_path.exists():
                raise FileNotFoundError(f"File non trovato: {old_path}")
            
            if not new_full_path.exists():
                raise FileNotFoundError(f"File non trovato: {new_path}")
            
            async with aiofiles.open(old_full_path, 'r', encoding='utf-8') as f:
                old_content = await f.read()
            
            async with aiofiles.open(new_full_path, 'r', encoding='utf-8') as f:
                new_content = await f.read()
            
            diff = self.generate_diff(old_content, new_content, f"{old_path} vs {new_path}")
            
            return f"📝 Differenze tra {old_path} e {new_path}:\n{diff}"
            
        except Exception as e:
            return f"❌ Errore confronto file: {str(e)}"
    
    async def _search_in_file(self, file_path: Path, pattern: str) -> List[str]:
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