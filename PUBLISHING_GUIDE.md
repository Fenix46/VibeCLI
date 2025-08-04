# 📦 Guida alla Pubblicazione di VibeCli

## 🎯 **Preparazione Pre-Pubblicazione**

### 1. **Account npm**
```bash
# Crea un account su https://www.npmjs.com se non ce l'hai
# Poi effettua il login
npm login
```

### 2. **Verifica Configurazione**
```bash
# Controlla che tutto sia configurato correttamente
npm whoami
npm config list
```

## 🚀 **Processo di Pubblicazione**

### Metodo 1: Script Automatico (Consigliato)
```bash
# Usa lo script di pubblicazione automatico
./scripts/publish.sh
```

### Metodo 2: Pubblicazione Manuale
```bash
# 1. Pulisci e compila
rm -rf dist/
npm run build

# 2. Verifica il contenuto del package
npm pack --dry-run

# 3. Pubblica
npm publish
```

## 📋 **Checklist Pre-Pubblicazione**

- [ ] **Nome Package**: `@vibecli/core` (disponibile su npm)
- [ ] **Versione**: Aggiornata correttamente nel `package.json`
- [ ] **Build**: Progetto compila senza errori
- [ ] **Files**: Solo i file necessari inclusi (vedi `.npmignore`)
- [ ] **License**: File LICENSE presente
- [ ] **README**: Documentazione completa e aggiornata
- [ ] **Repository**: URL GitHub configurato
- [ ] **Keywords**: Tag appropriati per la ricerca

## 🔧 **Configurazione Package.json**

Il package è già configurato con:
```json
{
  "name": "@vibecli/core",
  "version": "1.0.0",
  "bin": {
    "vibe": "./bin/vibe"
  },
  "files": [
    "dist/**/*",
    "bin/**/*",
    "README.md",
    "LICENSE"
  ],
  "publishConfig": {
    "access": "public"
  }
}
```

## 🌐 **Dopo la Pubblicazione**

### Verifica Installazione
```bash
# Installa il tuo package
npm install -g @vibecli/core

# Testa che funzioni
vibe --version
vibe --help
```

### Promuovi il Package
1. **GitHub**: Crea un repository e pusha il codice
2. **README**: Aggiungi badge npm
3. **Social**: Condividi sui social media
4. **Community**: Posta su Reddit, Discord, ecc.

## 📈 **Gestione Versioni**

### Semantic Versioning
```bash
# Patch (1.0.0 -> 1.0.1) - bug fixes
npm version patch

# Minor (1.0.0 -> 1.1.0) - nuove features
npm version minor

# Major (1.0.0 -> 2.0.0) - breaking changes
npm version major
```

### Pubblicazione Aggiornamenti
```bash
# Dopo aver aggiornato la versione
npm run build
npm publish
```

## 🏷️ **Tag e Release**

### Creare Tag Git
```bash
# Crea tag per la versione
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### GitHub Release
1. Vai su GitHub → Releases
2. Crea una nuova release
3. Usa il tag creato
4. Aggiungi note di rilascio

## 📊 **Monitoraggio**

### Statistiche npm
- Visita: https://www.npmjs.com/package/@vibecli/core
- Monitora download e feedback

### Analytics
```bash
# Vedi statistiche download
npm view @vibecli/core

# Vedi versioni pubblicate
npm view @vibecli/core versions --json
```

## 🛠️ **Manutenzione**

### Aggiornamenti Regolari
- Aggiorna dipendenze
- Correggi bug segnalati
- Aggiungi nuove features
- Mantieni documentazione aggiornata

### Supporto Community
- Rispondi alle issues su GitHub
- Aiuta gli utenti con problemi
- Considera i feedback per miglioramenti

## 🎯 **Comandi di Installazione per gli Utenti**

Dopo la pubblicazione, gli utenti potranno installare VibeCli con:

```bash
# Installazione globale
npm install -g @vibecli/core

# Uso con npx (senza installazione)
npx @vibecli/core setup
npx @vibecli/core chat

# Installazione in progetto locale
npm install @vibecli/core
```

## 🏆 **Best Practices**

1. **Testa sempre** prima di pubblicare
2. **Documenta** ogni release
3. **Mantieni** compatibilità backward quando possibile
4. **Rispondi** rapidamente ai bug reports
5. **Pianifica** le features future

## 🚨 **Troubleshooting**

### Errori Comuni
```bash
# Errore: package già esiste
# Soluzione: cambia nome o versione

# Errore: non autenticato
npm login

# Errore: permessi
# Verifica di essere owner del package
```

### Recovery
```bash
# Unpublish (solo entro 24h dalla pubblicazione)
npm unpublish @vibecli/core@1.0.0

# Deprecate una versione
npm deprecate @vibecli/core@1.0.0 "Versione deprecata, usa 1.0.1"
```

---

🎉 **Congratulazioni!** Una volta pubblicato, VibeCli sarà disponibile globalmente per tutti gli sviluppatori!
