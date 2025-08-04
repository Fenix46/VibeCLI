# 🚀 Quick Publish Guide

## ⚡ Pubblicazione Rapida (5 minuti)

### 1. **Login npm**
```bash
npm login
# Inserisci username, password, email e OTP se richiesto
```

### 2. **Pubblica**
```bash
# Metodo automatico (consigliato)
./scripts/publish.sh

# Oppure manuale
npm run build
npm publish
```

### 3. **Verifica**
```bash
# Controlla su npm
open https://www.npmjs.com/package/@vibecli/core

# Testa installazione
npm install -g @vibecli/core
vibe --version
```

## 📋 **Checklist Rapida**

- [ ] Account npm creato e verificato
- [ ] Login effettuato (`npm whoami`)
- [ ] Build funziona (`npm run build`)
- [ ] Package testato (`./test-installation.sh`)
- [ ] Pronto per pubblicare!

## 🎯 **Comandi Post-Pubblicazione**

Gli utenti potranno installare VibeCli con:

```bash
# Installazione globale
npm install -g @vibecli/core

# Setup e uso
vibe setup
vibe chat

# Uso temporaneo senza installazione
npx @vibecli/core setup
npx @vibecli/core chat
```

## 🔄 **Aggiornamenti Futuri**

```bash
# Incrementa versione
npm version patch  # 1.0.0 -> 1.0.1
npm version minor  # 1.0.0 -> 1.1.0
npm version major  # 1.0.0 -> 2.0.0

# Pubblica aggiornamento
npm publish
```

---

🎉 **Fatto!** VibeCli sarà disponibile globalmente su npm!
