"""
Conversation Engine for VibeCLI
Makes the agent truly conversational and intelligent like Cursor
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from config import get_settings
from .context_manager import ContextManager
from .intent_classifier import IntentClassifier
from .code_analyzer import SmartCodeAnalyzer


@dataclass
class ConversationResponse:
    """Response from conversation engine"""
    response: str
    suggested_actions: List[Dict[str, Any]]
    context_updates: Dict[str, Any]
    confidence: float


class ConversationEngine:
    """Intelligent conversation engine that understands context and intent"""
    
    def __init__(self, llm_client):
        self.settings = get_settings()
        self.llm_client = llm_client
        self.context_manager = ContextManager()
        self.intent_classifier = IntentClassifier()
        self.code_analyzer = SmartCodeAnalyzer()
        
    async def process_user_input(self, user_input: str, project_dir: str) -> ConversationResponse:
        """Process user input with full context understanding"""
        
        # 1. Analyze current project context
        await self.context_manager.update_project_context(project_dir)
        project_context = self.context_manager.get_project_summary()
        
        # 2. Classify user intent
        intent = await self.intent_classifier.classify_intent(user_input, project_context)
        
        # 3. Analyze code context if relevant
        code_context = ""
        if intent.involves_code:
            code_context = await self.code_analyzer.analyze_project(project_dir, intent.focus_areas)
        
        # 4. Build intelligent prompt
        intelligent_prompt = self._build_intelligent_prompt(
            user_input, project_context, code_context, intent
        )
        
        # 5. Get AI response with enhanced context
        chat_history = self.context_manager.get_conversation_history()
        ai_response = await self.llm_client.generate_response(
            intelligent_prompt, chat_history, project_dir
        )
        
        # 6. Extract suggested actions
        suggested_actions = self._extract_suggested_actions(ai_response, intent)
        
        # 7. Update conversation context
        self.context_manager.add_conversation_turn(user_input, ai_response["content"])
        
        return ConversationResponse(
            response=ai_response["content"],
            suggested_actions=suggested_actions,
            context_updates={"intent": intent.intent_type, "confidence": intent.confidence},
            confidence=intent.confidence
        )
    
    def _build_intelligent_prompt(self, user_input: str, project_context: str, 
                                 code_context: str, intent) -> str:
        """Build an intelligent prompt with full context"""
        
        prompt_parts = [
            "🤖 Sei un assistente AI per sviluppo software intelligente come Cursor IDE.",
            "📁 CONTESTO PROGETTO:",
            project_context,
            ""
        ]
        
        if code_context:
            prompt_parts.extend([
                "💻 ANALISI CODICE:",
                code_context,
                ""
            ])
        
        prompt_parts.extend([
            f"🎯 INTENT RILEVATO: {intent.intent_type} (confidenza: {intent.confidence:.1%})",
            f"🗣️ RICHIESTA UTENTE: {user_input}",
            "",
            "📋 ISTRUZIONI:",
            "1. Analizza la richiesta nel contesto del progetto",
            "2. Fornisci una risposta intelligente e contestuale", 
            "3. Suggerisci azioni concrete e specifiche",
            "4. Usa i tool disponibili per implementare le soluzioni",
            "5. Spiega il ragionamento dietro le tue scelte",
            "",
            "⚡ Rispondi in modo conversazionale e intelligente:"
        ])
        
        return "\n".join(prompt_parts)
    
    def _extract_suggested_actions(self, ai_response: Dict[str, Any], intent) -> List[Dict[str, Any]]:
        """Extract actionable suggestions from AI response"""
        suggestions = []
        
        # Add function calls as suggestions
        for func_call in ai_response.get("function_calls", []):
            suggestions.append({
                "type": "tool_call",
                "tool": func_call["name"],
                "args": func_call["arguments"],
                "description": f"Esegui {func_call['name']}"
            })
        
        # Add contextual suggestions based on intent
        if intent.intent_type == "code_analysis":
            suggestions.extend([
                {
                    "type": "action",
                    "action": "run_tests", 
                    "description": "Esegui test per verificare il codice"
                },
                {
                    "type": "action",
                    "action": "lint_code",
                    "description": "Controlla qualità del codice"
                }
            ])
        
        elif intent.intent_type == "bug_fixing":
            suggestions.extend([
                {
                    "type": "action", 
                    "action": "git_diff",
                    "description": "Vedi le modifiche recenti"
                },
                {
                    "type": "action",
                    "action": "search_logs",
                    "description": "Cerca nei log per errori"
                }
            ])
        
        return suggestions
    
    async def execute_suggested_action(self, action: Dict[str, Any], project_dir: str) -> str:
        """Execute a suggested action"""
        if action["type"] == "tool_call":
            from tools import ToolExecutor
            executor = ToolExecutor()
            
            function_call = {
                "name": action["tool"],
                "arguments": action["args"]
            }
            
            return await executor.execute_tool(function_call, project_dir)
        
        # Handle other action types
        return f"⚡ Azione {action['action']} eseguita"
    
    def get_conversation_context(self) -> Dict[str, Any]:
        """Get current conversation context"""
        return {
            "project_summary": self.context_manager.get_project_summary(),
            "recent_actions": self.context_manager.get_recent_actions(),
            "conversation_history": self.context_manager.get_conversation_history()[-5:],
            "current_focus": self.context_manager.get_current_focus()
        }
    
    async def provide_smart_suggestions(self, project_dir: str) -> List[str]:
        """Provide smart suggestions based on project state"""
        project_context = await self.context_manager.update_project_context(project_dir)
        
        suggestions = []
        
        # Analyze project health
        if project_context.get("has_errors"):
            suggestions.append("🔧 Rilevo errori nel codice - vuoi che li analizzi?")
        
        if project_context.get("missing_tests"):
            suggestions.append("🧪 Mancano test - posso aiutarti a crearne?")
        
        if project_context.get("outdated_deps"):
            suggestions.append("📦 Dipendenze non aggiornate - vuoi aggiornarle?")
        
        if not project_context.get("has_documentation"):
            suggestions.append("📚 Manca documentazione - posso generarla automaticamente?")
        
        return suggestions 