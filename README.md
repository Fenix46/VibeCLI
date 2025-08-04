# VibeCli 🤖

Un agente AI avanzato che vive nel tuo terminale, progettato per aiutarti attivamente con i tuoi progetti di sviluppo.

## ✨ Caratteristiche Principali

- **🚀 Streaming in Tempo Reale**: Risposte AI con streaming per feedback immediato
- **🛠️ Function Calling**: Esecuzione automatica di operazioni su file, Git e shell
- **⚙️ Setup Interattivo**: Configurazione guidata per API keys (OpenAI, Anthropic, Google)
- **🧠 Context Locale**: Memoria persistente del progetto per conversazioni contestuali
- **🔧 Tool Integration**: Operazioni reali su file, Git, e comandi shell
- **🌐 Multi-Provider**: Supporto flessibile per diversi provider AI
- **💻 Interfaccia CLI**: Comandi intuitivi e facili da usare
- **📝 Prompt Avanzati**: Sistema di prompt ottimizzato per sviluppatori

## 📦 Installazione

### Installazione Globale (Consigliata)
```bash
# Installa VibeCli globalmente da npm
npm install -g @vibecli/core

# Verifica l'installazione
vibe --version
```

### Installazione da Sorgente
```bash
# Clona il repository
git clone https://github.com/yourusername/vibecli.git
cd vibecli

# Installa le dipendenze
npm install

# Compila il progetto
npm run build

# Installa globalmente
npm install -g .
```

### Installazione con npx (Uso Temporaneo)
```bash
# Usa VibeCli senza installazione permanente
npx @vibecli/core setup
npx @vibecli/core chat
```

## Setup Iniziale

Prima di utilizzare VibeCli, esegui il setup per configurare il tuo provider AI:

```bash
vibe setup
```

Il wizard ti guiderà attraverso:
1. Selezione del provider AI (OpenAI, Anthropic, Google)
2. Inserimento della API key
3. Scelta del modello AI
4. Validazione della configurazione

## Utilizzo

### Chat Interattivo
```bash
# Avvia una sessione di chat interattiva
vibe chat

# Invia un singolo messaggio
vibe chat -m "Aiutami a creare un componente React"
```

### Gestione Context
```bash
# Mostra il context del progetto
vibe context --show

# Pulisci la cronologia messaggi
vibe context --clear

# Reset completo del context
vibe context --reset
```

### Tools Disponibili
```bash
# Lista tutti i tool disponibili
vibe tools --list

# Mostra help sui tool
vibe tools
```

## Struttura del Progetto

```
VibeCli/
├── src/
│   ├── cli/           # Comandi CLI
│   │   ├── setup.ts   # Wizard di setup
│   │   ├── chat.ts    # Gestione chat
│   │   ├── context.ts # Gestione context
│   │   └── tools.ts   # Gestione tools
│   ├── core/          # Logica principale
│   │   ├── config.ts  # Gestione configurazione
│   │   └── context.ts # Gestione memoria locale
│   ├── providers/     # Integrazioni AI
│   │   ├── ai-provider.ts # Provider unificato
│   │   └── validator.ts   # Validazione API keys
│   └── tools/         # Tool integrati
│       ├── file-tools.ts  # Operazioni file
│       ├── git-tools.ts   # Operazioni Git
│       └── shell-tools.ts # Comandi shell
├── bin/vibe           # Eseguibile principale
└── package.json
```

## Context Locale

VibeCli crea un context locale in ogni progetto nella cartella `.vibe/`:

- **Memoria Conversazioni**: Mantiene la cronologia delle chat
- **File Tracking**: Tiene traccia dei file importanti del progetto
- **Git Integration**: Informazioni su branch e commit
- **Project Metadata**: Informazioni generali del progetto

## Tool Integrati

### File Operations
- Lettura e scrittura file
- Navigazione directory
- Ricerca nel codice
- Operazioni filesystem

### Git Operations
- Status e diff
- Branch management
- Commit e push/pull
- Log e cronologia

### Shell Commands
- Esecuzione comandi
- Gestione processi
- Variabili ambiente
- Informazioni sistema

## Esempi di Utilizzo

```bash
# Setup iniziale
vibe setup

# Chat per aiuto con codice
vibe chat
> "Aiutami a creare un API endpoint in Express.js"

# Operazioni Git tramite chat
vibe chat -m "Mostra lo status git e crea un nuovo branch feature/auth"

# Gestione file tramite chat
vibe chat -m "Leggi il package.json e suggerisci miglioramenti"

# Verifica context del progetto
vibe context --show
```

## Configurazione

La configurazione globale viene salvata in `~/.vibe/config.json`.
Il context del progetto viene salvato in `.vibe/` nella directory del progetto.

## Sviluppo

```bash
# Modalità sviluppo
npm run dev

# Build
npm run build

# Watch mode
npm run watch
```

## Requisiti

- Node.js >= 16.0.0
- NPM o Yarn
- API key per almeno uno dei provider supportati

## Provider Supportati

- **OpenAI**: GPT-4, GPT-3.5 Turbo
- **Anthropic**: Claude 3 (Opus, Sonnet, Haiku)
- **Google**: Gemini Pro, Gemini Pro Vision

## Licenza

MIT License
