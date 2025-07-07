"""
Intelligence package for VibeCLI
Provides conversational AI, context understanding, and smart code analysis
"""

from .conversation_engine import ConversationEngine
from .code_analyzer import SmartCodeAnalyzer  
from .context_manager import ContextManager
from .intent_classifier import IntentClassifier

__all__ = [
    "ConversationEngine", 
    "SmartCodeAnalyzer", 
    "ContextManager", 
    "IntentClassifier"
] 