"""
Smart Code Analyzer for VibeCLI
Provides semantic code understanding and analysis
"""

import ast
import re
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from dataclasses import dataclass

from config import get_settings


@dataclass
class CodeElement:
    """Represents a code element (function, class, etc.)"""
    name: str
    type: str  # 'function', 'class', 'method', 'variable'
    file_path: str
    line_number: int
    docstring: Optional[str]
    complexity: int
    dependencies: List[str]


@dataclass
class CodeAnalysis:
    """Complete code analysis result"""
    summary: str
    elements: List[CodeElement]
    metrics: Dict[str, Any]
    issues: List[str]
    suggestions: List[str]


class SmartCodeAnalyzer:
    """Analyzes code semantically for better understanding"""
    
    def __init__(self):
        self.settings = get_settings()
        
    async def analyze_project(self, project_dir: str, focus_areas: List[str] = None) -> str:
        """Analyze entire project and return contextual summary"""
        project_path = Path(project_dir)
        
        # Find relevant files
        if focus_areas:
            files_to_analyze = self._find_focused_files(project_path, focus_areas)
        else:
            files_to_analyze = list(project_path.glob("**/*.py"))[:10]  # Limit to 10 files
        
        analysis_results = []
        
        for file_path in files_to_analyze:
            try:
                file_analysis = await self._analyze_file(file_path)
                if file_analysis:
                    analysis_results.append(file_analysis)
            except Exception as e:
                continue
        
        return self._create_analysis_summary(analysis_results, focus_areas)
    
    async def _analyze_file(self, file_path: Path) -> Optional[CodeAnalysis]:
        """Analyze a single Python file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            analyzer = CodeVisitor()
            analyzer.visit(tree)
            
            # Extract elements
            elements = []
            
            # Functions
            for func_node in analyzer.functions:
                element = CodeElement(
                    name=func_node.name,
                    type='function',
                    file_path=str(file_path),
                    line_number=func_node.lineno,
                    docstring=ast.get_docstring(func_node),
                    complexity=self._calculate_complexity(func_node),
                    dependencies=self._extract_dependencies(func_node)
                )
                elements.append(element)
            
            # Classes
            for class_node in analyzer.classes:
                element = CodeElement(
                    name=class_node.name,
                    type='class',
                    file_path=str(file_path),
                    line_number=class_node.lineno,
                    docstring=ast.get_docstring(class_node),
                    complexity=len(class_node.body),
                    dependencies=[]
                )
                elements.append(element)
                
                # Methods
                for node in class_node.body:
                    if isinstance(node, ast.FunctionDef):
                        method = CodeElement(
                            name=f"{class_node.name}.{node.name}",
                            type='method',
                            file_path=str(file_path),
                            line_number=node.lineno,
                            docstring=ast.get_docstring(node),
                            complexity=self._calculate_complexity(node),
                            dependencies=self._extract_dependencies(node)
                        )
                        elements.append(method)
            
            # Calculate metrics
            metrics = {
                "lines_of_code": len(content.split('\n')),
                "functions_count": len(analyzer.functions),
                "classes_count": len(analyzer.classes),
                "imports_count": len(analyzer.imports),
                "complexity_score": sum(elem.complexity for elem in elements),
                "documentation_coverage": len([e for e in elements if e.docstring]) / max(len(elements), 1)
            }
            
            # Identify issues
            issues = self._identify_issues(elements, content)
            
            # Generate suggestions
            suggestions = self._generate_suggestions(elements, metrics, issues)
            
            # Create summary
            summary = self._create_file_summary(file_path, elements, metrics)
            
            return CodeAnalysis(
                summary=summary,
                elements=elements,
                metrics=metrics,
                issues=issues,
                suggestions=suggestions
            )
            
        except Exception as e:
            return None
    
    def _find_focused_files(self, project_path: Path, focus_areas: List[str]) -> List[Path]:
        """Find files related to focus areas"""
        relevant_files = []
        
        for focus in focus_areas:
            # Direct file references
            if focus.endswith('.py'):
                file_path = project_path / focus
                if file_path.exists():
                    relevant_files.append(file_path)
            else:
                # Search for files containing the focus term
                for py_file in project_path.glob("**/*.py"):
                    if focus.lower() in py_file.name.lower():
                        relevant_files.append(py_file)
                    else:
                        # Check file content for focus term
                        try:
                            content = py_file.read_text(encoding='utf-8')
                            if focus.lower() in content.lower():
                                relevant_files.append(py_file)
                        except:
                            continue
        
        # Remove duplicates and limit
        return list(set(relevant_files))[:5]
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def _extract_dependencies(self, node: ast.FunctionDef) -> List[str]:
        """Extract function dependencies (called functions, used variables)"""
        dependencies = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                dependencies.append(child.func.id)
            elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                dependencies.append(child.id)
        
        # Remove duplicates and common built-ins
        built_ins = {'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple'}
        return list(set(dep for dep in dependencies if dep not in built_ins))[:5]
    
    def _identify_issues(self, elements: List[CodeElement], content: str) -> List[str]:
        """Identify potential code issues"""
        issues = []
        
        # Long functions
        long_functions = [e for e in elements if e.type == 'function' and e.complexity > 10]
        if long_functions:
            issues.append(f"🔥 {len(long_functions)} funzioni troppo complesse (>10 complexity)")
        
        # Missing docstrings
        missing_docs = [e for e in elements if not e.docstring and e.type in ['function', 'class']]
        if missing_docs:
            issues.append(f"📝 {len(missing_docs)} elementi senza documentazione")
        
        # TODO/FIXME comments
        todo_count = content.lower().count('todo') + content.lower().count('fixme')
        if todo_count > 0:
            issues.append(f"⚠️ {todo_count} TODO/FIXME nel codice")
        
        # Very long lines
        long_lines = [line for line in content.split('\n') if len(line) > 100]
        if long_lines:
            issues.append(f"📏 {len(long_lines)} righe troppo lunghe (>100 caratteri)")
        
        return issues
    
    def _generate_suggestions(self, elements: List[CodeElement], metrics: Dict[str, Any], 
                            issues: List[str]) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Documentation suggestions
        if metrics["documentation_coverage"] < 0.5:
            suggestions.append("📚 Aggiungi docstrings per migliorare la documentazione")
        
        # Complexity suggestions
        if metrics["complexity_score"] > 50:
            suggestions.append("🔧 Considera di refactorare le funzioni più complesse")
        
        # Structure suggestions
        if metrics["functions_count"] > 20 and metrics["classes_count"] == 0:
            suggestions.append("🏗️ Considera di organizzare il codice in classi")
        
        # Testing suggestions
        test_elements = [e for e in elements if 'test' in e.name.lower()]
        if not test_elements:
            suggestions.append("🧪 Aggiungi test unitari per verificare il codice")
        
        return suggestions
    
    def _create_file_summary(self, file_path: Path, elements: List[CodeElement], 
                           metrics: Dict[str, Any]) -> str:
        """Create a summary of file analysis"""
        summary_parts = [
            f"📄 {file_path.name}:",
            f"  📊 {metrics['lines_of_code']} righe, {metrics['functions_count']} funzioni, {metrics['classes_count']} classi"
        ]
        
        if elements:
            main_elements = [e.name for e in elements if e.type in ['function', 'class']][:3]
            summary_parts.append(f"  🔧 Elementi principali: {', '.join(main_elements)}")
        
        if metrics["complexity_score"] > 20:
            summary_parts.append(f"  ⚠️ Alta complessità ({metrics['complexity_score']})")
        
        return "\n".join(summary_parts)
    
    def _create_analysis_summary(self, analysis_results: List[CodeAnalysis], 
                               focus_areas: List[str] = None) -> str:
        """Create overall analysis summary"""
        if not analysis_results:
            return "❌ Nessun file Python analizzabile trovato"
        
        summary_parts = ["🔍 ANALISI CODICE INTELLIGENTE:"]
        
        if focus_areas:
            summary_parts.append(f"🎯 Focus: {', '.join(focus_areas)}")
        
        # Overall metrics
        total_elements = sum(len(analysis.elements) for analysis in analysis_results)
        total_issues = sum(len(analysis.issues) for analysis in analysis_results)
        
        summary_parts.extend([
            f"📊 {len(analysis_results)} file analizzati, {total_elements} elementi trovati",
            ""
        ])
        
        # File summaries
        for analysis in analysis_results[:3]:  # Show top 3 files
            summary_parts.append(analysis.summary)
        
        if len(analysis_results) > 3:
            summary_parts.append(f"... e altri {len(analysis_results) - 3} file")
        
        # Common issues
        if total_issues > 0:
            summary_parts.extend([
                "",
                "⚠️ PROBLEMI RILEVATI:"
            ])
            
            all_issues = []
            for analysis in analysis_results:
                all_issues.extend(analysis.issues)
            
            # Group similar issues
            issue_counts = {}
            for issue in all_issues:
                key = issue.split()[0]  # Get emoji/first word
                issue_counts[key] = issue_counts.get(key, 0) + 1
            
            for issue_type, count in issue_counts.items():
                if count > 1:
                    summary_parts.append(f"  {issue_type} Multipli problemi simili ({count})")
        
        # Best suggestions
        all_suggestions = []
        for analysis in analysis_results:
            all_suggestions.extend(analysis.suggestions)
        
        if all_suggestions:
            unique_suggestions = list(set(all_suggestions))[:3]
            summary_parts.extend([
                "",
                "💡 SUGGERIMENTI:",
                *[f"  {sugg}" for sugg in unique_suggestions]
            ])
        
        return "\n".join(summary_parts)


class CodeVisitor(ast.NodeVisitor):
    """AST visitor to extract code elements"""
    
    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []
        self.variables = []
    
    def visit_FunctionDef(self, node):
        self.functions.append(node)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        self.functions.append(node)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        self.classes.append(node)
        self.generic_visit(node)
    
    def visit_Import(self, node):
        self.imports.extend([alias.name for alias in node.names])
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node) 