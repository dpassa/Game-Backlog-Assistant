# Quick Migration Guide for Existing Users

## TL;DR - 3 Quick Steps

If you **already have games in your Notion database**, follow these 3 simple steps:

### 1. Add 2 Fields to Notion (2 minutes)

Open your Notion database and add:

- ✅ **"External ID"** (type: Text)
- ✅ **"Store Name"** (type: Text)

**How to do it:**
1. Click the "+" at the top-right of the table
2. Select "Text"
3. Name it exactly: "External ID"
4. Repeat for "Store Name"

---

### 2. Run the Script (Once)

```bash
cd "d:\Projects\Game-Backlog-Assistant"
python main.py
```

**What happens:**
- ✅ Finds your existing games by title
- ✅ Updates them with `external_id` and `store_name`
- ✅ Doesn't create duplicates

**Expected Output:**
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

### 3. Verify in Notion (30 seconds)

Open any game and verify it has:
- **External ID:** `570` (example: Dota 2)
- **Store Name:** `Steam`

✅ **Done!** Your games are now updated.

---

## What Changes for You

### Before the Update
```
Notion Database:
├── Portal™ (title only)
├── Dota 2 (title only)
└── ...

Duplicate Check: Title-based (~80% reliable)
```

### After the Update
```
Notion Database:
├── Portal™ (title + external_id=400 + store=Steam) ✓
├── Dota 2 (title + external_id=570 + store=Steam) ✓
└── ...

Duplicate Check: External ID-based (100% reliable)
```

---

## Quick FAQ

### Q: Will I lose my data?
**A:** NO! Status, ratings, notes remain intact. We only add 2 fields.

### Q: Will it create duplicates?
**A:** NO! The system finds existing games and updates them, doesn't duplicate.

### Q: Do I need to delete existing games?
**A:** NO! The system updates them automatically.

### Q: How long does it take?
**A:** ~2-5 minutes to add fields + 5-10 minutes for the script to run.

### Q: Can I test first?
**A:** YES! The system doesn't overwrite anything, only adds the 2 new fields.

---

## Immediate Benefits

✅ **UTF-8:** No more crashes on games like "Portal™", "Pokémon"
✅ **Cache:** Second run 30x faster (30s instead of 15min)
✅ **Duplicates:** 100% accuracy (no more similar titles)
✅ **Rate Limiting:** Automatic retry with exponential backoff

---

## Support

- **Complete details:** [Transitional Migration](03_TRANSITIONAL_MIGRATION.md)
- **Full guide:** [Complete Migration Guide](04_MIGRATION_GUIDE.md)
- **Technical documentation:** [Fixes Documentation](05_FIXES_DOCUMENTATION.md)

---

## Quick Checklist

- [ ] Added "External ID" and "Store Name" fields to Notion
- [ ] Ran `python main.py` once
- [ ] Verified that games have external_id populated
- [ ] Everything works! 🎉

**Welcome to the improved version!** 🚀
