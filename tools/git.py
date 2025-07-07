"""
Git tools for VibeCLI
Handles version control operations like status, diff, and commit
"""

import asyncio
from .base import BaseTool, ToolResult


class GitTools(BaseTool):
    """Git version control tools"""
    
    @property
    def name(self) -> str:
        return "git"
    
    @property
    def description(self) -> str:
        return "Git version control operations"
    
    @property
    def is_destructive(self) -> bool:
        return True  # Git commits are destructive
    
    async def execute(self, **kwargs) -> ToolResult:
        """Not used in this implementation - tools called directly"""
        pass
    
    async def git_status(self, project_dir: str) -> str:
        """Get Git repository status"""
        try:
            process = await asyncio.create_subprocess_exec(
                "git", "status", "--porcelain",
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                if b"not a git repository" in stderr:
                    return "📂 Non è un repository Git"
                else:
                    return f"❌ Errore Git: {stderr.decode('utf-8', errors='replace')}"
            
            status_output = stdout.decode('utf-8', errors='replace').strip()
            
            if not status_output:
                return "✅ Repository pulito - nessuna modifica"
            
            # Parse status output
            changes = {
                'modified': [],
                'added': [],
                'deleted': [],
                'untracked': []
            }
            
            for line in status_output.split('\n'):
                if len(line) >= 3:
                    status_code = line[:2]
                    filename = line[3:]
                    
                    if status_code.startswith('M'):
                        changes['modified'].append(filename)
                    elif status_code.startswith('A'):
                        changes['added'].append(filename)
                    elif status_code.startswith('D'):
                        changes['deleted'].append(filename)
                    elif status_code.startswith('??'):
                        changes['untracked'].append(filename)
            
            result = "📊 Status Git:\n"
            
            if changes['modified']:
                result += f"📝 Modificati ({len(changes['modified'])}):\n"
                result += "\n".join(f"  {f}" for f in changes['modified']) + "\n"
            
            if changes['added']:
                result += f"➕ Aggiunti ({len(changes['added'])}):\n"
                result += "\n".join(f"  {f}" for f in changes['added']) + "\n"
            
            if changes['deleted']:
                result += f"➖ Eliminati ({len(changes['deleted'])}):\n"
                result += "\n".join(f"  {f}" for f in changes['deleted']) + "\n"
            
            if changes['untracked']:
                result += f"❓ Non tracciati ({len(changes['untracked'])}):\n"
                result += "\n".join(f"  {f}" for f in changes['untracked']) + "\n"
            
            return result
            
        except Exception as e:
            return f"❌ Errore status Git: {str(e)}"
    
    async def git_diff(self, rev: str = "HEAD", project_dir: str = "") -> str:
        """Show Git diff"""
        try:
            # Get diff
            process = await asyncio.create_subprocess_exec(
                "git", "diff", rev,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return f"❌ Errore Git diff: {stderr.decode('utf-8', errors='replace')}"
            
            diff_output = stdout.decode('utf-8', errors='replace')
            
            if not diff_output.strip():
                return f"📝 Nessuna differenza rispetto a {rev}"
            
            # Limit output size
            if len(diff_output) > 3000:
                diff_output = diff_output[:3000] + "\n... (diff troncato)"
            
            return f"📝 Diff rispetto a {rev}:\n{diff_output}"
            
        except Exception as e:
            return f"❌ Errore Git diff: {str(e)}"
    
    async def git_commit(self, message: str, add_all: bool = True, project_dir: str = "") -> str:
        """Commit changes to Git"""
        try:
            if not message:
                raise ValueError("Messaggio commit richiesto")
            
            result = f"📝 Git commit: {message}\n"
            
            # Add files if requested
            if add_all:
                add_process = await asyncio.create_subprocess_exec(
                    "git", "add", ".",
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                _, add_stderr = await add_process.communicate()
                
                if add_process.returncode != 0:
                    return f"❌ Errore Git add: {add_stderr.decode('utf-8', errors='replace')}"
                
                result += "✅ File aggiunti al staging\n"
            
            # Commit
            commit_process = await asyncio.create_subprocess_exec(
                "git", "commit", "-m", message,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            commit_stdout, commit_stderr = await commit_process.communicate()
            
            if commit_process.returncode != 0:
                stderr_text = commit_stderr.decode('utf-8', errors='replace')
                if "nothing to commit" in stderr_text:
                    result += "ℹ️ Nessuna modifica da committare"
                else:
                    result += f"❌ Errore commit: {stderr_text}"
            else:
                commit_output = commit_stdout.decode('utf-8', errors='replace')
                result += f"✅ Commit effettuato:\n{commit_output}"
            
            return result
            
        except Exception as e:
            return f"❌ Errore Git commit: {str(e)}" 