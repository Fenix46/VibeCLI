"""
Analysis tools for VibeCLI
Handles documentation generation, code metrics, and security scanning
"""

import asyncio
import ast
from pathlib import Path
from typing import List

import aiofiles
from .base import BaseTool, ToolResult


class AnalysisTools(BaseTool):
    """Code analysis, documentation and security tools"""
    
    @property
    def name(self) -> str:
        return "analysis"
    
    @property
    def description(self) -> str:
        return "Code analysis, documentation generation, and security scanning"
    
    @property
    def is_destructive(self) -> bool:
        return False  # Analysis tools are read-only
    
    async def execute(self, **kwargs) -> ToolResult:
        """Not used in this implementation - tools called directly"""
        pass
    
    async def generate_doc(self, file_glob: str = "", style: str = "google", project_dir: str = "") -> str:
        """Generate documentation for code files"""
        try:
            if not file_glob:
                file_glob = "**/*.py"
            
            base_path = Path(project_dir)
            docs = []
            
            for file_path in base_path.glob(file_glob):
                if file_path.is_file() and not self.should_skip_file(file_path):
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                        
                        # Parse Python AST to extract docstrings
                        tree = ast.parse(content)
                        relative_path = file_path.relative_to(base_path)
                        
                        file_doc = f"\n## {relative_path}\n"
                        
                        # Extract module docstring
                        if ast.get_docstring(tree):
                            file_doc += f"**Module:** {ast.get_docstring(tree)}\n\n"
                        
                        # Extract class and function docstrings
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                class_doc = ast.get_docstring(node)
                                file_doc += f"### Class: {node.name}\n"
                                if class_doc:
                                    file_doc += f"{class_doc}\n\n"
                                else:
                                    file_doc += "_No documentation_\n\n"
                            
                            elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                                func_doc = ast.get_docstring(node)
                                # Get function signature
                                args = [arg.arg for arg in node.args.args]
                                file_doc += f"#### Function: {node.name}({', '.join(args)})\n"
                                if func_doc:
                                    file_doc += f"{func_doc}\n\n"
                                else:
                                    file_doc += "_No documentation_\n\n"
                        
                        if file_doc.strip() != f"## {relative_path}":
                            docs.append(file_doc)
                    
                    except (SyntaxError, UnicodeDecodeError):
                        continue
            
            if not docs:
                return f"📚 Nessuna documentazione trovata in {file_glob}"
            
            return f"📚 Documentazione trovata:\n" + "\n".join(docs)
            
        except Exception as e:
            return f"❌ Errore generazione documentazione: {str(e)}"
    
    async def code_metrics(self, file_glob: str = "**/*.py", project_dir: str = "") -> str:
        """Calculate code metrics"""
        try:
            base_path = Path(project_dir)
            metrics = {
                'files': 0,
                'lines': 0,
                'functions': 0,
                'classes': 0,
                'comments': 0,
                'docstrings': 0
            }
            
            detailed_files = []
            
            for file_path in base_path.glob(file_glob):
                if file_path.is_file() and not self.should_skip_file(file_path):
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                        
                        lines = content.splitlines()
                        metrics['files'] += 1
                        metrics['lines'] += len(lines)
                        
                        # Count comments
                        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
                        metrics['comments'] += comment_lines
                        
                        # Count functions, classes, and docstrings
                        file_functions = 0
                        file_classes = 0
                        file_docstrings = 0
                        
                        tree = ast.parse(content)
                        
                        # Module docstring
                        if ast.get_docstring(tree):
                            file_docstrings += 1
                        
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                file_functions += 1
                                if ast.get_docstring(node):
                                    file_docstrings += 1
                            elif isinstance(node, ast.ClassDef):
                                file_classes += 1
                                if ast.get_docstring(node):
                                    file_docstrings += 1
                        
                        metrics['functions'] += file_functions
                        metrics['classes'] += file_classes
                        metrics['docstrings'] += file_docstrings
                        
                        # File details
                        relative_path = file_path.relative_to(base_path)
                        detailed_files.append({
                            'path': str(relative_path),
                            'lines': len(lines),
                            'functions': file_functions,
                            'classes': file_classes,
                            'comments': comment_lines,
                            'docstrings': file_docstrings
                        })
                        
                    except Exception:
                        continue
            
            result = f"📊 Metriche codice per {file_glob}:\n\n"
            result += f"**Totali:**\n"
            result += f"📁 File: {metrics['files']}\n"
            result += f"📄 Righe: {metrics['lines']}\n"
            result += f"🔧 Funzioni: {metrics['functions']}\n"
            result += f"🏗️ Classi: {metrics['classes']}\n"
            result += f"💬 Commenti: {metrics['comments']}\n"
            result += f"📚 Docstrings: {metrics['docstrings']}\n"
            
            # Calculate averages
            if metrics['files'] > 0:
                avg_lines = metrics['lines'] / metrics['files']
                result += f"\n**Medie per file:**\n"
                result += f"📏 Righe medie: {avg_lines:.1f}\n"
                
                if metrics['functions'] > 0:
                    result += f"🔧 Funzioni medie: {metrics['functions'] / metrics['files']:.1f}\n"
                
                # Documentation coverage
                total_documentable = metrics['functions'] + metrics['classes'] + metrics['files']
                if total_documentable > 0:
                    doc_coverage = (metrics['docstrings'] / total_documentable) * 100
                    result += f"📚 Copertura documentazione: {doc_coverage:.1f}%\n"
            
            # Top files by size
            if detailed_files:
                result += f"\n**File più grandi:**\n"
                sorted_files = sorted(detailed_files, key=lambda x: x['lines'], reverse=True)[:5]
                for file_info in sorted_files:
                    result += f"📄 {file_info['path']}: {file_info['lines']} righe\n"
            
            return result
            
        except Exception as e:
            return f"❌ Errore calcolo metriche: {str(e)}"
    
    async def scan_secrets(self, file_glob: str = "**/*", project_dir: str = "") -> str:
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
                # Fallback to basic pattern matching
                return await self._basic_secret_scan(file_glob, project_dir)
            
            result = f"🔒 Scansione sicurezza con Bandit:\n"
            if stdout:
                result += stdout.decode('utf-8', errors='replace')
            if stderr:
                result += stderr.decode('utf-8', errors='replace')
            
            return result
            
        except Exception as e:
            return f"❌ Errore scansione sicurezza: {str(e)}"
    
    async def _basic_secret_scan(self, file_glob: str, project_dir: str) -> str:
        """Basic secret scanning using pattern matching"""
        try:
            base_path = Path(project_dir)
            
            # Common secret patterns
            secret_patterns = [
                r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{20,})',
                r'(?i)(secret[_-]?key|secretkey)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{20,})',
                r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?([^\s"\']{8,})',
                r'(?i)(token)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{20,})',
                r'(?i)(aws[_-]?access[_-]?key)\s*[=:]\s*["\']?([A-Z0-9]{20})',
                r'(?i)(aws[_-]?secret[_-]?key)\s*[=:]\s*["\']?([a-zA-Z0-9/+=]{40})',
            ]
            
            findings = []
            
            for file_path in base_path.glob(file_glob):
                if file_path.is_file() and not self.should_skip_file(file_path):
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                        
                        for i, line in enumerate(content.splitlines(), 1):
                            for pattern in secret_patterns:
                                import re
                                matches = re.finditer(pattern, line)
                                for match in matches:
                                    relative_path = file_path.relative_to(base_path)
                                    findings.append(f"⚠️ {relative_path}:{i} - Possibile {match.group(1)}")
                    
                    except (UnicodeDecodeError, PermissionError):
                        continue
            
            result = f"🔒 Scansione sicurezza base:\n"
            
            if findings:
                result += f"⚠️ Trovati {len(findings)} potenziali problemi:\n"
                result += "\n".join(findings)
            else:
                result += "✅ Nessun problema di sicurezza rilevato"
            
            return result
            
        except Exception as e:
            return f"❌ Errore scansione base: {str(e)}" 