# Test Project

Questo è un progetto di esempio per testare VibeCli.

## Come testare

1. Vai nella directory del progetto di test:
   ```bash
   cd examples/test-project
   ```

2. Esegui VibeCli dalla directory principale:
   ```bash
   ../../bin/vibe setup
   ```

3. Dopo il setup, prova i comandi:
   ```bash
   ../../bin/vibe chat -m "Analizza questo progetto"
   ../../bin/vibe context --show
   ../../bin/vibe tools --list
   ```

## Struttura del progetto

- `src/` - Codice sorgente di esempio
- `package.json` - Configurazione del progetto
- `.vibe/` - Context locale di VibeCli (creato automaticamente)
