#!/usr/bin/env python3
"""
Main agent script for VibeCLI
Handles menu system, chat loop, and user interactions
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table
from rich.syntax import Syntax
from rich.tree import Tree
from rich.layout import Layout
from rich.live import Live

from models import LLMClient
from tools import ToolExecutor
from utils import Colors, print_colored, confirm_yes_no
from intelligence import ConversationEngine
from config import get_settings

console = Console()


class AgentCLI:
    def __init__(self):
        self.project_dir: Optional[Path] = None
        self.llm_client = LLMClient()
        self.tool_executor = ToolExecutor()
        self.chat_history = []
        self.settings = get_settings()
        
        # 🧠 NEW: Intelligent conversation engine
        self.conversation_engine = ConversationEngine(self.llm_client)
        
        # 🎨 UI State
        self.modified_files = set()
        self.created_files = set()
        self.project_stats = {}
        self.layout = Layout()

    def _create_project_info_panel(self) -> Panel:
        """Create project information panel"""
        if not self.project_dir:
            return Panel("📁 Nessun progetto selezionato", title="🏠 Progetto", border_style="dim")
        
        # Project stats
        info_lines = [
            f"📂 Directory: {self.project_dir.name}",
            f"📍 Path: {str(self.project_dir)}"
        ]
        
        if self.project_stats:
            info_lines.extend([
                f"📄 File: {self.project_stats.get('files', 0)}",
                f"🐍 Python: {self.project_stats.get('python_files', 0)}",
                f"📝 Linee: {self.project_stats.get('lines', 0)}"
            ])
        
        # Recent activity
        if self.modified_files or self.created_files:
            info_lines.append("")
            info_lines.append("📊 Attività Recente:")
            
            if self.modified_files:
                info_lines.append(f"  ✏️  Modificati: {len(self.modified_files)}")
            if self.created_files:
                info_lines.append(f"  ➕ Creati: {len(self.created_files)}")
        
        return Panel("\n".join(info_lines), title="🏠 Progetto", border_style="cyan")

    def _create_file_canvas_panel(self) -> Panel:
        """Create file modifications canvas"""
        if not self.modified_files and not self.created_files:
            return Panel("🎨 Nessuna modifica recente", title="📝 Canvas", border_style="dim")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Stato", style="green", width=8)
        table.add_column("File", style="white")
        table.add_column("Tipo", style="yellow", width=10)
        
        # Add modified files
        for file_path in self.modified_files:
            file_type = "Python" if file_path.endswith('.py') else "Other"
            table.add_row("✏️ MOD", file_path, file_type)
        
        # Add created files
        for file_path in self.created_files:
            file_type = "Python" if file_path.endswith('.py') else "Other"
            table.add_row("➕ NEW", file_path, file_type)
        
        return Panel(table, title="📝 Canvas Modifiche", border_style="green")

    def _create_file_tree_panel(self) -> Panel:
        """Create file tree panel"""
        if not self.project_dir or not self.settings.show_file_tree:
            return Panel("🌳 File tree disabilitato", title="📁 Struttura", border_style="dim")
        
        tree = Tree(f"📁 {self.project_dir.name}")
        
        try:
            # Add only important files/directories
            for item in sorted(self.project_dir.iterdir()):
                if item.name.startswith('.'):
                    continue
                    
                if item.is_dir():
                    if item.name in ['__pycache__', 'node_modules', '.git']:
                        continue
                    branch = tree.add(f"📁 {item.name}")
                    
                    # Add a few files from each directory
                    try:
                        files = list(item.glob("*.py"))[:3]
                        for file in files:
                            branch.add(f"🐍 {file.name}")
                    except PermissionError:
                        pass
                        
                elif item.suffix in ['.py', '.js', '.ts', '.md', '.txt', '.json']:
                    icon = "🐍" if item.suffix == '.py' else "📄"
                    tree.add(f"{icon} {item.name}")
        except Exception:
            tree.add("❌ Errore lettura directory")
        
        return Panel(tree, title="📁 Struttura", border_style="blue")

    def print_enhanced_menu(self):
        """Print enhanced menu with project info and panels"""
        current_dir = str(self.project_dir) if self.project_dir else "vuoto"

        # Main menu
        menu = f"""
╔══════════════════════════════════════╗
║        🧠 VibeCLI INTELLIGENT        ║
╟──────────────────────────────────────╢
║ 1) Ristampa menu                     ║
║ 2) Cambia directory                  ║
║ 3) Cambia modello                    ║
║ 4) Toggle file tree                  ║
║ 5) Esci                              ║
╟──────────────────────────────────────╢
║ Directory: {current_dir:<22} ║
╚══════════════════════════════════════╝"""

        console.print(menu, style="cyan")
        
        # Enhanced panels if project is selected
        if self.project_dir:
            console.print()
            
            # Create panels
            project_panel = self._create_project_info_panel()
            canvas_panel = self._create_file_canvas_panel()
            
            # Display in columns
            if self.settings.show_file_tree:
                tree_panel = self._create_file_tree_panel()
                console.print(Columns([project_panel, canvas_panel, tree_panel], equal=True))
            else:
                console.print(Columns([project_panel, canvas_panel], equal=True))

    def print_menu(self):
        """Wrapper for enhanced menu"""
        self.print_enhanced_menu()

    async def _show_file_with_syntax_highlighting(self, file_path: str, content: str):
        """Show file content with syntax highlighting"""
        if not self.settings.syntax_highlighting:
            print_colored(f"📄 {file_path}:\n{content}", Colors.WHITE)
            return
        
        # Determine syntax based on file extension
        syntax_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.sh': 'bash',
            '.xml': 'xml'
        }
        
        file_ext = Path(file_path).suffix.lower()
        syntax_lang = syntax_map.get(file_ext, 'text')
        
        try:
            syntax = Syntax(content, syntax_lang, theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title=f"📄 {file_path}", border_style="green"))
        except Exception:
            # Fallback to plain text
            print_colored(f"📄 {file_path}:\n{content}", Colors.WHITE)

    def track_file_modification(self, file_path: str, is_new: bool = False):
        """Track file modifications for canvas"""
        if is_new:
            self.created_files.add(file_path)
        else:
            self.modified_files.add(file_path)
        
        # Limit tracking to recent changes
        if len(self.modified_files) > 10:
            self.modified_files = set(list(self.modified_files)[-10:])
        if len(self.created_files) > 10:
            self.created_files = set(list(self.created_files)[-10:])

    async def _update_project_stats(self):
        """Update project statistics"""
        if not self.project_dir:
            return
            
        try:
            python_files = list(self.project_dir.glob("**/*.py"))
            all_files = [f for f in self.project_dir.rglob("*") if f.is_file()]
            
            # Count lines in Python files
            total_lines = 0
            for py_file in python_files[:20]:  # Limit to avoid slow scanning
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        total_lines += len(f.readlines())
                except Exception:
                    pass
            
            self.project_stats = {
                'files': len(all_files),
                'python_files': len(python_files),
                'lines': total_lines
            }
        except Exception:
            self.project_stats = {}

    async def change_directory(self):
        """Enhanced directory change with project analysis"""
        directory_path = Prompt.ask("Inserisci il percorso della directory")
        dir_path = Path(directory_path).expanduser().resolve()

        if not dir_path.exists():
            if Confirm.ask(f"La directory '{dir_path}' non esiste. Vuoi crearla?"):
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print_colored(f"✅ Directory creata: {dir_path}", Colors.GREEN)
                except Exception as e:
                    print_colored(f"❌ Errore creazione directory: {e}", Colors.RED)
                    return
            else:
                print_colored("❌ Operazione annullata", Colors.YELLOW)
                return

        if not dir_path.is_dir():
            print_colored("❌ Il percorso specificato non è una directory", Colors.RED)
            return

        # Test write permissions
        test_file = dir_path / ".vibe_test"
        try:
            test_file.touch()
            test_file.unlink()
        except Exception:
            print_colored(
                "⚠️ Attenzione: Permessi di scrittura limitati in questa directory",
                Colors.YELLOW,
            )

        self.project_dir = dir_path
        print_colored(f"✅ Directory impostata: {dir_path}", Colors.GREEN)
        
        # 📊 Update project stats
        print_colored("📊 Analizzando progetto...", Colors.CYAN)
        await self._update_project_stats()
        
        # Clear previous tracking
        self.modified_files.clear()
        self.created_files.clear()
        
        print_colored("🚀 Avvio chat intelligente...", Colors.GREEN)
        await self.chat_loop()

    async def handle_menu_choice(self, choice: str) -> bool:
        """Handle menu selection. Returns True to continue, False to exit"""
        if choice == "1":
            # Just reprint menu - this is handled in the main loop
            return True

        elif choice == "2":
            # Change directory
            await self.change_directory()
            return True

        elif choice == "3":
            # Model change placeholder
            print_colored("⚙️  Funzionalità non ancora disponibile", Colors.YELLOW)
            input("Premi Enter per continuare...")
            return True

        elif choice == "4":
            # Toggle file tree
            self.settings.show_file_tree = not self.settings.show_file_tree
            print_colored(f"🌳 File tree {'abilitato' if self.settings.show_file_tree else 'disabilitato'}", Colors.GREEN)
            return True

        elif choice == "5":
            # Exit
            print_colored("👋  Arrivederci!", Colors.GREEN)
            return False

        else:
            print_colored("❌  Scelta non valida", Colors.RED)
            input("Premi Enter per continuare...")
            return True

    async def chat_loop(self):
        """🧠 INTELLIGENT chat loop with context understanding"""
        if not self.project_dir:
            print_colored(
                "❌  Nessuna directory impostata. Ritorno al menu...", Colors.RED
            )
            return

        # 🎯 Show intelligent welcome with project analysis
        await self._show_intelligent_welcome()

        print_colored(
            "💬  Scrivi cosa vuoi fare (digita 'menu' per tornare al menu) ›",
            Colors.CYAN,
        )

        while True:
            try:
                user_input = Prompt.ask("\n🤖")

                if user_input.lower().strip() == "menu":
                    break

                if not user_input.strip():
                    # 💡 Show smart suggestions when empty input
                    await self._show_smart_suggestions()
                    continue

                # 🧠 Process input with INTELLIGENCE
                print_colored("🧠  Reasoning: Analizzando la richiesta...", Colors.CYAN)
                
                conversation_response = await self.conversation_engine.process_user_input(
                    user_input, str(self.project_dir)
                )

                # 📊 Show intent understanding
                if conversation_response.confidence > 0.7:
                    intent_info = f"🎯 Capisco: {conversation_response.context_updates.get('intent', 'generale')} (confidenza: {conversation_response.confidence:.1%})"
                    print_colored(intent_info, Colors.BLUE)

                # 🤖 Show AI response
                if conversation_response.response:
                    print_colored(f"💭 {conversation_response.response}", Colors.GREEN)

                # ⚡ Execute suggested actions
                if conversation_response.suggested_actions:
                    await self._handle_suggested_actions(conversation_response.suggested_actions)

                # Update conversation history
                self.chat_history.append({"role": "user", "content": user_input})
                self.chat_history.append({"role": "assistant", "content": conversation_response.response})

            except KeyboardInterrupt:
                print_colored("\n👋  Ritorno al menu principale...", Colors.YELLOW)
                break
            except Exception as e:
                print_colored(f"❌  Errore nell'elaborazione intelligente: {str(e)}", Colors.RED)
                # Fallback to old behavior
                await self._fallback_processing(user_input)

    async def _show_intelligent_welcome(self):
        """Show intelligent welcome with project context"""
        print_colored("🧠  Analyzing project context...", Colors.CYAN)
        
        # Get smart suggestions for the project
        suggestions = await self.conversation_engine.provide_smart_suggestions(str(self.project_dir))
        
        # Show project summary
        context = self.conversation_engine.get_conversation_context()
        if context["project_summary"]:
            console.print(f"\n📋 {context['project_summary']}\n", style="dim")
        
        # Show smart suggestions
        if suggestions:
            print_colored("💡  Suggerimenti intelligenti:", Colors.YELLOW)
            for suggestion in suggestions[:3]:  # Show top 3
                console.print(f"  • {suggestion}", style="dim yellow")
            print()

    async def _show_smart_suggestions(self):
        """Show smart suggestions when user input is empty"""
        suggestions = await self.conversation_engine.provide_smart_suggestions(str(self.project_dir))
        
        if suggestions:
            print_colored("💡  Cosa posso fare per te?", Colors.YELLOW)
            for i, suggestion in enumerate(suggestions[:3], 1):
                console.print(f"  {i}. {suggestion}", style="dim yellow")
        else:
            print_colored("💭  Dimmi cosa vuoi fare con questo progetto...", Colors.BLUE)

    async def _handle_suggested_actions(self, suggested_actions):
        """Handle and execute suggested actions intelligently"""
        if not suggested_actions:
            return

        print_colored(f"⚡  Ho {len(suggested_actions)} azioni da proporre:", Colors.CYAN)
        
        for i, action in enumerate(suggested_actions, 1):
            description = action.get("description", f"Azione {action.get('type', 'unknown')}")
            console.print(f"  {i}. {description}", style="dim cyan")

        # Ask for confirmation for multiple actions
        if len(suggested_actions) > 1:
            if not Confirm.ask("🤔  Vuoi che esegua queste azioni?", default=True):
                print_colored("⏭️  Azioni saltate", Colors.YELLOW)
                return

        # Execute actions
        for action in suggested_actions:
            try:
                print_colored(f"🔧  Eseguendo: {action.get('description', 'Azione')}", Colors.BLUE)
                
                result = await self.conversation_engine.execute_suggested_action(
                    action, str(self.project_dir)
                )
                
                if result:
                    console.print(f"✅  {result}", style="green")
                    
            except Exception as e:
                print_colored(f"❌  Errore nell'azione: {str(e)}", Colors.RED)

    async def _fallback_processing(self, user_input):
        """Fallback to original processing when intelligence fails"""
        try:
            # Add to history
            self.chat_history.append({"role": "user", "content": user_input})

            # Get response from LLM (original method)
            response = await self.llm_client.generate_response(
                user_input, self.chat_history, str(self.project_dir)
            )

            if response.get("function_calls"):
                # Execute function calls
                await self.execute_function_calls(response["function_calls"])

                # Add assistant response to history if there was content
                if response.get("content"):
                    self.chat_history.append(
                        {
                            "role": "assistant",
                            "content": response.get("content", ""),
                        }
                    )
            else:
                # Regular response
                content = response.get("content", "No response")
                print_colored(f"🤖  {content}", Colors.BLUE)

                # Add assistant response to history
                self.chat_history.append({"role": "assistant", "content": content})
                
        except Exception as e:
            print_colored(f"❌  Errore anche nel fallback: {str(e)}", Colors.RED)

    async def execute_function_calls(self, function_calls: list):
        """Execute function calls with user confirmation for destructive operations"""
        # Separate safe and destructive operations
        safe_calls = []
        destructive_calls = []

        for call in function_calls:
            # Destructive tools that need confirmation
            destructive_tools = [
                "write_file",
                "append_file",
                "execute_shell",
                "delete_file",
                "search_replace",
                "pip_install",
                "git_commit",
            ]

            # Check for copy_file and move_file with overwrite
            if call["name"] in ["copy_file", "move_file"]:
                args = call.get("arguments", {})
                if args.get("overwrite", False):
                    destructive_calls.append(call)
                else:
                    safe_calls.append(call)
            elif call["name"] in destructive_tools:
                destructive_calls.append(call)
            else:
                safe_calls.append(call)

        # Execute safe operations in parallel
        if safe_calls:
            print_colored(
                "🧠  Reasoning: Eseguendo operazioni di lettura...", Colors.BLUE
            )
            safe_results = await asyncio.gather(
                *[
                    self.tool_executor.execute_tool(call, str(self.project_dir))
                    for call in safe_calls
                ],
                return_exceptions=True,
            )

            print_colored("✅  Results:", Colors.GREEN)
            for i, result in enumerate(safe_results):
                if isinstance(result, Exception):
                    print_colored(
                        f"❌  {safe_calls[i]['name']}: {str(result)}", Colors.RED
                    )
                else:
                    console.print(f"📄  {safe_calls[i]['name']}: {result}")

        # Handle destructive operations with confirmation
        for call in destructive_calls:
            description = self.get_operation_description(call)

            if Confirm.ask(f"⚠️  Posso procedere con: {description}?", default=False):
                print_colored(
                    f"🧠  Reasoning: Eseguendo {call['name']}...", Colors.BLUE
                )
                try:
                    result = await self.tool_executor.execute_tool(
                        call, str(self.project_dir)
                    )
                    print_colored("✅  Results:", Colors.GREEN)
                    console.print(f"📄  {call['name']}: {result}")
                except Exception as e:
                    print_colored(f"❌  {call['name']}: {str(e)}", Colors.RED)
            else:
                print_colored(f"⏭️  Saltando {call['name']}", Colors.YELLOW)

    def get_operation_description(self, call: dict) -> str:
        """Get human-readable description of operation"""
        name = call["name"]
        args = call.get("arguments", {})

        if name == "write_file":
            return f"scrivere file {args.get('file_path', 'unknown')}"
        elif name == "append_file":
            return f"aggiungere contenuto al file {args.get('file_path', 'unknown')}"
        elif name == "execute_shell":
            return f"eseguire comando shell: {args.get('command', 'unknown')}"
        elif name == "copy_file":
            return f"copiare {args.get('src', 'unknown')} → {args.get('dst', 'unknown')} (sovrascrivendo)"
        elif name == "move_file":
            return f"spostare {args.get('src', 'unknown')} → {args.get('dst', 'unknown')} (sovrascrivendo)"
        elif name == "delete_file":
            return f"eliminare {args.get('path', 'unknown')}"
        elif name == "search_replace":
            return f"sostituire '{args.get('pattern', 'unknown')}' con '{args.get('replacement', 'unknown')}' in {args.get('file_glob', 'unknown')}"
        elif name == "pip_install":
            package = args.get("package", "unknown")
            version = args.get("version")
            pkg_spec = f"{package}=={version}" if version else package
            return f"installare pacchetto {pkg_spec}"
        elif name == "git_commit":
            return f"commit git: {args.get('message', 'unknown')}"
        else:
            return f"operazione {name}"

    async def run(self):
        """Main application loop"""
        print_colored("🚀  Avvio Agent CLI...", Colors.GREEN)

        while True:
            os.system("clear" if os.name == "posix" else "cls")
            self.print_menu()

            choice = Prompt.ask("Seleziona [1-5]", choices=["1", "2", "3", "4", "5"])
            
            result = await self.handle_menu_choice(choice)
            
            if result is False:
                # Exit requested
                break
            elif result == "start_chat":
                # Directory was set successfully, start chat
                await self.chat_loop()
            # else continue with menu loop


def main():
    """Entry point"""
    try:
        agent = AgentCLI()
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print_colored("\n👋  Arrivederci!", Colors.GREEN)
        sys.exit(0)
    except Exception as e:
        print_colored(f"❌  Errore fatale: {str(e)}", Colors.RED)
        sys.exit(1)


if __name__ == "__main__":
    main()
