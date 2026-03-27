# Privacy Guide

## What this tool stores

`sss` builds a local search index from your Claude Code session files:

| File | Contains | Size |
|------|----------|------|
| `session-index.db` | Full text of all conversations | ~200–500 MB |
| `session-embeddings.npy` | Numeric vectors of conversation content | ~50–100 MB |
| `session-rowids.npy` | Index mapping | small |
| `session-meta.pkl` | Session metadata (timestamps, topics) | small |

**All data is stored locally on your machine.** Nothing is sent to any server.

## What NOT to commit to Git

The `.gitignore` in this repo already excludes all index files. Never commit:

- `session-index.db`
- `*.npy`, `*.pkl`
- `~/.claude/projects/` (your raw session JSONL files)

Your sessions contain your full conversation history including potentially:
- Internal project details
- API keys briefly shown in conversations
- Client information
- Business strategies

## If you fork this repo

Make sure your fork's `.gitignore` is intact before adding files. Run:

```bash
git status
```

and confirm no `.db`, `.npy`, `.pkl`, or `.jsonl` files appear before committing.

## Index location

By default: `~/.claude/session-index.db`

To use a different location (e.g., encrypted volume):

```bash
export SSS_DATA_DIR="/Volumes/encrypted/sss-data"
sss --index
```

## Deleting your index

```bash
rm ~/.claude/session-index.db
rm ~/.claude/session-embeddings.npy
rm ~/.claude/session-rowids.npy
rm ~/.claude/session-meta.pkl
```

This removes the search index but not your original session files (which Claude Code manages).
