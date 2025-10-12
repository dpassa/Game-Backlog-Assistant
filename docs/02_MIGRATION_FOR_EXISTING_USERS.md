# Quick Migration Guide per Utenti Esistenti

## TL;DR - 3 Passi Rapidi

Se hai **già giochi nel database Notion**, segui questi 3 semplici passi:

### 1. Aggiungi 2 Campi a Notion (2 minuti)

Apri il tuo database Notion e aggiungi:

- ✅ **"External ID"** (tipo: Text)
- ✅ **"Store Name"** (tipo: Text)

**Come fare:**
1. Click sul "+" in alto a destra nella tabella
2. Seleziona "Text"
3. Nomina esattamente: "External ID"
4. Ripeti per "Store Name"

---

### 2. Esegui lo Script (Una Volta)

```bash
cd "d:\Projects\Game-Backlog-Assistant"
python main.py
```

**Cosa succede:**
- ✅ Trova i tuoi giochi esistenti per titolo
- ✅ Li aggiorna con `external_id` e `store_name`
- ✅ Non crea duplicati

**Output Atteso:**
```
[1/100] --- Adding Portal™ ---
✓ Updated existing entry with external_id=400, store=Steam
⊘ Game 'Portal™' already exists, updated with external_id (skipped)

[2/100] --- Adding Dota 2 ---
✓ Updated existing entry with external_id=570, store=Steam
⊘ Game 'Dota 2' already exists, updated with external_id (skipped)

...

Added: 0 | Skipped: 100 | Errors: 0
📝 All 100 existing entries updated with external_id
```

---

### 3. Verifica in Notion (30 secondi)

Apri un gioco qualsiasi e verifica che abbia:
- **External ID:** `570` (esempio: Dota 2)
- **Store Name:** `Steam`

✅ **Fatto!** I tuoi giochi sono ora aggiornati.

---

## Cosa Cambia per Te

### Prima dell'Aggiornamento
```
Database Notion:
├── Portal™ (solo titolo)
├── Dota 2 (solo titolo)
└── ...

Duplicate Check: Controllo per titolo (~80% affidabile)
```

### Dopo l'Aggiornamento
```
Database Notion:
├── Portal™ (titolo + external_id=400 + store=Steam) ✓
├── Dota 2 (titolo + external_id=570 + store=Steam) ✓
└── ...

Duplicate Check: Controllo per external_id (100% affidabile)
```

---

## FAQ Rapide

### Q: Perderò i miei dati?
**A:** NO! Status, rating, note rimangono intatti. Aggiungiamo solo 2 campi.

### Q: Creerà duplicati?
**A:** NO! Il sistema trova i giochi esistenti e li aggiorna, non li duplica.

### Q: Devo cancellare i giochi esistenti?
**A:** NO! Il sistema li aggiorna automaticamente.

### Q: Quanto tempo ci vuole?
**A:** ~2-5 minuti per aggiungere i campi + 5-10 minuti per l'esecuzione.

### Q: Posso testare prima?
**A:** SÌ! Il sistema non sovrascrive nulla, solo aggiunge i 2 nuovi campi.

---

## Benefici Immediati

✅ **UTF-8:** Niente più crash su giochi come "Portal™", "Pokémon"
✅ **Cache:** Seconda esecuzione 30x più veloce (30s invece di 15min)
✅ **Duplicati:** 100% accuratezza (non più titoli simili)
✅ **Rate Limiting:** Retry automatico con exponential backoff

---

## Supporto

- **Dettagli completi:** [TRANSITIONAL_MIGRATION.md](TRANSITIONAL_MIGRATION.md)
- **Guida completa:** [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- **Documentazione tecnica:** [FIXES_DOCUMENTATION.md](FIXES_DOCUMENTATION.md)

---

## Checklist Veloce

- [ ] Aggiunti campi "External ID" e "Store Name" a Notion
- [ ] Eseguito `python main.py` una volta
- [ ] Verificato che i giochi hanno external_id popolato
- [ ] Tutto funziona! 🎉

**Benvenuto alla nuova versione migliorata!** 🚀
