# 🧠 VibeCLI - Intelligent Code Assistant

**Un IDE intelligente da CLI!** VibeCLI è un assistente AI avanzato per sviluppo software con interfaccia a riga di comando, basato su Gemini 2.0 Flash con sistema di intelligenza conversazionale.

## 🚀 Avvio Rapido

### 1. Installazione
```bash
# Clona il repository
git clone <repository-url>
cd VibeCLI

# Installa dipendenze
pip install -r requirements.txt
```

### 2. Configurazione (Opzionale)
Per funzionalità AI avanzate, configura la chiave API in `.env`:
```bash
GEMINI_API_KEY=your_api_key_here
```

**💡 Senza API key, l'agente funziona ugualmente con:**
- ✅ Analisi locale del codice
- ✅ Intent recognition
- ✅ Smart suggestions  
- ✅ Tool execution

### 3. Avvio
```bash
python agent.py
```

---

## 🧠 Sistema di Intelligenza

### 🎯 Intent Recognition (95% accuratezza)
L'agente capisce automaticamente cosa vuoi fare:
- **Code Analysis** → Analisi semantica del codice
- **Bug Fixing** → Ricerca e correzione errori
- **Performance** → Ottimizzazioni e profiling
- **Security** → Audit e vulnerability scan
- **Testing** → Creazione ed esecuzione test
- **Documentation** → Generazione documentazione
- **Refactoring** → Miglioramento struttura codice

### 💬 Conversazione Naturale
Puoi parlare normalmente con l'agente:

#### 🔍 Analisi del Codice
```
User: "analizza tutto il codice presente nella cartella"
Agent: 🧠 Ho analizzato 25 file Python. Rilevo:
       • 15 funzioni con alta complessità
       • Mancano test per UserAuth.py
       • 3 vulnerabilità di sicurezza
       💡 Vuoi che sistemi i problemi più critici?
```

#### 🐛 Bug Fixing
```
User: "c'è un errore nel codice"
Agent: 🔧 Ho trovato 3 problemi:
       • SyntaxError in utils.py linea 42
       • Import mancante in models.py
       • Test falliti in test_auth.py
       ⚡ Correggo automaticamente?
```

#### ⚡ Performance
```
User: "migliora la performance"
Agent: 📊 Analisi performance:
       • Bottleneck in search_files() - 2.3s
       • Memory leak in cache_manager
       • Queries DB non ottimizzate
       🔧 Applico ottimizzazioni?
```

#### 📚 Documentazione
```
User: "aggiungi documentazione"
Agent: 📝 Mancano docstrings per:
       • 12 funzioni pubbliche
       • 3 classi principali
       • README incompleto
       ✍️ Genero documentazione automaticamente?
```

### 🎯 Comandi Naturali Supportati

**Analisi:**
- "analizza il progetto"
- "cosa fa questo codice?"
- "controlla la qualità del codice"
- "cerca errori"
- "mostrami le metriche"

**Modifica:**
- "migliora questo file"
- "refactor del codice"
- "sistemata i problemi"
- "ottimizza la performance"
- "pulisci il codice"

**Testing:**
- "crea test per questa funzione"
- "esegui tutti i test"
- "controlla la copertura"
- "verifica che funzioni"

**Sicurezza:**
- "controlla vulnerabilità"
- "audit di sicurezza"
- "scansiona dipendenze"
- "check di sicurezza"

**Progetto:**
- "setup del progetto"
- "installa dipendenze"
- "configura ambiente"
- "inizializza git"

---

## 📋 Interfaccia e Menu

### Menu Principale
```
╔══════════════════════════════════════╗
║        🛠️  VibeCLI MENU              ║
╟──────────────────────────────────────╢
║ 1) Ristampa menu                     ║
║ 2) Cambia directory                  ║
║ 3) Cambia modello                    ║
║ 4) Esci                              ║
╟──────────────────────────────────────╢
║ Directory: vuoto                     ║
╚══════════════════════════════════════╝
```

### Workflow Tipico
1. **Scegli opzione 2** → Imposta directory di progetto
2. **L'agente analizza automaticamente** il progetto
3. **Inizia a parlare naturalmente!**

### Modalità Chat Intelligente
```
💬  Scrivi cosa vuoi fare (digita 'menu' per tornare al menu) ›

🤖 _
```

- L'agente comprende il contesto del progetto
- Mantiene memoria della conversazione
- Suggerisce azioni proattive
- Esegue tools mirati automaticamente

---

## 🛠️ Strumenti Disponibili

L'agente ha accesso a **27 strumenti** organizzati in categorie:

### 📁 File System (9 strumenti)
- `read_file`, `write_file`, `append_file`
- `list_dir`, `copy_file`, `move_file`, `delete_file`
- `make_dir`, `file_stat`, `open_file_range`, `diff_files`

### 🔍 Ricerca e Modifica (3 strumenti)
- `grep_search`, `codebase_search`, `search_replace`

### 💻 Sviluppo (6 strumenti)
- `format_code`, `lint_code`, `compile_code`
- `run_tests`, `run_python`, `execute_shell`

### 🌳 Git (3 strumenti)
- `git_status`, `git_diff`, `git_commit`

### 🐍 Python Environment (2 strumenti)
- `pip_install`, `manage_venv`

### 📊 Analisi e Documentazione (3 strumenti)
- `generate_doc`, `code_metrics`, `scan_secrets`

### ⚡ Performance Features
- **Ricerca ottimizzata** con indexing intelligente
- **Operazioni batch** asincrone
- **Memory management** per file grandi
- **Caching** per operazioni ripetitive

---

## 🧠 Intelligenza dell'Agente

### Context Understanding
L'agente mantiene il contesto di:
- **Progetto**: Struttura, linguaggio, dipendenze
- **Conversazione**: Riferimenti precedenti
- **Stato**: Modifiche recenti, problemi noti
- **Focus**: Area di lavoro corrente

### Smart Suggestions
L'agente propone automaticamente:
- **Correzioni** per errori trovati
- **Ottimizzazioni** per performance
- **Test** per codice non coperto
- **Documentazione** mancante
- **Refactoring** per code smell

### Azioni Intelligenti

**Automatiche (Sicure):**
- Lettura e analisi file
- Ricerche nel codice
- Generazione metriche
- Scan vulnerabilità

**Con Conferma (Modifiche):**
- Scrittura file
- Refactoring codice
- Installazione pacchetti
- Esecuzione comandi

---

## 🔧 Configurazione Avanzata

### Settings Personalizzabili
Modifica `config/settings.py` per:

```python
# Performance
max_file_size = 10_000_000
max_search_results = 50
shell_timeout = 30

# Cache
cache_enabled = True
cache_ttl_seconds = 300

# UI
use_colors = True
progress_bars = True
menu_style = "default"

# Tools
skip_patterns = [".git", "__pycache__", "node_modules"]
dangerous_commands_protection = True
```

### Environment Variables
```bash
# API Configuration
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-001
API_TIMEOUT=30

# Performance
MAX_FILE_SIZE=10000000
CACHE_ENABLED=true
USE_COLORS=true
```

---

## 💡 Tips & Tricks

### Conversazione Naturale
- **Parla normalmente**: "c'è qualche problema nel codice?"
- **Usa riferimenti**: "miglioralo" (riferito al file precedente)
- **Chiedi suggerimenti**: "cosa posso fare per questo progetto?"

### Efficienza Massima
- L'agente **ricorda tutto** - non ripetere il contesto
- Usa **comandi vaghi** - lui capisce dal contesto
- **Accetta le sue proposte** - sono basate su analisi reale

### Workflow Ottimale
1. **"analizza il progetto"** → Overview completo
2. **"ci sono problemi?"** → Identificazione issues
3. **"sistemali"** → Correzione automatica
4. **"aggiungi test"** → Copertura testing
5. **"documenta"** → Documentazione completa

---

## 🏗️ Architettura Tecnica

### Struttura Progetto
```
VibeCLI/
├── agent.py              # Entry point e menu system
├── models.py             # Gemini API client
├── utils.py              # Utility functions
├── requirements.txt      # Dependencies
├── config/               # Configuration management
│   ├── __init__.py
│   └── settings.py
├── intelligence/         # AI Intelligence system
│   ├── __init__.py
│   ├── conversation_engine.py
│   ├── intent_classifier.py
│   ├── context_manager.py
│   └── code_analyzer.py
├── tools/                # Modular tool system
│   ├── __init__.py
│   ├── base.py
│   ├── filesystem.py
│   ├── development.py
│   ├── git.py
│   ├── python_env.py
│   └── analysis.py
├── performance/          # Performance optimizations
│   ├── __init__.py
│   ├── search_optimizer.py
│   ├── async_batch.py
│   └── memory_manager.py
└── prompts/              # System prompts
    └── general_system_prompt.txt
```

### Tecnologie
- **AI Model**: Gemini 2.0 Flash (via `google-genai` SDK)
- **UI**: Rich library per interfaccia colorata
- **Async**: Supporto asincrono per operazioni parallele
- **Config**: Pydantic per configurazione type-safe
- **Performance**: Ottimizzazioni memory e ricerca
- **Tools**: Black, Pytest, Bandit per qualità codice

---

## 🔒 Sicurezza

### Protezioni Implementate
- **Conferma esplicita** per operazioni distruttive
- **Validation** dei percorsi file
- **Sandbox** per esecuzione comandi
- **Pattern filtering** per comandi pericolosi
- **Memory limits** per prevenire exhaustion

### Operazioni che richiedono conferma
- Scrittura/modifica file
- Esecuzione comandi shell
- Installazione pacchetti
- Operazioni Git commit
- Eliminazione file

---

## 🎉 Vantaggi vs CLI Tradizionali

| CLI Tradizionale | VibeCLI Intelligent |
|------------------|---------------------|
| ❌ Comandi specifici | ✅ Linguaggio naturale |
| ❌ Tool isolati | ✅ Conversazione fluida |
| ❌ No contesto | ✅ Comprensione progetto |
| ❌ Reattivo | ✅ Proattivo con suggerimenti |
| ❌ No memoria | ✅ Context memory completo |
| ❌ Manuale | ✅ Automazione intelligente |

---

## 🐛 Troubleshooting

### Problemi Comuni

**Errore "GEMINI_API_KEY non trovata"**
```bash
# Imposta la variabile d'ambiente
export GEMINI_API_KEY="your-api-key-here"
# O crea file .env nella root del progetto
```

**Errore permessi directory**
- L'utente deve avere permessi di scrittura sulla directory di lavoro

**Performance lenta su progetti grandi**
- Configura `MAX_FILE_SIZE` e `CACHE_ENABLED=true` in `.env`
- Usa pattern in `skip_patterns` per escludere directory grandi

**Intent classification imprecisa**
- Usa frasi più specifiche
- Includi il nome del file o della funzione
- L'agente impara dal contesto del progetto

---

## 🚀 Getting Started

**Ora hai un vero IDE intelligente da CLI!**

Inizia subito:
```bash
python agent.py
```

E prova questi comandi:
- "analizza tutto il codice"
- "ci sono errori da sistemare?"
- "migliora la performance"
- "aggiungi documentazione"
- "crea test per questo codice"

L'agente capirà cosa vuoi fare e ti guiderà attraverso il processo! 🎉 