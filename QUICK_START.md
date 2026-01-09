# Quick Start - Local CLI

## 🚀 Avvio Rapido

### Scenario 1: Hai già un modello .gguf scaricato

```bash
# 1. Build del progetto
npm run build

# 2. Lancia Local CLI
node dist/cli.js

# 3. Al primo avvio vedrai:
#    🎉 Welcome to Local CLI!
#    Press Enter to continue

# 4. Scegli opzione [2] Use a local .gguf file

# 5. Inserisci il path del tuo modello:
#    📁 C:\Users\tuonome\Downloads\llama-3.2-3b-instruct-q4_k_m.gguf

# 6. Fatto! Il modello è registrato e pronto

# 7. Dal Main Menu premi [1] per Chat
```

### Scenario 2: Vuoi scaricare un modello

```bash
# 1-2. Come sopra

# 3. Scegli opzione [1] Download from Hugging Face

# 4. Cerca modello:
#    🔍 llama

# 5. Seleziona con frecce, Enter per scaricare

# 6. Aspetta download... (può richiedere minuti)

# 7. Premi [1] per Chat
```

### Scenario 3: Hai già modelli e vuoi chattare

```bash
node dist/cli.js

# Main Menu appare subito
# Premi [1] → Chat si apre immediatamente
# Scrivi e chatta!
```

## 📁 Dove mettere i modelli?

I modelli locali possono stare ovunque, ma lo scanner automatico cerca in:

- `~/Downloads/` (Windows: `C:\Users\tuonome\Downloads\`)
- `~/Documents/` (Windows: `C:\Users\tuonome\Documents\`)
- Directory corrente da cui lanci il CLI

### Esempio percorsi comuni:

**Windows:**
```
C:\Users\emanuele\Downloads\llama-3.2-3b-instruct-q4_k_m.gguf
C:\Users\emanuele\Documents\models\mistral-7b-q5_k_m.gguf
C:\AI\models\qwen-2.5-7b-q4_k_m.gguf
```

**macOS/Linux:**
```
/Users/emanuele/Downloads/llama-3.2-3b-instruct-q4_k_m.gguf
/Users/emanuele/Documents/models/mistral-7b-q5_k_m.gguf
/home/emanuele/models/qwen-2.5-7b-q4_k_m.gguf
```

## 🤖 Gestione Modelli dalla TUI

### Aggiungere un modello locale:

```
1. Main Menu → [2] Models
2. Premi [l] per load local
3. Se il file è in Downloads/Documents/current:
   - Vedrai lista automaticamente
   - Seleziona con frecce + Enter
4. Se non viene trovato:
   - Premi [p] per path manuale
   - Incolla path completo
   - Enter
```

### Cambiare modello default:

```
1. Models → lista modelli (⭐ indica default)
2. Usa frecce per selezionare altro modello
3. Premi [d] → diventa default
4. Torna a Chat → userà nuovo modello
```

### Rimuovere un modello:

```
1. Models → seleziona con frecce
2. Premi [r] → conferma
3. Modello rimosso da registry
   (file NON cancellato se è local esterno)
```

## 💬 Usare la Chat

### Comandi Slash disponibili:

```
/help      - Mostra tutti i comandi
/clear     - Pulisci cronologia chat
/model     - Info modello corrente
/config    - Mostra configurazione
/tasks     - Lista task schedulati
/server    - Status server + URL
/exit      - Esci
```

### Shortcuts Chat:

- `Enter` - Invia messaggio
- `ESC` - Torna al Main Menu
- `Ctrl+Q` - Quit app

## 🔧 Configurazione Manuale

Se vuoi modificare configurazione avanzata:

**File config:**
- Windows: `%APPDATA%\local\config.json`
- macOS: `~/Library/Application Support/local/config.json`
- Linux: `~/.config/local/config.json`

**Esempio config.json:**
```json
{
  "defaultModelId": "local-llama-3.2-3b-instruct-q4_k_m",
  "serverPort": 60315,
  "ctxSize": 8192,
  "gpuLayers": 0,
  "idleTimeoutMinutes": 60,
  "llamaServerPath": null
}
```

**Parametri:**
- `serverPort` - Porta llama-server (default: 60315)
- `ctxSize` - Context window size in tokens (default: 8192)
- `gpuLayers` - Numero layer su GPU (0 = solo CPU)
- `idleTimeoutMinutes` - Minuti prima di stop server automatico
- `llamaServerPath` - Path custom a llama-server (null = usa PATH)

## 🐛 Troubleshooting

### "No model found" all'avvio chat

**Soluzione:**
```
1. Vai in Models ([2])
2. Controlla che ci sia almeno un modello
3. Se non c'è: aggiungi con [l] o [i]
4. Torna a Main Menu e riprova Chat
```

### "llama-server not found"

**Soluzione:**
```
1. Installa llama.cpp e llama-server
2. Oppure aggiungi llama-server a PATH
3. Oppure configura path custom in config.json:
   "llamaServerPath": "C:\\path\\to\\llama-server.exe"
```

### Modello caricato ma nessuna risposta

**Verifica:**
```
1. Main Menu → [5] Server
2. Controlla status: deve essere 🟢 Running
3. Leggi ultimi log per errori
4. Se errore "out of memory": riduci ctxSize o gpuLayers
```

### Scan non trova i miei modelli

**Soluzione:**
```
1. Models → [p] per path manuale
2. Copia path completo del file .gguf
3. Incolla e premi Enter
4. Modello aggiunto!
```

### Performance lente su CPU

**Ottimizzazioni:**
```
1. Usa modelli quantizzati Q4 o Q5 (non Q8)
2. Riduci ctxSize in config (es: 4096 invece di 8192)
3. Se hai GPU: aumenta gpuLayers (prova 10, 20, 33)
4. Usa modelli più piccoli (3B invece di 7B)
```

## 📚 Modelli Consigliati

Per iniziare, consiglio questi modelli (piccoli e veloci):

### Per CPU (facili da scaricare):
- **Llama 3.2 3B** - `bartowski/Llama-3.2-3B-Instruct-GGUF`
  - File: `Llama-3.2-3B-Instruct-Q4_K_M.gguf` (~2GB)

- **Qwen 2.5 3B** - `Qwen/Qwen2.5-3B-Instruct-GGUF`
  - File: `qwen2.5-3b-instruct-q4_k_m.gguf` (~2GB)

- **Phi 3.5** - `microsoft/Phi-3.5-mini-instruct-gguf`
  - File: `Phi-3.5-mini-instruct-q4.gguf` (~2.4GB)

### Per GPU (più potenti):
- **Llama 3.1 8B** - `bartowski/Meta-Llama-3.1-8B-Instruct-GGUF`
  - File: `Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf` (~5.7GB)

- **Mistral 7B** - `TheBloke/Mistral-7B-Instruct-v0.2-GGUF`
  - File: `mistral-7b-instruct-v0.2.Q5_K_M.gguf` (~5GB)

## 🎯 Tips & Tricks

1. **Usa modelli Q4/Q5 per bilanciare velocità e qualità**
2. **Chiudi altre app pesanti prima di usare modelli grandi**
3. **Il primo messaggio è più lento (caricamento modello)**
4. **Usa /clear se chat diventa lenta (troppi messaggi)**
5. **Premi ESC per tornare sempre al menu (non serve chiudere)**
6. **Monitor server in [5] per vedere cosa succede**
7. **Modelli local (💾) non vengono cancellati da remove**

## 🔗 Link Utili

- **Hugging Face GGUF Models:** https://huggingface.co/models?library=gguf
- **llama.cpp GitHub:** https://github.com/ggerganov/llama.cpp
- **GGUF Formats:** Q4_K_M = buono, Q5_K_M = migliore, Q8 = massima qualità

---

**Buon divertimento con Local CLI! 🚀**
