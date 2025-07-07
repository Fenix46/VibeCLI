"""
LLM Client module for CLI-IDE
Handles communication with Gemini API including function calling using google-genai SDK
"""

import os
import asyncio
from typing import Dict, List, Any
from pathlib import Path

from google import genai
from google.genai import types
from config import get_settings


class LLMClient:
    """Client for interacting with Gemini API with function calling support using google-genai SDK"""

    def __init__(self):
        self.settings = get_settings()
        
        # Check if API key is available
        if not self.settings.gemini_api_key:
            print("⚠️  GEMINI_API_KEY non configurata!")
            print("📝 Per configurare l'API key:")
            print("   1. Modifica il file .env")
            print("   2. Imposta GEMINI_API_KEY=your_api_key_here")
            print("   3. Oppure esporta la variabile d'ambiente")
            self.client = None
        else:
            # Initialize the new google-genai client
            self.client = genai.Client(api_key=self.settings.gemini_api_key)
        
        self.model_name = self.settings.gemini_model
        self.system_prompt = self._load_system_prompt()

        # Function definitions for Gemini (converted to new SDK format)
        self.functions = [
            # Original 5 tools
            types.FunctionDeclaration(
                name="read_file",
                description="Legge il contenuto di un file",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "file_path": types.Schema(
                            type=types.Type.STRING,
                            description="Percorso del file da leggere (relativo alla directory di progetto)",
                        )
                    },
                    required=["file_path"],
                ),
            ),
            types.FunctionDeclaration(
                name="write_file",
                description="Scrive contenuto in un file",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "file_path": types.Schema(
                            type=types.Type.STRING,
                            description="Percorso del file da scrivere (relativo alla directory di progetto)",
                        ),
                        "content": types.Schema(
                            type=types.Type.STRING,
                            description="Contenuto da scrivere nel file",
                        ),
                    },
                    required=["file_path", "content"],
                ),
            ),
            types.FunctionDeclaration(
                name="append_file",
                description="Aggiunge contenuto alla fine di un file",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "file_path": types.Schema(
                            type=types.Type.STRING,
                            description="Percorso del file a cui aggiungere contenuto",
                        ),
                        "content": types.Schema(
                            type=types.Type.STRING,
                            description="Contenuto da aggiungere al file",
                        ),
                    },
                    required=["file_path", "content"],
                ),
            ),
            types.FunctionDeclaration(
                name="grep_search",
                description="Cerca un pattern in file o directory",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "pattern": types.Schema(
                            type=types.Type.STRING,
                            description="Pattern regex da cercare",
                        ),
                        "file_path": types.Schema(
                            type=types.Type.STRING,
                            description="File o directory in cui cercare (default: '.' per directory corrente)",
                        ),
                    },
                    required=["pattern"],
                ),
            ),
            types.FunctionDeclaration(
                name="execute_shell",
                description="Esegue un comando shell",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "command": types.Schema(
                            type=types.Type.STRING,
                            description="Comando shell da eseguire",
                        )
                    },
                    required=["command"],
                ),
            ),
            # New 22 tools
            types.FunctionDeclaration(
                name="list_dir",
                description="Lista contenuti di una directory",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "path": types.Schema(
                            type=types.Type.STRING,
                            description="Percorso della directory da listare (default: '.')",
                        ),
                        "recursive": types.Schema(
                            type=types.Type.BOOLEAN,
                            description="Se true, lista ricorsivamente (default: false)",
                        ),
                    },
                    required=[],
                ),
            ),
            types.FunctionDeclaration(
                name="copy_file",
                description="Copia file o directory",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "src": types.Schema(
                            type=types.Type.STRING, description="Percorso sorgente"
                        ),
                        "dst": types.Schema(
                            type=types.Type.STRING, description="Percorso destinazione"
                        ),
                        "overwrite": types.Schema(
                            type=types.Type.BOOLEAN,
                            description="Se sovrascrivere file esistenti (default: false)",
                        ),
                    },
                    required=["src", "dst"],
                ),
            ),
            types.FunctionDeclaration(
                name="move_file",
                description="Sposta file o directory",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "src": types.Schema(
                            type=types.Type.STRING, description="Percorso sorgente"
                        ),
                        "dst": types.Schema(
                            type=types.Type.STRING, description="Percorso destinazione"
                        ),
                        "overwrite": types.Schema(
                            type=types.Type.BOOLEAN,
                            description="Se sovrascrivere file esistenti (default: false)",
                        ),
                    },
                    required=["src", "dst"],
                ),
            ),
            types.FunctionDeclaration(
                name="delete_file",
                description="Elimina file o directory",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "path": types.Schema(
                            type=types.Type.STRING,
                            description="Percorso del file/directory da eliminare",
                        ),
                        "force": types.Schema(
                            type=types.Type.BOOLEAN,
                            description="Se forzare eliminazione directory non vuote (default: false)",
                        ),
                    },
                    required=["path"],
                ),
            ),
            types.FunctionDeclaration(
                name="make_dir",
                description="Crea directory",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "path": types.Schema(
                            type=types.Type.STRING,
                            description="Percorso della directory da creare",
                        ),
                        "exist_ok": types.Schema(
                            type=types.Type.BOOLEAN,
                            description="Se non dare errore se già esiste (default: true)",
                        ),
                    },
                    required=["path"],
                ),
            ),
            types.FunctionDeclaration(
                name="file_stat",
                description="Ottieni statistiche di un file",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "path": types.Schema(
                            type=types.Type.STRING, description="Percorso del file"
                        )
                    },
                    required=["path"],
                ),
            ),
            types.FunctionDeclaration(
                name="codebase_search",
                description="Cerca pattern nel codebase",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "query": types.Schema(
                            type=types.Type.STRING, description="Pattern da cercare"
                        ),
                        "file_glob": types.Schema(
                            type=types.Type.STRING,
                            description="Pattern glob per i file (default: '**/*.{py,ts,js}')",
                        ),
                    },
                    required=["query"],
                ),
            ),
            types.FunctionDeclaration(
                name="search_replace",
                description="Cerca e sostituisci testo nei file",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "pattern": types.Schema(
                            type=types.Type.STRING,
                            description="Pattern regex da cercare",
                        ),
                        "replacement": types.Schema(
                            type=types.Type.STRING, description="Testo sostitutivo"
                        ),
                        "file_glob": types.Schema(
                            type=types.Type.STRING,
                            description="Pattern glob per i file",
                        ),
                        "preview": types.Schema(
                            type=types.Type.BOOLEAN,
                            description="Se solo mostrare anteprima (default: true)",
                        ),
                    },
                    required=["pattern", "replacement", "file_glob"],
                ),
            ),
            types.FunctionDeclaration(
                name="format_code",
                description="Formatta codice",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "file_glob": types.Schema(
                            type=types.Type.STRING,
                            description="Pattern glob per i file (default: '**/*.py')",
                        ),
                        "style": types.Schema(
                            type=types.Type.STRING,
                            description="Stile di formattazione (default: 'black')",
                        ),
                    },
                    required=[],
                ),
            ),
            types.FunctionDeclaration(
                name="lint_code",
                description="Analizza codice con linter",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "file_glob": types.Schema(
                            type=types.Type.STRING,
                            description="Pattern glob per i file (default: '**/*.py')",
                        ),
                        "linter": types.Schema(
                            type=types.Type.STRING,
                            description="Linter da usare (default: 'ruff')",
                        ),
                    },
                    required=[],
                ),
            ),
            types.FunctionDeclaration(
                name="run_tests",
                description="Esegue test",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "test_cmd": types.Schema(
                            type=types.Type.STRING,
                            description="Comando per eseguire i test (default: 'pytest -q')",
                        )
                    },
                    required=[],
                ),
            ),
            types.FunctionDeclaration(
                name="run_python",
                description="Esegue modulo o script Python",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "module_or_path": types.Schema(
                            type=types.Type.STRING,
                            description="Modulo o percorso script da eseguire",
                        ),
                        "args": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(type=types.Type.STRING),
                            description="Argomenti aggiuntivi (default: [])",
                        ),
                    },
                    required=["module_or_path"],
                ),
            ),
            types.FunctionDeclaration(
                name="compile_code",
                description="Compila/controlla sintassi codice Python",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "file_glob": types.Schema(
                            type=types.Type.STRING,
                            description="Pattern glob per i file (default: '**/*.py')",
                        )
                    },
                    required=[],
                ),
            ),
            types.FunctionDeclaration(
                name="git_status",
                description="Ottieni status git",
                parameters=types.Schema(
                    type=types.Type.OBJECT, properties={}, required=[]
                ),
            ),
            types.FunctionDeclaration(
                name="git_diff",
                description="Ottieni diff git",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "rev": types.Schema(
                            type=types.Type.STRING,
                            description="Revisione da confrontare (default: 'HEAD')",
                        )
                    },
                    required=[],
                ),
            ),
            types.FunctionDeclaration(
                name="git_commit",
                description="Commit modifiche git",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "message": types.Schema(
                            type=types.Type.STRING, description="Messaggio di commit"
                        ),
                        "add_all": types.Schema(
                            type=types.Type.BOOLEAN,
                            description="Se aggiungere tutti i file (default: true)",
                        ),
                    },
                    required=["message"],
                ),
            ),
            types.FunctionDeclaration(
                name="pip_install",
                description="Installa pacchetto Python",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "package": types.Schema(
                            type=types.Type.STRING, description="Nome del pacchetto"
                        ),
                        "version": types.Schema(
                            type=types.Type.STRING,
                            description="Versione specifica (opzionale)",
                        ),
                    },
                    required=["package"],
                ),
            ),
            types.FunctionDeclaration(
                name="manage_venv",
                description="Gestisce virtual environment Python",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "action": types.Schema(
                            type=types.Type.STRING,
                            description="Azione: 'create', 'activate', 'deactivate'",
                        ),
                        "path": types.Schema(
                            type=types.Type.STRING,
                            description="Percorso del virtual environment",
                        ),
                    },
                    required=["action"],
                ),
            ),
            types.FunctionDeclaration(
                name="generate_doc",
                description="Genera documentazione dal codice",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "file_glob": types.Schema(
                            type=types.Type.STRING,
                            description="Pattern glob per i file",
                        ),
                        "style": types.Schema(
                            type=types.Type.STRING,
                            description="Stile documentazione (default: 'google')",
                        ),
                    },
                    required=["file_glob"],
                ),
            ),
            types.FunctionDeclaration(
                name="code_metrics",
                description="Calcola metriche del codice",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "file_glob": types.Schema(
                            type=types.Type.STRING,
                            description="Pattern glob per i file (default: '**/*.py')",
                        )
                    },
                    required=[],
                ),
            ),
            types.FunctionDeclaration(
                name="scan_secrets",
                description="Scansiona per segreti nel codice",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "file_glob": types.Schema(
                            type=types.Type.STRING,
                            description="Pattern glob per i file (default: '**/*')",
                        )
                    },
                    required=[],
                ),
            ),
            types.FunctionDeclaration(
                name="open_file_range",
                description="Legge range specifico di righe da file",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "path": types.Schema(
                            type=types.Type.STRING, description="Percorso del file"
                        ),
                        "start": types.Schema(
                            type=types.Type.INTEGER,
                            description="Riga di inizio (1-based)",
                        ),
                        "end": types.Schema(
                            type=types.Type.INTEGER,
                            description="Riga di fine (inclusive)",
                        ),
                    },
                    required=["path", "start", "end"],
                ),
            ),
            types.FunctionDeclaration(
                name="diff_files",
                description="Confronta due file",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "old_path": types.Schema(
                            type=types.Type.STRING,
                            description="Percorso del primo file",
                        ),
                        "new_path": types.Schema(
                            type=types.Type.STRING,
                            description="Percorso del secondo file",
                        ),
                    },
                    required=["old_path", "new_path"],
                ),
            ),
        ]

    def _load_system_prompt(self) -> str:
        """Load system prompt from file"""
        try:
            prompt_path = Path("prompts/general_system_prompt.txt")
            if prompt_path.exists():
                with open(prompt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception:
            pass

        # Fallback system prompt
        return """Sei un assistente AI che aiuta con la programmazione e lo sviluppo software.
        Hai accesso a 27 strumenti principali per operazioni su file, sviluppo, git e testing.
        Usa questi strumenti per aiutare l'utente con le sue richieste di programmazione.
        Sii preciso e dettagliato nelle tue risposte."""

    async def generate_response(
        self, user_input: str, chat_history: List[Dict], project_dir: str
    ) -> Dict[str, Any]:
        """Generate response from Gemini API with function calling support using new SDK"""

        # Check if client is available
        if not self.client:
            return {
                "content": "❌ Client API non disponibile. Configura GEMINI_API_KEY nel file .env",
                "function_calls": [],
            }

        # Prepare messages
        contents = self._prepare_contents(user_input, chat_history, project_dir)

        # Create generation config
        config = types.GenerateContentConfig(
            temperature=0.7,
            top_k=40,
            top_p=0.95,
            max_output_tokens=8192,
            tools=[types.Tool(function_declarations=self.functions)],
        )

        try:
            # Use the new SDK for generation
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=contents,
                config=config,
            )

            return self._parse_response(response)

        except Exception as e:
            return {
                "content": f"Errore nella comunicazione con l'API: {str(e)}",
                "function_calls": [],
            }

    def _prepare_contents(
        self, user_input: str, chat_history: List[Dict], project_dir: str
    ) -> List[types.Content]:
        """Prepare contents for Gemini API using new SDK types"""
        contents = []

        # Add system message as first user message
        system_message = (
            f"{self.system_prompt}\n\nDirectory di lavoro corrente: {project_dir}"
        )
        contents.append(
            types.Content(role="user", parts=[types.Part(text=system_message)])
        )

        # Add chat history (last 10 messages to avoid token limit)
        recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history

        for message in recent_history:
            role = "user" if message["role"] == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part(text=message["content"])])
            )

        # Add current user input
        contents.append(types.Content(role="user", parts=[types.Part(text=user_input)]))

        return contents

    def _parse_response(self, response) -> Dict[str, Any]:
        """Parse Gemini API response and extract function calls using new SDK"""
        try:
            if not response.candidates:
                return {
                    "content": "Nessuna risposta ricevuta dall'API",
                    "function_calls": [],
                }

            candidate = response.candidates[0]

            if not candidate.content:
                return {"content": "Risposta malformata dall'API", "function_calls": []}

            function_calls = []
            text_content = ""

            # Extract parts using new SDK structure
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    text_content += part.text
                elif hasattr(part, "function_call") and part.function_call:
                    func_call = part.function_call
                    # Convert function call arguments to dict
                    args = {}
                    if hasattr(func_call, "args") and func_call.args:
                        for key, value in func_call.args.items():
                            args[key] = value

                    function_calls.append({"name": func_call.name, "arguments": args})

            return {"content": text_content.strip(), "function_calls": function_calls}

        except Exception as e:
            return {
                "content": f"Errore nel parsing della risposta: {str(e)}",
                "function_calls": [],
            }

    async def generate_simple_response(self, prompt: str) -> str:
        """Generate a simple text response without function calling using new SDK"""
        
        # Check if client is available
        if not self.client:
            return "❌ Client API non disponibile. Configura GEMINI_API_KEY nel file .env"
        
        contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]

        config = types.GenerateContentConfig(
            temperature=0.7,
            top_k=40,
            top_p=0.95,
            max_output_tokens=2048,
        )

        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=contents,
                config=config,
            )

            if response.candidates and response.candidates[0].content:
                parts = response.candidates[0].content.parts
                if parts and hasattr(parts[0], "text"):
                    return parts[0].text

            return "Nessuna risposta ricevuta"

        except Exception as e:
            return f"Errore: {str(e)}"
