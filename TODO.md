# TODO List - Local CLI

## 🔴 **CRITICHE (Alta Priorità)**

### 1. SHA256 Verification sui Download Modelli
- **Problema**: I modelli scaricati non vengono verificati per integrità
- **Impatto**: File corrotti possono essere usati silenziosamente, rischio malware
- **File**: `src/hf/client.ts:67-118`
- **Soluzione**:
  - Calcolare SHA256 dopo download
  - Confrontare con hash da Hugging Face API
  - Rimuovere file se hash non corrisponde

### 2. Context Overflow nell'Agent Loop
- **Problema**: L'agent accumula messaggi senza limite nel loop
- **Impatto**: Context window può saturarsi, agent perde contesto iniziale, loop infinito
- **File**: `src/agent/engine.ts:43-110`
- **Soluzione**:
  - Implementare sliding window per mantenere ultimi N messaggi
  - Summarize messaggi vecchi prima di rimuoverli
  - Alert quando si avvicina al limite context

### 3. Path Traversal Validation
- **Problema**: Il check `startsWith()` può essere bypassato su Windows
- **Impatto**: Accesso a file di sistema sensibili
- **File**: `src/agent/engine.ts:183-191`, `src/agent/patch.ts:40`
- **Soluzione**:
  - Usare `path.normalize()` prima del check
  - Verificare che non ci siano `..` dopo normalizzazione
  - Usare `path.relative()` e verificare che non inizi con `..`

### 4. Diff Parsing Fragile
- **Problema**: Crash su righe vuote, nessun rollback su errore
- **Impatto**: Stato file inconsistente, possibile perdita dati
- **File**: `src/utils/diff.ts:9-43`
- **Soluzione**:
  - Aggiungere check bounds su tutti gli accessi array
  - Implementare transazione con backup/restore
  - Usare libreria diff robusta invece di parser custom

---

## 🟡 **IMPORTANTI (Media Priorità)**

### 5. Task Scheduling Race Conditions
- **Problema**: Due processi `tick` simultanei eseguono task duplicati
- **Impatto**: Task eseguiti multiple volte, spreco risorse
- **File**: `src/tasks/runner.ts:66-80`
- **Soluzione**:
  - Usare file lock durante tickTasks
  - Marcare task come "running" prima di eseguirli
  - Cleanup task "running" stale al boot

### 6. Stream Buffer Unbounded
- **Problema**: Buffer può crescere senza limite su risposte lunghe
- **Impatto**: Out of Memory (OOM)
- **File**: `src/server/llmClient.ts:54`
- **Soluzione**:
  - Limite max buffer size (es: 100MB)
  - Truncate o stream to disk se supera limite
  - Alert utente se risposta troppo lunga

### 7. Error Handling Inconsistente
- **Problema**: Alcuni moduli usano try/catch, altri propagano
- **Impatto**: Crash inaspettati, debug difficile
- **File**: Vari
- **Soluzione**:
  - Definire strategia error handling globale
  - Wrapper per tutte le funzioni async
  - Error boundary a livello CLI

### 8. ID Generation Debole
- **Problema**: `Math.random()` non crittografico nonostante nome "cryptoRandomId"
- **Impatto**: Collisioni possibili, predictable IDs
- **File**: `src/tasks/runner.ts:82`, `src/cli.ts:166`
- **Soluzione**:
  - Usare `crypto.randomUUID()` nativo Node.js
  - Oppure `crypto.randomBytes(16).toString('hex')`

---

## 🟢 **NICE TO HAVE (Bassa Priorità)**

### 9. Refactor cli.ts Monolitico
- **Problema**: 211 righe con troppa logica inline
- **Impatto**: Difficile da mantenere e testare
- **File**: `src/cli.ts`
- **Soluzione**:
  - Estrarre command handlers in `src/commands/`
  - Ogni comando in file separato
  - cli.ts diventa solo routing

### 10. Test Coverage
- **Problema**: Solo 2 test nel progetto (<5% coverage)
- **Impatto**: Regressioni non rilevate
- **File**: `tests/`
- **Soluzione**:
  - Aggiungere test per funzioni critiche:
    - Lock atomici
    - Backup/restore
    - Command parsing
    - Diff application
  - Target: 60% coverage

### 11. Graceful Shutdown
- **Problema**: Mancano signal handlers (SIGINT, SIGTERM)
- **Impatto**: Server può rimanere zombie, cleanup non eseguito
- **File**: `src/cli.ts`
- **Soluzione**:
  - Registrare handler per SIGINT, SIGTERM
  - Cleanup: stop server, save state, close connections
  - Timeout per force exit

### 12. Session Storage Retention
- **Problema**: Sessioni accumulate senza limiti
- **Impatto**: Può riempire disco
- **File**: `src/utils/sessions.ts`
- **Soluzione**:
  - Retention policy: cancella sessioni più vecchie di N giorni
  - Limite max sessioni: es. 1000
  - Comando per cleanup manuale

---

## 📊 **METRICHE PROBLEMATICHE**

| Categoria | Quantità |
|-----------|----------|
| Time Bombs critiche | 4 |
| Violazioni architetturali gravi | 3 |
| Codice duplicato | ~150 righe |
| Security issues | 3 |
| Test coverage | <5% |
| File senza error handling | 8 |

---

## 🎯 **PRIORITÀ ESECUZIONE**

1. **Week 1**: Critiche #1, #2, #3, #4
2. **Week 2**: Importanti #5, #6, #7, #8
3. **Week 3**: Nice to Have #9, #10, #11, #12

---

## ✅ **COMPLETATE**

- [x] Lock atomici con PID per ensureServer()
- [x] Rimuovere shell: true da RUN_CMD e sanitizzare comandi
- [x] Aggiungere backup automatici per config/registry/tasks
- [x] Aggiungere timeout a fetch/stream LLM calls
- [x] Unificare defaultModelId in config.json (eliminare duplicazione)
- [x] Fix file descriptor leak nel server spawn
- [x] Interfaccia TUI con chat interattiva
- [x] Sistema comandi slash (/help, /clear, /model, etc.)

---

## 📝 **NOTE**

- Progetto giovane (2 commit) con buona base architettturale
- Pattern inconsistenti dovuti a sviluppo rapido
- Focus su stabilità e sicurezza prima di nuove feature
- Considerare refactor agent protocol per estensibilità
