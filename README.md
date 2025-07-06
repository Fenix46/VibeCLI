# VibeCli Agent

Un assistente AI per sviluppo software con interfaccia a riga di comando, ora migrato al nuovo SDK `google-genai`.

## 🚀 Avvio Rapido

### 1. Installazione Dipendenze
```bash
pip install -r requirements.txt
```

### 2. Configurazione API Key
Imposta la variabile d'ambiente per l'API di Gemini:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 3. Avvio
```bash
python3 agent.py
```

## 📋 Funzionalità Menu

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

### Opzioni Menu

**1) Ristampa menu** - Aggiorna la visualizzazione del menu

**2) Cambia directory** - Imposta la directory di lavoro
- Richiede il percorso della directory
- Se la directory non esiste, chiede se crearla
- Verifica i permessi di scrittura
- **Avvia automaticamente la chat** dopo aver impostato la directory

**3) Cambia modello** - Funzionalità non ancora disponibile

**4) Esci** - Chiude l'applicazione

## 💬 Chat Mode

Una volta impostata una directory di lavoro, il sistema passa automaticamente alla modalità chat:

```
💬  Inserisci il tuo comando (digita 'menu' per tornare al menu) ›

🤖 _
```

### Comandi Chat
- Digita qualsiasi comando o richiesta per l'AI
- Scrivi `menu` per tornare al menu principale
- Usa `Ctrl+C` per tornare al menu principale

## 🛠️ Strumenti Disponibili

L'AI ha accesso a **27 strumenti** per aiutarti nello sviluppo:

### File System (6 strumenti)
- `read_file`, `write_file`, `append_file`
- `list_dir`, `copy_file`, `move_file`, `delete_file`
- `make_dir`, `file_stat`

### Ricerca e Modifica (4 strumenti)
- `grep_search`, `codebase_search`
- `search_replace`, `open_file_range`, `diff_files`

### Sviluppo (5 strumenti)
- `format_code`, `lint_code`, `compile_code`
- `run_tests`, `run_python`

### Git (3 strumenti)
- `git_status`, `git_diff`, `git_commit`

### Python Environment (2 strumenti)
- `pip_install`, `manage_venv`

### Documentazione e Analisi (3 strumenti)
- `generate_doc`, `code_metrics`, `scan_secrets`

### Shell (1 strumento)
- `execute_shell`

## 🔒 Sicurezza

Gli strumenti distruttivi richiedono conferma esplicita:
- Scrittura/modifica file
- Esecuzione comandi shell
- Installazione pacchetti
- Operazioni Git
- Eliminazione file

## 🔧 Tecnologie

- **AI Model**: Gemini 2.0 Flash (tramite `google-genai` SDK)
- **UI**: Rich library per interfaccia colorata
- **Async**: Supporto asincrono per operazioni parallele
- **Tools**: Black, Ruff, Pytest, Bandit per sviluppo

## 📁 Struttura Progetto

```
CLI-IDE/
├── agent.py           # Menu principale e chat loop
├── models.py          # Client Gemini API
├── tools.py           # Implementazione strumenti
├── utils.py           # Funzioni utility
├── requirements.txt   # Dipendenze Python
└── prompts/          # Prompt di sistema
```

## 🐛 Troubleshooting

### Errore "GEMINI_API_KEY non trovata"
Assicurati di aver impostato la variabile d'ambiente:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### Errore permessi directory
L'utente deve avere permessi di scrittura sulla directory di lavoro.

### Problemi di importazione
Verifica che tutte le dipendenze siano installate:
```bash
pip install -r requirements.txt
``` 