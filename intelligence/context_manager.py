"""
Context Manager for VibeCLI
Maintains conversation state and project understanding
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

from config import get_settings


@dataclass
class ProjectContext:
    """Project context information"""
    name: str
    type: str
    files_count: int
    main_language: str
    has_tests: bool
    has_documentation: bool
    has_errors: bool
    dependencies: List[str]
    recent_changes: List[str]
    structure_summary: str


@dataclass
class ConversationTurn:
    """Single conversation turn"""
    timestamp: str
    user_input: str
    ai_response: str
    intent_type: str
    actions_taken: List[str]


class ContextManager:
    """Manages conversation and project context"""
    
    def __init__(self):
        self.settings = get_settings()
        self.conversation_history: List[ConversationTurn] = []
        self.project_context: Optional[ProjectContext] = None
        self.current_focus: str = ""
        self.recent_actions: List[Dict[str, Any]] = []
        
    async def update_project_context(self, project_dir: str) -> Dict[str, Any]:
        """Update project context by analyzing current state"""
        project_path = Path(project_dir)
        
        # Basic project info
        project_name = project_path.name
        
        # Count files and determine main language
        python_files = list(project_path.glob("**/*.py"))
        js_files = list(project_path.glob("**/*.js"))
        ts_files = list(project_path.glob("**/*.ts"))
        
        total_files = len(python_files) + len(js_files) + len(ts_files)
        
        if python_files:
            main_language = "Python"
        elif js_files or ts_files:
            main_language = "JavaScript/TypeScript"
        else:
            main_language = "Unknown"
        
        # Check for tests
        has_tests = any([
            (project_path / "tests").exists(),
            (project_path / "test").exists(),
            bool(list(project_path.glob("**/test_*.py"))),
            bool(list(project_path.glob("**/*_test.py")))
        ])
        
        # Check for documentation
        has_documentation = any([
            (project_path / "README.md").exists(),
            (project_path / "docs").exists(),
            (project_path / "documentation").exists()
        ])
        
        # Check for common dependency files
        dependencies = []
        if (project_path / "requirements.txt").exists():
            try:
                deps_content = (project_path / "requirements.txt").read_text()
                dependencies = [line.split("==")[0] for line in deps_content.split("\n") if line.strip()]
            except:
                pass
        
        if (project_path / "package.json").exists():
            try:
                package_json = json.loads((project_path / "package.json").read_text())
                dependencies.extend(package_json.get("dependencies", {}).keys())
            except:
                pass
        
        # Analyze project structure
        structure_summary = await self._analyze_project_structure(project_path)
        
        # Check for recent changes (simplified)
        recent_changes = await self._get_recent_changes(project_path)
        
        # Simple error detection (check for common error patterns)
        has_errors = await self._check_for_errors(project_path)
        
        # Update context
        self.project_context = ProjectContext(
            name=project_name,
            type=main_language,
            files_count=total_files,
            main_language=main_language,
            has_tests=has_tests,
            has_documentation=has_documentation,
            has_errors=has_errors,
            dependencies=dependencies[:10],  # Limit to top 10
            recent_changes=recent_changes,
            structure_summary=structure_summary
        )
        
        return asdict(self.project_context)
    
    async def _analyze_project_structure(self, project_path: Path) -> str:
        """Analyze and summarize project structure"""
        structure_parts = []
        
        # Main directories
        important_dirs = ["src", "lib", "app", "components", "models", "views", "controllers"]
        found_dirs = []
        
        for dir_name in important_dirs:
            if (project_path / dir_name).exists():
                found_dirs.append(dir_name)
        
        if found_dirs:
            structure_parts.append(f"📁 Directories: {', '.join(found_dirs)}")
        
        # Configuration files
        config_files = ["setup.py", "pyproject.toml", "package.json", "Dockerfile"]
        found_configs = []
        
        for config_file in config_files:
            if (project_path / config_file).exists():
                found_configs.append(config_file)
        
        if found_configs:
            structure_parts.append(f"⚙️ Config: {', '.join(found_configs)}")
        
        # Main entry points
        entry_points = ["main.py", "app.py", "index.py", "server.py", "__init__.py"]
        found_entries = []
        
        for entry in entry_points:
            if (project_path / entry).exists():
                found_entries.append(entry)
        
        if found_entries:
            structure_parts.append(f"🚀 Entry points: {', '.join(found_entries)}")
        
        return " | ".join(structure_parts) if structure_parts else "Standard project structure"
    
    async def _get_recent_changes(self, project_path: Path) -> List[str]:
        """Get recent changes (simplified version)"""
        # In a real implementation, this would use git to get recent commits
        changes = []
        
        # Check for recently modified files (last 24h would be ideal)
        try:
            for py_file in project_path.glob("**/*.py"):
                if py_file.stat().st_mtime > (datetime.now().timestamp() - 86400):
                    changes.append(f"Modified: {py_file.name}")
                    if len(changes) >= 5:  # Limit to 5 recent changes
                        break
        except:
            pass
        
        return changes
    
    async def _check_for_errors(self, project_path: Path) -> bool:
        """Check for common error indicators"""
        try:
            # Check for Python syntax errors in main files
            for py_file in list(project_path.glob("*.py"))[:5]:  # Check first 5 files
                try:
                    content = py_file.read_text(encoding='utf-8')
                    # Simple checks for error patterns
                    if any(pattern in content.lower() for pattern in [
                        "traceback", "exception", "error:", "failed", "todo: fix"
                    ]):
                        return True
                except:
                    continue
        except:
            pass
        
        return False
    
    def add_conversation_turn(self, user_input: str, ai_response: str, 
                            intent_type: str = "", actions_taken: List[str] = None) -> None:
        """Add a conversation turn to history"""
        turn = ConversationTurn(
            timestamp=datetime.now().isoformat(),
            user_input=user_input,
            ai_response=ai_response,
            intent_type=intent_type,
            actions_taken=actions_taken or []
        )
        
        self.conversation_history.append(turn)
        
        # Keep only last 20 turns to manage memory
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def add_action(self, action_type: str, details: Dict[str, Any]) -> None:
        """Record an action taken by the agent"""
        action = {
            "timestamp": datetime.now().isoformat(),
            "type": action_type,
            "details": details
        }
        
        self.recent_actions.append(action)
        
        # Keep only last 10 actions
        if len(self.recent_actions) > 10:
            self.recent_actions = self.recent_actions[-10:]
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        recent_turns = self.conversation_history[-limit:]
        return [
            {
                "user": turn.user_input,
                "assistant": turn.ai_response,
                "intent": turn.intent_type,
                "timestamp": turn.timestamp
            }
            for turn in recent_turns
        ]
    
    def get_project_summary(self) -> str:
        """Get a concise project summary"""
        if not self.project_context:
            return "🔍 Progetto non ancora analizzato"
        
        ctx = self.project_context
        summary_parts = [
            f"📦 Progetto: {ctx.name} ({ctx.main_language})",
            f"📄 Files: {ctx.files_count}",
            f"🧪 Tests: {'✅' if ctx.has_tests else '❌'}",
            f"📚 Docs: {'✅' if ctx.has_documentation else '❌'}",
        ]
        
        if ctx.has_errors:
            summary_parts.append("⚠️ Errori rilevati")
        
        if ctx.dependencies:
            summary_parts.append(f"📦 Deps: {len(ctx.dependencies)} packages")
        
        summary_parts.append(f"🏗️ {ctx.structure_summary}")
        
        return "\n".join(summary_parts)
    
    def get_recent_actions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent actions taken"""
        return self.recent_actions[-limit:]
    
    def set_current_focus(self, focus: str) -> None:
        """Set current area of focus"""
        self.current_focus = focus
        self.add_action("focus_change", {"new_focus": focus})
    
    def get_current_focus(self) -> str:
        """Get current focus area"""
        return self.current_focus
    
    def get_context_for_ai(self) -> Dict[str, Any]:
        """Get complete context for AI consumption"""
        return {
            "project": asdict(self.project_context) if self.project_context else None,
            "conversation_summary": self._get_conversation_summary(),
            "current_focus": self.current_focus,
            "recent_actions": self.get_recent_actions(),
            "capabilities": self._get_available_capabilities()
        }
    
    def _get_conversation_summary(self) -> str:
        """Get a summary of recent conversation"""
        if not self.conversation_history:
            return "Prima conversazione"
        
        recent_intents = [turn.intent_type for turn in self.conversation_history[-5:] if turn.intent_type]
        intent_summary = f"Recenti intenti: {', '.join(set(recent_intents))}" if recent_intents else ""
        
        return f"Conversazione attiva con {len(self.conversation_history)} scambi. {intent_summary}"
    
    def _get_available_capabilities(self) -> List[str]:
        """Get list of available capabilities"""
        return [
            "🔍 Analisi codice",
            "🛠️ Modifica file", 
            "🧪 Esecuzione test",
            "📦 Gestione dipendenze",
            "🗂️ Ricerca file",
            "📊 Metriche qualità",
            "🔧 Debugging",
            "📝 Documentazione"
        ] 