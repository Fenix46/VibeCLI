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

from models import LLMClient
from tools import ToolExecutor
from utils import Colors, print_colored, confirm_yes_no

console = Console()


class AgentCLI:
    def __init__(self):
        self.project_dir: Optional[Path] = None
        self.llm_client = LLMClient()
        self.tool_executor = ToolExecutor()
        self.chat_history = []

    def print_menu(self):
        """Print the ASCII menu"""
        current_dir = str(self.project_dir) if self.project_dir else "vuoto"

        menu = f"""
╔══════════════════════════════════════╗
║        🛠️  VibeCLI MENU              ║
╟──────────────────────────────────────╢
║ 1) Ristampa menu                     ║
║ 2) Cambia directory                  ║
║ 3) Cambia modello                    ║
║ 4) Esci                              ║
╟──────────────────────────────────────╢
║ Directory: {current_dir:<22} ║
╚══════════════════════════════════════╝"""

        console.print(menu, style="cyan")

    def handle_directory_change(self) -> bool:
        """Handle directory change with creation option. Returns True if directory was set successfully"""
        new_dir = Prompt.ask("📂  Inserisci il nuovo percorso della directory")

        if not new_dir.strip():
            print_colored("❌  Percorso non valido", Colors.RED)
            return False

        dir_path = Path(new_dir).resolve()

        # Check if directory exists
        if not dir_path.exists():
            if confirm_yes_no(f'La directory "{dir_path}" non esiste. Vuoi crearla?'):
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print_colored(f"✅  Directory creata: {dir_path}", Colors.GREEN)
                except Exception as e:
                    print_colored(
                        f"❌  Errore nella creazione della directory: {str(e)}",
                        Colors.RED,
                    )
                    return False
            else:
                print_colored("❌  Operazione annullata", Colors.YELLOW)
                return False

        # Check if it's actually a directory
        if not dir_path.is_dir():
            print_colored(
                f"❌  Il percorso non è una directory: {dir_path}", Colors.RED
            )
            return False

        # Check write permissions
        if not os.access(dir_path, os.W_OK):
            print_colored(f"❌  Permessi di scrittura negati: {dir_path}", Colors.RED)
            return False

        # Set the project directory
        self.project_dir = dir_path
        print_colored(f"📂  Working directory set to: {self.project_dir}", Colors.GREEN)
        return True

    def handle_menu_choice(self, choice: str) -> bool:
        """Handle menu selection. Returns True to continue, False to exit"""
        if choice == "1":
            # Just reprint menu - this is handled in the main loop
            return True

        elif choice == "2":
            # Change directory
            if self.handle_directory_change():
                # Automatically start chat if directory was set successfully
                return "start_chat"
            else:
                input("Premi Enter per continuare...")
                return True

        elif choice == "3":
            # Model change placeholder
            print_colored("⚙️  Funzionalità non ancora disponibile", Colors.YELLOW)
            input("Premi Enter per continuare...")
            return True

        elif choice == "4":
            # Exit
            print_colored("👋  Arrivederci!", Colors.GREEN)
            return False

        else:
            print_colored("❌  Scelta non valida", Colors.RED)
            input("Premi Enter per continuare...")
            return True

    async def chat_loop(self):
        """Main chat loop when project directory is set"""
        if not self.project_dir:
            print_colored(
                "❌  Nessuna directory impostata. Ritorno al menu...", Colors.RED
            )
            return

        print_colored(
            "💬  Inserisci il tuo comando (digita 'menu' per tornare al menu) ›",
            Colors.CYAN,
        )

        while True:
            try:
                user_input = Prompt.ask("\n🤖")

                if user_input.lower().strip() == "menu":
                    break

                if not user_input.strip():
                    continue

                # Add to history
                self.chat_history.append({"role": "user", "content": user_input})

                # Get response from LLM
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

            except KeyboardInterrupt:
                print_colored("\n👋  Ritorno al menu principale...", Colors.YELLOW)
                break
            except Exception as e:
                print_colored(f"❌  Errore: {str(e)}", Colors.RED)

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

            choice = Prompt.ask("Seleziona [1-4]", choices=["1", "2", "3", "4"])
            
            result = self.handle_menu_choice(choice)
            
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
