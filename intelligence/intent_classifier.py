"""
Intent Classification for VibeCLI
Understands user intent from natural language input
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class IntentType(Enum):
    """Types of user intents"""
    CODE_ANALYSIS = "code_analysis"
    BUG_FIXING = "bug_fixing" 
    FEATURE_REQUEST = "feature_request"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    PROJECT_SETUP = "project_setup"
    PERFORMANCE = "performance"
    SECURITY = "security"
    GENERAL_QUERY = "general_query"


@dataclass
class Intent:
    """Classified intent result"""
    intent_type: str
    confidence: float
    involves_code: bool
    focus_areas: List[str]
    keywords: List[str]
    suggested_tools: List[str]


class IntentClassifier:
    """Classifies user intent from natural language"""
    
    def __init__(self):
        self.intent_patterns = {
            IntentType.CODE_ANALYSIS: {
                "keywords": [
                    "analizza", "analisi", "codice", "cosa fa", "come funziona", 
                    "comprendi", "spiega", "leggi", "esamina", "studia",
                    "metrics", "metriche", "complessità", "quality"
                ],
                "patterns": [
                    r"analizza.*codice",
                    r"cosa.*fa.*questo",
                    r"come.*funziona",
                    r"comprendi.*progetto",
                    r"spiega.*codice"
                ],
                "tools": ["analyze_code", "code_metrics", "read_file", "search_files"]
            },
            
            IntentType.BUG_FIXING: {
                "keywords": [
                    "errore", "bug", "problema", "non funziona", "crash",
                    "exception", "error", "traceback", "debug", "fix",
                    "risolvi", "correggi", "system error"
                ],
                "patterns": [
                    r"errore.*nel.*codice",
                    r"bug.*in",
                    r"non.*funziona",
                    r"problema.*con",
                    r"fix.*error"
                ],
                "tools": ["lint_code", "run_tests", "search_files", "git_diff"]
            },
            
            IntentType.FEATURE_REQUEST: {
                "keywords": [
                    "aggiungi", "crea", "implementa", "nuovo", "feature",
                    "funzionalità", "sviluppa", "costruisci", "build",
                    "add", "create", "implement"
                ],
                "patterns": [
                    r"aggiungi.*feature",
                    r"crea.*nuovo",
                    r"implementa.*funzione",
                    r"build.*new"
                ],
                "tools": ["create_file", "edit_file", "generate_code", "git_add"]
            },
            
            IntentType.REFACTORING: {
                "keywords": [
                    "refactor", "ristruttura", "migliora", "ottimizza",
                    "pulisci", "reorganizza", "clean", "improve",
                    "restructure", "modernize"
                ],
                "patterns": [
                    r"refactor.*codice",
                    r"migliora.*struttura",
                    r"ristruttura.*progetto",
                    r"clean.*up"
                ],
                "tools": ["format_code", "lint_code", "analyze_code", "edit_file"]
            },
            
            IntentType.TESTING: {
                "keywords": [
                    "test", "testing", "verifica", "check", "validate",
                    "unit test", "integration", "coverage", "pytest"
                ],
                "patterns": [
                    r"test.*codice",
                    r"verifica.*funzioni",
                    r"run.*tests",
                    r"coverage.*report"
                ],
                "tools": ["run_tests", "test_coverage", "create_test", "lint_code"]
            },
            
            IntentType.DOCUMENTATION: {
                "keywords": [
                    "documentazione", "docs", "readme", "comments",
                    "docstring", "documenta", "spiega", "description"
                ],
                "patterns": [
                    r"genera.*documentazione",
                    r"aggiungi.*commenti",
                    r"create.*docs",
                    r"documenta.*codice"
                ],
                "tools": ["generate_docs", "add_docstrings", "create_readme"]
            },
            
            IntentType.PROJECT_SETUP: {
                "keywords": [
                    "setup", "inizializza", "configura", "install",
                    "dependencies", "requirements", "package", "init"
                ],
                "patterns": [
                    r"setup.*progetto",
                    r"inizializza.*ambiente",
                    r"install.*dependencies",
                    r"configure.*project"
                ],
                "tools": ["install_package", "create_venv", "generate_requirements"]
            },
            
            IntentType.PERFORMANCE: {
                "keywords": [
                    "performance", "ottimizza", "velocità", "lento",
                    "profiling", "benchmark", "memory", "cpu"
                ],
                "patterns": [
                    r"ottimizza.*performance",
                    r"migliora.*velocità",
                    r"profile.*code",
                    r"memory.*usage"
                ],
                "tools": ["profile_code", "benchmark", "analyze_performance"]
            },
            
            IntentType.SECURITY: {
                "keywords": [
                    "security", "sicurezza", "vulnerabilità", "exploit",
                    "audit", "scan", "authentication", "authorization"
                ],
                "patterns": [
                    r"security.*audit",
                    r"scan.*vulnerabilità",
                    r"check.*security",
                    r"auth.*implementation"
                ],
                "tools": ["security_scan", "audit_dependencies", "check_vulns"]
            }
        }
    
    async def classify_intent(self, user_input: str, project_context: str = "") -> Intent:
        """Classify user intent from input"""
        user_input_lower = user_input.lower()
        
        # Score each intent type
        intent_scores = {}
        
        for intent_type, config in self.intent_patterns.items():
            score = 0
            matched_keywords = []
            
            # Check keywords
            for keyword in config["keywords"]:
                if keyword.lower() in user_input_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            # Check patterns
            for pattern in config["patterns"]:
                if re.search(pattern, user_input_lower):
                    score += 2  # Patterns weight more than keywords
            
            # Context boost
            if project_context:
                context_boost = self._calculate_context_boost(
                    intent_type, user_input_lower, project_context.lower()
                )
                score += context_boost
            
            if score > 0:
                intent_scores[intent_type] = {
                    "score": score,
                    "keywords": matched_keywords,
                    "tools": config["tools"]
                }
        
        # Determine best intent
        if not intent_scores:
            return Intent(
                intent_type=IntentType.GENERAL_QUERY.value,
                confidence=0.3,
                involves_code=False,
                focus_areas=[],
                keywords=[],
                suggested_tools=["search_files", "read_file"]
            )
        
        best_intent = max(intent_scores.items(), key=lambda x: x[1]["score"])
        intent_type, intent_data = best_intent
        
        # Calculate confidence
        total_score = sum(data["score"] for data in intent_scores.values())
        confidence = intent_data["score"] / total_score if total_score > 0 else 0.3
        
        # Determine if involves code
        involves_code = intent_type != IntentType.GENERAL_QUERY
        
        # Extract focus areas
        focus_areas = self._extract_focus_areas(user_input_lower)
        
        return Intent(
            intent_type=intent_type.value,
            confidence=min(confidence, 0.95),  # Cap confidence at 95%
            involves_code=involves_code,
            focus_areas=focus_areas,
            keywords=intent_data["keywords"],
            suggested_tools=intent_data["tools"]
        )
    
    def _calculate_context_boost(self, intent_type: IntentType, user_input: str, 
                               project_context: str) -> float:
        """Calculate context boost for intent scoring"""
        boost = 0
        
        # Check if project context supports the intent
        if intent_type == IntentType.BUG_FIXING:
            if any(word in project_context for word in ["error", "exception", "failed"]):
                boost += 1
        
        elif intent_type == IntentType.TESTING:
            if any(word in project_context for word in ["test", "pytest", "unittest"]):
                boost += 1
        
        elif intent_type == IntentType.PERFORMANCE:
            if any(word in project_context for word in ["slow", "performance", "memory"]):
                boost += 1
        
        # File extension context
        if ".py" in user_input and intent_type in [
            IntentType.CODE_ANALYSIS, IntentType.REFACTORING, IntentType.BUG_FIXING
        ]:
            boost += 0.5
        
        return boost
    
    def _extract_focus_areas(self, user_input: str) -> List[str]:
        """Extract specific areas of focus from user input"""
        focus_areas = []
        
        # File patterns
        file_patterns = re.findall(r'[\w/]+\.[\w]+', user_input)
        focus_areas.extend(file_patterns)
        
        # Function/class names (capitalized words)
        entities = re.findall(r'\b[A-Z][a-zA-Z]*\b', user_input)
        focus_areas.extend(entities)
        
        # Technology keywords
        tech_keywords = [
            "python", "javascript", "react", "django", "flask",
            "api", "database", "sql", "json", "xml", "html", "css"
        ]
        
        for keyword in tech_keywords:
            if keyword in user_input:
                focus_areas.append(keyword)
        
        return list(set(focus_areas))  # Remove duplicates
    
    def get_intent_suggestions(self, intent_type: str) -> List[str]:
        """Get suggestions based on intent type"""
        suggestions = {
            IntentType.CODE_ANALYSIS.value: [
                "Posso analizzare la struttura del codice",
                "Vuoi che generi metriche di qualità?",
                "Posso spiegare come funziona una specifica funzione"
            ],
            
            IntentType.BUG_FIXING.value: [
                "Analizziamo gli errori nel codice",
                "Controlliamo i log per tracce di errori",
                "Eseguiamo i test per identificare problemi"
            ],
            
            IntentType.FEATURE_REQUEST.value: [
                "Posso aiutarti a progettare la nuova feature",
                "Generiamo il codice scheletro",
                "Aggiungiamo test per la nuova funzionalità"
            ],
            
            IntentType.REFACTORING.value: [
                "Identifichiamo codice duplicato",
                "Miglioriamo la struttura delle classi",
                "Ottimizziamo le performance"
            ]
        }
        
        return suggestions.get(intent_type, [
            "Come posso aiutarti con questo progetto?",
            "Fammi sapere cosa vorresti fare",
            "Posso analizzare il codice se vuoi"
        ]) 