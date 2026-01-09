# Local CLI - TUI Guide

## 🎨 Interfaccia Grafica Completa

L'applicazione ora ha una **TUI (Terminal User Interface)** completa e navigabile, costruita con **Ink (React per terminale)**.

## 🚀 Come Lanciare

```bash
# Build del progetto
npm run build

# Lancia la TUI (automatico se nessun argomento)
node dist/cli.js
# oppure
npm start
```

## 📱 Funzionalità TUI

### 1. **Onboarding Automatico**
- Se non hai modelli installati, verrai guidato automaticamente
- Ricerca modelli da Hugging Face
- Download integrato con progress
- Setup automatico del primo modello

### 2. **Main Menu Navigabile**
Menu principale con 6 opzioni:

- **💬 [1] Chat** - Chat interattiva con LLM
- **🤖 [2] Models** - Gestione modelli
- **📋 [3] Tasks** - Task schedulati
- **⚙️ [4] Config** - Configurazione
- **🖥️ [5] Server** - Status server
- **🚪 [q] Exit** - Uscita

**Navigazione:**
- `↑/↓` - Muoversi tra opzioni
- `1-5, q` - Selezione diretta
- `Enter` - Conferma selezione

### 3. **💬 Chat View**
Interfaccia chat completa:

- **Streaming real-time** delle risposte LLM
- **Comandi slash** integrati (`/help`, `/clear`, `/model`, etc.)
- **Storia conversazione** persistente
- **Auto-start server** quando entri in chat

**Shortcuts:**
- `ESC` - Torna al menu
- `Enter` - Invia messaggio

**Comandi Slash Disponibili:**
```
/help     - Mostra comandi disponibili
/clear    - Pulisci chat
/model    - Info modello corrente
/config   - Mostra configurazione
/tasks    - Lista task
/server   - Status server
/exit     - Esci dall'app
```

### 4. **🤖 Model Manager**
Gestione completa modelli dalla TUI:

**Funzionalità:**
- **Lista modelli** installati con indicatori:
  - ⭐ Default model
  - 💾 Local model (non da Hugging Face)
- **Ricerca modelli** da Hugging Face
- **Download integrato** con progress
- **Load modelli locali** già scaricati (NEW!)
- **Scan automatico** directories comuni (Downloads, Documents)
- **Input manuale path** per modelli custom
- **Rimozione modelli** (file + registry)
- **Set default** model

**Navigazione:**
- `↑/↓` - Naviga tra modelli
- `[i]` - Installa da Hugging Face
- `[l]` - Load local model (scan automatico)
- `[p]` - Enter path manuale
- `[d]` - Set modello come default
- `[r]` - Rimuovi modello
- `ESC` - Torna indietro

**Flow Install da HF:**
1. Premi `[i]` per cercare
2. Digita nome modello (es: "llama", "mistral")
3. Seleziona da risultati
4. Conferma download (automatico download del file più piccolo)
5. Attendi completamento

**Flow Load Local:**
1. Premi `[l]` - scansiona Downloads, Documents, current dir
2. Se trovati: seleziona con frecce, Enter per aggiungere
3. Se non trovati: premi `[p]` per path manuale
4. Oppure premi direttamente `[p]` per saltare scan
5. Digita path completo: `C:\path\to\model.gguf`
6. Enter - modello aggiunto al registry!

### 5. **📋 Tasks View**
Vista task schedulati:

- Lista tutti i task configurati
- Mostra tipo, schedule, ultima esecuzione
- Numero runs per task

**Nota:** Creazione task ancora via CLI:
```bash
local task create
local task run <name>
```

### 6. **⚙️ Config View**
Visualizza configurazione corrente:

- Default model
- Server port
- Context size
- GPU layers
- Idle timeout
- llama-server path (se custom)

**Nota:** Modifica config ancora via file diretto o CLI

### 7. **🖥️ Server View**
Monitoraggio server real-time:

- **Status** (Running/Stopped)
- **PID, Port, URL**
- **Modello caricato**
- **Data avvio**
- **Ultimi 10 log** del server
- **Auto-refresh** ogni 2 secondi

## ⌨️ Shortcuts Globali

- **Ctrl+Q** - Quit application (ovunque)
- **ESC** - Torna indietro/chiudi view
- **↑/↓** - Navigazione liste
- **Enter** - Conferma
- **[lettere]** - Azioni rapide (context-dependent)

## 🎯 Flow Tipico d'Uso

### Primo Avvio (Nessun Modello)
```
1. Lancia `local`
2. Onboarding automatico → scegli [1] HF o [2] Local
3a. Se [1]: cerca modello → seleziona → download automatico
3b. Se [2]: digita path del tuo .gguf → aggiunto!
4. Premi Enter → vai al Main Menu
5. Premi [1] → entra in Chat
6. Scrivi messaggio → chat con LLM!
```

### Uso Normale
```
1. Lancia `local`
2. Main Menu → scegli azione
3. [1] Chat → conversa
4. [2] Models → gestisci modelli
5. [5] Server → monitora status
6. ESC → torna sempre indietro
7. Ctrl+Q → esci
```

## 🔧 Troubleshooting

### Server non parte in Chat
- Vai in Server View ([5]) e controlla i log
- Verifica che llama-server sia in PATH
- Controlla config con Config View ([4])

### Download modello fallisce
- Verifica connessione internet
- Prova con `HF_TOKEN` environment variable se rate-limited
- Riprova con modello più piccolo

### TUI non si vede bene
- Usa terminale con supporto colori (Windows Terminal, iTerm2, etc.)
- Ingrandisci finestra terminale
- Supporto emoji richiesto

## 📦 Comandi CLI Ancora Disponibili

La TUI non sostituisce tutti i comandi CLI. Alcuni sono ancora disponibili:

```bash
# Chat/Code da CLI (senza TUI)
local chat
local code

# Model management da CLI
local model search <query>
local model install <repoId>
local model list
local model remove <id>
local model set-default <id>

# Task management
local task create
local task list
local task run <name>
local task tick

# Server management
local server start
local server stop
local server status

# Diagnostics
local doctor
```

## 🆕 Cosa Cambia

**Prima:**
```bash
# Devi installare modelli via CLI
local model search llama
local model install bartowski/Meta-Llama-3.1-8B-Instruct-GGUF

# Poi lanciare chat
local chat
```

**Ora:**
```bash
# Solo un comando!
local

# → Onboarding automatico se nessun modello
# → Download integrato
# → Chat direttamente dalla TUI
# → Tutto navigabile con keyboard
```

## 🎨 Feature Highlights

✅ **Onboarding** automatico per nuovi utenti
✅ **Download modelli** integrato nella TUI
✅ **Load modelli locali** - usa i tuoi .gguf già scaricati! 🆕
✅ **Scan automatico** - trova .gguf in Downloads/Documents 🆕
✅ **Chat streaming** real-time
✅ **Comandi slash** stile Discord/Slack
✅ **Gestione completa** modelli (install/remove/set default)
✅ **Monitoring server** con auto-refresh
✅ **Navigazione keyboard** completa
✅ **View multiple** (Chat, Models, Tasks, Config, Server)
✅ **Shortcuts** intuitivi (ESC torna indietro, Ctrl+Q quit)
✅ **Error handling** visuale (messaggi errore in rosso)
✅ **Status indicators** (🟢 server ready, ⭐ default, 💾 local)

## 🚀 Prossimi Step

Vedi `TODO.md` per lista completa delle migliorie pianificate:
- SHA256 verification download
- Context overflow protection
- Path traversal validation robusta
- Diff parsing sicuro
- ...e altro!
